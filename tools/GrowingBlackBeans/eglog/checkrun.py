#!/usr/bin/env python3
"""checkrun.py RUN_FOLDER [--expect-build 01.219.911] [--others DIR ...]

Run this on a run folder right after copying it off the console, before packing. It catches the copy mistakes
that cost us runs: a log from another session, an env that doesn't match the log, a log copied twice, a build
other than the one installed. Exit code 1 if anything is wrong (packers can refuse), 0 if clean.

Checks:
  1. eden_log.txt is there and has play windows; boot-trace build matches --expect-build if given.
  2. Every switch with a known log signature: set in env.txt <=> its lines are in the log (both directions;
     a log that shows a switch the env doesn't set means the log came from another run).
  3. stderr.log belongs to the same session (its EDEN_GPU_TIME count matches the 5 s windows within 3).
  4. The log is not byte-identical to any eden_log in --others (default: sibling run folders).
  5. Lists files in logs/ that are not from this session (other pids, old crash logs, guest code dumps), so they
     don't get packed or confused with this run.
Standard library only.
"""
import argparse
import glob
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eglog  # noqa: E402

# switch -> (where, regex that its lines match). Only switches whose effect is visible in the log.
SIGNATURES = {
    "EDEN_UP_AHEAD_GUARD": ("log", r"EDEN_UP_AHEAD_GUARD="),
    "EDEN_NX2_GPU_PROFILE": ("log", r"GPU (back )?thread per second"),
    "EDEN_NX2_OVERWRITE_CHECK": ("log", r"EDEN_NX2_OVERWRITE_CHECK=1"),
    "EDEN_NX2_READBACK_WAIT": ("log", r"EDEN_NX2_READBACK_WAIT=\d"),
    "EDEN_NX2_SPLIT_WAITS": ("log", r"GPU split per second"),
    "EDEN_GBB_SVC_PROFILE": ("log", r"EDEN_GBB_SVCPROF"),
    "EDEN_GBB_COST": ("log", r"EDEN_GBB_COST"),
    "EDEN_GBB_BACK_CALLS": ("log", r"EDEN_GBB_BACK 5 s"),
    "EDEN_GBB_NAN_GUARD": ("log", r"colour NaN guard on"),
    "EDEN_GPU_TIME": ("stderr", r"EDEN_GPU_TIME wall_ms"),
    "EDEN_GBB_VITALS": ("log", r"EDEN_GBB_VITALS t_ms="),
    "EDEN_GBB_TIMELINE": ("log", r"EDEN_GBB_TIMELINE: (recording|\d+ events)"),
}
# Switches with no log line of their own (can't be checked from the log): say so instead of passing silently.
SILENT = ["EDEN_GBB_GUARD_EARLY", "EDEN_UP_AHEAD_ALWAYS", "EDEN_GBB_TRUST_COPY"]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run")
    ap.add_argument("--expect-build")
    ap.add_argument("--others", nargs="*")
    a = ap.parse_args()
    problems, notes = [], []
    folder = a.run.rstrip("/")
    try:
        run = eglog.load(folder)
    except FileNotFoundError as e:
        print(f"FAIL {e}")
        return 1
    if not run.play():
        problems.append("no play windows in the log (crashed early, or not the right log?)")
    if a.expect_build and (run.build or "").split(" ")[0] != a.expect_build:
        problems.append(f"build {run.build} in the boot trace, expected {a.expect_build} (old build installed, or old logs folder?)")
    log_text = eglog._open(run.log_path).read()
    err_text = eglog._open(run.stderr_path).read() if run.stderr_path else ""
    for sw, (where, rx) in SIGNATURES.items():
        on = run.env.get(sw, "0") not in ("0", "")
        seen = bool(re.search(rx, log_text if where == "log" else err_text))
        if where == "stderr" and not run.stderr_path:
            continue
        if on and not seen:
            problems.append(f"{sw}={run.env[sw]} is in env.txt but its lines are not in the {where} (wrong env, or log from another run)")
        if seen and not on:
            problems.append(f"the {where} shows {sw} but env.txt doesn't set it (log from another run?)")
    silent = [s for s in SILENT if run.env.get(s, "0") not in ("0", "")]
    if silent:
        notes.append("set but not visible in the log, can't be verified: " + ", ".join(silent))
    if run.stderr_path and run.windows:
        n_gpu = len(run.gpu)
        if run.env.get("EDEN_GPU_TIME") and abs(n_gpu - len(run.windows)) > 8:
            problems.append(f"stderr has {n_gpu} GPU-time lines for {len(run.windows)} 5 s windows: stderr from another session?")
    others = a.others if a.others is not None else [d for d in glob.glob(os.path.join(os.path.dirname(os.path.abspath(folder)), "*/"))
                                                     if os.path.abspath(d).rstrip("/") != os.path.abspath(folder)]
    mine = sha(run.log_path)
    for d in others:
        for name in ("eden_log.txt", "eden_log.txt.gz"):
            p = os.path.join(d, name)
            if os.path.exists(p) and os.path.getsize(p) == os.path.getsize(run.log_path) and sha(p) == mine:
                problems.append(f"eden_log is identical to {p}: copied the same log twice?")
    logs = os.path.join(folder, "logs")
    if os.path.isdir(logs):
        pid = None
        bt = os.path.join(logs, "boot-trace.txt")
        if os.path.exists(bt):
            m = re.search(r"pid (\d+)", open(bt, errors="replace").read())
            pid = m[1] if m else None
        stale = []
        for f in sorted(os.listdir(logs)):
            if f.startswith("guest-main"):
                stale.append(f)
            elif f.startswith("sample-") and pid and not f.startswith(f"sample-{pid}-"):
                stale.append(f)
            elif f.startswith("crash-"):
                stale.append(f)
        if stale:
            dumps = sum(1 for f in stale if f.startswith("guest-main"))
            notes.append(f"{len(stale)} files in logs/ are not from this session or must never be shared "
                         f"({dumps} guest code dumps, the rest old samples/crash logs); packers skip them")
    s = run.summary()
    print(f"{s['run']}: build {run.build}, {s['play_windows']} play windows, {s['play_fps']} fps, "
          f"heavy {s['regimes']['heavy']['windows']} windows")
    for n in notes:
        print("  note:", n)
    for p in problems:
        print("  PROBLEM:", p)
    print("  OK" if not problems else f"  {len(problems)} problem(s): fix before packing")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
