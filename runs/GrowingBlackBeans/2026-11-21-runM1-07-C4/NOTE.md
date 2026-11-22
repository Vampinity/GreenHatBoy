# runM1-07-C4, control 4 (21 Nov 2026)

- Env identical to C1's. Boot warm: store prep_5093ab9e reused (80770), 3 own, count 4; 01.219.028.
- Proof lines: pressure passes 1,787 (3,983 MiB); on-refusal asked 51 (267 MiB); reclaim 79 slots in 3 calls;
  swap ahead set.
- Largest free block at the black 1,139 MiB; low 1 in the load, recovered; through the load; no crash files.
- stk_gate against WF2-5: field walk 18.6 leans low (C2 and S3 leaned high); the rest within the noise. One start.
- `*.prev.*` files are S3's logs (byte-identical): the logs folder wasn't renamed before this start.
- Corrected 22 Nov: not an eligible control. The shutdown started but didn't finish (`end_kind: log_cut`,
  `control_eligible: false`), and warm-run-steps.md doesn't count such a start. Kept as data.
