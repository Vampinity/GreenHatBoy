#!/usr/bin/env python3
"""Per guest thread: running time per frame (0913, outside SVCs) split into emulator work (0917
EDEN_GBB_COST lines) and the rest (translated game code + preemption), per time segment.
usage: costprof.py runNN/eden_log.txt S0-S1:label [S2-S3:label ...]"""
import collections, re, sys
PROF = re.compile(r'^\[\s*([\d.]+)\].*EDEN_GBB_SVCPROF t(\d+) [\d.]+ ms, (\d+) frames .*?outside (-?[\d.]+) ms \((-?[\d.]+)/frame\)')
COST = re.compile(r'^\[\s*([\d.]+)\].*EDEN_GBB_COST t(\d+) ms per frame: (.*)$')
PART = re.compile(r'([a-zA-Z ]+?) ([\d.]+)/frame \((\d+) calls\)')
segs = []
for a in sys.argv[2:]:
    rng, _, label = a.partition(':'); s0, s1 = (float(x) for x in rng.split('-')); segs.append((s0, s1, label))
def seg_of(t):
    for s0, s1, l in segs:
        if s0 <= t < s1: return l
out = collections.defaultdict(lambda: collections.defaultdict(lambda: {'n': 0, 'outside': 0.0, 'cost': collections.Counter(), 'calls': collections.Counter()}))
for line in open(sys.argv[1], errors='replace'):
    m = PROF.match(line)
    if m:
        l = seg_of(float(m.group(1)))
        if l: d = out[int(m.group(2))][l]; d['n'] += 1; d['outside'] += float(m.group(5))
        continue
    m = COST.match(line)
    if m:
        l = seg_of(float(m.group(1)))
        if not l: continue
        d = out[int(m.group(2))][l]
        for name, ms, calls in PART.findall(m.group(3)):
            d['cost'][name.strip()] += float(ms); d['calls'][name.strip()] += int(calls)
for tid in sorted(out):
    print(f'== t{tid}')
    for s0, s1, l in segs:
        d = out[tid].get(l)
        if not d or not d['n']: continue
        n = d['n']; outside = d['outside'] / n
        cost = {k: v / n for k, v in d['cost'].items()}
        emu = cost.get('guest writes to GPU pages', 0) + cost.get('guest reads of GPU pages', 0) + cost.get('JIT compile', 0)
        print(f"  {l:9s} running {outside:5.2f} ms/frame | " + '; '.join(f"{k} {v:.2f}" for k, v in cost.items()) +
              f" | GPU-page callbacks + compile ≈ {emu:.2f} ({100*emu/outside if outside else 0:.0f}%)")
