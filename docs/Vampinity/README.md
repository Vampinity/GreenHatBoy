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

## Being worked on now (12 Nov 2026, evening)

- **The very first start on a fresh install.** Five settings-only rounds on T134 (v7 to v11) settled it:
  - From the second start on, the house door is solved: 16 of 16 warm starts reached the village, with `EDEN_NX2_PIPELINE_WORKERS=2` (one group had `=1`).
  - A true first start (empty caches) reached the village 4 of 9 times with the best settings, none with memory to spare. The deaths are mostly at the house door, most of them a `std::bad_alloc` on the file-service thread (about 0.9 MB asked, where the size was logged).
  - The cause is the wave at a cold door: about 40 new pipelines are built there at once and the heap grows by 0.4-0.8 GiB within ~2 s. `EDEN_UP_NEW_WAIT_MS=2000`, `EDEN_UP_HEAP_RESCUE=1` and the two `EDEN_UP_IR_FREE` lines did not stop it: 2 of 4 first starts with all of them on.
  - Notes: [fresh-install-v7](findings/fresh-install-v7-2026-11-12.md), [fresh-install-v8](findings/fresh-install-v8-2026-11-12.md), [fresh-install-v10](findings/fresh-install-v10-2026-11-12.md). Rounds v9 and v11 have no note of their own: v9 lost both first starts with the wait and the rescue on (the wait fired for an 871,571-byte file-service request, waited its 2000 ms and gave up), and v11 lost both first starts with v10's first group's settings.
- **A first fix, turned down in review, not built.** A byte budget for pipeline builds in flight (`EDEN_UP_BUILD_BUDGET_MIB`). With two builders it can only mean one build at a time, and one builder was already measured cold on 12 Nov: door waves of +640 and +608 MiB, against +544 and +448 MiB with two. So fewer builds at once does not shrink the wave.
- **Next: a measuring build.** One log line per window at the door that names the thread whose requests made the heap grow (the existing per-thread growth counter, printed with thread names). The wave is 450 to 810 MiB in heap pieces while live bytes rise only 26 to 66 MiB, so the owner is not known yet; it may sit outside the builder threads.
- **T135, written, not built.** It hands back whole heap spaces that hold only idle arenas (`EDEN_UP_ARENA_SPACES=1`, off by default). Two reviews put its net gain before the door at about -100 to +130 MiB, against a wave of ~800 MiB, so it is a measurement build at most, not the fix.
- **Planned for a coming build, unchanged since the morning:**
  - waveydude's fixes from his branch `w11-two-frame-guard` (the ones that apply to our tree; credited to him),
  - the title-movie settings as code defaults: 8 decoder threads and a frame delay of 4 ([title-movie-test](findings/title-movie-test-2026-11-12.md)),
  - the first-start settings that got 6 of 6 starts past the black screen ([fresh-install-v6](findings/fresh-install-v6-2026-11-12.md)).

If you want to take one of these parts, say so in the thread first.

## Notes on these files

- They are copies of my local notes from 12 Nov, with local paths and private details taken out. Images, videos and raw logs are not included; the run logs that are public are in `runs/`.
- Paths in the notes (`queue-t132a.json`, `env-play-v27-fast-docked.txt`, folder names like `auto-20261112-...`) point to my machine. They are there so the notes stay exact, not because the files are in this repo.
- "READ" in a note means seen in a log, a frame or the source. "INFERRED" means reasoning. Most notes were checked twice; where the second check corrected the first, the corrections are listed in the note.
- One run is no verdict. Where a note gives a result from one or two runs, it says so.
