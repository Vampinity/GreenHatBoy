#!/usr/bin/env python3
"""Summarise EDEN_GBB_SVCPROF lines (patch 0913) per thread for time segments.
usage: svcprof.py runNN/eden_log.txt S0-S1[:label] [S2-S3[:label] ...]
Per thread and segment: ms/frame in svc and outside, top SVCs by ms/frame, top wait addresses."""
import collections, re, sys
LINE = re.compile(r'^\[\s*([\d.]+)\].*EDEN_GBB_SVCPROF t(\d+) ([\d.]+) ms, (\d+) frames \(([\d.]+) ms/frame\): '
                  r'in svc ([\d.]+) ms \(([\d.]+)/frame\), outside (-?[\d.]+) ms \((-?[\d.]+)/frame\)(.*?) \| waits at(.*) \| signals(.*)$')
CALL = re.compile(r'; (0x[0-9a-f]+) n=(\d+) (\d+)ms \(([\d.]+)/frame, max ([\d.]+)\)')
NAMES = {'0x34': 'WaitForAddress', '0x35': 'SignalToAddress', '0x0b': 'SleepThread', '0x1a': 'ArbitrateLock',
         '0x1b': 'ArbitrateUnlock', '0x1c': 'WaitProcessWideKey', '0x1d': 'SignalProcessWideKey',
         '0x18': 'WaitSynchronization', '0x21': 'SendSyncRequest', '0x13': 'MapSharedMemory', '0xf3': 'OoT poll'}
path = sys.argv[1]
segs = []
for a in sys.argv[2:]:
    rng, _, label = a.partition(':')
    s0, s1 = (float(x) for x in rng.split('-'))
    segs.append((s0, s1, label or rng))
data = collections.defaultdict(lambda: collections.defaultdict(lambda: {'wall': 0, 'frames': 0, 'in': 0, 'out': 0, 'calls': collections.Counter(), 'waits': collections.Counter()}))
for line in open(path, errors='replace'):
    m = LINE.match(line)
    if not m:
        continue
    t = float(m.group(1)); tid = int(m.group(2))
    for s0, s1, label in segs:
        if s0 <= t < s1:
            d = data[tid][label]
            d['wall'] += float(m.group(3)); d['frames'] += int(m.group(4))
            d['in'] += float(m.group(6)); d['out'] += float(m.group(8))
            for c in CALL.finditer(m.group(10)):
                d['calls'][c.group(1)] += float(c.group(3))
            for w in re.finditer(r' (0x[0-9a-f]+)=(\d+)ms', m.group(11)):
                d['waits'][w.group(1)] += float(w.group(2))
for tid in sorted(data):
    print(f'== t{tid}')
    for s0, s1, label in segs:
        d = data[tid].get(label)
        if not d or not d['frames']:
            continue
        f = d['frames']
        print(f"  {label:10s} {f:5d} frames, {d['wall']/f:5.1f} ms/frame: in svc {d['in']/f:5.1f}, outside {d['out']/f:5.1f} | " +
              ', '.join(f"{NAMES.get(c, c)} {ms/f:.1f}" for c, ms in d['calls'].most_common(5)) +
              ' | waits ' + ', '.join(f"{a} {ms/f:.1f}" for a, ms in d['waits'].most_common(3)))
