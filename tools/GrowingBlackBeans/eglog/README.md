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

As of 12 Nov 2026:

| Piece | State |
|---|---|
| `eglog.py`, `runreport.py`, `abcompare.py` (including `--live`), `checkrun.py`, `index-gbb.py`, `ingest.sh` | **Tested** on all runs in this repo and on raw folders; unit tests pass (`tests/`). 12 Nov: `abcompare`'s "smallest possible p" footnote was wrong for unequal run counts (fixed: 1/C, not 2/C). |
| Menu settings from stderr (`run.menu`) | **Tested** on real logs. |
| `timeline.py` | **Tested on a real capture** (run V1, 12 Nov: the per-frame table showed the doubled 80-94 ms frames with one frame in flight). |
| Patch 0921, `EDEN_GBB_BACK_CALLS` | **Ran on the console** (V1). Its own cost has not been measured on its own. |
| Patch 0922, `EDEN_GBB_VITALS`, `EDEN_GBB_TIMELINE` | **Ran on the console**: vitals in every run since 12 Nov, timeline in V1. Vitals are on in both arms of every comparison, so their cost cancels; it hasn't been measured on its own. |
| Patch 0923, `EDEN_GBB_FLIGHT`, `EDEN_GBB_ENV` | **Ran on the console** (F1, the 12 Nov morning runs). `checkrun.py` relies on the env line. The flight recorder still dumps during loading screens and should skip them. |
| Touchpad + R3 marker (0923) | Works, but too awkward to press while playing; the flash counter replaces it. |
| Patch 0928, `EDEN_GBB_FLASH`, and `flashes.py` | **Ran on the console** (12 Nov, FC3 / FX3 / XG3, t120-gbb9). Ranks control < two-slot guard < one slot like the player's eye. The detector is unit-tested on synthetic frames (pans, fades, cuts, one- and two-frame strips, a white flash). Its own log lines are too sensitive (about 1,200 small "flashes" a run, the game's own motion): use `flashes.py grids` and the v25 / v40 columns (Vampinity's sizes) as the headline. Cost not measured on its own. |

Reading flash runs: `flashes.py grids RUN [RUN ...]` takes run folders (raw, or packed here with `gbb-flash-*.bin.gz`) and finds each run's own grid file from its log; `--pictures DIR` draws the frame before, the flash and the frame after.

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
