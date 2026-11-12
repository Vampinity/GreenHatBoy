# PS5 session, 12 Nov (evening)

**Goal:** confirm the automatic flash count works, then judge the two-frame guard by numbers. If the guard holds, two frames in flight (about +2 fps walking, a third off the slowest frames) becomes everyday.

**Build:** `t120-gbb9`. **It doesn't exist yet**: I build it during the day on 12 Nov in two steps, and I'll tell you when it's ready.
- **gbb8:** automatic flash count (`EDEN_GBB_FLASH=1`), plus flight-recorder fixes: no dumps during loading, and the triggering frame kept.
- **gbb9:** gbb8 plus the two-frame guard (`EDEN_GBB_GUARD_FRAMES=2`).

**Everyday env** already includes tonight's two adoptions: the usage tracker and preload-all. Faster CPU emulation on, standard route, one line per run on how it looked.

| # | Folder | What changes | Watch for |
|---|---|---|---|
| 1 | `runFC1` | control + flash count | the flash count's first real run |
| 2 | `runFX1` | two frames ahead, **no** two-frame guard | flicker, as in X1-3; the count should be clearly higher than run 1 |
| 3 | `runXG1` | two frames ahead **with** the two-frame guard | flicker back to control level? speed like run 2? |
| 4 | `runFC2` | control | |
| 5 | `runFX2` | two frames ahead, no guard | |
| 6 | `runXG2` | two frames ahead + guard | |
| 7 | `runFC3` | control | |
| 8 | `runFX3` | two frames ahead, no guard | |
| 9 | `runXG3` | two frames ahead + guard | |

About 9 runs at roughly 6 minutes: about an hour. Three a side makes each comparison a call, not just a screen. If short on time, do 1-6.

**Decision rules:**
1. **The flash count works** if every FX run counts more flashes than every FC run. If not, we fall back to your ratings, and I fix the detector the next day.
2. **The two-frame guard works** if every XG run's flash count sits within the FC runs' range, and XG walking fps stays within 0.5 of FX. If both hold, two frames ahead plus the guard goes into the everyday env.
3. **If the guard cuts the flashes but costs fps,** the copy cost needs trimming before adopting.

**Copying:** as usual, `eden_log.txt` and the `logs/` folder into each run's folder.
