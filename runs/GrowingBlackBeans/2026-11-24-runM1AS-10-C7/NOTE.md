# runM1AS-10-C7, batch AS start 10 of 12: control (24 Nov 2026)

- Batch AS, the drain at area split (alpha T186 01.219.028, base PS5 13.60, handheld 1x, warm field route c4fada64155f, rules 133e19b181fb, order and cut-short rule in docs/GrowingBlackBeans/batch-as-rules/ORDER.md). One sitting on 24 Nov, 12 of 12 starts back, 8 eligible controls. The batch's read is in docs/GrowingBlackBeans/batch-as-memory-2026-11-24.md.
- Boot warm: 80,770 known, 3 records read (3 own), Total Pipeline Count 4; settings as written; closed normally. `control_eligible: true`.
- Graphics refusals to script_end 10; largest block at the black 1,258 MiB; 24 s under 16 MiB; worst frame after the black 2,551 ms; load 21.5 s; field walk 18.94 fps; distinct failed shapes 3.
- C7's first try (pid 237) ran the same env and hung after the load at the black (no frames from about 200 s; closed by hand, no crash file). It was rerun at once in start 10's place; this is the rerun. The try isn't packed: the app kept no eden_log.txt for it (only stderr, heap and boot trace), and the packer needs one. See the read.
