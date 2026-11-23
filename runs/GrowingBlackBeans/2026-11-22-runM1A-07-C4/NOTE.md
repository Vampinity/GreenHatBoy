# runM1A-07-C4, batch A start 7 of 24: control (22 Nov 2026)

- Batch A sitting 1 (alpha T186 01.219.028, base PS5 13.60, handheld 1x, warm field route c4fada64155f, rules ffbf5cface7f). Sitting 1 of 2: starts 1-14 ran on 22 Nov, and starts 15-24 plus the C4 and C6 reruns follow on 23 Nov under an amendment (two sittings, controls pooled after a check that the two sittings' controls agree). No verdict until the batch is read.
- **Not a control:** the logs were copied before the app finished closing (`end_kind log_cut`); the log stops at
  the game's normal quit (`SetTerminateResult ... 2010-0212`, `Userspace PANIC`, as at every control's quit). Not a
  crash. Boot warm, settings as written, the route completed. Kept as data.
- Graphics refusals to script_end 15; largest block at the black 1255 MiB; 46 s under 16 MiB; worst frame after
  the black 2,635 ms; load 21.8 s; field walk 19.07 fps; distinct failed shapes 5. One start: no call.
