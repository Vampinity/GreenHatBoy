# runM1A1: crashed in the load past the gate; the cache was not in the warm state (20 Nov 2026)

**What happened:**
- The script reached the gate: the black was met at script 151 s (line 92).
- It crashed about 59 s into the load into the area past the field (app 220 s): SIGSEGV on CPUCore_5, writing guest
  memory, with **the largest free block 1 MiB of 12,352**.
- A memory-wall crash, at the load this route was built to reproduce. WF2-5 (the floor) all got through this load.

**What held:**
- Build 01.219.028. The store was reused (80,770). The swapper's lines were absent: 0 `EDEN_SWAP`, 0 `EDEN_UP_PACK`
  lines. `CRAM_RESERVE` stayed on.

**What didn't hold:**
- The boot read **179 own records, Total Pipeline Count 180**, not 3 and 4: the caches were play5's, not the
  warm-restore copy. WF2-5 read 3 and 4.
- By WARM-RUN-STEPS that makes it not a control-condition start.

**Read:** on its own, as a likely harm signal. It isn't one of M1A's four.
- The crash is what swap off was expected to risk.
- The extra 176 records are the only other difference from WF2-5, and their direction on memory isn't known.

**Next:** M1A2 with step 0 done in full. If M1A2 crashes in the same load, M1A1 can count as the second early end
under the rule (two → stop and call the arm worse). Discuss that before running a third.
