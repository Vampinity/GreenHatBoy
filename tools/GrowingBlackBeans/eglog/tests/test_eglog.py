#!/usr/bin/env python3
"""Tests for eglog on a small synthetic run. Run: python3 tests/test_eglog.py (exit 0 = pass). Standard library."""
import gzip, json, os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import eglog  # noqa: E402

def line(t, text):
    return f"[{t:12.6f}] Service <Info> core/hle/service/nx2_gsv.h:2171:PresentClientBuffer: {text}\n"

def make_run(folder):
    L = []
    t = 30.0
    for _ in range(4):                                   # intro at 60
        L.append(line(t, "nx2:vi2 5 s: 300 frames, 60.0 fps, mean 16.7 ms, 1% low 18.0 ms, worst 20.0 ms, fence 0.0 ms")); t += 5
    L.append(line(t, "nx2:vi2 5 s: 75 frames, 15.0 fps, mean 66.7 ms, 1% low 600.0 ms, worst 640.0 ms, fence 8.0 ms")); t += 5  # door
    door = t - 5
    for _ in range(14):                                  # standing, light
        L.append(line(t, "nx2:vi2 5 s: 165 frames, 33.0 fps, mean 30.3 ms, 1% low 36.0 ms, worst 40.0 ms, fence 0.0 ms")); t += 5
    for k in range(6):                                   # walking: heavy, light alternating
        if k % 2 == 0:
            L.append(line(t, "nx2:vi2 5 s: 105 frames, 21.0 fps, mean 47.6 ms, 1% low 90.0 ms, worst 120.0 ms, fence 20.0 ms"))
            L.append(f"[{t - 1:12.6f}] Render.Vulkan <Info> build/headless/vk_pipeline_cache_cost.cpp:2949:ReportRuntimePipeline: Graphics pipeline built on the GPU thread in 60.0 ms: on disk, not built at boot abc\n")
        else:
            L.append(line(t, "nx2:vi2 5 s: 150 frames, 30.0 fps, mean 33.3 ms, 1% low 40.0 ms, worst 45.0 ms, fence 0.5 ms"))
        t += 5
    # one split line covering the last heavy window's midpoint
    L.append(f"[{t - 4:12.6f}] HW.GPU <Info> video_core/gpu_split.cpp:900:ReportWaits: GPU split per second: back idle 230.0 ms, 3200000 ring words, front waited 550.0 ms, list writers 150.0 ms (4000/s, longest 5.0 ms), dma snapshot miss 180.0 ms (1800/s, longest 3.0 ms)\n")
    os.makedirs(folder, exist_ok=True)
    with gzip.open(os.path.join(folder, "eden_log.txt.gz"), "wt") as f:
        f.writelines(L)
    open(os.path.join(folder, "env.txt"), "w").write("EDEN_NX2_FRAMES_AHEAD=1\nEDEN_NX2_SPLIT_WAITS=1\n")
    return door

def main():
    with tempfile.TemporaryDirectory() as d:
        folder = os.path.join(d, "runs", "Tester", "2026-11-11-T1")
        door = make_run(folder)
        r = eglog.load(folder)
        s = r.summary()
        checks = [
            ("windows parsed", len(r.windows) == 25),
            ("menu windows", sum(w.kind == "menu" for w in r.windows) == 4),
            ("door found", s["door_s"] == door),
            ("door is a load window", [w for w in r.windows if w.t == door][0].kind == "load"),
            ("era ahead-1", s["era"] == "ahead-1"),
            ("standing fps", s["standing"]["fps"] == 33.0),
            ("heavy windows", s["regimes"]["heavy"]["windows"] == 3),
            ("heavy fps", s["regimes"]["heavy"]["fps"] == 21.0),
            ("split joined to its window", any(w.back_busy_ms_per_frame for w in r.windows)),
            ("back busy per frame", any(abs((w.back_busy_ms_per_frame or 0) - 770 / w.fps) < 0.05 for w in r.windows)),
            ("pipelines counted", s["pipelines_in_play"] == 3),
            ("hitches attributed", all("shaders" in h["cause"] for h in s["hitches"])),
            ("summary is JSON-able", bool(json.dumps(s))),
        ]
        bad = [n for n, ok in checks if not ok]
        for n, ok in checks:
            print(("ok   " if ok else "FAIL ") + n)
        return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
