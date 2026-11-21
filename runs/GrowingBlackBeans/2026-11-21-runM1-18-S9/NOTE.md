# runM1-18-S9, split S9: A (swap ahead) and T (cold time) out; P R C in (21 Nov 2026)

- Env: C1's minus `EDEN_GUEST_SWAP_AHEAD_MIB=2048` and `EDEN_GUEST_SWAP_COLD_S=15`.
- Boot warm: store prep_5093ab9e reused (80770), 3 own, count 4; 01.219.028. Logs folder renamed.
- Removed: no EDEN_SWAP_AHEAD line; T has no line.
- Kept units act: pressure passes 2,487 (3,953 MiB); on-refusal asked 48 (584 MiB); reclaim 79 slots in 2 calls.
- Largest free block at the black 1,341 MiB (controls 986-1,366). Low 0, recovered; through the load; no crash
  files; worst frame 3,735 ms; refused pool events 0. Looks like a control.
