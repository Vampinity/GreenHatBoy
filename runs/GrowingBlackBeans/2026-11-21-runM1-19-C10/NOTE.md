# runM1-19-C10, control 10 (21 Nov 2026)

- Env identical to C1's. Boot warm: store prep_5093ab9e reused (80770), 3 own, count 4; 01.219.028. Logs folder
  renamed.
- Proof lines: pressure passes 4,379 (4,927 MiB; the most in the batch); on-refusal asked 74 (657 MiB); reclaim
  74 slots in 2 calls; swap ahead set.
- Largest free block at the black 1,224 MiB (controls 986-1,366). Low 0, recovered; through the load; no crash
  files; worst frame 3,823 ms; refused pool events 2.
- Corrected 22 Nov: not an eligible control. The log has no shutdown lines (`end_kind: log_cut`,
  `control_eligible: false`), and warm-run-steps.md doesn't count such a start. Kept as data. (First written as the
  tenth, then the ninth counted control.)
- stk_gate against WF2-5: after-field 13.9 leans low, field walk 19.22 high, as several controls have; one start.
