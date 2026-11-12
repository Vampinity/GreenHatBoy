# Review, night session 11-12 Nov (16 runs, t120-gbb7)

Runs: `runs/GrowingBlackBeans/2026-11-12-*`. Walking = means over the walk; "real" = every run of one side beyond every run of the other with p < 0.05 (`abcompare.py`).

| Change | Result | Status |
|---|---|---|
| Two frames ahead (0924), X1-3 | +2.0 fps walking vs 5 comparable runs (p 0.018); present wait 13 → 0.7 ms per frame; slowest 1% 75 → 57 ms; heavy windows 67% → 0%; flickers (9-15% of presents find the one-frame guard busy) | confirmed; needs a two-frame guard |
| `EDEN_UP_FRITCHII_USAGE_TRACKER=1`, U1-3 | +1.6 fps walking, +1.9 in heavy windows, back -8.5% per heavy frame (p 0.018) | **adopted** |
| `EDEN_NX2_PRELOAD_ALL_PIPELINES=1`, P1-2 | 0 pipelines built in play (controls 24-60); worst walking frame 227 → 115 ms; no boot or memory cost on the ~1,570-pipeline Kokiri cache | **adopted** |
| Two frames + tracker, XU1 | 26.7 fps walking, worst window 21.4, slowest 1% 52 ms | 1 run; repeat with the guard |
| Guard before the gpu_behind wait (0919), G2/G4 | fps unchanged; flicker same / worse by eye; guard misses 5.5-5.7% vs 4.5-4.8% | **parked** |
| Tools: vitals, timeline, flight recorder | all work; markers impractical by hand | flight recorder: skip loading, keep the triggering frame |

## What we learned
- **Frame doubling.** One frame in flight turns a GPU-side overrun into a doubled frame (80-94 ms between ~35 ms frames). It's in V1's timeline and in all four of F1's gameplay dumps; none were shader builds. Two frames in flight removes it.
- **What limits walking with two frames ahead:** windows where the back thread is over 80% busy and holds the game up through the command queue ("queued"), at 22-24 fps.
- **The game's own ceiling:** light and standing windows sat at about 31 fps in all 16 runs. That's the game chain, at the limit.
- **Eye ratings of flicker vary too much** run to run to decide on a guard; an automatic count is needed.

## Corrections
- The guess that P2's tree-line flicker improved because shader stalls had looked like dark flashes is unproven: there were no skipped draws, and the guard misses were unchanged.
- `abcompare.py` called 2-a-side splits "consistent"; with 2 a side, noise does that 1 time in 3. It now says "screen only".

## Plan
1. **Flash count** (gbb8): mean luminance of each presented frame, compared with a running median; a jump and return within 1-2 frames counts as a flash. Logged every second and per event.
2. **Two-frame guard** (gbb9): copies kept per frame generation, so two frames in flight each read the bytes they were presented with.
3. **Session** (`session-plan-2026-11-12.md`): 3 controls, 3 two-frames-ahead without the guard, 3 with it, all with the flash count.
4. **Then:** the back thread's cost per draw (the draw-end path; Lichii #1095), a rebase onto T130, and about 10% off the game chain.
