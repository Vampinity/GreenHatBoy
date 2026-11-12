# Guard cost, 11 Nov 2026 (T120)

> **Found:** The copy guard (EDEN_UP_AHEAD_GUARD=3) costs about 0.7 fps (3%) standing in the village and 0 to 0.7 fps at the overlook; it removed the small dark flashes but not the one-frame white flash.
>
> **So:** Ship the guard as an opt-in line, not as the default in the fast file yet.

What the copy guard (`EDEN_UP_AHEAD_GUARD=3`) costs when standing still, with fast settings (`EDEN_NX2_FRAMES_AHEAD=1`) and the tracker (`EDEN_UP_FRITCHII_USAGE_TRACKER=1`) on in both arms.

- Overlook (heavy spot): `auto-20261111-163143-batch-stand-heavy-guard`, order tracker, guard, guard, tracker
- Village: `auto-20261111-165334-batch-stand-guard-cost`, order warm-up (guard), control, guard, guard, control, control, guard

Terms, one line each:
- **copy guard**: makes the emulated CPU wait for or copy memory pages the GPU is still reading, so a frame drawn one step ahead does not pick up half-written data.
- **p99 frame time**: the frame time that only 1 frame in 100 is slower than (the log calls it "1% low").
- **worst frame**: the single slowest frame in the window.
- **noise floor**: how far two starts with the *same* settings land apart; a difference smaller than that means nothing.
- **flash meter**: flicker-score.py, finds short dark dips in the video; it does not see bright flashes.
- **video check**: video-check.py, also flags short all-white moments ("white" events).

## Short answer

- **Village: the guard costs about 0.7 fps (3%)**, 24.4 → 23.7 fps. Honest range 0.35 to 1.2 fps (1.4% to 4.8%). Every guard start was slower than every control start.
- **Overlook: 0 to 0.7 fps, best guess about 0.4 fps (2%)**, but this batch cannot pin it: the four starts stood at slightly different spots (see the draw counts), and one tracker start ran 0.6 fps faster than the other.
- Frame-time spikes (p99, worst frame) were **not** worse with the guard at either spot.
- Standing still, the guard removed the small dark flashes (overlook 2 of 2 runs without, 0 of 2 with; village 1 of 3 vs 0 of 3) but **not** the one-frame all-white flash at the overlook (1 of 2 runs without the guard, 2 of 2 runs with it).
- Verdict: do not make it the default in the release's fast file yet; ship it as an opt-in line. Details at the end.

## 1. Validity per run

