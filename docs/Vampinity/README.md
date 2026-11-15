# Vampinity's log

What I built, what each switch does and what my tests found. Read this before you start a big job, so we don't build the same thing twice.

| File | What is in it |
|---|---|
| [BUILDS.md](BUILDS.md) | Every test build, newest first: what it added, what it was built on, how it tested. T14 to T187. |
| [SWITCHES.md](SWITCHES.md) | Every `EDEN_...` switch, one row each: patch, default, first build that has it, values in my play settings, how many runs used it, and the latest verdict. |
| [findings/](findings/) | One note per finding from the last days (9 to 15 Nov). Each starts with two lines: what was found, and what follows from it. |

## How to search

Search by the switch name, the patch number or the build number. Plain words work too (`door`, `title movie`, `heap steal`).

- On GitHub: type this in the search box at the top:
  `repo:Vampinity/GreenHatBoy EDEN_UP_AHEAD_GUARD`
  or `repo:Vampinity/GreenHatBoy 0586`, or `repo:Vampinity/GreenHatBoy T133`.
- In a clone:
  `grep -rn "EDEN_UP_AHEAD_GUARD" docs/ patches/ CHANGELOG.md`
- An AI assistant can do the same: tell it to search `docs/`, `patches/` and `CHANGELOG.md` for the switch or the idea before it writes any code. [AGENTS.md](../../AGENTS.md) says this for it.

If the switch or the idea is already here, build on it. If it is new, claim it first in the pinned "Who is working on what" thread in Discussions.

## Being worked on now (15 Nov 2026, early morning)

- **The scripted gate on T186, with frame ahead off.** Frame ahead is off since 14 Nov: with it on, the ground near Link loses its sunlight for a frame and flags and cloth blink; with it off, 0 of either in our tests ([frame-ahead-flicker](findings/frame-ahead-flicker-2026-11-14.md)). The candidate play settings v4.0 ([`envs/Vampinity/play-v40.env.txt`](../../envs/Vampinity/play-v40.env.txt), arm CB) got through the load from the field into the next area 6 of 6 times in scripted starts on T185, and the graphics thread never waited for memory ([load-window](findings/load-window-2026-11-14.md)). Not cleared: in one start a game thread waited 4.0 s inside the black. Not played by hand yet. Counts per build in [BUILDS.md](BUILDS.md).
- **The memory wall at that load**, the part I took in discussion 5. With 384 MiB or more taken away before the load (a stand-in for a long session) the candidate crawls, and at 576 MiB it crashed (one start each). `EDEN_UP_DRAIN_TO_POOL=1` got 2 of 2 through in two batches with 512 MiB taken away; T186's `EDEN_UP_DRAIN_ON_GROWTH=1` 2 of 2 in one batch. Neither is in the play settings yet.
- **Flashes**, the other part I took in discussion 5: the ground flashes and the cloth blink go with frame ahead off; the rarer kinds are judged in longer play.
- **Speed in the area after the field** (about 14 fps with frame ahead off, handheld, 1x): the command reader waits on the graphics chip about 18 ms a frame, nearly all of it for one grid list ([reader-list-wait-t186](findings/reader-list-wait-t186-2026-11-15.md)). That wait is the next thing to work on.
- **Census tables** of the transitions and the crashes over my scripted runs, with GrowingBlackBeans' four columns. They go up once they are checked.
- **The house door on a first start:** the cause was one graphics driver compile. With `EDEN_NX2_RADV_COPY_PROP_FREE=1` it takes 78 to 89 MB instead of up to 909 MB, and 2 of 2 scripted first starts got through into the village (T144, docked, 1x, [door-compile-fix-t144](findings/door-compile-fix-t144-2026-11-13.md)). With the candidate settings and the shaders already built, 2 of 2 first starts on a new game reached the village (T185, handheld, 1x).

If you want to take one of these parts, say so in the thread first.

## Notes on these files

- They are copies of my local notes from 9 to 13 Nov, with local paths and private details taken out. The notes of 14 and 15 Nov are shorter summaries of checked readings. Images, videos and raw logs are not included; the run logs that are public are in `runs/`.
- Paths in the notes (`queue-t132a.json`, `env-play-v27-fast-docked.txt`, folder names like `auto-20261112-...`) point to my machine. They are there so the notes stay exact, not because the files are in this repo.
- "READ" in a note means seen in a log, a frame or the source. "INFERRED" means reasoning. Most notes were checked twice; where the second check corrected the first, the corrections are listed in the note.
- One run is no verdict. Where a note gives a result from one or two runs, it says so.
