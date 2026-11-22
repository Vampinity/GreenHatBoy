# runM1-06-S3, split S3: R (pack on refusal) and T (cold time) out; P C A in (21 Nov 2026)

- Env: C1's minus `EDEN_UP_PACK_ON_REFUSAL=1` and `EDEN_GUEST_SWAP_COLD_S=15`; nothing else.
- Boot: warm (the restore worked after C3's miss): store prep_5093ab9e reused (80770), 3 own, count 4; crossed build
  yes, probes 3; 01.219.028.
- R gone: 0 on-refusal asks, `on_refusal=0` in the settings echo. T has no line (rides for harm only).
- Kept units act: pressure passes 2,037 (3,568 MiB); swap ahead set; reclaim 276 slots in 110 calls, the most so
  far (C1-C2 71-72, S1 0, S2 49): with refusals not packed, graphics took slots back instead.
- Largest free block at the black 1,309 MiB; low 0 in the load, recovered; through the load; normal shutdown; no
  crash files.
- stk_gate against WF2-5: after-field 13.9 leans low, field walk 19.3 leans high, as C2 did; one start.
