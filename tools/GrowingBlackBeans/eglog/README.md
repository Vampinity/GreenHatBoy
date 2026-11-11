# eglog: run-log toolkit

Standard-library Python. Works on packed runs (`runs/<author>/<date>-<id>/`) and on raw folders copied off the console.

| Tool | Use it for |
|---|---|
| `LOGS.md` | What every log line means, its switch, its cost, how it has misled us. Read first. |
| `eglog.py` | The parser. `summary RUN...` one line per run; `windows RUN [--csv]` every 5 s window with split, GPU time and shaders joined; `json RUN`; `families RUN`. Import it for your own analysis. |
| `runreport.py RUN` | A one-page Markdown report: what ran, speed by regime, where a frame went, front waits by site, hitches with causes, what the run can't tell you. |
| `abcompare.py --a RUNS --b RUNS` | Whether B differs from A beyond run-to-run noise (run-level, permutation test, noise floor). |
| `checkrun.py RUN` | Before packing: env matches log, stderr from the same session, not a duplicate log, right build, stale files listed. |
| `ingest.sh RUN ID` | check → pack (`pack-gbb.py`) → `report.md` → index. Needs `REPO=<shared repo clone>`. |

Regimes (all tools): light = present fence wait < 1 ms per frame (the game's CPU sets the pace), mid 1-5, heavy ≥ 5 (the GPU thread sets the pace).

Typical agent session:
1. `index.csv`: pick runs.
2. `eglog.py summary` on them.
3. `runreport.py` on the interesting ones.
4. `abcompare.py` for any claimed gain.
5. `eglog.py windows --csv` or the library for anything deeper.
