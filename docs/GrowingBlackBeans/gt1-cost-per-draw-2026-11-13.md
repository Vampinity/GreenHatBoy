# runGT1: the heavy places are heavy because each draw costs more, not because there are more (13 Nov)

GrowingBlackBeans. t134-gbb9 (01.219.925), `EDEN_GBB_BACK_CALLS=1` only, the same four standing stops
as `runGP1`. `checkrun` OK, 22.98 fps. `anatomy.py stops` found all four.

## Which stops can be compared with runGP1

The comparison only holds where the same view was on screen, so ring words per frame are the check:

| stop | ring words runGP1 | runGT1 | |
|---|---|---|---|
| A outside the house | 160,033 | 160,727 | same (+0.4%) |
| B back of the forest | 92,883 | 92,609 | same (-0.3%) |
| C cliff edge | 142,047 | 167,100 | **different (+18%)** — not compared; see below |
| D shop sign | 189,075 | 176,710 | close (-7%) |

**Why C differs, from the player:** at the cliff face, pressing target made the camera pan down, in
**both** runs, so C did not hold the same view as the other stops. The camera tilted early and then held
a lower angle, which is why each C still reads as a steady stop: inside each stop the spread is 1.8% in
`runGP1` and 4.0% in `runGT1`, and the drift at C (-1.9% / -7.7%) is no larger than at A in `runGT1`
(-7.8%), where nothing panned. **The stop detector cannot see a pan; the comparison across runs did.**
That cross-run check on ring words per frame is the safeguard to keep using. For the next run with these
stops, stand a step back from the cliff face so targeting does not tilt the camera.

## What the back-call timer costs on its own — and a correction

Measured for the first time, from the two matched stops:

| stop | back thread, clean | with the timer | | fps clean | with the timer |
|---|---|---|---|---|---|
| A | 34.1 ms | 42.0 ms | **+23%** | 24.5 | 21.4 (-12.7%) |
| B | 17.2 ms | 21.7 ms | **+26%** | 34.1 | 33.8 (-0.9%) |

**`EDEN_GBB_BACK_CALLS` adds about a quarter to the back thread's time.** It costs frame rate only where
the back sets the pace (A), not where the game's own CPU does (B). `LOGS.md` lists it as "expected under
2%, not yet measured"; it is now measured, and it is not small.

**Correction.** Earlier tonight I wrote that `runV1` against `runRD1` shows "the thread profiler is the
expensive instrument, not the back-call timer". That comparison only showed the thread profiler adds
about 12% *on top of* the back-call timer. On its own the back-call timer costs about 25%. Both are
expensive. The profiled runs' "87-90% back share" carried both, which is why clean runs read 71%.

## The result: draw count is nearly flat; draw cost doubles

| stop | fps | draws / frame | cost per draw | draw ms / frame | all commands ms / frame | draw share |
|---|---|---|---|---|---|---|
| B (light) | 33.8 | 11,583 | **0.674 us** | 7.81 | 14.78 | 53% |
| A | 21.4 | 13,990 | 1.301 us | 18.20 | 30.94 | 59% |
| D (heaviest) | 18.9 | 14,461 | **1.514 us** | 21.89 | 35.94 | 61% |
| C (unmatched) | 20.2 | 13,758 | 1.444 us | 19.87 | 33.38 | 60% |

Between the lightest and heaviest stop, **draws per frame rise 25% but the cost of each draw rises 125%.**
Draw's share of command time is 53-61% everywhere — the same 57-58% `runRD1` and `runV1` showed — so
`draw` dominates at every place, and it is the *per-draw* cost that moves.

The timer's overhead is roughly a fixed amount per ring entry, so it inflates every absolute figure
above by about a quarter, but it cannot manufacture a 2.2x difference between two places. The ratio is
the finding; the microseconds are not clean.

## What it means for M2

The earlier framing was "fewer draws or cheaper draws", then (from `runGP1`) "the draws are the game's,
so only cheaper draws". This narrows it again: **the draw count is the game's and is roughly constant;
what makes a place heavy is how much work each draw does when it is issued.** In this emulator family a
`draw` register write is where state set since the last draw is validated and committed — pipeline,
descriptors, buffers, render targets — so a busier scene means more state to commit per draw.

That points at one code path rather than the whole back thread: the work done at draw time (the
"draw-end path" in the roadmap's M2 item 2, where a Lichii #1095 port is already named). And B shows the
size of the prize: at B's 0.67 us a draw, D would spend about half what it does on draws.

Ring words per draw back this up — B about 8, A about 11.5, D about 12.2 — heavier scenes push more
state between draws, and each draw then has more to commit.
