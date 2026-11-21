# runM1A2: a clean start that crashed in the same load as M1A1 (20 Nov 2026)

**The start was clean:** store reused (80,770), 80,770 known, 3 records read (3 own), Total Pipeline Count 4.
That's the warm state, the same as WF2-5. There were 0 swapper or pack lines.

**What happened:**
- The black at the gate came at script 163.8 s.
- The crash came at app 222 s, about 54 s into the load, with the largest free block 1 MiB of 12,352.
- SIGSEGV on CPUCore_5, writing guest memory (eboot+0x4c8498; M1A1's was +0x4c867b, so likely the same function).

**Free memory, largest block, at the black, then in the load:**

| start | at the black | in the load |
|---|---|---|
| WF2 | 1,194 MiB | 0, recovered |
| WF3 | 1,030 MiB (corrected 21 Nov; 2,368 was a stale census line) | 2, recovered |
| WF4 | 1,051 MiB (corrected 21 Nov; 2,239 was a stale census line) | 0, recovered |
| WF5 | 1,239 MiB (corrected 21 Nov; 1,201 was a census line) | 0, recovered |
| M1A1 (play5's caches) | 603 MiB | 1, crashed ~59 s in |
| M1A2 | 458 MiB | 1, crashed ~54 s in |

Every start hits the bottom in this load. With the swapper on, the controls reach the gate with 1.0-1.2 GB to spare (corrected 21 Nov from 1.2-2.4: the driver line, not the census)
and come back from it. With it off, the starts reach the gate with about 0.5 GB and don't come back.

**Rule:** one clean early end (this) plus M1A1 (an early end with dirty caches). M1A3 was already running when this
was read. If M1A3 crashes too, that's two clean early ends: the arm is worse, M1A4 is not run, and the family gets
split.
