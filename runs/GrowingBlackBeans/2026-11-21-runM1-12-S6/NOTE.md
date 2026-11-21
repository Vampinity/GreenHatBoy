# runM1-12-S6, split S6: P R C T out; only A (swap ahead) kept (21 Nov 2026)

- Env: C1's minus `EDEN_GUEST_SWAP_RECLAIM=1`, `EDEN_GUEST_SWAP_COLD_S=15`, the three `EDEN_UP_PACK_PRESSURE_*`
  lines and `EDEN_UP_PACK_ON_REFUSAL=1`; nothing else.
- Boot warm: store prep_5093ab9e reused (80770), 3 own, count 4; 01.219.028. Logs folder renamed.
- Removed units gone: no EDEN_UP_PACK line, 0 reclaim lines. Kept: EDEN_SWAP_AHEAD set.
- Largest free block at the black 1,042 MiB: the fourth P-out start, but higher than the other three (838-911) and
  just under the controls (1,106-1,366). Low 0 in the load, recovered; through the load; no crash files.
- First harm signs in the batch, all "not yet shown" (one start) against WF2-5: worst frame 6,922 ms (WF2-5 mean
  3,995; every other start in this batch 3,742-4,063); refused pool events 33 (WF2-5 mean 5.75; this batch 0-14); field walk 18.62.
  With no packing and no reclaim, refusals had nowhere to go. Read with the table, not alone.
