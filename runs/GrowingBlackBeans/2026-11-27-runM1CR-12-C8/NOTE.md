# runM1CR-12-C8, batch CR start 12 of 12: control (27 Nov 2026)

- Batch CR, batch C's table reserve out repeated alone (alpha T186 01.219.028, base PS5 13.60, handheld 1x, warm field route c4fada64155f, rules 9088f44c6340 in docs/GrowingBlackBeans/batch-cr-rules/, with L7 amendment 2's points 1, 4, 5 and 6). Run on the runner (Vampinity's PR 38 at 31ace18), all 12 in one run on 27 Nov with the whole cache restored before every start; 12 of 12 back, none in the fast state, 8 eligible controls. The read is in docs/GrowingBlackBeans/batch-cr-memory-2026-11-27.md.
- Boot warm: 80,770 known, 3 records read (3 own), Total Pipeline Count 4; settings as written; script done; **the log is cut at the close** (a thread dump while the shutdown waited, after the script, past the read's window of script_done + 10 s): the scorer's control_eligible reads false, and the control counts by L7 amendment 2's point 6 (docs/GrowingBlackBeans/batch-cr-rules/CLOSE-CUTS.md).
- Field state normal (state-check: median ring words a frame 90-140 s at 110k or more).
- Whole-cache restore before this start: copy ws2 (made 2026-11-25 06:57:21), 27 files, 2.1 GiB, 209 s, at 2026-11-27 09:15:16; read back 26 + 13 files; user-cache digest 07472daf4d3a, cache digest 48d0fe46e312 (the same in every start).
- VMA dumps left on the console: 0.
- Graphics refusals to script_end 0; largest block at the black 1,021 MiB; 30 s under 16 MiB; worst frame after the black 1,253 ms; load 18.6 s; field walk 19.09 fps; distinct failed shapes 0.
