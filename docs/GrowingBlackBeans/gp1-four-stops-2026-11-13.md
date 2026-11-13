# runGP1: the game's demand is its own, and frame time is a straight line in GPU work (13 Nov)

GrowingBlackBeans. t134-gbb9, build 01.219.925, `EDEN_GBB_GPFIFO=1`, no profilers. Two frames ahead,
no read sync (the `runRX2` arm). `checkrun`: env verified, 26.23 fps over 65 windows. The benchmark
route with four standing stops, camera snapped behind Link at each, 60 s or more:

- **A** — out of Link's house, hopped down, facing down the main path
- **B** — the back of the forest, facing the Kokiri blocking the path
- **C** — the cliff edge after the ivy wall, facing out over the drop
- **D** — the shop sign at the end of the route, facing it

`anatomy.py stops` found all four from the data alone.

## The four places

| stop | fps | frame ms | ring words / frame | GPFIFO words / frame | back ms / frame | back share |
|---|---|---|---|---|---|---|
| A outside the house | 24.5 | 40.8 | 160,033 | 217,276 | 34.1 | 84% |
| B back of the forest | **34.1** | **29.3** | **92,883** | 108,589 | 17.2 | **59%** |
| C cliff edge | 27.7 | 36.1 | 142,047 | 190,531 | 29.8 | 83% |
| D shop sign | **20.7** | **48.3** | **189,075** | 259,373 | 41.2 | 85% |

**Stop C, after the fact:** pressing target at the cliff face panned the camera down, so C held a
lower view than intended (in this run and in `runGT1`). It is still a valid point for the fit — frame
time and GPU work are measured at the same moments, whatever the view — but it is not a fixed place, and
it does not compare with C in another run.

A two-to-one spread in demand between the lightest and heaviest places — the variation the fit was
missing on one route — and a clean run, so the back shares are trustworthy, unlike the profiled runs.

## Answer 1: the demand is the game's, not our front end's

Ring words against GPFIFO words: **0.74, 0.86, 0.75, 0.73.** The back receives *fewer* words than the
game submits, at every stop. So there is no amplification on the front: if anything it absorbs about a
quarter of the words itself (the likely candidates are words it handles without forwarding — macro
uploads, DMA control, semaphores — but that is inference, and nothing here pins it down).

**So the 13,294 draws a frame are genuinely what the game asks for.** Of the two levers in the earlier
write-up — fewer draws, or cheaper draws — only one exists: **the cost of each command on the back.**

## Answer 2: frame time is a straight line in GPU-thread work, measured three ways

Across the four stops: **frame = 10.21 ms + 0.195 ms per 1,000 ring words, R^2 0.968.**

| measurement | ms per 1,000 ring words |
|---|---|
| 11 Nov, 128 runs, all regimes | 0.213 |
| 13 Nov, 45 clean runs, back-paced seconds | 0.203 |
| **13 Nov, four stops in one run** | **0.195** |

Three independent methods within 9% of each other. Four points is few, but they agree with 43 and 128
runs, so this is the most solid number the project has.

## What that means for M2, in one figure

At today's cost per word, 30 fps (33.3 ms) is possible below about **118,000 ring words a frame**.
B is under it and runs at 34 fps. The other three are over it. To hold 30 fps at each, the back-thread
work has to get cheaper per word by:

| stop | ring words / frame | reduction in cost per word needed for 30 fps |
|---|---|---|
| C cliff edge | 142,047 | **17%** |
| A outside the house | 160,033 | **26%** |
| D shop sign | 189,075 | **37%** |

Fixed cost alone cannot do it: even at zero fixed cost, D would still be 36.9 ms. **The target is the
back thread's cost per command, by about a quarter to a third.** That is the first time M2 has been a
number rather than a hope, and it says where to look: `draw` is 57-58% of that cost.

## Where the game's CPU sets the pace

At B the back is only 59% of the frame and the frame is 29.3 ms, faster than 30 fps. That is the 11 Nov
two-regime picture again: light places are paced by the game's own CPU chain, heavy places by the back.
The fit holds across both here (B is predicted at 28.3 ms and measured at 29.3).

## The flicker at stop D (parked — recorded, not chased)

**Observed by eye:** continuous flashing at stop D for the full 60 s, standing still with the camera
fixed. A flicker that persists with a constant view is not camera-motion related, and it makes stop D
the ideal place to point a capture-video flash meter.

**The guard counters at each stop**, normalised per 300-present window:

| stop | "armed beside another" (two frames really in flight) per window | unguarded presents |
|---|---|---|
| A | 143 | 0 |
| B | **16** | 0 |
| C | 148 | 0 |
| D | 149 | 0 |

Two frames are in flight equally often at the three heavy stops and nine times less often at B. The
counters do **not** single D out. They make a testable prediction instead: if flashing tracks two frames
in flight, then **B was clean while A, C and D flashed.** A was already known to flash (it is the
"step out of Link's house" hotspot).

Exposure ran 1.6-2.8% in steady windows at every stop, with spikes only at the transitions; it does
not separate the stops either.

## Update: B was clean (confirmed by eye, after the prediction above was written)

The prediction held: **B clean; A and D flashing** (C was not called either way). The one stop where
two frames are rarely in flight — and where the back keeps up — was the one stop without flicker.

**What it does and does not show.** It is tempting to read this as "two frames in flight cause the
flicker". The older runs say that is too narrow:

| arm | two frames really in flight | by eye |
|---|---|---|
| `runDC1-3` one frame ahead, no read sync | **0** (only one frame ahead) | **flashes** |
| `runRE1/RE2` read sync, 250 us escape | 8 / 15 | **flashes** |
| `runDX1-3`, `runRX1/2` two ahead | hundreds | flashes |
| `runDXS1-3`, `runRO1/2` two ahead + read sync | 0 | clean |
| `runGP1` stop B | 16 a window | **clean** |
| `runGP1` stops A, D | ~145 a window | flashes |

One frame ahead flashes with **zero** frames in flight beside another, so two-in-flight cannot be the
whole mechanism. What B has that the flashing stops lack is simpler: **the back keeps up there** (59% of
the frame against 83-85%). Two frames piling up is a *symptom* of the back falling behind, not
necessarily the cause of the flicker.

**The hypothesis this leaves, stated as one: the flicker appears where the back thread cannot keep up
with the game.** Every arm in the table fits it — read sync is clean because it throttles the game down
to the back's pace; the 250 us escape flashes because it gives up waiting before the back catches up;
one frame ahead flashes at heavy places because the back still falls behind there.

**Why that matters even with the flicker parked:** if it is right, the flicker and M2 have the same
lever. Making the back 17-37% cheaper per command — the M2 target from this run — would bring the heavy
stops toward B's situation, and B is both above 30 fps and clean.

**How to test it, when the flicker comes off the shelf:** not by another guard switch. Make a heavy stop
light and see if it goes clean — for example stop D at a lower internal resolution or with distant
geometry trimmed, so the back keeps up at the same place. If D goes clean when the back keeps up, the
hypothesis holds. One run, one place, and it separates "the back is behind" from "this place is cursed".
