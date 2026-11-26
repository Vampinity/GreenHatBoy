# runner-proving-2, the runner's shakedown start 2 of 2: control (25 Nov 2026, 07:33), not read

- Alpha T186 01.219.028, base PS5 13.60, handheld 1x, warm field route c4fada64155f, the control env. One control start on the runner (Vampinity's PR 38 at 31ace18), run before batch B to prove the runner on our console. Not part of any batch and not read; kept and posted so every start of the day is in GHB.
- Boot warm: 80,770 known, 3 records read (3 own), Total Pipeline Count 4; completed, script done.
- Log cut after the quit (`end_kind log_cut`): the close was not captured, so the scorer marks it not eligible as a control. Not read anyway.
- Whole-cache restore before this start: copy ws2 (made 2026-11-25 06:57:21), 27 files, 2.1 GiB, 217 s, at 2026-11-25 07:38:36; read back 26 + 13 files; user-cache digest 07472daf4d3a, cache digest 48d0fe46e312 (the same in every start).
- VMA dumps left on the console: 0.
- Graphics refusals to script_end 5; largest block at the black 1,149 MiB; 16 s under 16 MiB; worst frame after the black 1,253 ms; load 19.2 s; field walk 18.97 fps; distinct failed shapes 1.
