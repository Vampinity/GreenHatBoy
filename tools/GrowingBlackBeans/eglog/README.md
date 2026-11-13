# eglog: run-log toolkit

Standard-library Python. Works on packed runs (`runs/<author>/<date>-<id>/`) and on raw folders copied off the console.

| Tool | Use it for |
|---|---|
| `LOGS.md` | What every log line means, its switch, its cost, how it has misled us. Read first. |
| `eglog.py` | The parser. `summary RUN...` one line per run; `windows RUN [--csv]` every 5 s window with split, GPU time and shaders joined; `json RUN`; `families RUN`. Import it for your own analysis. |
| `runreport.py RUN` | A one-page Markdown report: what ran, speed by regime, where a frame went, front waits by site, hitches with causes, what the run can't tell you. |
| `abcompare.py --a RUNS --b RUNS` | Whether B differs from A beyond run-to-run noise (run-level, permutation test, noise floor). |
| `checkrun.py RUN` | Before packing: env matches log, stderr from the same session, not a duplicate log, right build, stale files listed. |
| `ingest.sh RUN ID` | check → pack (`pack-gbb.py`) → `report.md` → both indexes. Needs `REPO=<shared repo clone>`. |
| `index-gbb.py REPO` | `index-regimes.csv`: per run era, standing/walking fps, fps per regime, back and host GPU per heavy frame, shaders, texture churn, memory events, live-switch labels. Joins `index.csv` on `path`. |
| `abcompare.py --live RUNS` | Compares the labelled phases of in-run live-switch runs: the most precise A/B (A/A noise about ±0.5 fps). |
| `timeline.py FILE.bin [--perfetto out.json] [--frames out.csv]` | Reads an `EDEN_GBB_TIMELINE` capture: per frame, the interval, present wait, back busy, front waits (and top site), shaders, and when the frame's fence was signalled; plus a Perfetto trace. |
| `tests/` | Parser and timeline tests on synthetic data; run after changing either. |

Regimes (all tools; details in LOGS.md):
- **light:** no present wait and the back idle; the game's CPU sets the pace.
- **queued:** no present wait but the back over 80% busy; the GPU side throttles through the command queue.
- **mid:** 1-5 ms wait.
- **heavy:** 5 ms or more wait; the GPU side sets the pace.

Runs also get an era (full-wait or ahead-1; never pool them) and, on hand-played routes, standing and walking phases found from the door.

## What has been tested

As of 11 Nov 2026:

| Piece | State |
|---|---|
| `eglog.py`, `runreport.py`, `abcompare.py` (including `--live`), `checkrun.py`, `index-gbb.py`, `ingest.sh` | **Tested** on all 1,219 runs in this repo and on raw folders; unit tests pass (`tests/`). |
| Menu settings from stderr (`run.menu`) | **Tested** on real logs. |
| `timeline.py` | Tested **only on synthetic files** (`tests/test_timeline.py`). Never on a real capture. |
| Patch 0921, `EDEN_GBB_BACK_CALLS` | Builds (t120-gbb4). **Never run.** Its cost is unknown. |
| Patch 0922, `EDEN_GBB_VITALS`, `EDEN_GBB_TIMELINE` | Builds (t120-gbb5). **Never run.** The cost, the file write and the event mix are all unchecked. |
| Patch 0923, `EDEN_GBB_FLIGHT`, `EDEN_GBB_ENV`, the touchpad + R3 marker | Builds (t120-gbb6). **Never run.** The pad chord is untested: check that the touchpad doesn't also tap the game's Minus. |
| eglog parsing of the 0921-0923 lines (vitals, env, marks, flights) | Written against the format strings in the patches; **never fed real output.** |

To test 0921-0923 for the first time, one run on t120-gbb6 with `envs/GrowingBlackBeans/V-vitals-back-timeline.env.txt` covers vitals, back calls and timeline. Add `EDEN_GBB_FLIGHT=100` in a second run. Press touchpad + R3 a few times in each. Check:
1. `EDEN_GBB_VITALS` lines, one a second, with sane numbers. Compare `fps` with the `nx2:vi2 5 s` lines.
2. `EDEN_GBB_ENV` and `checkrun.py` agreeing.
3. `EDEN_GBB_MARK` lines, with no Minus press reaching the game.
4. `gbb-timeline-<pid>.bin` and `gbb-flight-*.bin` in `logs/`, readable with `timeline.py`.
5. Fps against the same env without the switches (`abcompare.py`), to put a number on their cost.

