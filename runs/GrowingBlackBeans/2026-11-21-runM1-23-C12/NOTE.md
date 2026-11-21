# runM1-23-C12, control 12 (21 Nov 2026)

- Env identical to C1's. Boot warm: store prep_5093ab9e reused (80770), 3 own, count 4; 01.219.028.
- The logs folder was not renamed before the start: the *.prev.* files are S11's (stderr.prev.log is byte-identical
  to runM1-22-S11/stderr.log). Ignore them.
- Left running ~13 min after the script (script_end 458 s, log to t_s 1,244); counts are up to script_end.
- Proof lines: pressure passes 1,441 (3,488 MiB); on-refusal asked 60; reclaim 82 slots in 4 calls (58 MiB); swap
  ahead set.
- Largest free block at the black 1,174 MiB (controls 986-1,366). Low 0, recovered; through the load; no crash
  files; worst frame 3,736 ms; refused pool events 1.
- The 11th counted control (C3 ran cold and is not counted). C3r makes 12.
- stk_gate against WF2-5: everything within the noise, after-field included (14.1).
