# runM1-01-C1, the smoke control (21 Nov 2026)

- Boot: diagnostic build 01.219.028; store prep_5093ab9e reused (80770), 80770 known, 3 records read (3 own),
  Total Pipeline Count 4. Counts as a warm control.
- New: "crossed build yes, probes 3". The reinstall gave the eboot a new install stamp (84698430.1795229367 vs
  WF2-5's .1794945205), so this boot re-translated 3 stored records and compared them; nothing differed, and the
  store was kept ("reused", not "reset"). Every start in this batch restores the same cache onto the same install,
  so all of them should cross the same way. Same gate key as WF2-5.
- Swap proof lines (stderr.log): pressure passes 2,258 (3,597 MiB freed); on-refusal asked 38 (208 MiB);
  reclaim for graphics 71 slots in 2 calls; EDEN_SWAP_AHEAD 2048MiB, swap mode 3. All inside or near WF2-5's range
  (reclaim a bit under WF2-5's 93-137 slots).
- Got through the load; closed normally (driver cache written at shutdown); no crash files.
- stk_gate against the warm field floor (WF2-5): every number within the noise; stranded-at-low better beyond the
  noise, not shown from one start. No drift against 19 Nov.
- Largest free block at the black: 1,212 MiB (driver line, the rule in M1-DESIGN.md, fixed 21 Nov); low in the load 0, recovered.
