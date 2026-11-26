# Batch B: the reserves that act (GrowingBlackBeans, 25 Nov 2026)

**All three quiet: reserve floor out and DMA scratch out, no change seen; reserved tables out, no harm seen (its cap).**
**Reserve floor out leans the way written before start 1 (more seconds under 16 MiB, p 0.021), not called.**

Phase 4, memory first: batch A's twin for the other three memory parts of the control. Alpha T186 (01.219.028) + play
v4.0 with swap ahead 2048, base PS5, 13.60, handheld 1x, the warm field route (c4fada64155f), the shared warm store
(prep_5093ab9e, 80,770), the whole cache restored before every start. 4 starts of each arm against 12 controls,
interleaved (C x C y C z C z C y C x C x C y C z C z C y C x).

Rules frozen 24 Nov before start 1 (sha1 9e13ca644841) and pushed with three amendments, each pushed before the starts it
covers: [`batch-b-rules/`](batch-b-rules/).
- **Amendment 1:** try 1 (by hand) was stopped after 4 starts and set aside, and the batch restarted on the runner.
- **Amendment 2:** how the runner runs a start: Vampinity's PR 38 at 31ace18.
- **Amendment 3:** all 24 starts in one run, after the runner's first start 1 ran without the cache restore and was not
  counted.

**Moved:** a crash in an arm when no control crashed, or a two-sided permutation p < 0.01 on any of the six numbers. Read
needs 10 or more eligible controls.

| number | 11 controls | x, reserve floor out | y, reserved tables out | z, DMA scratch out |
|---|---|---|---|---|
| graphics refusals, to script_end (tries) | 0-27 | 10-23 (p 0.32) | 3-21 (p 0.93) | 0-8 (p 0.14) |
| distinct failed shapes (beside refusals) | 0-6 | 2-10 (p 0.29) | 1-8 (p 0.53) | 0-1 (p 0.16) |
| largest free block at the black, MiB | 1088-1296 | 928-1242 (p 0.18) | 1101-1416 (p 0.53) | 1166-1300 (p 0.97) |
| s under 16 MiB | 14-50 | 36-76 (p 0.021) | 8-48 (p 0.66) | 2-52 (p 0.31) |
| worst frame after the black, ms | 1,204-4,402 | 2,387-3,146 (p 0.70) | 1,189-3,916 (p 0.70) | 1,238-4,203 (p 0.47) |
| load s | 12.0-31.5 | 23.3-31.4 (p 0.24) | 18.7-26.2 (p 0.89) | 11.6-21.5 (p 0.045) |
| field walk fps | 18.93-19.39 | 19.05-19.09 (p 0.36) | 19.10-19.35 (p 0.16) | 18.80-19.24 (p 0.10) |

**Proof lines:**
- **x:** the JIT lend line reads `(floor 32)` in every control and in every y and z start, and `(floor 128)` in every x
  start. With the floor out, the reserve sat at or under 32 blocks in 0-1 lines, against 28-29 in every control. So the
  "no change seen" verdict this arm's cap allows is met.
- **y:** the two `EDEN_UP_RESERVE_TABLES` lines are in every start but the y starts. No table refusal anywhere (0 in all).
- **z:** the four `EDEN_UP_DMA_SCRATCH_MIB:` lines are in every start but the z starts. No DMA stripe and no GPU
  bad_alloc anywhere.

**What this does and does not say**

- **No line moved.** Two lean without being called:
  - x has more time near empty: 36-76 s under 16 MiB against 14-50 (p 0.021). That is the direction the rules wrote
    down before start 1 ("more seconds under 16 MiB"), so "no change seen" stands beside a lean the right way, not
    called at p 0.01. X4 has the smallest room at the black of any start, 928 MiB.
  - z has a shorter load: 11.6-21.5 s (p 0.045).
  At three arms, about 1 batch in 9 shows a false move, so leans at this size are what identical controls also give.
- **z's census heap** at the last census line before the black: arm 604-725 MiB against controls 688-800. The 88 MiB of
  scratch not reserved is mostly not taken at that moment, as expected. It doesn't show as room at the black (p 0.97).
- **y can only show harm:** 4 starts miss the risky growth (tables doubling with memory at the bottom) about 1 time in 5.
  "No harm seen" is the best this batch can say about it.
- **No start crashed or hung.** Three starts lost the end of their log just after the quit (`end_kind log_cut`): the
  control C5 and the arm starts Y1 and X3. C5 is not an eligible control, so 11 eligible controls remain. Y1 and X3 keep
  their count (a bad quit after script_end keeps an arm start's count) and are read.
- **C5 was not rerun, and the rules ask for it** (a start that doesn't count and didn't crash is rerun at the end). We
  missed it: the runner ran all 24 in one go, and we only found C5 ineligible at the read, after the console had moved
  on to batch C. The read stands on 11 controls, which the rules allow (10 or more), but the rerun line wasn't followed.
  A rerun now would come from another day and another sitting, so we report the miss instead. Batch C and L7 are checked
  for this before the read.
- **Every start was checked for the whole-cache restore** in the runner's own log before the import. All 24 had it (27
  files, 2.1 GiB, 203-224 s each, the same two digests every time), and all 24 booted warm. Each run's NOTE.md now
  carries its own restore line (time, size, seconds, files read back, digests; no address or paths).
