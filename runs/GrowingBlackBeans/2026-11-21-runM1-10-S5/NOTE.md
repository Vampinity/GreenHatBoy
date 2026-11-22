# runM1-10-S5, split S5: P (pressure pack), R (pack on refusal) and A (swap ahead) out; C T in (21 Nov 2026)

- Env: C1's minus `EDEN_GUEST_SWAP_AHEAD_MIB=2048`, the three `EDEN_UP_PACK_PRESSURE_*` lines and
  `EDEN_UP_PACK_ON_REFUSAL=1`; nothing else.
- Boot warm: store prep_5093ab9e reused (80770), 3 own, count 4; 01.219.028. Logs folder renamed.
- Removed units gone: no `EDEN_UP_PACK` line at all (with pressure and on-refusal both off the packer has nothing
  to report); no EDEN_SWAP_AHEAD line.
- Kept unit acts hard: reclaim 458 slots in 252 calls (controls 71-87).
- Largest free block at the black 911 MiB: the third P-out start, all three 838-911 (P-in starts 1,106-1,366).
  Low 0 in the load, recovered; through the load; no crash files.
- stk_gate against WF2-5: stranded 727 (better), median 14.35 and field walk 19.38 lean better; one start.
