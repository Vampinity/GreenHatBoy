# runM1-20-S10, split S10: P (pressure pack) and T (cold time) out; R C A in (21 Nov 2026)

- Env: C1's minus the three `EDEN_UP_PACK_PRESSURE_*` lines and `EDEN_GUEST_SWAP_COLD_S=15`.
- Boot warm: store prep_5093ab9e reused (80770), 3 own, count 4; 01.219.028. Logs folder renamed.
- Removed: pressure passes=0 (`pressure_ms=0`); T has no line.
- Kept units act: on-refusal asked 94 (589 MiB); reclaim 52 slots in 4 calls; swap ahead set.
- Largest free block at the black 974 MiB: the fifth P-out start (P-out 838-1,042, mean 928; P-in 986-1,366).
  Low 0, recovered; through the load; no crash files; worst frame 3,746 ms; refused pool events 2.
