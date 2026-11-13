# Scripted Kokiri route with fixed stops: plan (13 Nov 2026)

**Why it's needed.** The anatomy plan's own rule: "if places disagree, the scripted route stops being
optional". They do. Hand-played stops also drift: A and B repeat within 0.4% and 1.2%, the old stop C
panned in two runs, and stop D fell 12% over three runs (`docs/GrowingBlackBeans/kokiri-stops.md`). A script puts Link on the same
point, facing the same way, on every run, with nobody at the controller.

## What already exists (standing-rule overlap check, GHB fetched 13 Nov, head c6b0df7)

| Piece | Where | State |
|---|---|---|
| Script runner: WAIT / LOOK / GONE / MAYBE / END / STEER | `headless/test_harness.h`, **already in gbb9** | Vampinity's; run by him on T160-T181 only, never on a T134 build |
| Minimap tracker (Link's position + camera bearing) | `headless/minimap_steer.h`, in gbb9 | calibrated on 9 Nov video: arrowhead found 99-100% of village frames |
| Input recorder `EDEN_TEST_RECORD=1` | test_harness.h, in gbb9 | writes `logs/recorded-input.txt` in script format |
| Save protection `EDEN_TEST_DISCARD_SAVE=1` | savedata_factory.cpp, **in gbb9** | game saves go to a throwaway copy; Vampinity's README thought it was missing from T134 builds, but ours has it |
| LOOK-grid cutter | our `eglog/make-look.py` | tested; Vampinity's README now points at it |
| House → door opening (title, Continue, load, door) | `tools/Vampinity/routes/house-door-village.txt` | 16 of 18 starts got through the door |
| **Kokiri STEER scripts** | Vampinity runs `run1076` (tunnel mouth, 13 points, met) and `run1110` (exit control, 32 + 1 + 5 points, all met, script done) | **the script files aren't in GHB**; only three other routes are shared |
| Turning a recorded walk into STEER points | `steer-route.py` / `tools/steer_cli.cpp` (named in the harness headers) | **not public**; README: "that tool is not in this folder yet" |

So almost everything is built. Two pieces are missing: Vampinity's Kokiri point lists, and the tool
that turns a recording into points.

## How each part of "a fixed stop" is pinned, without a new build

| Part of the stop | How | Check in the log |
|---|---|---|
| Where Link stands | STEER to the stop point; it's only met within r per mille (default 6) | `steer_met line=..` |
| Which way he faces | an approach point just before each stop point, so the last leg always runs the same way; then ZL swings the camera behind him | same |
| Camera tilt and what's on screen | a one-look `MAYBE 1 LOOK` of the whole screen at the start and end of each stand. It never matches, so it times out, and `wait_skipped` prints the grid it saw | compare the `seen=` grids across runs |
| Nothing moving | the cross-run ring-words check (~3%) | `anatomy.py stops` |

**One rule for the stands.** Don't use a never-matching MAYBE as the 60 s stand, as Vampinity's
`-stand` route does: a WAIT reads the whole frame back every 500 ms, which would land in the window
we measure. A stand is just a gap in the script's seconds, with no WAIT, so no readbacks.
STEER does read frames back while walking, but only on the walking legs, never at the stops.

Optional, not needed to start: a small patch that adds `x=`, `y=` and `angle=` to the `steer_point`
and `steer_met` lines, so each run records where it actually stopped instead of "within 6 per mille".

## Steps

**0. Desk: ask before building.** Asked Vampinity in D5 (13 Nov) for (a) the
`run1076` and `run1110` Kokiri script files and (b) `steer-route.py` / `steer_cli.cpp`. If his
points cover our route, step 2 shrinks to editing them.

**1. Console: one recorded walk.** gbb9, the GP1 env, plus `EDEN_TEST_RECORD=1`. Start from a save in
Link's house that is the newest entry. Play the benchmark route with the four stops as usual (ZL, 60 s),
and record it with the PS5's own capture (Create button) at the same time. The recording gives
the minimap path; `recorded-input.txt` gives the stick and button timings for the parts STEER can't
do: the ivy-wall climb and the hops. This is also a normal counts run, a fourth sample of A-D.

**2. Desk: build the script.**
- If Vampinity's tool doesn't come: write `steer-route.py`, a faithful Python port of
  `minimap_steer::Find`, run over the capture video, the same way `make-look.py` ports `GridOf`.
  Test it against the C++ on the same frames: `minimap_steer.h` has no dependencies, so a ten-line
  host program can run the real `Find` on the same extracted frames.
- Opening: Vampinity's house-door lines unchanged (title, Continue, load, door).
- Then STEER legs to A, B, C, D. Each stop gets an approach point, then STEER to the stop, then ZL,
  then a 1-look fingerprint, a 65 s gap, a second fingerprint, and the next leg.
- Risky legs: the ivy-wall climb and the cliff path near stop C (a fall ends the run). Those may need
  open-loop pushes taken from the recording, as Vampinity's bridge leg uses, with points kept well
  back from the edge.

**3. Console: three scripted counts runs** with `EDEN_TEST_DISCARD_SAVE=1` (and your save backed
up once anyway). Pass mark: all four `steer_met` lines at every start, ring words at each stop
within ~3% across runs, and matching fingerprint grids. If a stop fails, move its point and run again.

**4. Then the script is the route** for every comparison that needs 4 runs a side (abcompare's
floor), and for repeats of GP1/GT1/GS1 that can be compared stop for stop.

## What it does not fix

- The harness clock is wall time and the walk varies by ~30 s between starts (Vampinity's field
  route). Line up measurements by the `steer_met` lines, not by script seconds.
- STEER only moves the left stick. Anything else in the route (climbing, hops, ZL) is timed presses.
- The tracker only works where the minimap is on screen: not in Link's house, not during a scene.
