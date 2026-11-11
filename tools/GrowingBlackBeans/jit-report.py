#!/usr/bin/env python3
"""Where a guest core's time goes inside the JIT: sample-<pid>-<n>-CPUCore_K.bin plus its
-blocks.bin (headless/mkw_native_sample.inc, WriteBlocks).

usage: jit-report.py [--main 0x805dc000] [--top 25] [--disasm 8] sample-...-CPUCore_K.bin [...]

--main: the guest base of module main ("Module main loaded at" in eden_log.txt), to print guest
        pcs as main+offset (Fritchii and Vampinity name sites that way).
For each window: the share of samples in JIT code, in the app (eboot) and elsewhere; the guest
blocks with the most samples; a rough split of the JIT samples by the kind of host instruction
they landed on; and the hottest blocks' host code with samples per instruction. Run where GNU
objdump is (the eps5-build container).
"""
import collections
import os
import re
import struct
import subprocess
import sys
import tempfile

SAMPLE_MAGIC = 0x4d4b5753414d5032
BLOCKS_MAGIC = 0x31534b4c424b574d
PC_MASK = (1 << 56) - 1


def read_samples(path):
    raw = open(path, 'rb').read()
    h = struct.unpack_from('<13Q', raw, 0)
    if h[0] != SAMPLE_MAGIC:
        sys.exit(f'{path}: not a sampler v2 file')
    _, pid, target, count, size, t0, t1, sent, ms, low, high, nstack, nframes = h
    pcs = []
    at = 13 * 8
    for _ in range(count):
        pc, = struct.unpack_from('<Q', raw, at)
        pcs.append(pc)
        at += size
    return pcs, (t0, t1), ms


def read_blocks(path):
    raw = open(path, 'rb').read()
    magic, known, listed, with_code = struct.unpack_from('<4Q', raw, 0)
    if magic != BLOCKS_MAGIC:
        sys.exit(f'{path}: not a blocks file')
    rows = []
    at = 32
    for _ in range(listed):
        entry, size, location, hits, kept = struct.unpack_from('<5Q', raw, at)
        rows.append([entry, size, location, hits, kept, b''])
        at += 40
    for row in rows[:with_code]:
        row[5] = raw[at:at + row[4]]
        at += row[4]
    return known, rows


# Rough kinds of host instructions (AT&T mnemonics from objdump).
CALL_RE = re.compile(r'^call')
JUMP_RE = re.compile(r'^(j[a-z]+|ret)')


def classify(mnemonic, operands):
    if CALL_RE.match(mnemonic):
        return 'call out of JIT code'
    if JUMP_RE.match(mnemonic):
        return 'branch/dispatch'
    if '%xmm' in operands or '%ymm' in operands or '%zmm' in operands:
        return 'float/vector'
    if '(' in operands and not mnemonic.startswith('lea'):
        return 'memory access'
    return 'integer/flags'


def disassemble(code, base):
    with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
        f.write(code)
        name = f.name
    try:
        out = subprocess.run(['objdump', '-D', '-b', 'binary', '-m', 'i386:x86-64',
                              f'--adjust-vma={base:#x}', name],
                             capture_output=True, text=True, check=True).stdout
    finally:
        os.unlink(name)
    rows = []
    for line in out.splitlines():
        m = re.match(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2} )+\s*(\S+)\s*(.*)$', line)
        if m:
            rows.append((int(m.group(1), 16), m.group(2), m.group(3).strip()))
    return rows


def main():
    args = sys.argv[1:]
    main_base, top, disasm_n = None, 25, 8
    for flag in ('--main', '--top', '--disasm'):
        if flag in args:
            i = args.index(flag)
            value = args[i + 1]
            del args[i:i + 2]
            if flag == '--main':
                main_base = int(value, 16)
            elif flag == '--top':
                top = int(value)
            else:
                disasm_n = int(value)
    if not args:
        sys.exit(__doc__)

    def guest(location):
        pc = location & PC_MASK
        if main_base is not None and pc >= main_base:
            return f'main+{pc - main_base:#x}'
        return f'{pc:#x}'

    for path in args:
        blocks_path = path[:-4] + '-blocks.bin'
        if not os.path.exists(blocks_path):
            print(f'{path}: no {os.path.basename(blocks_path)}')
            continue
        pcs, (t0, t1), ms = read_samples(path)
        known, rows = read_blocks(blocks_path)
        n = len(pcs)
        starts = sorted((r[0], k) for k, r in enumerate(rows))
        entries = [s for s, _ in starts]
        import bisect
        owner = []
        for pc in pcs:
            i = bisect.bisect_right(entries, pc) - 1
            k = None
            while i >= 0 and pc - entries[i] < (1 << 20):
                r = rows[starts[i][1]]
                if pc < r[0] + r[1]:
                    k = starts[i][1]
                    break
                i -= 1
            owner.append(k)
        in_jit = sum(1 for k in owner if k is not None)
        in_app = sum(1 for k, pc in zip(owner, pcs) if k is None and t0 <= pc < t1)
        print(f'\n=== {os.path.basename(path)}: {n} samples over {ms / 1000:.1f} s; '
              f'{known} JIT blocks compiled, {len(rows)} with samples')
        print(f'    in JIT code {100 * in_jit / n:.1f}%, in the app (eboot) {100 * in_app / n:.1f}%, '
              f'elsewhere (system, kernel waits) {100 * (n - in_jit - in_app) / n:.1f}%')

        by_guest = collections.Counter()
        for k in owner:
            if k is not None:
                by_guest[rows[k][2] & PC_MASK] += 1
        print(f'  -- guest blocks with the most samples (top {top}); share of all samples, cumulative')
        cum = 0
        for pc, c in by_guest.most_common(top):
            cum += c
            print(f'  {100 * c / n:5.1f}%  {100 * cum / n:5.1f}%  {guest(pc)}')

        # Per-instruction samples in the blocks we have code for.
        kinds = collections.Counter()
        per_insn = {}
        covered = 0
        for k, r in enumerate(rows):
            if not r[5]:
                continue
            insns = disassemble(r[5], r[0])
            addrs = [a for a, _, _ in insns]
            counts = collections.Counter()
            for pc, o in zip(pcs, owner):
                if o == k:
                    j = bisect.bisect_right(addrs, pc) - 1
                    if j >= 0:
                        counts[j] += 1
            for j, c in counts.items():
                _, mn, ops = insns[j]
                kinds[classify(mn, ops)] += c
                covered += c
            per_insn[k] = (insns, counts)
        if covered:
            print(f'  -- kind of host instruction the JIT samples landed on ({covered} samples in the '
                  f'{sum(1 for r in rows if r[5])} blocks with code, {100 * covered / max(in_jit, 1):.0f}% of JIT samples)')
            for kind, c in kinds.most_common():
                print(f'  {100 * c / covered:5.1f}%  {kind}')
            print('  (a sample is on the instruction after the one that stalled, roughly: read kinds as a guide)')

        for k in sorted(per_insn, key=lambda k: -rows[k][3])[:disasm_n]:
            insns, counts = per_insn[k]
            r = rows[k]
            print(f'\n  -- block {guest(r[2])} ({100 * r[3] / n:.1f}% of samples, {r[1]} bytes of host code)')
            for j, (a, mn, ops) in enumerate(insns):
                c = counts.get(j, 0)
                mark = f'{c:5d}' if c else '     '
                print(f'  {mark}  {a - r[0]:5x}  {mn:8s} {ops}')


if __name__ == '__main__':
    main()