Spot check: two frames from each recording (about 110 s and 30 s before the video's final black, both inside the standing window), pulled with ffmpeg and looked at. "Draws steady" = draws per frame (overlook, `EDEN_UP_SUBMIT_STATS`) and GPU command words per frame (both batches, `FETCH_COUNT` "seen" growth / frames) inside each live phase.

| Run | Arm | env.txt guard | Spot in frames | Draws/frame | Cmd words/frame | Ending | Valid |
|---|---|---|---|---|---|---|---|
| 1149 tracker1 | no guard | absent (ok) | overlook, view turned a bit left | 23.5-24.2 | 11400-11600 | script done | yes, but different view |
| 1150 guard1 | guard | `=3` (ok) | overlook | 24.1-25.2 | 11400-11460 | script done | yes |
| 1151 guard2 | guard | `=3` (ok) | overlook | 24.5-25.1 | 11310-11460 | script done | yes |
| 1152 tracker2 | no guard | absent (ok) | overlook, slightly heavier view | 26.5-27.5 | 12000-12110 | script done | yes, but different view |
| 1153 warmguard1 | guard (warm-up) | `=3` (ok) | village | n/a | 5260-5410 | script done | warm-up, not counted |
| 1154 control1 | no guard | absent (ok) | village | n/a | 5330-5530 | script done | yes |
| 1155 guard1 | guard | `=3` (ok) | village | n/a | 5230-5520 | script done | yes |
| 1156 guard2 | guard | `=3` (ok) | village | n/a | 5360-5510 | script done | yes |
| 1157 control2 | no guard | absent (ok) | village | n/a | 5420-5510 | script done | yes |
| 1158 control3 | no guard | absent (ok) | village | n/a | 5400-5480 | script done | yes |
| 1159 guard3 | guard | `=3` (ok) | village | n/a | 5340-5510 | script done | yes |

- No crash in any run: all ended "script done"; crash-index.txt only lists the old crashes from the night (00:08-06:02).
- `EDEN_NX2_FRAMES_AHEAD=1` and the tracker are in every env.txt.
- Village: all seven starts stand at the same place (the porch in front of the house, same camera), draws steady within 1-3% and equal between arms. Clean comparison.
- Overlook: same area in all four, but the steered walk ends a little differently each start. tracker2 draws about 10% more per frame than the others (more on screen); tracker1 draws a bit less and faces further left. So at the overlook the arms are mixed with "which view" differences, which is why its price is only a range.
- The village batch's env lacks the extra stats switches the overlook batch had (SUBMIT_STATS, L1094/L949 stats, SPLIT_WAITS, ZPASS_CUT_LOG); same in both arms there, so no effect on the comparison, but the two spots' absolute fps are not like for like.

## 2. fps per run

Window: the six 20 s live phases the app logs itself after the test spot is reached (first 2 s of each phase dropped by the app, so 6 × 18 s = about 108 s counted per start). Same window in every run; fps = all frames / all counted seconds. Read from the `EndPhase` lines in eden_log.txt (they match live.json).

### Overlook

| Run | Arm | fps | p99 (median of phases) | p99 worst phase | Worst frame | Frames >100 ms |
|---|---|---|---|---|---|---|
| tracker1 | no guard | 17.36 | 70.5 ms | 78.6 ms | 109 ms | 2 |
| tracker2 | no guard | 16.71 | 69.8 ms | 71.3 ms | 105 ms | 2 |
| guard1 | guard | 16.63 | 71.0 ms | 72.2 ms | 95 ms | 0 |
| guard2 | guard | 16.69 | 68.4 ms | 82.6 ms | 109 ms | 1 |

Per arm: no guard 17.03 fps (spread 0.64), guard 16.66 fps (spread 0.06).
tracker1's third phase dropped to 16.4; its other phases ran 17.4-17.7.

### Village

| Run | Arm | fps | p99 (median of phases) | p99 worst phase | Worst frame | Frames >100 ms |
|---|---|---|---|---|---|---|
| warmguard1 | guard (warm-up) | 23.41 | 75.6 ms | 78.7 ms | 111 ms | 1 |
| control1 | no guard | 24.33 | 76.9 ms | 78.9 ms | 97 ms | 0 |
| control2 | no guard | 24.17 | 75.8 ms | 78.2 ms | 90 ms | 0 |
| control3 | no guard | 24.71 | 76.2 ms | 77.1 ms | 95 ms | 0 |
| guard1 | guard | 23.69 | 75.8 ms | 78.5 ms | 92 ms | 0 |
| guard2 | guard | 23.52 | 75.0 ms | 76.7 ms | 93 ms | 0 |
| guard3 | guard | 23.82 | 73.9 ms | 77.9 ms | 94 ms | 0 |

Per arm: no guard 24.40 fps (spread 0.54), guard 23.68 fps (spread 0.30).

Noise floor: about 0.3-0.5 fps between same-arm starts at the village, 0.06-0.64 at the overlook. The plan expected the village ruler to be tighter (between-start sd 0.03-0.15); today it was not (control sd about 0.27).

Side note: at the village the phases alternate slow / fast by 0.5-1 fps in every run, both arms, although nothing is switched (the "live" A and B carry the same switches). Something in the scene runs on a roughly 40 s cycle. Averaging all six phases cancels it, so it does not touch the comparison.

## 3. The guard's price

| Spot | No guard | Guard | Price | Range | Same-arm spread |
|---|---|---|---|---|---|
| Village | 24.40 | 23.68 | **0.73 fps (3.0%)** | 0.35 to 1.19 fps (1.4% to 4.8%), neighbour pairs 0.65 / 0.65 / 0.89 | 0.30-0.54 |
| Overlook | 17.03 | 16.66 | **0.37 fps (2.2%)** | 0.02 to 0.72 fps (0.1% to 4.2%) | 0.06-0.64 |

- Village: the gap (0.73) is larger than the noise (0.3-0.5), and all three guard starts are below all three controls (the most extreme split possible with 3 + 3; chance alone would give it 1 in 20 times). Read: a real cost, about 0.7 fps, could be as little as 0.4 or as much as 1.1.
- Overlook: cannot tell a real cost from "which view the walk stopped at". tracker2, the heaviest view, ran at the guard runs' speed (0.02-0.08 above them); tracker1, the lightest view, ran 0.7 above. If the view is what matters, the true price there is nearer 0 than 0.7.
- Does it differ between the spots? In percent the two guesses (3.0% and 2.2%) sit inside each other's range: no evidence of a difference. The overlook is too loose to say more.
- The agreed bar ("about half an fps or less at the heavy spot") is met by the overlook's best guess but not proven; the village, the more precise ruler today, is above it.

## 4. Glitches per arm (benefit beside the price)

Standing window only (the live phases):

| Spot | Measure | No guard | Guard |
|---|---|---|---|
| Overlook | flash meter, small dark dips | 2 of 2 runs show a flash | 0 of 2 runs |
| Overlook | video check, one-frame all-white screen | 1 of 2 runs (tracker1) | 2 of 2 runs (guard1, guard2) |
| Village | flash meter | 1 of 3 runs | 0 of 3 runs (warm-up also 0) |
| Village | video check, all-white | 0 of 3 runs | 0 of 3 runs |

- I looked at the all-white moments in tracker1 (video 163 s) and guard2 (video 233 s): the whole picture blows out to white for one game frame, then back. Same kind of glitch in both arms. **The guard does not stop this one.** It is the kind GBB's NaN guard pair stopped on 10 Nov (3 of 3 controls glitched, 0 of 3 with the pair); those switches are not in this env.
- Whole recordings (incl. loading and the walk to the spot) show no arm difference at the village (both arms about 3-7 flashes a minute, door and porch moments included), so that number says nothing about the guard.
- The guard's real benefit comes from walking, not standing: the HUD-icon glitch on the walking loop was 41-44 moments without the guard, 0 with it (walk-hud, 11 Nov). Standing still the HUD glitch does not appear in either arm (stand-hud, 0 in six starts).

## 5. Verdict

The guard costs about 0.7 fps (3%) when standing in the village, with a range of 0.4 to 1.1 fps. At the overlook the cost is somewhere from nothing to 0.7 fps (best guess 0.4), but the walk stopped at slightly different views each start, so that batch cannot be more exact. It does not make frame spikes worse. In return it removes the HUD-icon glitch when walking (41-44 → 0) and the small dark flashes seen here, but not the one-frame all-white flash at the overlook, which happened with the guard on too. My advice: **do not make it the default in the release's fast settings file yet; ship it as a ready-made opt-in line** ("add this for a clean HUD, costs about 3%"). Two things block the default: these tests stood still, so they could not see door loads, scene cuts or camera swings, which is exactly where the guard is known to cause trouble (the second after a door or cut comes out too bright, door walk failed 3 of 3 on T107, the guard-door fix is not landed), and where its copying cost is probably largest. If the guard-door fix passes the door walk, re-price the guard with a door walk and a walking-loop fps run (old, new, old) before making it the default. Vampinity's call.

## What this could not see

- Movement, door loads, cuts, camera swings: no data at all.
- The overlook arms stood at slightly different views; a cleaner overlook price needs the same stop point (or more starts per arm).
- Only 2 + 2 starts at the overlook and 3 + 3 at the village; the per-run flash counts are small.
- The flash meter only sees dark dips; the all-white count comes from video-check white events and two frames checked by eye, not a full scan.py run.

Files: frames pulled to working folder (`heavy.jpg`, `village.jpg`, `g2strip.jpg`, `t1strip.jpg`), not kept.

## Check (second time)

Re-derived from the raw logs with my own script (EndPhase lines, live.json, SUBMIT_STATS lines, video-check.txt), plus one in-window frame per run tiled and looked at. Result: the village price and the advice stand; one reading of the overlook is turned the wrong way round.

**Confirmed**
- env.txt: `EDEN_UP_AHEAD_GUARD=3` in exactly 1150, 1151, 1153, 1155, 1156, 1159; absent in 1149, 1152, 1154, 1157, 1158. FRAMES_AHEAD=1 and tracker in all 11. The guard really ran: its own log lines (`ahead_guard.h`) appear 41-55 times in each guard run and 0 times in the others. The live phases never touch the guard switch.
- No crash: all 11 `"ending": "script_end"`. The only "crash" word in stderr is the crash handler being installed.
- fps, their window (six live phases, 2 s settle dropped): identical to the table, all 11 runs.
- fps, my own window (present counter from phase 1 start to the end of phase 6, so the full 120 s including the settle seconds): village control 24.31 / 24.19 / 24.64, guard 23.68 / 23.48 / 23.82, price 0.72 fps. Rounds 2-3 only (last 80 s): price 0.69 fps. Overlook full window: no guard 17.34 / 16.70, guard 16.63 / 16.66. So the window choice moves nothing.
- Order/drift: at the village both arms drift up a little over the batch (control first 24.33, last 24.71; guard first 23.69, last 23.82). Guard starts sit at positions 3, 4, 7, controls at 2, 5, 6, so drift would favour the guard if anything. It cannot explain the gap. Every guard start is below every control start, and the gap (0.72) is bigger than either arm's spread (0.30 / 0.54).
- Draws per frame at the overlook (my count): tracker1 23.5-23.8, guard1 23.9-25.2, guard2 24.5-25.1, tracker2 26.5-27.4. Matches.
- Frames: all four village starts show the same porch and camera. At the overlook the four views differ: tracker1 is turned left, tracker2 stands nearer the plants on the right, and guard2 also stands a bit differently from guard1.
- Flash meter (live.json flashes per phase): overlook tracker1 yes (5), tracker2 yes (only 1, in one phase), guard runs 0; village control1 1, all others 0. "2 of 2 vs 0 of 2" and "1 of 3 vs 0 of 3" hold. tracker2's single flash makes the overlook split thin.
- White flashes, mapped onto the standing window (video window ≈ 120-241 s, tracker1 131-251 s): tracker1 4 inside, tracker2 0, guard1 1, guard2 2 (a third at 253 s falls just after the window). Village 0 in all 7. "1 of 2 without vs 2 of 2 with" holds.

**Corrections**
1. Overlook reading turned round. The report says "if the view is what matters, the true price there is nearer 0 than 0.7". The data point the other way. tracker2 had about 9% more draws than the guard runs and still ran as fast as they did, so the guard costs about as much as that extra work. Drawing a line through the two no-guard starts (fps against draws) and reading it off at the guard runs' draws (~24.6) gives about 17.15 fps without the guard against 16.66 with it: **about 0.5 fps (3%)**, the same percent as the village. That is only two points, so it is a hint, not a measurement. Better wording: "the overlook is consistent with the village's 3%; nothing here points to a cost near 0."
2. tracker1 also reached the spot 12 s later than the other three (live phases start at log 134 s against 122.4-122.7 s). That is another sign its walk went differently. And because it was the first run, "first run of the batch" and "different view" cannot be told apart for its 0.65 fps lead.
3. The p99 "median of phases" is the upper of the two middle values of six, not the median. Real medians: overlook 68.3 / 69.7 (no guard) vs 70.6 / 68.2 (guard); village 76.3 / 75.6 / 75.8 vs 75.4 / 74.6 / 73.2 ms. The conclusion (no worse with the guard) is unchanged.
4. Small points: the neighbour pair control1-guard1 is 0.64, not 0.65. "1 in 20 by chance" is the one-sided figure (two-sided 1 in 10); still a clear split.
5. The village slow/fast swing is locked to the A/B phases in all seven runs (every A slower than the B after it), not just "a roughly 40 s cycle". That fits a scene cycle that starts in step with the script. Averaging three A and three B phases still cancels it, so the price is unaffected.

**Verdict after check:** the village price of about 0.7 fps (3%, range 0.35-1.19) holds under both windows and is not caused by run order. At the overlook the best reading is about 3% as well, not "near 0". The benefit side holds: the small dark flashes go, the one-frame white flash stays. The advice also holds: opt-in line, not the default yet, and re-price on a door walk and walking fps run after the guard-door fix.
