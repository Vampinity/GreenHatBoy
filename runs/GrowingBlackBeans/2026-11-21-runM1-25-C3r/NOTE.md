# runM1-25-C3r, control 3 rerun, start 25 of 25 (21 Nov 2026)

- Env identical to C1's. Boot warm: store prep_5093ab9e reused (80770), count 4; 01.219.028. Replaces C3, which
  ran cold and is not counted.
- The console's log files arrived in a logs/ subfolder; moved up to the run folder (no names overlapped).
- Left running ~2 h after the script (script_end 448 s, log to t_s 8,359); counts are up to script_end.
- Proof lines: pressure passes 1,390 (3,113 MiB); on-refusal asked 39; reclaim 91 slots in 2 calls (48 MiB); swap
  ahead set.
- Largest free block at the black 1,176 MiB (controls 986-1,366). Through the load; no crash files; worst frame
  3,764 ms; refused pool events 0.
- Corrected 22 Nov: the ninth and last eligible control (first written as the 12th). The batch is complete.
- stk_gate against WF2-5: field walk 19.43 leans high, one start; everything else within the noise.
