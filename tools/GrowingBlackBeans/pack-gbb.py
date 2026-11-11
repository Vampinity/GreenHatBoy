#!/usr/bin/env python3
"""Pack GrowingBlackBeans runs into GreenHatBoy's layout (run.json format 0, plus a "gbb" block).

usage: pack-gbb.py <GreenHatBoy clone> <run dir> --id ID [--route ...] [--notes ...] [--build-tag ...]

Redaction = GreenHatBoy's tools/pack-run.py redact() (home paths, e-mail, LAN, MAC, console user number in
decimal/hex, login name, ~/.eglantine-private words) + a final check that no ~/.eglantine-private string or PSN
user number survives in any written file; on a hit the run folder is deleted. Files taken: eden_log.txt,
logs/stderr.log, env.txt only (never guest-main dumps, saves, caches or old crash logs).
"""
import argparse, gzip, importlib.util, json, os, re, shutil, statistics as st, sys, datetime, hashlib, pathlib

ap = argparse.ArgumentParser()
ap.add_argument("repo"); ap.add_argument("run"); ap.add_argument("--id", required=True)
ap.add_argument("--route", default="GrowingBlackBeans Kokiri benchmark: Continue, house, out, walk loop to the water")
ap.add_argument("--notes", default=""); ap.add_argument("--build-tag", default=None)
ap.add_argument("--console", default="PS5 base 13.60")
a = ap.parse_args()
spec = importlib.util.spec_from_file_location("ghb_pack", os.path.join(a.repo, "tools/pack-run.py"))
ghb = importlib.util.module_from_spec(spec); spec.loader.exec_module(ghb)

run = pathlib.Path(a.run); log_path = run / "eden_log.txt"
if not log_path.exists(): sys.exit(f"no eden_log.txt in {run}")
raw = log_path.read_text(errors="replace")
date = datetime.date.fromtimestamp(log_path.stat().st_mtime).isoformat()
time = datetime.datetime.fromtimestamp(log_path.stat().st_mtime).strftime("%H:%M:%S")
target = pathlib.Path(a.repo) / "runs" / "GrowingBlackBeans" / f"{date}-{a.id}"
if target.exists(): sys.exit(f"{target} exists")
target.mkdir(parents=True)
secrets = set(re.findall(r"EDEN_PAD_\w+ .*?(?:user|foreground|initial)=(\d{6,})", raw))
for s in list(secrets): secrets |= {hex(int(s))[2:], f"{int(s):08x}"}
pf = os.path.expanduser("~/.eglantine-private")
if os.path.exists(pf): secrets |= {l.strip() for l in open(pf) if l.strip() and not l.startswith("#") and len(l.strip()) >= 6}
counts = {}
try:
    log = ghb.redact(raw, counts)
    with gzip.open(target / "eden_log.txt.gz", "wt", compresslevel=9) as f: f.write(log)
    se = run / "logs" / "stderr.log"
    if se.exists():
        err = se.read_text(errors="replace")
        # The launcher logs the profile's name, which can be an account name: never pack it.
        err, n = re.subn(r"(launch: Profile ).*", r"\1<redacted>", err)
        if n: counts["profile_name"] = n
        with gzip.open(target / "stderr.log.gz", "wt", compresslevel=9) as f: f.write(ghb.redact(err, counts))
    env_lines = []
    if (run / "env.txt").exists():
        env = ghb.redact((run / "env.txt").read_text(errors="replace"), counts)
        (target / "env.txt").write_text(env)
        env_lines = [l for l in env.splitlines() if l.strip() and not l.startswith("#")]
    W = []
    for l in log.splitlines():
        m = re.match(r"^\[\s*([\d.]+)\].*nx2:vi2 5 s: (\d+) frames, ([\d.]+) fps, mean ([\d.]+) ms, 1% low ([\d.]+) ms, worst ([\d.]+) ms, fence ([\d.]+) ms", l)
        if m: W.append([float(m[1]), int(m[2]), float(m[3]), float(m[5]), float(m[6]), float(m[7])])
    play = [w for w in W if w[2] < 45 and w[1] >= 40]
    heavy = [w for w in play if w[5] >= 5]; light = [w for w in play if w[5] < 1]
    avg = lambda ws: round(st.mean(w[2] for w in ws), 2) if ws else None
    bm = re.search(r"diagnostic build ([\d.]+) \(([^)]*)\)", (run / "logs" / "boot-trace.txt").read_text(errors="replace")) if (run / "logs" / "boot-trace.txt").exists() else None
    pipes = len(re.findall(r"pipeline built on the GPU thread", log))
    info = {
        "format": 0, "author": "GrowingBlackBeans", "run_id": a.id, "date": date, "time": time,
        "batch": None, "test": a.id, "game": "0400486024DEC000",
        "build": {"tag": a.build_tag, "commit": None, "version": f"{bm[1]} ({bm[2]})" if bm else None, "eboot_sha256_16": None},
        "firmware": None, "console": a.console,
        "route": {"script": a.route, "script_sha": None}, "menu_settings": None,
        "env_lines": len(env_lines), "env_hash": hashlib.sha256("\n".join(env_lines).encode()).hexdigest()[:10] if env_lines else None,
        "control": None, "ending": {"kind": "hand_stopped", "class": None, "seconds": W[-1][0] if W else None, "crash_app_s": None},
        "valid": bool(play), "gameplay_s": round(len(play) * 5.0, 1) if play else None,
        "fps": {"mean": avg(play), "source": "nx2:vi2 5 s lines (play windows under 45 fps)",
                "p99_ms": round(st.median(w[3] for w in play), 1) if play else None, "worst_ms": max((w[4] for w in play), default=None)},
        "worst_frame_ms": max((w[4] for w in play), default=None), "runtime_pipeline_builds": pipes,
        "flashes_per_min": None, "note": None, "impressions": a.notes, "flash_times": [],
        "gbb": {"windows_5s_columns": ["log_s", "frames", "fps", "1pct_low_ms", "worst_ms", "fence_ms"], "windows_5s": W,
                "heavy_windows": len(heavy), "heavy_fps": avg(heavy), "light_windows": len(light), "light_fps": avg(light),
                "regimes": "play windows (<45 fps); heavy = present fence wait >= 5 ms per frame (GPU thread bound), light = < 1 ms (game CPU bound)"},
    }
    info = ghb.scrub(info, counts); info["redacted"] = counts
    (target / "run.json").write_text(json.dumps(info, indent=1, ensure_ascii=False) + "\n")
    for f in target.iterdir():
        text = gzip.open(f, "rt").read() if f.suffix == ".gz" else f.read_text()
        for s in secrets:
            if s.lower() in text.lower(): raise RuntimeError(f"private string left in {f.name}")
except Exception:
    shutil.rmtree(target); raise
print(target.name, counts, "play", info["fps"]["mean"], "heavy", info["gbb"]["heavy_fps"])
