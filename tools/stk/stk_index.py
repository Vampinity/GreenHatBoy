#!/usr/bin/env python3
"""Batch indexer (stk_index.py) producing a standardized scores.csv table.

Original: waveydude. Run-contract change (GrowingBlackBeans, 16 Nov 2026): no default roots - pass
--roots or set $STK_RUN_ROOTS (colon-separated); a run folder is any folder holding eden_log.txt or
stderr.log, raw or .gz, flat or under logs/.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stk_score import DEFAULT_ALPHA_ENV, score_run  # noqa: E402

DEFAULT_ROOTS = [r for r in os.environ.get("STK_RUN_ROOTS", "").split(":") if r]
RUN_MARKERS = ("eden_log.txt", "stderr.log", "eden_log.txt.gz", "stderr.log.gz")


def discover_runs(roots: list[str]) -> list[Path]:
    seen_real: set[Path] = set()
    runs: list[Path] = []
    for root in roots:
        rp = Path(root)
        if not rp.exists():
            continue
        for cur, _dirs, files in os.walk(rp):
            if Path(cur).name == "logs" and any(m in os.listdir(Path(cur).parent) for m in RUN_MARKERS):
                continue
            if any(m in files for m in RUN_MARKERS):
                p = Path(cur).resolve()
                if p not in seen_real:
                    seen_real.add(p)
                    runs.append(p)
    return sorted(runs)


def build_index(roots: list[str], out_csv: Path, alpha_env: str) -> list[dict]:
    run_dirs = discover_runs(roots)
    rows = [score_run(d, alpha_env) for d in run_dirs]
    rows.sort(
        key=lambda r: (
            str(r.get("firmware") or "zz"),
            str(r.get("settings_profile") or "zz"),
            str(r.get("route") or "zz"),
            str(r.get("run_id") or ""),
        )
    )
    if rows:
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        keys: list[str] = []
        for r in rows:
            keys += [k for k in r if k not in keys]
        with out_csv.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(rows)
    return rows


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Build standardized scores.csv across saved runs.")
    ap.add_argument("--roots", nargs="*", default=DEFAULT_ROOTS)
    ap.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parent / "scores.csv"),
        help="Output CSV path",
    )
    ap.add_argument("--alpha-env", default=DEFAULT_ALPHA_ENV)
    args = ap.parse_args(argv)
    if not args.roots:
        ap.error("no run roots: pass --roots or set STK_RUN_ROOTS")

    rows = build_index(args.roots, Path(args.out), args.alpha_env)
    print(f"Wrote {len(rows)} rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
