#!/usr/bin/env python3
"""Per-frame budget from one start's eden_log.txt: frame, present-blocked ('nx2:vi2 5 s' lines), back idle /
front waited / ring words ('GPU split per second' lines). It also collects reader list-copy wait lines
('#1094') but does not print them.

One row per 'GPU split per second' line in the window, matched to the 'nx2:vi2 5 s' lines of the 10 s
before it. game = frame minus present-blocked. back_busy and back_idle are ms per frame of the back
(recorder) thread, front_waited is ms per frame the front (reader) stood waiting for the back, words/f is
ring words per frame. The last line is the mean over all rows.

usage: frame_split.py eden_log.txt[.gz] t0 t1 [max_frame_ms] [--json]
  t0 t1          window in app seconds
  max_frame_ms   leave out rows whose mean frame is above this (to drop hitchy stretches)
  --json         print the same numbers as one JSON object on stdout instead of the text
"""
import re, sys, gzip, json


def open_log(path):
    if path.endswith('.gz'):
        return gzip.open(path, 'rt', errors='replace')
    return open(path, errors='replace')


as_json = '--json' in sys.argv[1:]
args = [x for x in sys.argv[1:] if x != '--json']
path, t0, t1 = args[0], float(args[1]), float(args[2])
maxf = float(args[3]) if len(args) > 3 else 1e9
vi, sp, lc = [], [], []
for l in open_log(path):
    m = re.match(r'\[\s*([0-9.]+)\]', l)
    if not m:
        continue
    t = float(m.group(1))
    if 'nx2:vi2 5 s:' in l:
        a = re.search(r'([0-9]+) frames, ([0-9.]+) fps, mean ([0-9.]+) ms.*fence ([0-9.]+) ms', l)
        if a:
            vi.append((t, int(a.group(1)), float(a.group(3)), float(a.group(4))))
    elif 'GPU split per second:' in l:
        a = re.search(r'back idle ([0-9.]+) ms, ([0-9]+) ring words, front waited ([0-9.]+) ms', l)
        if a:
            sp.append((t, float(a.group(1)), int(a.group(2)), float(a.group(3))))
    elif 'copy_wait' in l or ('#1094' in l and 'copy' in l):
        a = re.search(r'copy_waits[= ]([0-9]+).*?copy_wait_ns[= ]([0-9]+)', l)
        if a:
            lc.append((t, int(a.group(1)), int(a.group(2))))
rows = []
for t, bi, words, fw in sp:
    if not (t0 <= t <= t1):
        continue
    sel = [v for v in vi if t - 10.5 < v[0] <= t + 0.5]
    if not sel:
        continue
    frames = sum(v[1] for v in sel)
    frame = sum(v[1] * v[2] for v in sel) / frames
    fence = sum(v[1] * v[3] for v in sel) / frames
    if frame > maxf:
        continue
    fps = 1000.0 / frame
    rows.append((t, frame, fence, (1000 - bi) / fps, bi / fps, fw / fps, words / fps))
names = ('frame', 'blocked', 'game', 'back_busy', 'back_idle', 'front_waited', 'words_per_frame')


def as_dict(vals):
    """The printed numbers, rounded the way the text rounds them: ms to 0.1, words to whole words."""
    d = {k: float('%.1f' % v) for k, v in zip(names, vals)}
    d['words_per_frame'] = int('%.0f' % vals[-1])
    return d


out = {'rows': [], 'mean': None}
for r in rows:
    if as_json:
        out['rows'].append(dict({'t': float('%.1f' % r[0])}, **as_dict((r[1], r[2], r[1] - r[2], r[3], r[4], r[5], r[6]))))
        continue
    print("t=%6.1f frame=%5.1f blocked=%5.1f game=%5.1f back_busy=%5.1f back_idle=%5.1f front_waited=%5.1f words/f=%7.0f" %
          (r[0], r[1], r[2], r[1] - r[2], r[3], r[4], r[5], r[6]))
if rows:
    n = len(rows)
    avg = [sum(r[i] for r in rows) / n for i in range(1, 7)]
    if as_json:
        out['mean'] = dict({'n': n}, **as_dict((avg[0], avg[1], avg[0] - avg[1], avg[2], avg[3], avg[4], avg[5])))
    else:
        print("MEAN n=%d frame=%.1f blocked=%.1f game=%.1f back_busy=%.1f back_idle=%.1f front_waited=%.1f words/f=%.0f" %
              (n, avg[0], avg[1], avg[0] - avg[1], avg[2], avg[3], avg[4], avg[5]))
if as_json:
    print(json.dumps(out, indent=1))
