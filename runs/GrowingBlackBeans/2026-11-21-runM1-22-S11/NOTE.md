# runM1-22-S11, split 11: pack on refusal out (21 Nov 2026)

- Env = C1's minus EDEN_UP_PACK_ON_REFUSAL=1, nothing else. Boot warm: store prep_5093ab9e reused (80770), 3 own,
  count 4; 01.219.028.
- The logs folder was not renamed before the start: the *.prev.* files are C11's (stderr.prev.log is byte-identical
  to runM1-21-C11/stderr.log). Ignore them.
- The game was left running after the script ended (script_end at 470 s; the log runs to t_s 7,908, about 2 h).
  Counts below are up to script_end; the black and the load are unaffected.
- Proof lines: no EDEN_UP_PACK_ON_REFUSAL line (refusals=0 in the pack summary); pressure passes 1,479 (3,901 MiB)
  by the script end; reclaim 149 calls, 177 slots, 110 MiB (controls: 2-3 calls); swap ahead set.
- Largest free block at the black 1,270 MiB (controls 986-1,366). Low 0, recovered; through the load; no crash
  files (the one "crash" line is the handler install); worst frame 3,814 ms; refused pool events 6.
- Fits the compensation pattern: with R out, reclaim is called far more often.
- stk_gate against WF2-5: after-field 13.9 leans low, as several controls have; everything else within the noise.
