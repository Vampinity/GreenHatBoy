# runM1A3: the second clean start to crash in the load; M1A is worse (20 Nov 2026)

**The start was clean:** store 80,770 reused, 3 own records, Total Pipeline Count 4. There were 0 swapper or pack
lines.

**What happened:**
- The black at the gate came at script 176.5 s, with the largest free block at 452 MiB.
- The crash came at app 221 s, about 41 s into the load, with 1 MiB free of 12,352.
- SIGSEGV on CPUCore_5, again writing guest memory (0x816c000000). This time the faulting code was outside the eboot
  (generated code, the JIT), not eboot+0x4c84xx. Same wall, a different instruction hit it.

**The folder also holds `crash-20261120-115703*` and `mkw-vma-108-*`:** M1A2's crash, carried over, because the
console's `logs/` wasn't renamed before this start (step 2). Only `crash-20261120-121216*` is M1A3's.

**Rule (written before any start):** two clean early ends (M1A2, M1A3), plus M1A1 (dirty caches, the same crash).
The arm is called **worse**. M1A4 isn't needed. If it was run anyway, it's extra evidence, not part of the call.