Fix whatever breaks. The code is in `patches/GrowingBlackBeans/0921-0923` and `video_core/gbb_trace.h`.

## The typical workflow

### 1. Before a session: plan the runs

- Decide what you're testing and how you'll know. Write the decision rule down first, for example: "adopt if heavy-window fps rises by 2 or more across 3 runs per side".
- Use at least two runs per side; three or more to make a call. Identical setups differ by up to about 3.6 fps between runs. With two per side, `abcompare.py` can only say "consistent", never "real".
- Make one folder per run (`runA1/`, `runA2/`, ...), each with its `env.txt`, written from the everyday env plus the change. Keep costly diagnostics (`EDEN_NX2_GPU_PROFILE`, the overwrite audit) out of runs whose fps you want to compare; `runreport.py` flags them.
- Alternate the sides (A, B, A, B), so a slow session doesn't land on one side.

### 2. After each run: check, pack, report

Copy `eden_log.txt` and the console's `logs/` folder into the run's folder, then:

```
REPO=<your clone of the shared repo> tools/GrowingBlackBeans/eglog/ingest.sh runA1 A1 \
    --expect-build 01.219.911 --build-tag t120-gbb4 --notes "flash at the door, smooth by the water"
```

- `checkrun.py` runs first and stops on problems, before anything is packed. It catches:
  - a log from another run (its switch lines disagree with env.txt);
  - the same log copied twice;
  - stderr from another session;
  - the wrong build installed.
- Then the run is packed into `runs/<you>/<date>-<id>/` with redaction (`pack-gbb.py`), and gets a `report.md` and a fresh `index.csv`.
- Write what you saw in `--notes`: flashes and roughly when, stutters, how it felt. Logs can't see the picture.
- Read `report.md` straight away. If "What this run cannot tell you" lists something you needed, fix the env before the next run, not after the batch.
- Review the diff, then commit and push.

### 3. After the batch: compare

```
tools/GrowingBlackBeans/eglog/abcompare.py --a runs/<you>/*-A1 runs/<you>/*-A3 \
                                           --b runs/<you>/*-A2 runs/<you>/*-A4
```

- Compare per regime (`light`, `heavy`, `heavy_share`), not just `play`. A change in overall fps is often just more or fewer heavy windows.
- The verdict means:
  - **real:** p < 0.05 and beyond the noise floor;
  - **consistent:** every B run is beyond every A run, but there are too few runs for a p-value;
  - **noise:** otherwise.

  Only "real" or "consistent" justifies adopting something.

### 4. Digging deeper

- `eglog.py summary` on any set of runs: one line each, light/mid/heavy fps, back busy and host GPU per heavy frame, worst frame, shaders built in play.
- `eglog.py windows RUN --csv` gives every 5 s window with everything joined, for spreadsheets or your own scripts.
- `import eglog` in Python, for cross-run analysis; `run.windows` and `run.summary()` hold everything the CLI prints.
- `eglog.py families RUN` shows which log lines a run has, which tells you which questions it can answer.

### 5. Taking stock

Use the `review-regroup-replan` skill (in `.claude/skills/`). It starts from `index.csv`, runs these tools across everything since the last cycle, and ends with a plan that has decision rules.

### For agents

Start from `index.csv` and `index-regimes.csv`. Run `eglog.py summary` on the runs that matter, `runreport.py` on the interesting ones, and `abcompare.py` before calling any difference. Read `LOGS.md` before trusting any line you haven't seen before. Never claim a gain from one run per side.

## anatomy.py (new, 13 Nov) — demand against supply

    anatomy.py table  RUNDIR...   per-second demand and supply per frame, plus a critical-path verdict
    anatomy.py methods RUNDIR...  back-thread cost per method id (ms/s, count/s, us each)
    anatomy.py fit    RUNDIR...   frame time regressed on demand by class
    anatomy.py budget RUNDIR...   measured stage time and affordable cost per unit at 30 fps

What the game asks the emulator for, against what each stage spends supplying it. Spine is
`EDEN_GBB_VITALS` (one line a second), joined with `EDEN_GBB_BACK_CALLS`, the split-waits line and the
texture cache line. Drops the first 60 s by default: the load-in window has a different demand profile
and averaging across it is what produced the wrong "96,000 methods a frame" figure on 13 Nov.

