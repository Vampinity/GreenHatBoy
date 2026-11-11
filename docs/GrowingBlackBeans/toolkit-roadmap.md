# Log toolkit: what's built, what's designed, what's next

GrowingBlackBeans, 11 Nov 2026. The tools live in `tools/GrowingBlackBeans/eglog/` (see its README for tested/untested). This page tracks the rest of the plan, so anyone can pick a piece up.

## Built

| Piece | Where | State |
|---|---|---|
| Parser, per-run report, A/B with noise (cross-run and in-run live phases), run checker, ingest, regimes index | `eglog/` | tested |
| Guide to every log line | `eglog/LOGS.md` | |
| Back-thread breakdown (`EDEN_GBB_BACK_CALLS`) | patch 0921 | built, never run |
| Per-second vitals (`EDEN_GBB_VITALS`), per-event timeline (`EDEN_GBB_TIMELINE`) and reader | patch 0922, `eglog/timeline.py` | built, never run; reader tested on synthetic data |
| Flight recorder (`EDEN_GBB_FLIGHT`), effective env line, touchpad + R3 marker | patch 0923 | built, never run |

## Designed, not built

### Where the player is (scene and room per second)

- **Why:** compare windows by place instead of by time, across routes and people. "Heavy" is a property of where you stand.
- **How:**
  - find the game's current-scene and current-room variables in guest memory (the decomp layout of the original game is a starting point; the Switch 2 build will differ);
  - confirm them with a memory scan across a door transition;
  - log `EDEN_GBB_WHERE scene=.. room=.. pos=x,y,z` once a second from the present thread, reading guest memory through the memory manager.
- **Blocker:** the addresses. This needs a session with a debugger or a guest memory dump on both sides of a door. Patch 0903 can dump guest code; data dumps are similar.

### Automatic flash count

- **Why:** an objective flashes-per-minute instead of impressions. One of the run formats already has a `flashes_per_min` field; check how it's computed first and reuse it.
- **How:**
  - after Composite, a tiny compute pass reduces the presented image to its mean luminance (64×64 downsample, then a sum) into a ring of 32-bit values;
  - read it back a few frames late (no stall);
  - log a flash when luminance jumps more than k sigma from the running median for one or two frames, then returns;
  - log `EDEN_GBB_LUMA` per second (min, median, max) and `EDEN_GBB_FLASH frame=.. delta=..`.
- **Cost:** one small dispatch per present.

### Scripted Kokiri route

- **Why:** hand-played runs differ by up to 3.6 fps; the share of heavy windows swings from 0.3 to 0.9 with where you walk. A scripted route makes runs comparable and lets them happen without a player.
- **How:** write our route (Continue, through Link's house, out, the walking loop to the water) in the existing script-runner format, which drives the development input file (`headless/development_input.h`: "id mask duration [lx ly rx ry]"). Record the hand route once with markers to get the timings.

### Per-session log folders

- **Why:** the console's `logs/` folder piles up files from earlier sessions: samples, crash logs, guest code dumps. `checkrun.py` lists them, but a folder per session would remove the confusion at the source.
- **How:** logs go to `logs/<date>-<pid>/`. Needs agreement on the shared layout first, because other tools read `logs/` directly.

## Ideas not yet designed

- Guest-thread state sampling into the timeline (which guest thread is running or waiting at each present), to see the game's own chain frame by frame.
- Host CPU placement (which PS5 core each host thread runs on), to check SMT contention.
