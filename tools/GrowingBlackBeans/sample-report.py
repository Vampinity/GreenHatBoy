#!/usr/bin/env python3
"""Summarise stack-sampler windows (logs/sample-<pid>-<n>-<thread>.bin, headless/mkw_native_sample.inc).

usage: sample-report.py llvm-pie.elf sample-*.bin [--folded out.txt] [--jit stderr.log|klog ...]
                        [--timeline SECONDS]

--timeline: also print, for each slice of that many seconds (window time, from its first sample),
the commonest call chains in it, 6 deep, so a stall shows as one chain over consecutive slices.

--jit: files with EDEN_JIT_MEMORY lines (code=<base> of=<size>); pcs in those ranges are counted
as "[JIT: guest code]" instead of "[outside eboot]".

For each file: where the thread was (self, by function), what it was inside (inclusive, by
function, from the frame-pointer chain plus call-checked stack words) and the commonest short
call chains. Run where llvm-symbolizer-18 is (the eps5-build container).
"""
import collections
import re
import shutil
import struct
import subprocess
import sys

HEADER_WORDS = 13
MAGIC = 0x4d4b5753414d5032


def sections(data):
    shoff, = struct.unpack_from('<Q', data, 0x28)
    shentsize, shnum, shstrndx = struct.unpack_from('<HHH', data, 0x3A)
    headers = [struct.unpack_from('<IIQQQQIIQQ', data, shoff + i * shentsize) for i in range(shnum)]
    names_at = headers[shstrndx][4]
    found = {}
    for name, _kind, _flags, address, offset, size, *_ in headers:
        end = data.index(b'\0', names_at + name)
        found[data[names_at + name:end].decode()] = (address, offset, size)
    return found


def after_call(code):
    if len(code) != 8:
        return False
    if code[3] == 0xE8:
        return True
    for length in (2, 3, 4, 6, 7):
        at = code[8 - length:]
        if at[0] == 0xFF and at[1] & 0x38 == 0x10:
            return True
        if length >= 3 and at[0] & 0xF0 == 0x40 and at[1] == 0xFF and at[2] & 0x38 == 0x10:
            return True
    return False


def short(name):
    """Drop argument lists and template arguments so one function is one name."""
    name = re.sub(r'\(.*\)( const)?$', '', name)
    depth, out = 0, []
    for ch in name:
        if ch == '<':
            depth += 1
        elif ch == '>':
            depth = max(depth - 1, 0)
        elif depth == 0:
            out.append(ch)
    name = ''.join(out)
    return name.replace('(anonymous namespace)::', '')


