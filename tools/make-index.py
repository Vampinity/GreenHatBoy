#!/usr/bin/env python3
"""make-index.py <repo root>: writes index.csv, one row per run, from every runs/<author>/<run>/run.json.
Agents start from the index and only open the logs they need. Standard library only."""
import csv, json, pathlib, sys

root = pathlib.Path(sys.argv[1])
COLUMNS = ["author", "date", "time", "run_id", "build", "commit", "batch", "test", "route", "control", "valid", "ending",
           "seconds", "gameplay_s", "fps_mean", "p99_ms", "worst_frame_ms", "runtime_pipeline_builds", "flashes_per_min",
           "env_lines", "env_hash", "path"]
rows = []
for f in sorted(root.glob("runs/*/*/run.json")):
    r = json.loads(f.read_text())
    rows.append({
        "author": r["author"], "date": r["date"], "time": r["time"], "run_id": r["run_id"],
        "build": r["build"]["tag"], "commit": r["build"]["commit"], "batch": r["batch"], "test": r["test"],
        "route": r["route"]["script"], "control": r["control"], "valid": r["valid"], "ending": r["ending"]["kind"],
        "seconds": r["ending"]["seconds"], "gameplay_s": r["gameplay_s"], "fps_mean": r["fps"]["mean"],
        "p99_ms": r["fps"]["p99_ms"], "worst_frame_ms": r["worst_frame_ms"] or r["fps"]["worst_ms"],
        "runtime_pipeline_builds": r["runtime_pipeline_builds"], "flashes_per_min": r["flashes_per_min"],
        "env_lines": r["env_lines"], "env_hash": r["env_hash"], "path": str(f.parent.relative_to(root)),
    })
rows.sort(key=lambda x: (x["date"], x["time"] or "", x["run_id"]))
with open(root / "index.csv", "w", newline="") as handle:
    w = csv.DictWriter(handle, fieldnames=COLUMNS)
    w.writeheader()
    w.writerows(rows)
print(f"index.csv: {len(rows)} runs")
