# runM1C-29-PROBE, batch C start 29: the waits probe (25 Nov 2026), not read with C

- Batch C, the memory parts handed over by Vampinity on 25 Nov (alpha T186 01.219.028, base PS5 13.60, handheld 1x, warm field route c4fada64155f, rules 4d083ca2d204 in docs/GrowingBlackBeans/batch-c-rules/). Run on the runner (Vampinity's PR 38 at 31ace18), all 29 in one run with the whole cache restored before every start; 28 of 28 back, 12 eligible controls. The read is in docs/GrowingBlackBeans/batch-c-memory-2026-11-25.md.
- The control env plus `EDEN_UP_FAULT_LOG=1`, log-only on this control (GPU_READ_THROUGH=2 and FAULT_RESERVE=1 already turn the fault path on). Not a control, not read for numbers: it decides batch D (`waits.py`, beside the rules).
- Two guest-write waits, both on the cpu-jit thread near 175 s, 2 and 95 ms, both got a block. No JIT commit or new-handler wait in it.
- Boot warm; script done.
- Whole-cache restore before this start: copy ws2 (made 2026-11-25 06:57:21), 27 files, 2.1 GiB, 204 s, at 2026-11-25 19:00:50; read back 26 + 13 files; user-cache digest 07472daf4d3a, cache digest 48d0fe46e312 (the same in every start).
- VMA dumps left on the console: 0.
- Graphics refusals to script_end 14; largest block at the black 1,225 MiB; 42 s under 16 MiB; worst frame after the black 3,253 ms; load 24.8 s; field walk 18.88 fps; distinct failed shapes 5.
