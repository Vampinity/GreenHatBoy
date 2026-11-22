# runM1-15-C8, control 8 (21 Nov 2026)

- Env identical to C1's. Boot warm: store prep_5093ab9e reused (80770), 3 own, count 4; 01.219.028. Logs folder
  renamed.
- Proof lines: pressure passes 2,072 (4,011 MiB); on-refusal asked 4 (131 MiB); reclaim 65 slots in 1 call; swap
  ahead set.
- Largest free block at the black 986 MiB: the lowest control so far (others 1,106-1,366). It overlaps S6 (1,042)
  and sits near S5 (911), so the P-out gap narrows: P-out 838-1,042 against controls 986-1,366. Low 5 in the load,
  recovered; through the load; no crash files; worst frame 3,822 ms; 0 refused pool events.
- stk_gate against WF2-5: field walk 18.66 leans low; the rest within the noise.
