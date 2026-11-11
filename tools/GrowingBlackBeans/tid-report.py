#!/usr/bin/env python3
"""Per guest thread: where CPUCore samples went (needs a build whose sampler stores the guest thread
id in the sample's marker word: core patch 0909 + sampler commit 726e41c).

usage: tid-report.py --main 0x80084000 [--threads 86,152,153] sample-...-CPUCore_K.bin [...]

For each window: the guest threads by share of samples; for each of the top threads (or those
given), the share in JIT code / the app / elsewhere and the guest 4 KiB regions with most samples.
"""
import bisect
import collections
import importlib.util
import os
import struct
import sys

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('jr', os.path.join(here, 'jit-report.py'))
jr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jr)

NAMES = {0xf0000: 'zstd decoder', 0x58f000: 'name lookup', 0x590000: 'name lookup', 0x591000: 'name lookup'}


def read(path):
    raw = open(path, 'rb').read()
    h = struct.unpack_from('<13Q', raw, 0)
    _, pid, target, count, size, t0, t1, sent, ms, low, high, nstack, nframes = h
    rows = []
    at = 13 * 8
    for _ in range(count):
        pc, hw, rsp, rbp, marker = struct.unpack_from('<5Q', raw, at)
        rows.append((pc, marker))
        at += size
    return rows, (t0, t1), ms


def main():
    args = sys.argv[1:]
    main_base, wanted = 0, None
    if '--main' in args:
        i = args.index('--main'); main_base = int(args[i + 1], 16); del args[i:i + 2]
    if '--threads' in args:
        i = args.index('--threads'); wanted = [int(x) for x in args[i + 1].split(',')]; del args[i:i + 2]
    for path in args:
        rows, (t0, t1), ms = read(path)
        known, blocks = jr.read_blocks(path[:-4] + '-blocks.bin')
        starts = sorted((b[0], k) for k, b in enumerate(blocks))
        entries = [s for s, _ in starts]

        def owner(pc):
            i = bisect.bisect_right(entries, pc) - 1
            while i >= 0 and pc - entries[i] < (1 << 20):
                b = blocks[starts[i][1]]
                if pc < b[0] + b[1]:
                    return b
                i -= 1
            return None

        n = len(rows)
        by_tid = collections.Counter(t for _, t in rows)
        print(f'\n=== {os.path.basename(path)}: {n} samples over {ms / 1000:.1f} s')
        print('  guest threads by share: ' + ', '.join(f't{t} {100 * c / n:.0f}%' for t, c in by_tid.most_common(8)))
        threads = wanted or [t for t, _ in by_tid.most_common(4)]
        for tid in threads:
            mine = [pc for pc, t in rows if t == tid]
            if not mine:
                continue
            kinds = collections.Counter()
            regions = collections.Counter()
            for pc in mine:
                b = owner(pc)
                if b is not None:
                    kinds['JIT'] += 1
                    g = ((b[2] & jr.PC_MASK) - main_base) & ~0xfff
                    regions[g] += 1
                elif t0 <= pc < t1:
                    kinds['app'] += 1
                else:
                    kinds['elsewhere'] += 1
            m = len(mine)
            print(f'  -- t{tid}: {100 * m / n:.0f}% of the window; ' +
                  ', '.join(f'{k} {100 * c / m:.0f}%' for k, c in kinds.most_common()))
            for g, c in regions.most_common(5):
                print(f'       {100 * c / m:5.1f}%  main+{g:#x} {NAMES.get(g, "")}')


if __name__ == '__main__':
    main()
