# runM1B-09-C5, batch B start 9 of 24: control (25 Nov 2026)

- Batch B, the reserves that act (alpha T186 01.219.028, base PS5 13.60, handheld 1x, warm field route c4fada64155f, rules 9e13ca644841 in docs/GrowingBlackBeans/batch-b-rules/ with amendments 1-3). Run on the runner (Vampinity's PR 38 at 31ace18), all 24 in one run with the whole cache restored before every start; 24 of 24 back, 11 eligible controls. The read is in docs/GrowingBlackBeans/batch-b-memory-2026-11-25.md.
- Boot warm: 80,770 known, 3 records read (3 own), Total Pipeline Count 4; settings as written; script done.
- **Not an eligible control:** its log stops just after the quit (`end_kind log_cut`): the close was not captured. Left out of the read; 11 eligible controls remain. The rules ask for a start that does not count to be rerun at the end; it was not (see the read).
- Whole-cache restore before this start: copy ws2 (made 2026-11-25 06:57:21), 27 files, 2.1 GiB, 211 s, at 2026-11-25 09:53:43; read back 26 + 13 files; user-cache digest 07472daf4d3a, cache digest 48d0fe46e312 (the same in every start).
- VMA dumps left on the console: 0.
- Graphics refusals to script_end 11; largest block at the black 1,118 MiB; 34 s under 16 MiB; worst frame after the black 3,030 ms; load 20.3 s; field walk 19.44 fps; distinct failed shapes 3.
