# runM1-02-S1, split S1: C (reclaim) out, P R A T in (21 Nov 2026)

- Boot: 01.219.028; store prep_5093ab9e reused (80770), 80770 known, 3 own, count 4; crossed build yes, probes 3
  (as C1). Warm, same gate key.
- The removed unit is gone: 0 `EDEN_SWAP reclaim for graphics` lines (C1: 71 slots in 2 calls).
- The kept units act: pressure passes 2,185 (4,044 MiB freed); on-refusal asked 144 (257 MiB); EDEN_SWAP_AHEAD
  2048MiB, mode 3.
- Got through the load; normal shutdown lines; no crash files.
- stk_gate against WF2-5: all within the noise; field walk 19.52 "better beyond the noise, not yet shown" (one start).
- `*.prev.*` files are C1's logs (byte-identical): the console's logs folder wasn't renamed before this start, so
  the app rotated them. The current files are S1's own.
- Largest free block at the black: 1,193 MiB (driver line, the rule in M1-DESIGN.md); low in the load 0, recovered.
