# Vampinity's log

What I built, what each switch does and what my tests found. Read this before you start a big job, so we don't build the same thing twice.

| File | What is in it |
|---|---|
| [BUILDS.md](BUILDS.md) | Every test build, newest first: what it added, what it was built on, how it tested. T14 to T183. |
| [SWITCHES.md](SWITCHES.md) | Every `EDEN_...` switch, one row each: patch, default, first build that has it, values in my play settings, how many runs used it, and the latest verdict. |
| [findings/](findings/) | One note per finding from the last days (9 to 13 Nov). Each starts with two lines: what was found, and what follows from it. |

## How to search

Search by the switch name, the patch number or the build number. Plain words work too (`door`, `title movie`, `heap steal`).

- On GitHub: type this in the search box at the top:
  `repo:Vampinity/GreenHatBoy EDEN_UP_AHEAD_GUARD`
  or `repo:Vampinity/GreenHatBoy 0586`, or `repo:Vampinity/GreenHatBoy T133`.
- In a clone:
  `grep -rn "EDEN_UP_AHEAD_GUARD" docs/ patches/ CHANGELOG.md`
- An AI assistant can do the same: tell it to search `docs/`, `patches/` and `CHANGELOG.md` for the switch or the idea before it writes any code. [AGENTS.md](../../AGENTS.md) says this for it.

If the switch or the idea is already here, build on it. If it is new, claim it first in the pinned "Who is working on what" thread in Discussions.

## Being worked on now (14 Nov 2026, early morning)

- **The load from the field into the next area.** Played by hand on 13 Nov every start crashed, the last three at this load. In scripted starts (handheld, 1x) most starts now get through, the more so with the lines that pack idle game memory sooner. Both deaths on T179 were the same kind: a thread waited 10 s for one 2 MiB block while no frame was drawn, so nothing freed memory. T181 adds `EDEN_UP_WAIT_RECLAIM=1` for that: 3 of 3 through with it, 2 of 3 with v3.9 alone in the same round. Not played by hand yet. Counts per build in [BUILDS.md](BUILDS.md) and the 13 November entry of the [changelog](../../CHANGELOG.md).
- **The area after the field runs at about 15 fps** (T180, handheld, 1x). The graphics work there takes about 41 ms a frame, against 17 to 19 in the field. T183 adds `EDEN_UP_GFX_SCALE_TIER` (the game draws its own 3D smaller when asked) and the Lichii draw ports of T182 and T183, all off by default and not run yet.
- **The house door on a first start:** the cause was one graphics driver compile. With `EDEN_NX2_RADV_COPY_PROP_FREE=1` it takes 78 to 89 MB instead of up to 909 MB, and 2 of 2 scripted first starts got through into the village (T144, docked, 1x, [door-compile-fix-t144](findings/door-compile-fix-t144-2026-11-13.md)).

If you want to take one of these parts, say so in the thread first.

## Notes on these files

- They are copies of my local notes from 9 to 13 Nov, with local paths and private details taken out. Images, videos and raw logs are not included; the run logs that are public are in `runs/`.
- Paths in the notes (`queue-t132a.json`, `env-play-v27-fast-docked.txt`, folder names like `auto-20261112-...`) point to my machine. They are there so the notes stay exact, not because the files are in this repo.
- "READ" in a note means seen in a log, a frame or the source. "INFERRED" means reasoning. Most notes were checked twice; where the second check corrected the first, the corrections are listed in the note.
- One run is no verdict. Where a note gives a result from one or two runs, it says so.
