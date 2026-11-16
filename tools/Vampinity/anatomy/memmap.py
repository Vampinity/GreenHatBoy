#!/usr/bin/env python3
"""Who holds the memory at the worst moment of a load, one row per start.

For every stderr.log under FOLDER it takes the memory census lines (EDEN_MEM_CENSUS, every 2 s) that come
after the route's load marker ("wait_met line=N"), and prints:
  - the census line with the lowest largest free block (the "low"), its time and target= (render targets);
  - the pool line of that same census (EDEN_MEM_CENSUS_POOL): out, guest, reserve, jit, tables, heap,
    GPU blocks, GPU blocks used (vused), slack;
  - the highest target= after the load and when;
  - the longest reclaim stretch (EDEN_UP_WAIT_RECLAIM totals) with its unserved count, and how many
    stretches reached 10 s.
All values are MiB, times are app seconds.

usage: memmap.py FOLDER [--glob PATTERN] [--load-line N] [--json]
  FOLDER         a batch folder, or a folder of run folders
  --glob         which stderr logs to read, relative to FOLDER (default: every stderr.log and
                 stderr.log.gz below FOLDER)
  --load-line    the route script line whose wait_met marks the load (default 92, the field load on
                 the field-to-past-field route)
  --json         print the same numbers as one JSON object on stdout instead of the text
"""
import re, sys, glob, os, gzip, argparse, json

ap = argparse.ArgumentParser()
ap.add_argument('folder')
ap.add_argument('--glob', default=None)
ap.add_argument('--load-line', type=int, default=92)
ap.add_argument('--json', action='store_true', help='print the same numbers as one JSON object on stdout instead of the text')
a = ap.parse_args()
base = a.folder
if a.glob:
    runs = sorted(glob.glob(os.path.join(base, a.glob), recursive=True))
else:
    runs = sorted(glob.glob(os.path.join(base, '**', 'stderr.log'), recursive=True) +
                  glob.glob(os.path.join(base, '**', 'stderr.log.gz'), recursive=True))
marker = 'wait_met line=%d' % a.load_line


def read_text(path):
    if path.endswith('.gz'):
        with gzip.open(path, 'rt', errors='replace') as f:
            return f.read()
    with open(path, errors='replace') as f:
        return f.read()


cre = re.compile(r'^EDEN_MEM_CENSUS n=(\d+) why=\S+ t_s=([\d.]+) largest=(\d+) .*? target=(\d+)')
pre = re.compile(r'^EDEN_MEM_CENSUS_POOL n=(\d+) out=(\d+) guest=(\d+) reserve=(\d+) jit=(\d+) tables=(\d+) heap=(\d+) .*?vma_blocks=(\d+) vma_used=(\d+) vma_slack=(\d+)')
wre = re.compile(r'EDEN_UP_WAIT_RECLAIM totals.*?stretch_ms=(\d+).*?unserved=(\d+)')
out = []
if not a.json:
    print('run | after_load_censuses | low (lowest largest) t_s largest target | pool at the low: out guest reserve jit tables heap vblocks vused slack | target max after load (t_s) | max stretch_ms (unserved) n>=10000')
for s in runs:
    d = os.path.dirname(s)
    name = os.path.basename(d)
    lines = read_text(s).split('\n')
    start = None
    for i, l in enumerate(lines):
        if marker in l:
            start = i; break
    cens = {}; pools = {}
    for i, l in enumerate(lines):
        if start is None or i < start: continue
        m = cre.match(l)
        if m: cens[int(m.group(1))] = (float(m.group(2)), int(m.group(3)), int(m.group(4)))
        m = pre.match(l)
        if m: pools[int(m.group(1))] = tuple(int(x) for x in m.groups()[1:])
    stretches = [(int(x), int(y)) for x, y in wre.findall('\n'.join(lines))]
    big = [x for x in stretches if x[0] >= 10000]
    mx = max(stretches) if stretches else None
    row = {'run': name, 'after_load_censuses': len(cens), 'low': None, 'pool': None, 'tmax': None,
           'maxstretch': {'stretch_ms': mx[0], 'unserved': mx[1]} if mx is not None else None, 'n10k': len(big)}
    if not cens:
        if a.json:
            out.append(row); continue
        print(name, '| no census after load |', 'max stretch', mx, 'n10k', len(big)); continue
    # low = lowest largest free block; tie -> first
    pk = min(cens, key=lambda n: (cens[n][1], n))
    tmax = max(cens, key=lambda n: cens[n][2])
    p = pools.get(pk)
    if a.json:
        row['low'] = {'t_s': float('%.1f' % cens[pk][0]), 'largest': cens[pk][1], 'target': cens[pk][2]}
        if p:
            row['pool'] = dict(zip(('out', 'guest', 'reserve', 'jit', 'tables', 'heap', 'vblocks', 'vused', 'slack'), p))
        row['tmax'] = {'target': cens[tmax][2], 't_s': float('%.1f' % cens[tmax][0])}
        out.append(row); continue
    pstr = ('out=%d guest=%d reserve=%d jit=%d tables=%d heap=%d vblocks=%d vused=%d slack=%d' % p) if p else 'no pool line'
    print(name, '|', len(cens), '| t_s=%.1f largest=%d target=%d' % cens[pk], '|', pstr, '| tmax=%d @%.1f' % (cens[tmax][2], cens[tmax][0]), '| maxstretch', mx, 'n10k', len(big))
if a.json:
    print(json.dumps({'runs': out}, indent=1))
