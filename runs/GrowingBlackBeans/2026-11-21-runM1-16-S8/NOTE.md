# runM1-16-S8, split S8: C (reclaim), A (swap ahead) and T (cold time) out; P R in (21 Nov 2026)

- Env: C1's minus `EDEN_GUEST_SWAP_AHEAD_MIB=2048`, `EDEN_GUEST_SWAP_RECLAIM=1` and `EDEN_GUEST_SWAP_COLD_S=15`.
- Boot warm: store prep_5093ab9e reused (80770), 3 own, count 4; 01.219.028. Logs folder renamed.
- Removed units gone: 0 reclaim lines, no EDEN_SWAP_AHEAD line. T has no line.
- Kept units act: pressure passes 2,866 (4,090 MiB); on-refusal asked 66 (624 MiB).
- Largest free block at the black 1,082 MiB (controls 986-1,366). Low 0, recovered; through the load; no crash
  files; worst frame 3,762 ms.
- Refused pool events 3: with C out but R in, refusal-pack took the refusals (as S1 and S4). Fits the R x C pattern
  (only S6 and S7, with both out, reached 32-33).
- Corrected 22 Nov: the 32-33 above are throttled report lines. Graphics refusals to script_end: this start 3, S6 144,
  S7 41.
