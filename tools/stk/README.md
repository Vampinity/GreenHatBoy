# tools/stk — the shared scorer under the run contract

One scorer for every run, whoever made it. The rules it implements are in
[`docs/RUN-CONTRACT.md`](../../docs/RUN-CONTRACT.md); the measuring rules it serves are in
[`docs/MEASURING.md`](../../docs/MEASURING.md).

**Authors.** The scorer and the route check are **waveydude's** (`stk_score.py`, `stk_index.py`,
`route_check.py`). The run-contract changes, the shared run-folder reader (`runfolder.py`) and the route
windows (`windows.json`) are GrowingBlackBeans'. Every change against waveydude's version is listed in
[`CHANGES.md`](CHANGES.md). The village, field-walk and after-the-field windows are Vampinity's
definitions, transcribed from `runs/Vampinity/2026-11-15-t186-control-README.md`.

    python3 tools/stk/stk_score.py <run folder> [...] --alpha-env <the alpha's env.txt> [--format csv] [--out FILE]
    python3 tools/stk/stk_index.py --roots runs --out scores.csv
    python3 -m unittest discover -s tools/stk/tests -v

A run folder can be raw (flat, or with `logs/`) or packed (`runs/<author>/…`, logs `.gz`). Standard library
only; it reads and never writes, except `--out`. Missing numbers are `null` with a reason, never 0.
