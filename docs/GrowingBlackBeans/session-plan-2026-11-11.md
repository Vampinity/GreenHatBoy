# Tonight's PS5 session (11 Nov)

**Build:** install `t120-gbb7` once (version 01.219.914). It has every patch through 0924. Faster CPU emulation on, as always.

**Every run:** the standard route (Continue, through Link's house, out, the walking loop to the water). Copy that run's env into place before launching; afterwards, copy `eden_log.txt` and the `logs/` folder into the same run folder. If you have time, delete the console's `logs/gbb-*.bin` files between runs.

**Marker:** press **touchpad + R3** whenever you see a flash, and once when you start walking. It's new and untested: check that it doesn't open anything in the game.

| # | Folder | What changes | Why | Watch for |
|---|---|---|---|---|
| 1 | `runV1` | vitals + back breakdown + 10 s timeline (about 120 s after the intro starts, mid-walk) | First test of the new tools | One hitch about 10 s into the walk is the timeline file being written. Anything odd. |
| 2 | `runC1` | control (everyday + vitals) | Baseline for 3-7 | Flashes, as usual |
| 3 | `runX1` | two frames ahead (`EDEN_GBB_FRAMES_AHEAD2=1`) | Does depth buy fps in heavy views? Model says +3-6 | **Expect flashes** (the guard covers one frame). It could also misread commands or crash: if it does, stop and tell me. |
| 4 | `runG2` | guard fix (`EDEN_GBB_GUARD_EARLY=1`) | Does it look as clean as the control, or better? | Dark moments or flashes, compared with run 2 |
| 5 | `runC2` | control | Second baseline | |
| 6 | `runX2` | two frames ahead | Second run | as run 3 |
| 7 | `runG4` | guard fix | Second run | as run 4 |
| 8 | `runU1` | faster buffer usage tracker (`EDEN_UP_FRITCHII_USAGE_TRACKER=1`) | Our 9 Nov back-thread profile puts the always-on usage tracker at about 7% of the back's busy time; this switch is the optimized version | Optional |
| 9 | `runU2` | usage tracker | Second run | Optional |
| 10 | `runF1` | vitals + back breakdown + flight recorder (dumps the 2 s before any frame of 100 ms or more) | First test of the flight recorder | One extra hitch right after a big one is the dump being written. Optional. |
| 11 | `runP1` | build every pipeline at boot (`EDEN_NX2_PRELOAD_ALL_PIPELINES=1`) | Removes the shader stutter? (71% of runtime builds were on disk; boot only builds pipelines used in the last 2 boots) | **Boot takes longer**: say roughly how much. Stutter while walking. |
| 12 | `runP2` | preload all | Second run | as run 11 |

Preload runs are last: building everything at boot may change what the disk store keeps for later runs.

**What each comparison answers** (2 runs a side, so a screen, not a final call):
- **X vs C:** fps in heavy windows. If +3 or more on both runs, the two-frame guard is worth building.
- **G vs C:** your picture rating. Stale-read counts already favour G (E1).
- **P vs C:** shaders built in play (target under 5) and the worst frames, against boot time and memory.
- **V1 and F1:** whether vitals, the timeline, the flight recorder and the marker all work.

About 10-12 runs at roughly 6 minutes each: about an hour. If short on time, do 1-7 and skip the rest.
