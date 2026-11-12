# Roadmap (draft for discussion)

GrowingBlackBeans, 12 Nov 2026. A proposal, not a decision. Each milestone has exit criteria we can measure with the shared logs, so "done" doesn't depend on whoever played last. Areas past the start are named generically, to keep the public pages free of story spoilers.

## How we measure (for every milestone)

- **Hardware:** base PS5 on 13.60 first. Other firmwares (12.40, 11.40, 9.40) and the Pro get checked at each milestone, not chased in between.
- **Speed:** fps per regime (light / queued / mid / heavy, `tools/GrowingBlackBeans/eglog`), the slowest 1% of frames (p99), and the worst frame. Never a single fps.
- **Proof:** 3 runs a side for any change we adopt (`abcompare.py` "real", p < 0.05); 2 a side is a screen only.
- **Flicker:** an automatic flash count once it exists. Until then, ratings against a control in the same session.
- **Stability:** minutes played without a crash, the least free memory, and how each session ended.
- **Routes:** scripted where we have them, so runs compare. Today only the Kokiri route is shared by hand.

## Milestones

### M0: First public alpha (owner: Vampinity; in progress)
**Exit:**
- On a fresh install, a new game and Continue both reach gameplay on the first start, 3 of 3 times, on base PS5 13.60.
- The same works once each on 12.40 and one older firmware.
- An install guide exists, and the env and menu settings are picked by the build (firmware-aware), not by hand.

**Status (12 Nov):** the black screen on first start is fixed. A new game still crashes in the house on the first start and at the door on the second. The title-movie stutter is fixed in the next dev build.

### M1: The starting area is stable and clean
**Exit:**
- Kokiri route, 3 runs: no crash in 30 minutes of play.
- No pipelines built in play.
- No out-of-memory events at the area transitions.
- Flash count at control level, which for this milestone means the copy guard with every fix in. A visible-flicker rating of "none or rare" from at least two people.

**Status:**
- Pipelines built in play: done on our route (`EDEN_NX2_PRELOAD_ALL_PIPELINES=1`, 0 builds; Vampinity's refused-translation fix covers bigger caches).
- Flicker: near-gone with the one-frame guard. With two frames in flight, waveydude's two-slot guard covers both frames (12 Nov, run XG1: no frame left unguarded, against 6% with one slot), but the flicker stayed, and the next control looked cleaner. So something outside the buffer guard flickers with two frames in flight. An automatic flash counter is being built so this can be measured rather than eyeballed.
- Memory: on our Kokiri route the least free memory is 177-288 MiB, with about 0.8-1 GB of headroom at the village door. Fine here, but it's the same wall that stops M3.

### M2: 30 fps in the starting area (the first performance target)
**Exit:**
- Kokiri route, 3 runs: 95% of 5 s walking windows at 30 fps or better.
- Standing at 30 or better.
- p99 frame under 45 ms.
- No regression on M1.

**Status:**
- Standing: about 31.3 (the game's own CPU chain, with no margin).
- Walking: 24.6 with the current everyday setup, 26.7 with two frames in flight (one run).
- The gap is in windows where the back thread holds the game up through the command queue (22-24 fps).

**Work, in order of measured size:**
1. Two frames in flight: +2 fps walking, p99 -25%, no cost from the two-slot guard. Held back by the flicker above.
2. The back thread's cost per draw: the draw-end path is about 414 ms/s of its time; Lichii #1095 ports.
3. About 10% off the game's own chain, for margin: JIT memory callbacks (about 2 ms a frame), about 130 short yields a frame per thread, thread placement; Lichii #1373 is a candidate.

### M3: The first hours playable
The areas after the forest, up to and including the first dungeon.

**Exit:**
- 60 minutes of play with no crash, on 2 consoles.
- At least 25 fps in 90% of play windows.
- No pipelines built in play on a second visit.
- Memory never under 256 MiB free at a transition.

**Status:** waveydude has reached the first dungeon at 0.75× resolution, with crashes at single large allocations (32 MiB and 62 MiB requests) fixed one by one. Free memory sits at 1 MiB for long stretches. The heap's free room is stranded in other threads' arenas, and requests of 64 KiB or more never use them (Vampinity is working on the arenas).

**Work:** the memory wall first (arena fix, fragmentation, area-transition peak, VMA slack), then the M2 speed work, which carries over.

### M4: The whole game playable
**Exit:**
- Every area reachable without a crash on base PS5 13.60.
- 20 fps or better nearly everywhere.
- Saves work.
- Audio and video in cutscenes are in sync.

**Status:** the bigger areas still crash out of memory (reported by testers).

### M5: Polish
**Exit:**
- 30 fps in most of the game on a base PS5.
- Firmware coverage documented.
- The Pro has its own presets.

**Not planned:** 60 fps in gameplay. By our analysis (`technical-limits.md`), the game's own CPU chain sits near 33 ms on a base PS5, so 60 would need a game patch on top of the emulator being faster than the real console.

## Cross-cutting
- **Tools:**
  - automatic flash count (GrowingBlackBeans; Vampinity has a capture-card one);
  - scripted routes for every milestone route;
  - the shared log pool and its index.
- **Process:**
  - one line in "Who is working on what" before any job over an hour;
  - results in each person's docs folder;
  - a review cycle after each batch of runs.

## Open questions for the team
1. Is "30 fps in the starting area" the right first performance target, or should M3 (the first hours stable at 25) come first for players?
2. Who owns the memory wall (M3) alongside Vampinity's alpha work?
3. Do we want a scripted route for M2 and M3, so everyone's numbers compare directly?
