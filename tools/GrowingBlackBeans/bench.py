#!/usr/bin/env python3
"""Benchmark summary from the 5 s game-frame lines (patch 9997, "nx2:vi2 5 s:").

usage: bench.py runNN [runMM ...]            all windows, one row each
       bench.py runNN:S0-S1:W0-W1 [...]      averages for a standing segment S0-S1 and a walking
                                             segment W0-W1 (seconds of the eden_log clock)
"""
import re
import statistics as st
import sys

LINE = re.compile(r'^\[\s*([\d.]+)\].*nx2:vi2 5 s: (\d+) frames, ([\d.]+) fps, mean ([\d.]+) ms, '
                  r'1% low ([\d.]+) ms, worst ([\d.]+) ms, fence ([\d.]+) ms')


def load(run):
    rows = []
    for line in open(f'{run}/eden_log.txt', errors='replace'):
        m = LINE.search(line)
        if m:
            rows.append(tuple(float(x) for x in m.groups()))
    return rows


def summary(rows, label):
    if not rows:
        print(f'  {label}: no windows')
        return
    fps = [r[2] for r in rows]
    print(f'  {label}: {len(rows)} windows, fps {st.mean(fps):5.1f} (min {min(fps):4.1f}), '
          f'frame {st.mean(r[3] for r in rows):5.1f} ms, 1% low {st.mean(r[4] for r in rows):5.1f} ms, '
          f'worst {max(r[5] for r in rows):6.1f} ms, fence {st.mean(r[6] for r in rows):4.1f} ms')


for arg in sys.argv[1:]:
    parts = arg.split(':')
    rows = load(parts[0])
    print(f'== {parts[0]}')
    if len(parts) == 1:
        for t, n, fps, mean, low, worst, fence in rows:
            print(f'  {t:7.1f}s {int(n):4d} frames {fps:5.1f} fps  mean {mean:5.1f}  1%low {low:6.1f}  '
                  f'worst {worst:6.1f}  fence {fence:4.1f}')
        continue
    for label, span in zip(('standing', 'walking'), parts[1:]):
        a, b = (float(x) for x in span.split('-'))
        summary([r for r in rows if a <= r[0] <= b], label)
