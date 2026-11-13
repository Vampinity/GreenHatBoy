# Closing the anatomy phase: the four decision rules against what we measured (13 Nov, late)

GrowingBlackBeans. Desk only. Sources: `runGP1`, `runGT1`, `runGS1` (four standing stops, t134-gbb9),
the fit over 45 clean local runs (`anatomy.py fitall`), and one new cut of those 45 runs below. The rules
are the ones written into the plan before any of this was measured (night review, section 10).

## The question the phase was set

For each place: what the game asks the emulator for, what each stage spends supplying it, what one unit
of demand costs, and what we can afford at 30 fps.

| | answer | how solid |
|---|---|---|
| What the game asks for | ~108k-259k GPFIFO words a frame by place; 11.6k-14.5k draws a frame | two runs, ratio repeats to 0.01 |
| Is it the game's own, or our front end's? | **the game's**: ring/GPFIFO 0.73-0.86, nothing amplified | `runGP1` and `runGS1` |
| What one unit costs | **0.195-0.213 ms per 1,000 ring words**, three independent ways | 4 stops, 45 runs, 128 runs |
| What the frame costs with no work | ~10.2 ms fixed | the same fits |
| Where the back's time goes | `draw` 53-61% of back command time at every place | `runGT1`, `runV1`, `runRD1` |
| What makes a place heavy | **each draw costs more** (0.67 → 1.51 us, +125%); draws rise only 25% | `runGT1`, within one run |
| What 30 fps allows | below ~118k ring words a frame at today's cost | the fit |

## Rule 1: "any class over 2x its 30 fps budget becomes a work item"

Only one demand class is identified (ring words; GPU submissions correlate at r = 0.985 and the rest
come out negative). Its affordable cost at each stop, (33.3 ms - 10.2 ms fixed) / words a frame:

| stop | ring words / frame | affordable ms per 1k | measured | over budget by |
|---|---|---|---|---|
| B | 92,883 | 0.249 | 0.195 | under |
| C (old spot) | 142,047 | 0.163 | 0.195 | 1.2x |
| A | 160,033 | 0.144 | 0.195 | 1.35x |
| D | 189,075 | 0.122 | 0.195 | 1.6x |

**Nothing is over 2x, so the rule as written doesn't fire.** Its fallback ("then the frame is fixed
cost and the target is the dispatch loop") doesn't apply either: fixed cost is 10 ms of a 41-48 ms
frame. The 2x line was set before we knew there would be one class, not several. Read plainly, the
result is **one work item, with its size measured: back-thread cost per word 17-37% cheaper**, worth
15 ms a frame at D, 7.5 at A and 2.8 at C. Inside that item, `draw` is most of the cost, and the
per-draw cost is what moves between places.

## Rule 2: "if the residual is over ~25%, find what's unmeasured before optimising"

- **Where the back sets the pace:** four stops R^2 0.968; 45 runs, one point each, R^2 0.792. Doesn't fire.
- **Where it doesn't:** 27% unexplained. **This fired**, and it isn't resolved. The unmeasured stage
  is the one 11 Nov named, the game's own CPU chain, which vitals doesn't carry.

A new cut of the same 45 runs (first 60 s skipped, 8,247 seconds) shows how much that matters:

| seconds | count | median frame | at or under 34.5 ms | over 40 ms |
|---|---|---|---|---|
| back busy >= 80% of the frame | 2,002 | 39.7 ms | 20% | 49% |
| back busy < 80% | 6,245 | **32.2 ms** | **60%** | 20% |

Most seconds the back doesn't pace are **already at the game's 30 fps**, so the unexplained 27% is
mostly in frames that are fine. Of the **slow** seconds (over 40 ms, 2,251 of them), the back is busy a
median **79%** of the frame, and at least 60% in 90% of them. So the slow frames are mostly back
frames, even when the 80% line doesn't call them that. The residual stays open, ranked below the back.
The data to start on it is `EDEN_GBB_SVC_PROFILE`, which is in 7 runs.

## Rule 3: "if every place returns the same verdict, one stage owns M2"

They don't. A, C and D are back-bound (83-85% of the frame). B is paced by the game's CPU (back 59%,
29.3 ms, faster than 30 fps). And Vampinity's later area runs 17-21 ms slower than the Kokiri fit
predicts for its ~181k words, a gap the fit doesn't explain.

## Rule 4: "if places disagree, the scripted route stops being optional"

**Fired.** It's planned in `scripted-route-plan-2026-11-13.md`, and needs no new build. Fixed places are also
thinner than the method assumed: only A (0.4%) and B (1.2%) repeat across runs; D drifted 12%.

## The ranked problem list this phase leaves

1. **Back-thread cost per draw.** 17-37% at the heavy Kokiri stops. It's the work committed at draw
   time: the roadmap's M2 item 2, draw-end path, where a Lichii #1095 port is already named. If the
   parked flicker hypothesis holds ("it flashes where the back can't keep up"), this is the same lever.
2. **The later area's 17-21 ms the fit doesn't explain.** Needs the anatomy run there; Vampinity's
   draws-per-frame counts are the first piece.
3. **The game's CPU chain**, the 27% residual. Mostly in frames already at 30 fps, so third.

## What the phase didn't cover (said so it isn't assumed)

- Demand classes never put in the fit: texture uploads and decodes (`EDEN_NX2_TC_LOG`), guest SVC waits,
  reads of GPU-written memory, writes to GPU-tracked pages. The first is in 113 runs and unread here.
- Per-method costs come from runs with a timer that adds ~25% to the back. The ratios hold; the
  microseconds don't.
- Four places in one area. The fit is Kokiri's; the later area already disagrees with it.