def main():
    args = sys.argv[1:]
    folded_path = None
    jit_ranges = []
    while '--jit' in args:
        i = args.index('--jit')
        for line in open(args[i + 1], errors='replace'):
            m = re.search(r'EDEN_JIT_MEMORY code=([0-9a-f]+) held=\d+ of=(\d+)', line)
            if m:
                jit_ranges.append((int(m[1], 16), int(m[1], 16) + int(m[2])))
        del args[i:i + 2]
    jit_ranges = sorted(set(jit_ranges))
    timeline = None
    if '--timeline' in args:
        i = args.index('--timeline')
        timeline = float(args[i + 1])
        del args[i:i + 2]
    if '--folded' in args:
        i = args.index('--folded')
        folded_path = args[i + 1]
        del args[i:i + 2]
    if len(args) < 2:
        sys.exit(__doc__)
    elf = args[0]
    data = open(elf, 'rb').read()
    text_addr, text_off, text_size = sections(data)['.text']

    windows = []
    for path in args[1:]:
        raw = open(path, 'rb').read()
        h = struct.unpack_from(f'<{HEADER_WORDS}Q', raw, 0)
        if h[0] != MAGIC:
            print(f'{path}: not a sampler v2 file')
            continue
        _, pid, target, count, size, t0, t1, sent, ms, low, high, nstack, nframes = h
        if t1 - t0 != text_size:
            print(f'WARNING {path}: code size 0x{t1 - t0:x} but ELF .text is 0x{text_size:x}: wrong ELF?')
        samples = []
        at = HEADER_WORDS * 8
        for _ in range(count):
            words = struct.unpack_from(f'<{size // 8}Q', raw, at)
            at += size
            pc, _hw, rsp, rbp, _marker = words[:5]
            stack = words[5:5 + nstack]
            frames = [f for f in words[5 + nstack:5 + nstack + nframes] if f]
            samples.append((pc, stack, frames))
        windows.append((path, target, sent, ms, t0, t1, samples))

    # Every address we need a name for, as ELF addresses.
    def to_elf(a, t0, t1):
        return text_addr + (a - t0) if t0 <= a < t1 else None

    def checked(off):
        return 8 <= off <= text_size and after_call(data[text_off + off - 8:text_off + off])

    wanted = set()
    prepared = []
    for path, target, sent, ms, t0, t1, samples in windows:
        rows = []
        for pc, stack, frames in samples:
            leaf = to_elf(pc, t0, t1)
            chain = []  # callers, most recent first: frame pointers, then checked stack words
            for f in frames:
                e = to_elf(f, t0, t1)
                if e is not None and checked(f - t0):
                    chain.append(e - 1)
            scan = []
            for w in stack:
                e = to_elf(w, t0, t1)
                if e is not None and checked(w - t0):
                    scan.append(e - 1)
            rows.append((leaf, chain, scan, pc))
            for a in [leaf] + chain + scan:
                if a is not None:
                    wanted.add(a)
        prepared.append((path, target, sent, ms, rows))

    names = {}
    if wanted:
        symbolizer = shutil.which('llvm-symbolizer-18') or shutil.which('llvm-symbolizer')
        order = sorted(wanted)
        out = subprocess.run([symbolizer, '-e', elf, '-f', '-C', '--no-inlines', '--output-style=GNU'],
                             input='\n'.join(hex(a) for a in order), capture_output=True, text=True,
                             check=True).stdout.splitlines()
        # GNU style: two lines per address (function, file:line).
        for i, a in enumerate(order):
            fn = out[2 * i] if 2 * i < len(out) else '??'
            where = out[2 * i + 1] if 2 * i + 1 < len(out) else ''
            names[a] = (short(fn), where.split('/')[-1])

    def name(a):
        return names.get(a, ('??', ''))[0] if a is not None else '[outside eboot: system or JIT]'

    def outside(pc):
        return '[JIT: guest code]' if any(b <= pc < e for b, e in jit_ranges) else '[system library]'

    folded = collections.Counter()
    for path, target, sent, ms, rows in prepared:
        n = len(rows)
        print(f'\n=== {path.split("/")[-1]}: {n} samples of {sent} signals over {ms / 1000:.1f} s')
        with_chain = sum(1 for _l, c, _s, _p in rows if c)
        kinds = collections.Counter(('host (eboot)' if l is not None else outside(p)) for l, _c, _s, p in rows)
        print('    ' + ', '.join(f'{k} {100 * v / max(n, 1):.1f}%' for k, v in kinds.most_common()))
        print(f'    frame-pointer chain on {100 * with_chain / max(n, 1):.0f}% of samples')
        self_ = collections.Counter()
        self_outside = collections.Counter()
        incl = collections.Counter()
        chains = collections.Counter()
        for leaf, chain, scan, pc in rows:
            callers = chain if chain else scan
            kind = outside(pc) if leaf is None else None
            if leaf is None and kind == '[JIT: guest code]':
                self_[kind] += 1
            elif leaf is None:
                via = name(callers[0]) if callers else '?'
                self_[f'[system] <- {via}'] += 1
                self_outside[via] += 1
            else:
                self_[name(leaf)] += 1
            seen = set()
            for a in [leaf] + chain + scan:
                if a is None:
                    continue
                fn = name(a)
                if fn not in seen:
                    seen.add(fn)
                    incl[fn] += 1
            path_names = [name(leaf) if leaf is not None else kind] + [name(a) for a in callers[:3]]
            chains[' <- '.join(path_names)] += 1
            folded[';'.join(reversed([name(leaf) if leaf is not None else kind] +
                                     [name(a) for a in callers]))] += 1
        print('  -- self (where the thread was), top 30')
        for fn, c in self_.most_common(30):
            print(f'  {100 * c / n:5.1f}%  {fn}')
        print('  -- inclusive (inside this function somewhere), top 40')
        for fn, c in incl.most_common(40):
            print(f'  {100 * c / n:5.1f}%  {fn}')
        print('  -- commonest chains (leaf <- callers), top 25')
        for ch, c in chains.most_common(25):
            print(f'  {100 * c / n:5.1f}%  {ch}')
        if timeline:
            per = max(1, round(timeline * 1000 * n / max(ms, 1)))
            print(f'  -- timeline: {per} samples per {timeline} s slice, top 2 chains each')
            skip = {'void* std::__1::__thread_proxy[abi:ne180100]', 'thread_start'}
            for s in range(0, n, per):
                slice_ = collections.Counter()
                for leaf, chain, scan, pc in rows[s:s + per]:
                    callers = chain if chain else scan
                    kind = outside(pc) if leaf is None else None
                    names_ = [name(leaf) if leaf is not None else kind] + [name(a) for a in callers]
                    names_ = [x for x in names_ if x not in skip][:6]
                    slice_[' <- '.join(names_)] += 1
                m = len(rows[s:s + per])
                top = ' || '.join(f'{100 * c / m:.0f}% {ch}' for ch, c in slice_.most_common(2))
                print(f'  {s * ms / n / 1000:6.2f}s  {top}')
    if folded_path:
        with open(folded_path, 'w') as f:
            for k, v in folded.most_common():
                f.write(f'{k} {v}\n')


if __name__ == '__main__':
    main()
