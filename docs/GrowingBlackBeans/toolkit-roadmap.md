# Log toolkit: what's built, what's designed, what's next

GrowingBlackBeans, 11 Nov 2026, brought up to date 13 Nov (late). The tools live in
`tools/GrowingBlackBeans/eglog/` (its README says which are tested and how); the patches are in
`patches/GrowingBlackBeans/t134/`. This page tracks the rest of the plan, so anyone can pick a piece up.

## Built

| Piece | Where | State |
|---|---|---|
| Parser, per-run report, A/B with noise (cross-run and in-run live phases), run checker, ingest, regimes index | `eglog/` | tested on every run in this repo |
| Guide to every log line, with each switch's measured cost | `eglog/LOGS.md` | |
| Back-thread breakdown (`EDEN_GBB_BACK_CALLS`) | patch 0921 | ran (V1, RD1, GT1). **Costs about 25% of the back's time**: counts only, not times |
| Per-second vitals (`EDEN_GBB_VITALS`), per-event timeline and reader | patch 0922, `eglog/timeline.py` | ran; reader tested on a real capture |
| Flight recorder, effective env line, touchpad + R3 marker | patch 0923 | ran; the marker is too awkward to press while playing |
| Flash counter (`EDEN_GBB_FLASH`) | patch 0928, `eglog/flashes.py` | **retracted as a flicker measure**. Use Vampinity's `tools/Vampinity/flash-counter/` on capture video |
| GPFIFO counter (`EDEN_GBB_GPFIFO`): what the game submits, per channel | patch 0934, host test 16/16 | ran twice (GP1, GS1): ring/GPFIFO 0.73-0.86, the demand is the game's own |
| Per-session log folders (`EDEN_GBB_LOG_SESSION`) | patch 0935 | built (gbb9); not yet switched on in a run |
| Frame anatomy: per-window demand and supply, per-method cost, fit, 30 fps budget, fit across many runs, GPFIFO ratio, stops found from the data, `EDEN_UP_SUBMIT_STATS` reader | `eglog/anatomy.py` (`table methods fit budget fitall gpfifo stops submits`) | tested on RD1/RD2/V1, 45 clean runs, GP1/GT1/GS1 |
| The copy guard's own counters (arming, exposure, two frames in flight) | `eglog/guard.py` | tested on 77 runs |
| LOOK grids for the test harness, cut from a picture with the harness's own arithmetic | `eglog/make-look.py` | self-test 8/8; Vampinity's routes README points at it |

## Designed, not built

### Scripted Kokiri route with fixed stops

- **Why:** the anatomy's own rule fired. Places disagree, and hand-played stops drift (A and B repeat
  within 0.4% and 1.2%; D drifted 12% over three runs). A script puts Link on the same point, facing
  the same way, every run.
- **How:** Vampinity's test harness (`headless/test_harness.h`, STEER over `minimap_steer.h`) is
  already in t134-gbb9, with `EDEN_TEST_RECORD` and `EDEN_TEST_DISCARD_SAVE`. The plan:
  `docs/GrowingBlackBeans/scripted-route-plan-2026-11-13.md`. It needs no new build.
- **Missing:** Kokiri STEER point lists, and a tool to turn a recorded walk into points
  (`steer-route.py`, named in the harness, not public). Asked for first. If they can't be shared, we
  write it as a Python port of `minimap_steer::Find`, the way `make-look.py` ports `GridOf`.

### Where the player is

Replaced by the minimap tracker: STEER pins the position to within r per mille. A small optional
patch would add `x=`, `y=` and `angle=` to the `steer_point` / `steer_met` lines. The guest-memory
scene/room reader designed on 11 Nov is no longer needed for this.

## Ideas not yet designed

- Put texture uploads and decodes (`EDEN_NX2_TC_LOG`, in 113 runs) and guest SVC waits into the
  anatomy fit. They are the demand classes it hasn't covered.
- Guest-thread state sampling into the timeline (which guest thread is running or waiting at each present).
- Host CPU placement (which PS5 core each host thread runs on), to check SMT contention.

## Where the anatomy phase ended

`docs/GrowingBlackBeans/anatomy-phase-closeout-2026-11-13.md`: the four decision rules against what
was measured, and the ranked problem list (back cost per draw first).
