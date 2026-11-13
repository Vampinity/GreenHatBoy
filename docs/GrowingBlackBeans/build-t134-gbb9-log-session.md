# t134-gbb9: one folder per session (patch 0935)

GrowingBlackBeans, 13 Nov 2026. **01.219.925**, in `EglantinePS5-package/t134-gbb9`, commit `3b94348`.
Symbols at `/work2/keep/t134-gbb9-llvm-pie.elf`. Built with `EDEN_SKIP_SOURCE_CHECKS=1`, BUILD-EXIT=0,
switch and log line confirmed in the eboot.

| Switch | What |
|---|---|
| `EDEN_GBB_LOG_SESSION=1` | Boot, off by default. The dumps **this build** writes go to `/data/eglantineps5/logs/s<YYYYMMDD-HHMMSS>-<pid>/` instead of straight into `logs/`. Unset, every path is byte-for-byte what it was. One line at first use naming the folder. |

## Why

The console's `logs/` keeps every session's dumps, so copying it after a run brings all the earlier ones
along. **Every `checkrun` we run says so** — "183 files in logs/ are not from this session" — and on
13 Nov it nearly cost a conclusion: twelve runs each held twelve sessions' flash-grid files, and the
right one could only be found by reading the pid out of each run's own log.

This is the general version of 0929's `DeleteOtherSessions`, which deletes our own writers' older files
before writing. That only ever covered the prefixes we pass it, and the bulk of the clutter is not ours.

## Scope, stated plainly

**Moved:** the flash grids (`gbb-flash-<pid>.bin`), the timeline (`gbb-timeline-<pid>.bin`) and the
flight recorder (`gbb-flight-<pid>-<k>.bin`) — the three writers we own, and the big ones (a grid file
is 45 MB).

**Not moved**, because they belong to other people's code and the layout is shared:

| file | written by |
|---|---|
| `guest-main+<offset>.bin` (81 per run folder) | `core.cpp` |
| `sample-<pid>-<window>-<thread>.bin` | the stack sampler in the frontend |
| crash reports | the crash handler |
| `eden_log.txt`, `stderr.log` | the launcher |

Each is a one-line change to call `VideoCommon::GbbLogDir::Path`. They are left for their owners, or to
agree on first — the toolkit roadmap flagged exactly this ("needs agreement on the shared layout first,
because other tools read `logs/` directly"), and unset changes nothing for anyone either way.

When the session folder is in use, 0929's sweep is skipped: inside its own folder there is nothing of
another session's to delete.

## Toolkit

`checkrun.py` now names the session folder when it finds one — "this session's dumps are in
`logs/s20261113-194500-4242/`: copy that folder, not all of logs/" — and its existing stale-file count
is unchanged for runs without one. Tested both ways.

## Tested

Host build only (BUILD-EXIT=0, no warnings on the three touched files). **Not run on a console.** What a
run adds is whether the folder is created where expected and whether the three writers land in it.

The first run with it on wants `EDEN_GBB_FLASH=2` or `EDEN_GBB_TIMELINE` set so there is something to
write, and then: copy `logs/s<stamp>-<pid>/` instead of all of `logs/`, and see whether `checkrun`'s
stale count falls to the files listed above.
