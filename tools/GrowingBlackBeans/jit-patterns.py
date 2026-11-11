#!/usr/bin/env python3
"""Tally codegen patterns in the hottest JIT blocks (the ones the sampler saved host code for),
weighted by samples. usage: jit-patterns.py sample-...-CPUCore_K.bin [...]
Patterns: guest memory page-table lookups (shr $0xc + table load), flag save (lahf/seto),
flag reload (sahf), redundant reload (sahf with no flag-changing insn since the last lahf),
block-exit dispatch, halt checks; and samples landing inside each kind of sequence."""
import bisect, collections, importlib.util, os, re, sys
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('jr', os.path.join(here, 'jit-report.py'))
jr = importlib.util.module_from_spec(spec); spec.loader.exec_module(jr)
FLAG_WRITERS = re.compile(r'^(add|adc|sub|sbb|cmp|test|and|or|xor|neg|inc|dec|shl|shr|sar|rol|ror|bt|cmc|stc|clc|sahf|popf|imul|mul|lzcnt|tzcnt|popcnt|bsr|bsf|comis|ucomis)')
tot = collections.Counter(); samp = collections.Counter(); insn_total = 0; insn_samp_total = 0
for path in sys.argv[1:]:
    pcs, (t0, t1), ms = jr.read_samples(path)
    known, rows = jr.read_blocks(path[:-4] + '-blocks.bin')
    per_pc = collections.Counter(pcs)
    for r in rows:
        code = r[5]
        if not code: continue
        ins = jr.disassemble(code, r[0])
        # samples per insn: a sample at pc counts for the insn ending at/containing pc (approx: insn starting <= pc)
        starts = [a for a, _, _ in ins]
        w = collections.Counter()
        for pc, c in per_pc.items():
            if r[0] <= pc < r[0] + len(code):
                i = bisect.bisect_right(starts, pc) - 1
                if i >= 0: w[i] += c
        last_lahf = None; flags_dirty = True
        kind = ['other'] * len(ins)
        for i, (a, m, ops) in enumerate(ins):
            insn_total += 1; insn_samp_total += w[i]
            if m == 'shr' and ops.startswith('$0xc,'):
                # page lookup sequence: shr, test, jne, mov (table), test, je, access
                for j in range(i, min(i + 7, len(ins))): kind[j] = 'page lookup'
                tot['page lookups'] += 1
            if m == 'lahf':
                tot['flag saves (lahf)'] += 1; last_lahf = i; flags_dirty = False; kind[i] = 'flag save/reload'
            elif m == 'seto': kind[i] = 'flag save/reload'
            elif m == 'sahf':
                tot['flag reloads (sahf)'] += 1; kind[i] = 'flag save/reload'
                if last_lahf is not None and not flags_dirty:
                    tot['redundant reloads (no flag change since lahf)'] += 1
                flags_dirty = True
            elif FLAG_WRITERS.match(m):
                flags_dirty = True if last_lahf is not None else flags_dirty
            if m == 'cmpl' and '0x328(%r15)' in ops:
                tot['halt checks'] += 1; kind[i] = 'halt check'
            if m == 'jmp' and ops.startswith('0x') and i > 0 and '0x100(%r15)' in ins[i - 1][2]:
                tot['block exits to dispatcher'] += 1
        for i, k in enumerate(kind):
            samp[k] += w[i]
print(f'instructions in hot blocks: {insn_total}, samples on them: {insn_samp_total}')
for k, v in tot.most_common(): print(f'  {v:7d}  {k}')
print('samples by sequence kind:')
for k, v in samp.most_common(): print(f'  {100*v/max(1,insn_samp_total):5.1f}%  {k}')
