# runM1-08-S4, split S4: P (pressure pack) and C (reclaim) out; R A T in (21 Nov 2026)

- Env: C1's minus `EDEN_GUEST_SWAP_RECLAIM=1` and the three `EDEN_UP_PACK_PRESSURE_*` lines; nothing else.
- Boot warm: store prep_5093ab9e reused (80770), 3 own, count 4; 01.219.028. Logs folder renamed (no .prev files).
- Removed units gone: pressure passes=0 (`pressure_ms=0`); 0 reclaim lines.
- Kept units act: on-refusal asked 63 (552 MiB); swap ahead set.
- Largest free block at the black 838 MiB (S2, the other P-out start so far: 873; P-in starts 1,139-1,366).
  Low in the load 8 MiB (every other warm start this batch hit 0-1), recovered; through the load; no crash files.
- stk_gate against WF2-5: driver low 8 leans better, median fps 14.1 leans low; one start.
