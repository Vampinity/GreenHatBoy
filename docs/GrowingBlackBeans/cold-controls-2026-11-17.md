# Cold controls on the alpha, 17 Nov 2026

**Four of five scopes now have cold floors on the control, from four eligible starts each. The one standout is
memory after the field: 0–2 MiB of largest free block on every start, with about 1 GiB stranded in fragments.**

All runs: alpha T186 release eboot (01.219.028), `env-control` with only the script line changed, base PS5, firmware
13.60, handheld 1×, caches set aside (cold). Packed in `runs/GrowingBlackBeans/2026-11-17-run*`, scored with `tools/stk`.

## Floors

| scope (route) | eligible starts | floor | spread | memory low (largest free block) |
|---|---|---|---|---|
| baseline (`new-game-v9`) | BW1, BW2, BW4, BW5 | whole-run median **26.74 fps** | sd 0.8% | 165–362 MiB |
| Kokiri (`kokiri-four-stops`, v1) | KC1, KC2, KC3, KC5 | stop A 19.27, B 29.66, C 17.68, D 17.79 fps | sd 0.3–1.6% | 221–476 MiB |
| field walk (`field-to-past-field`) | FC2–FC5 | 13.42 fps | sd 4.0% (coarse) | 415–1061 MiB |
| after the field (same route) | FC2–FC5 | **13.90 fps** | sd 0.5% | **0–2 MiB** |
| later area | — | waiting on waveydude's route | | |

Not pooled: KC4 and BW3 (half warm: the driver cache and pipeline records loaded), FC1 (quit before END).

## Notes

- **Kokiri C and D:** the fps floors are fine, but the view isn't the same from start to start (GPU ring words a
  frame spread 6.5% at C and 4.7% at D; A 1.0%, B 2.7%). Anything per unit of work uses A and B only. v2 of the route
  is being tested as KV1–KV4: see `tools/GrowingBlackBeans/steer/kokiri-four-stops/README.md`.
- **Baseline door:** v6 missed the house door 3 times in 14 cold starts. v9 removes the timed camera swing, and opened
  the door 5 of 5 times. See `tools/GrowingBlackBeans/steer/baseline-door/README.md`. The v6 starts in this batch
  (BC1, BD1, BD2) and the failed v8 try (BX1) are packed too.
- **Baseline village, two speeds:** BW1 and BW2 stand at 22.4–22.6 fps, BW4 and BW5 at 18.6–18.8, with the same GPU
  work. It comes after a longer stall in the arrival scene. Not explained yet, so the village window isn't a floor on
  v9. Tabled for phase 4.
- **After the field:** at the low point the census names 919–1155 MiB in allocator slack, a fragmented heap and free
  heap pages (plus ~117 MiB stale clean), while the largest block is 0–2 MiB. The VMA dumps agree (60–538 MiB slack in
  300–525 holes, none over 16 MiB). It's fragmentation, not exhaustion. Vampinity's T186 warm field starts reach
  0–2 MiB too, so it isn't a cold-start effect. Tabled for phase 4.
- **Filmed start (BC1):** recording didn't move the numbers (inside CC1–CC3's range; memory low the highest).
- **Switch verdicts:** of the control's 80 switches without a verdict, none can be settled from the archive one line
  at a time. They always ran as bundles. Only the load-window bundle has a verdict, in Vampinity's
  `findings/load-window-2026-11-14.md`. The rest is phase 4 console work, the newest 37-switch bundle first.
