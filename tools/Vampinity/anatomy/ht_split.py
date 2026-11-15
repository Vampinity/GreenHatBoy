#!/usr/bin/env python3
"""Split the GPU-thread hitch trace of one start into three windows: before the load, inside it, after it.

Reads the "Hitch trace: frame N took X ms on the GPU thread; traced Y ms | kind Z ms (...)" lines that
EDEN_UP_HITCH_TRACE=1 writes to eden_log.txt. Only frames of 100 ms or more count.
For each window it prints: long frames, their total ms, the traced (named) ms, the traced share and the
four biggest named kinds.

usage: ht_split.py eden_log.txt[.gz] load_start_app_s load_end_app_s
The two times are app seconds (the [ stamp ] at the start of each eden_log line).
"""
import re, sys, collections, gzip


def open_log(path):
    if path.endswith('.gz'):
        return gzip.open(path, 'rt', errors='replace')
    return open(path, errors='replace')


path = sys.argv[1]; ls = float(sys.argv[2]); le = float(sys.argv[3])
pat = re.compile(r'^\[\s*([\d.]+)\].*Hitch trace: frame (\d+) took ([\d.]+) ms on the GPU thread; traced ([\d.]+) ms(.*)$')
kind = re.compile(r'\| ([a-zA-Z ]+?) ([\d.]+) ms \(')
win = {'before': [0, 0, 0, collections.Counter()], 'load': [0, 0, 0, collections.Counter()], 'after': [0, 0, 0, collections.Counter()]}
for line in open_log(path):
    m = pat.search(line)
    if not m: continue
    t = float(m.group(1)); took = float(m.group(3)); tr = float(m.group(4))
    if took < 100: continue
    w = 'before' if t < ls else ('load' if t <= le else 'after')
    W = win[w]; W[0] += 1; W[1] += took; W[2] += tr
    for k, v in kind.findall(m.group(5)): W[3][k.strip()] += float(v)
for w, (n, took, tr, c) in win.items():
    print(f"{w}: frames={n} took_ms={took:.0f} traced_ms={tr:.0f} traced_share={(tr/took*100 if took else 0):.1f}% top={[(k,round(v)) for k,v in c.most_common(4)]}")
