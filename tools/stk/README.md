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

## Shader store preflight

    python3 tools/stk/stamp_guard.py reference.env candidate.env --cpp /path/to/vk_pipeline_prep.cpp

Use the warm run's environment as the reference and the renderer source from the build
being tested. Add `--reference-overlay` and `--candidate-overlay` for title-specific
environment files. Later values take precedence, as on the console. A changed stamp
input exits 1 and lists the difference. Missing or unreadable inputs exit 2.

Use `--source-stamp` when the target build is known to use its source translation stamp.
The check covers the supplied environment files. Keep the build, driver, runtime settings
(including render scale), and existing store consistent, and confirm reuse in the boot log.

Originally written by waveydude for the local tester workflow.