**Tested** on runRD1 and runRD2 (13 Nov). Known limits, which it prints rather than hides:
- It cannot see GPFIFO entries or words. That needs a new counter; it is the demand boundary.
- `fit` is **not identified** on one route: methods, calls and ring words correlate above 0.95, so the
  joint solve hands one a positive cost and another a negative one. It drops the collinear members,
  reports the condition number, and falls back to one class at a time, which is an upper bound. Several
  places with different demand mixes are what fix this, not more runs of the same route.
- Times from an instrumented run are inflated (runRD1 stands at 24.5 fps against runRX1/RX2 at
  27.8/27.9, so about 12%). Collect counts and times in separate runs.

## guard.py (new, 13 Nov) — the copy guard's own counters

    guard.py show    RUNDIR...   per run: arming, exposure, two-frame evidence
    guard.py compare RUNDIR...   one table, with each run's arm read from env.txt
    guard.py windows RUNDIR      per-window detail

`EDEN_UP_AHEAD_GUARD` has printed two lines every 300 presents in **77 of our runs since 9 Nov** and
nothing read them. Three results came out of the first run of this tool, all from logs we already had:

- **The one-slot gap is real and 0927 fixed it.** `runFX1` (two ahead, one slot) shows **239** presents
  that armed while a guard was still up; `runX1` **169**. Every run with `EDEN_UP_AHEAD_GUARD_SLOTS=2`
  shows **0**.
- **With read sync on, two frames are never really in flight.** "armed beside another" and "reads took a
  newer frame's copy" are in the hundreds in `runDX1-3` and `runRX1/2`, and are **0** in `runDXS1-3` and
  `runRO1/2`. So read sync's cost and the loss of the lookahead gain are one fact, not two.
- **Exposure does not separate the arms.** 3.5-4.9% of pages first read with a guard up were not in it,
  in every arm, flashing or clean, in steady windows.

**Exposure is not harm.** The counter says a page was read while unprotected, where a guest write would
go unseen; it cannot say such a write happened. On 13 Nov I used it to rule out the copy guard as our
flicker mechanism and that inference does not follow. The direct test is
`EDEN_UP_AHEAD_GUARD_ALL_WRITES=1`, which is in the eboot and has never been set in any run (`runGW1` is
prepared).

Default `--skip 110` drops the load-in spike: aggregate exposure looks build-dependent only because the
.918 runs have one window at 21-31% around 75-80 s. Steady windows are the same across builds.

## flashdet.py (new, 13 Nov) — flashes from the saved grids, offline

    flashdet.py score|sweep|frames RUNDIR...

Reads the grid files `EDEN_GBB_FLASH=2` wrote (120x67 brightness per presented frame) and looks for a
one-frame excursion that reverts. **Result: nothing separates the flashing arms from the clean ones at
any threshold**, on whole-frame mean, p05, p95, dark-cell count or per-cell tests — and the clean arms
score higher. See `findings-2026-11-13-flicker-is-not-brightness.md`. Take a run's grid file from the
pid its own log names; the same filenames appear in other folders as stale copies.

## make-look.py (new, 13 Nov) — author a LOOK line for the route harness

    make-look.py PICTURE --region X,Y,W,H [--cells COLSxROWS] [--at S] [--timeout S] [--min N]
    make-look.py PICTURE --probe        the picture's size and an 8x8 brightness map, to pick a region
    make-look.py --selftest             the cell arithmetic against images with known means

The route harness waits on `<s> WAIT <timeout> LOOK <x> <y> <w> <h> <cols>x<rows>:<hex> [<min>]`, where
the region is in per mille of the picture and the hex is each cell's mean brightness. **The script that
cuts that grid out of a screenshot is referenced by the harness and does not ship**, so until now nobody
but its author could write a WAIT line. This is it.

The arithmetic is deliberately identical to the harness's own `GridOf` — per-mille region, integer cell
cuts, and the same integer luma `(29B + 150G + 77R) / 256` floored over the cell's pixels — so a line
made here matches what the app computes at run time. Reads P6 PPM (what the shot switch writes) and PNG,
with no third-party modules.

Two things it will tell you that are easy to get wrong:
- `--probe` first. A region has to have structure in it; the run-time score is a **correlation**, so a
  flat region matches almost any screen. The script warns when the cells span under 12 of 255.
- A LOOK **cannot see a flash**. Correlation normalises brightness away by design. For flashes use
  Vampinity's capture-video flash meter.

**Tested:** 8 self-test cases (black/white splits, per-mille regions, more cells than pixels, the
channel weighting, hex ordering) plus an end-to-end run on a synthetic picture. All pass.
