# runM1-04-S2, split S2: P (pressure pack) and A (swap ahead) out; R C T in (21 Nov 2026)

- Env: C1's minus `EDEN_GUEST_SWAP_AHEAD_MIB=2048` and the three `EDEN_UP_PACK_PRESSURE_*` lines; nothing else.
- Boot: 01.219.028; store prep_5093ab9e reused (80770), 3 own, count 4; crossed build yes, probes 3.
- Removed units gone: pressure passes=0 (pressure_ms=0 in the settings echo); no EDEN_SWAP_AHEAD line.
- Kept units act: on-refusal asked 293 (838 MiB back; C1-C2 38-87); reclaim 49 slots in 15 calls.
- Largest free block at the black 873 MiB (controls this batch 1,212 and 1,366; S1 1,193). Low 0 in the load,
  recovered; through the load; normal shutdown; no crash files.
- stk_gate against WF2-5: seconds under 16 MiB 74 against 35 ("worse beyond the noise, not yet shown"); the rest
  within the noise. One start: read with the table, not alone.
