# Two-slot guard on the console, and the flash counter (12 Nov 2026)

> **Found:** waveydude's two-slot guard (0927) leaves no frame unguarded, costs nothing and halves the big flashes, but two frames ahead still has about twice the control's medium flashes.
>
> **So:** Two frames ahead stays out of the everyday env for now. Next: a flash floor with no frame ahead, to know what "flicker-free" means.

GrowingBlackBeans. Runs `runs/GrowingBlackBeans/2026-11-12-{FC,FX,XG}{1,2,3}` and `2026-11-12-FX1-freeze1`. Base PS5 13.60, standard Kokiri route, Faster CPU on, everyday env (`envs/GrowingBlackBeans/`), builds t120-gbb8 (T120 + my series + waveydude's 0927) and t120-gbb9 (the same + patch 0928, the flash counter; third set only). Posted in Discussion #2.

| | FC (3) | FX (3) | XG (3) |
|---|---|---|---|
| Walking fps | 24.6 / 23.9 / 24.7 | 25.0 / 26.0 / 25.6 | 25.6 / 25.9 / 24.8 |
| Heavy windows (present wait ≥ 5 ms) | 4-6 per run | 0 | 0 |
| Presents armed while another was still armed | 0 | 5-6% | **0** |
| Second-slot arms per run | - | - | 320 / 715 / 1,051 |
| Flashes ≥ 4.3% of the screen (third set only) | 15 | 44 | **34** |
| ≥ 6.9% | 3 | 15 | **7** |
| Of those, motion-proof | 2 | 10 | **2** |
| Flicker by eye, all three sets | least, only at two hotspots | most | in between |

**Speed:** two frames ahead is +1.1 fps walking. Every one of the 6 two-ahead runs beat every control (p 0.012), but that's under my 1.2 fps cross-run noise floor, so call it small and real. The heavy windows go away entirely. XG against FX: −0.1 fps, noise. The second slot costs nothing measurable.

**Guard counters:** XG never had a frame unguarded. Shared copies were 2.6-5.0k per run and newer-copy reads 1.2-1.8k, with no pool-full and no waits.

**Flicker:**
- **The guard closes what it targets.** The big flashes halve and the motion-proof ones go back to control level.
- **What's left:** about twice the control's medium flashes, mostly bright, in bursts of 4-7 consecutive frames. XG3 had them at about 141, 164, 172 and 185 s.
- **So something outside the buffer guard still races** with two frames in flight. Vampinity's note that particle size may sit in per-frame vertex data rather than a uniform block fits what's left (bright, medium-sized, bursty), but I haven't confirmed it.

**How flashes are counted** (patch 0928, `EDEN_GBB_FLASH`):
- Each presented frame is shrunk on the GPU to a 120x67 brightness grid and read back late, with no stall.
- A flash is a cell that jumps by 24+ brightness levels for one or two frames while the frames either side agree.
- Sizes follow Vampinity's definition: 25+ and 40+ cells of a 32x18 grid, i.e. 4.3% and 6.9% of the screen. Below that it's mostly the game's own motion.
- "Motion-proof" means the cells are also outside the range of their 3x3 neighbourhood in both neighbouring frames.
- With `=2` it saves the grids (about 15 MB a minute), and `tools/GrowingBlackBeans/eglog/flashes.py grids` re-counts them and draws the frames around each flash.
- First check: it ranks the runs control < XG < FX like the player does. It also finds the control's house-door hotspot, where the lit wall around the door goes dark for one frame as Link starts to run.
- It needs no capture card. Vampinity, once I'm on T134 I'll look at whether it should sit on `black_probe.h` instead.

**One more thing for waveydude: a first-start freeze with `EDEN_UP_AHEAD_TWO=1` and one slot.**
- It happened on 2 of 3 first starts (FX1 and FX2), both at about 44 s into the title sequence. The retries ran fine. XG was fine on 3 of 3 starts, and the control on all of its starts.
- **Pattern:** the back goes about 1,000 ms/s busy, the front waits about 1,000 ms/s on it, then presents stop. There's no hang report.
- The vitals and flight-recorder dumps are in the runs.
- Three starts is thin, but it's the same spot both times.

## Corrections and checks from the review the same day

- **Light windows.** Two frames ahead showed light windows 1.35 fps slower (p 0.012). That is most likely a regime mix, not a cost: windows that were heavy are now counted as light and are slower ones. Standing, which is all light, didn't move (31.4 → 31.5). Inferred, not tested.
- **Walking +1.1 fps** is under the 1.2 fps cross-run noise floor even though all 6 runs beat all 3 controls; read it as small and real.
- **The control flashes too.** 15 flashes of 4.3%+ in FC3, at the same two places the player sees them every run: starting to run out of the house (127.5-134 s, including all 3 big ones; at 127.8 s the lit wall around the door goes dark for one frame) and stopping at the water. Vampinity's no-frame-ahead videos had none of that size (`docs/Vampinity/findings/frame-ahead-glitches-2026-11-09.md`), so these may be from running one frame ahead too. The next test checks it: 3 runs with `EDEN_NX2_FRAMES_AHEAD=0` against 3 controls, all with flash grids.
- **The counter's own log lines are too sensitive.** About 1,200 small "flashes" a run are Link's animation and the game's own motion. Count with `flashes.py grids` at Vampinity's sizes (v25 / v40).
- **Grid files.** The console's `logs/` folder keeps earlier sessions' grids. `flashes.py` now takes the file each run's log names.

## Reproduce

```
python3 tools/GrowingBlackBeans/eglog/flashes.py grids runs/GrowingBlackBeans/2026-11-12-FC3 runs/GrowingBlackBeans/2026-11-12-FX3 runs/GrowingBlackBeans/2026-11-12-XG3
python3 tools/GrowingBlackBeans/eglog/abcompare.py --a runs/GrowingBlackBeans/2026-11-12-FC{1,2,3} --b runs/GrowingBlackBeans/2026-11-12-{FX,XG}{1,2,3}
```