- **VMA dumps left on the console: 0** in every start, the five set-aside ones included.
- **Repacked 25 Nov** with the alpha env as the reference, so each `run.json` reads `control_eligible` as the scorer
  does: true for the 11 eligible controls, false for C5 and the arm starts. The set-aside controls (`-try1`, `-nowarm`)
  read true there too, as starts, but are not read with B.
- **Starts that are kept and not read:**
  - try 1's four starts: `runM1B-01-C1-try1` to `-04-Y1-try1`, by hand, all clean;
  - the runner's first start 1 without the restore: `runM1B-01-C1-nowarm`. It booted warm by its numbers on the cache
    the console had, but it didn't get the restore the rules require.
- A screen on this route, handheld, from a fresh start, at 4 against 11. Nothing is adopted or removed: phase 4 explains
  the control and changes nothing until the programme ends.
- **Next, ours:**
  - batch C, handed over by Vampinity on 25 Nov, with the waits probe deciding batch D;
  - batch L7, lane 7's re-opened lines.

**Every start** (all warm: 80,770 known, 3 own records, Total Pipeline Count 4; all ended at script done)

| # | start | arm | refusals | shapes | at the black MiB | s < 16 MiB | worst after the black ms | load s | field walk fps |
|---|---|---|---|---|---|---|---|---|---|
| 1 | C1 | control | 20 | 6 | 1244 | 38 | 3533.1 | 24.9 | 19.39 |
| 2 | X1 | reserve floor out | 16 | 5 | 1242 | 42 | 3146.3 | 25.2 | 19.09 |
| 3 | C2 | control | 0 | 0 | 1291 | 20 | 1288.6 | 18.5 | 19.05 |
| 4 | Y1 | reserved tables out | 18 | 5 | 1297 | 38 | 3916.0 | 26.2 | 19.35 |
| 5 | C3 | control | 2 | 1 | 1264 | 44 | 1260.7 | 18 | 19.35 |
| 6 | Z1 | DMA scratch out | 8 | 1 | 1230 | 52 | 4202.8 | 21.5 | 19.24 |
| 7 | C4 | control | 1 | 0 | 1141 | 14 | 1203.6 | 19.2 | 19.05 |
| 8 | Z2 | DMA scratch out | 2 | 1 | 1166 | 24 | 1307.3 | 11.6 | 18.92 |
| 9 | C5 | control (not eligible: log cut after the quit) | 11 | 3 | 1118 | 34 | 3029.9 | 20.3 | 19.44 |
| 10 | Y2 | reserved tables out | 21 | 8 | 1101 | 48 | 2699.6 | 25.2 | 19.26 |
| 11 | C6 | control | 9 | 4 | 1088 | 42 | 1369.0 | 24.4 | 19.19 |
| 12 | X2 | reserve floor out | 16 | 2 | 1238 | 76 | 2979.5 | 23.7 | 19.05 |
| 13 | C7 | control | 10 | 0 | 1261 | 14 | 3685.1 | 21.9 | 18.93 |
| 14 | X3 | reserve floor out | 10 | 2 | 1168 | 36 | 2387.1 | 23.3 | 19.09 |
| 15 | C8 | control | 27 | 6 | 1296 | 30 | 4109.5 | 25.5 | 19.06 |
| 16 | Y3 | reserved tables out | 4 | 2 | 1416 | 12 | 1189.4 | 18.7 | 19.10 |
| 17 | C9 | control | 14 | 4 | 1165 | 34 | 4402.3 | 25.1 | 19.14 |
| 18 | Z3 | DMA scratch out | 0 | 0 | 1182 | 6 | 1275.6 | 11.9 | 18.80 |
| 19 | C10 | control | 0 | 0 | 1245 | 14 | 1312.4 | 12 | 19.06 |
| 20 | Z4 | DMA scratch out | 1 | 0 | 1300 | 2 | 1238.1 | 18 | 18.97 |
| 21 | C11 | control | 23 | 6 | 1268 | 50 | 3664.0 | 31.5 | 19.28 |
| 22 | Y4 | reserved tables out | 3 | 1 | 1207 | 8 | 1215.3 | 20.4 | 19.34 |
| 23 | C12 | control | 14 | 4 | 1170 | 40 | 2274.0 | 23.5 | 19.06 |
| 24 | X4 | reserve floor out | 23 | 10 | 928 | 66 | 2788.1 | 31.4 | 19.05 |

Runs: `runs/GrowingBlackBeans/2026-11-25-runM1B-01-C1` to `-24-X4`, each with a NOTE.md, plus the five set-aside starts.
Read with the batch kit (`batch_kit.py read`, exact two-sided permutation on means), scorer stk_score 10. The runner's
result folders are not posted: they hold the console's network address. Each start's logs came from them, flat, through
a checked import (the env and the route that ran are the folder's).
