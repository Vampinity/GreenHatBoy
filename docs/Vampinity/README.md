# Vampinity's log

What I built, what each switch does and what my tests found. Read this before you start a big job, so we don't build the same thing twice.

| File | What is in it |
|---|---|
| [BUILDS.md](BUILDS.md) | Every test build, newest first: what it added, what it was built on, how it tested. T14 to T134. |
| [SWITCHES.md](SWITCHES.md) | Every `EDEN_...` switch, one row each: patch, default, first build that has it, values in my play settings, how many runs used it, and the latest verdict. |
| [findings/](findings/) | One note per finding from the last days (9 to 12 Nov). Each starts with two lines: what was found, and what follows from it. |

## How to search

Search by the switch name, the patch number or the build number. Plain words work too (`door`, `title movie`, `heap steal`).

- On GitHub: type this in the search box at the top:
  `repo:Vampinity/GreenHatBoy EDEN_UP_AHEAD_GUARD`
  or `repo:Vampinity/GreenHatBoy 0586`, or `repo:Vampinity/GreenHatBoy T133`.
- In a clone:
  `grep -rn "EDEN_UP_AHEAD_GUARD" docs/ patches/ CHANGELOG.md`
- An AI assistant can do the same: tell it to search `docs/`, `patches/` and `CHANGELOG.md` for the switch or the idea before it writes any code. [AGENTS.md](../../AGENTS.md) says this for it.

If the switch or the idea is already here, build on it. If it is new, claim it first in the pinned "Who is working on what" thread in Discussions.

## Being worked on now (12 Nov 2026, 10:45)

- **The house door on a fresh install.** A new game on empty caches still crashes at the house door: the heap grows about 0.7 GiB in seconds there ([door-burst-source](findings/door-burst-source-2026-11-12.md), [fresh-install-v6](findings/fresh-install-v6-2026-11-12.md)). Test round v7 is running now: settings-only ways to get through, on T134.
- **T135, planned.** It takes:
  - waveydude's fixes from his branch `w11-two-frame-guard` (the ones that apply to our tree; credited to him),
  - the title-movie settings as code defaults: 8 decoder threads and a frame delay of 4 ([title-movie-test](findings/title-movie-test-2026-11-12.md)),
  - the first-start settings that got 6 of 6 starts past the black screen ([fresh-install-v6](findings/fresh-install-v6-2026-11-12.md)).

Nothing in T135 is built yet. If you want to take one of these parts, say so in the thread first.

## Notes on these files

- They are copies of my local notes from 12 Nov, with local paths and private details taken out. Images, videos and raw logs are not included; the run logs that are public are in `runs/`.
- Paths in the notes (`queue-t132a.json`, `env-play-v27-fast-docked.txt`, folder names like `auto-20261112-...`) point to my machine. They are there so the notes stay exact, not because the files are in this repo.
- "READ" in a note means seen in a log, a frame or the source. "INFERRED" means reasoning. Most notes were checked twice; where the second check corrected the first, the corrections are listed in the note.
- One run is no verdict. Where a note gives a result from one or two runs, it says so.
