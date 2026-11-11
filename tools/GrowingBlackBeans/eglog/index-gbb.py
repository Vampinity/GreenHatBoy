#!/usr/bin/env python3
"""index-gbb.py REPO: writes REPO/index-regimes.csv, one row per run with what index.csv doesn't have.

Columns: era, door, standing/walking fps, light/queued/mid/heavy fps and window counts, back busy and host GPU per
heavy frame, shaders built in play, texture churn while walking, memory-margin events, live-switch labels. It sits
next to index.csv (made by tools/make-index.py) and joins on `path`. Re-run after adding runs. Standard library.
"""
import csv
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eglog  # noqa: E402

COLS = ["path", "author", "run", "build", "era", "door_s", "standing_fps", "walking_fps", "walking_heavy_share",
        "light_fps", "light_n", "queued_fps", "queued_n", "mid_fps", "mid_n", "heavy_fps", "heavy_n",
        "heavy_back_busy_ms", "heavy_gpu_ms", "worst_ms", "shaders_in_play", "tc_created_600", "tc_upload_mib_600",
        "oom_events", "live_labels", "has_split", "has_gpu_time"]


def row(path, root):
    r = eglog.load(path)
    s = r.summary()
    g = s["regimes"]
    c = s.get("texture_churn_per_600_frames") or {}
    return {
        "path": os.path.relpath(path, root).rstrip("/"), "author": s["author"], "run": s["run"], "build": s["build"],
        "era": s["era"], "door_s": s["door_s"], "standing_fps": s["standing"]["fps"], "walking_fps": s["walking"]["fps"],
        "walking_heavy_share": s["walking"]["heavy_share"],
        **{f"{k}_fps": g[k]["fps"] for k in ("light", "queued", "mid", "heavy")},
        **{f"{k}_n": g[k]["windows"] for k in ("light", "queued", "mid", "heavy")},
        "heavy_back_busy_ms": g["heavy"]["back_busy_ms"], "heavy_gpu_ms": g["heavy"]["gpu_ms"],
        "worst_ms": s["worst_ms"], "shaders_in_play": s["pipelines_in_play"],
        "tc_created_600": c.get("created"), "tc_upload_mib_600": c.get("upload_mib"),
        "oom_events": (s.get("memory") or {}).get("out_of_memory_events"),
        "live_labels": " ".join(sorted((s.get("live_phases") or {}).keys())),
        "has_split": s["has"]["split"], "has_gpu_time": s["has"]["gpu_time"],
    }


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    rows, failed = [], 0
    for path in sorted(glob.glob(os.path.join(root, "runs", "*", "*", ""))):
        try:
            rows.append(row(path, root))
        except Exception as e:  # a broken or empty log must not stop the index
            failed += 1
            print(f"skip {path}: {e}", file=sys.stderr)
    with open(os.path.join(root, "index-regimes.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    print(f"index-regimes.csv: {len(rows)} runs ({failed} skipped)")


if __name__ == "__main__":
    main()
