#!/usr/bin/env python3
"""eglog: one parser for EglantinePS5 run logs, for people and agents.

A run is a folder holding eden_log.txt or eden_log.txt.gz, and optionally stderr.log(.gz) (or logs/stderr.log),
env.txt, run.json and logs/boot-trace.txt. Works on both the packed shared-repo layout and a raw copied folder.

Library:
    import eglog
    run = eglog.load("runs/GrowingBlackBeans/2026-11-11-R120a")
    run.windows        # list of Window: one per nx2:vi2 5 s line, enriched (regime, split stats, GPU time, pipelines)
    run.summary()      # dict: play fps, regimes, stage budget per regime, hitches with causes
    run.env            # dict of env switches

CLI:
    eglog.py summary RUN [RUN ...]          one line per run
    eglog.py windows RUN [--csv]            every 5 s window with everything joined
    eglog.py json RUN                       the full summary as JSON
    eglog.py families RUN                   which log line families the run has (what you can ask it)

Definitions (keep them in one place; see LOGS.md for every line family):
    play window   fps < 45 and at least 40 frames, and not a load window (worst < 500 ms)
    regime        by the present's fence wait per frame: light < 1 ms (game CPU sets the pace),
                  mid 1-5 ms, heavy >= 5 ms (the GPU thread sets the pace)
    back busy     1000 - "back idle" from the split's per-second line, per frame (no profiler needed)
    GPU time      EDEN_GPU_TIME lines on stderr have no timestamps; they are aligned to the 5 s windows by the
                  END of the session (both logs stop together). Treat as approximate within one window.
Standard library only.
"""
from __future__ import annotations

import csv
import gzip
import json
import os
import re
import statistics as st
import sys
from dataclasses import dataclass, field, asdict

TS = re.compile(r"^\[\s*([\d.]+)\]")
FPS5 = re.compile(r"nx2:vi2 5 s: (\d+) frames, ([\d.]+) fps, mean ([\d.]+) ms, 1% low ([\d.]+) ms, "
                  r"worst ([\d.]+) ms, fence ([\d.]+) ms")
SPLIT = re.compile(r"GPU split per second: back idle ([\d.]+) ms, (\d+) ring words, front waited ([\d.]+) ms(.*)")
SITE = re.compile(r"([a-z][a-z \-]+?) ([\d.]+) ms \((\d+)/s, longest ([\d.]+) ms\)")
PIPE = re.compile(r"(Graphics|Compute) pipeline built on the GPU thread in ([\d.]+) ms: ([^\n]*)")
GPUTIME = re.compile(r"EDEN_GPU_TIME wall_ms=([\d.]+) busy_ms=([\d.]+) submissions=(\d+) max_ms=([\d.]+)")
SVCPROF = re.compile(r"EDEN_GBB_SVCPROF t(\d+) (\d+) ms, (\d+) frames \(([\d.]+) ms/frame\): in svc (\d+) ms "
                     r"\(([\d.]+)/frame\), outside (\d+) ms \(([\d.]+)/frame\)")
GUARD = re.compile(r"EDEN_UP_AHEAD_GUARD copies: (\d+) pages copied before a write .*?most (\d+) of (\d+)\), "
                   r"the pool was full (\d+) times")
BUILD = re.compile(r"diagnostic build ([\d.]+) \(([^)]*)\), firmware sdk_version (0x[0-9a-f]+)")
BACKCALLS = re.compile(r"EDEN_GBB_BACK 5 s \(ms per s\): busy ([\d.]+), waiting ([\d.]+), idle hook ([\d.]+)")

LIGHT_MAX, HEAVY_MIN = 1.0, 5.0


def _open(path):
    if path.endswith(".gz"):
        return gzip.open(path, "rt", errors="replace")
    return open(path, errors="replace")


def _first(folder, *names):
    for n in names:
        p = os.path.join(folder, n)
        if os.path.exists(p):
            return p
    return None


@dataclass
class Window:
    t: float                  # log seconds at the end of the window
    frames: int
    fps: float
    mean_ms: float
    low1_ms: float            # 1% low frame time
    worst_ms: float
    fence_ms: float           # present fence wait per frame
    kind: str = ""            # load / menu / play
    regime: str = ""          # light / mid / heavy (play windows only)
    ring_kwords_per_frame: float | None = None
    back_busy_ms_per_frame: float | None = None
    front_waited_ms_per_frame: float | None = None
    drains: dict = field(default_factory=dict)      # site -> [ms per frame, count per frame]
    gpu_busy_pct: float | None = None
    gpu_ms_per_frame: float | None = None
    gpu_submissions_per_frame: float | None = None
    pipelines: int = 0
    pipeline_ms: float = 0.0


class Run:
    def __init__(self, folder):
        self.folder = folder.rstrip("/")
        self.name = os.path.basename(self.folder)
        log = _first(self.folder, "eden_log.txt", "eden_log.txt.gz")
        if not log:
            raise FileNotFoundError(f"no eden_log in {folder}")
        self.log_path = log
        self.stderr_path = _first(self.folder, "stderr.log.gz", "stderr.log", "logs/stderr.log")
        self.meta = json.load(open(os.path.join(self.folder, "run.json"))) if os.path.exists(
            os.path.join(self.folder, "run.json")) else {}
        self.env = {}
        envp = _first(self.folder, "env.txt")
        if envp:
            for line in open(envp, errors="replace"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    self.env[k.strip()] = v.strip()
        self.build = self.build_time = self.firmware = None
        bt = _first(self.folder, "logs/boot-trace.txt", "boot-trace.txt")
        if bt:
            m = BUILD.search(open(bt, errors="replace").read())
            if m:
                self.build, self.build_time, self.firmware = m[1], m[2], m[3]
        if not self.build and self.meta.get("build"):
            self.build = (self.meta["build"] or {}).get("version")
        self._parse()

    # ---- parsing -------------------------------------------------------------------------------------------
    def _parse(self):
        self.windows: list[Window] = []
        self.split: list[dict] = []
        self.pipelines: list[tuple] = []          # (t, ms, kind, detail)
        self.svcprof: list[tuple] = []            # (t, tid, frames, ms/frame, svc/frame, outside/frame)
        self.guard: list[tuple] = []              # (t, copies, most, pool, full)
        self.backcalls: list[tuple] = []          # (t, busy, waiting, hook)
        self.families: dict[str, int] = {}
        fam = re.compile(r"^\[\s*[\d.]+\] [\w.]+ <\w+> ([\w/.\-]+):\d+:(\w+)")
        with _open(self.log_path) as fh:
            for line in fh:
                m = TS.match(line)
                if not m:
                    continue
                t = float(m[1])
                f = fam.match(line)
                if f:
                    k = os.path.basename(f[1]) + ":" + f[2]
                    self.families[k] = self.families.get(k, 0) + 1
                w = FPS5.search(line)
                if w:
                    self.windows.append(Window(t, int(w[1]), float(w[2]), float(w[3]), float(w[4]), float(w[5]),
                                               float(w[6])))
                    continue
                s = SPLIT.search(line)
                if s:
                    rec = {"t": t, "back_idle": float(s[1]), "ring": int(s[2]), "front_waited": float(s[3]),
                           "sites": {}}
                    for sm in SITE.finditer(s[4]):
                        rec["sites"][sm[1].strip()] = (float(sm[2]), int(sm[3]), float(sm[4]))
                    self.split.append(rec)
                    continue
                p = PIPE.search(line)
                if p:
                    self.pipelines.append((t, float(p[2]), p[1], p[3][:80]))
                    continue
                sp = SVCPROF.search(line)
                if sp:
                    self.svcprof.append((t, int(sp[1]), int(sp[3]), float(sp[4]), float(sp[6]), float(sp[8])))
                    continue
                g = GUARD.search(line)
                if g:
                    self.guard.append((t, int(g[1]), int(g[2]), int(g[3]), int(g[4])))
                    continue
                b = BACKCALLS.search(line)
                if b:
                    self.backcalls.append((t, float(b[1]), float(b[2]), float(b[3])))
        self.gpu = []
        if self.stderr_path:
            with _open(self.stderr_path) as fh:
                self.gpu = [(float(m[1]), float(m[2]), int(m[3]), float(m[4])) for m in GPUTIME.finditer(fh.read())]
        self._enrich()

    def _enrich(self):
        for w in self.windows:
            if w.fps >= 45:
                w.kind = "menu"
            elif w.frames < 40 or w.worst_ms >= 500:
                w.kind = "load"
            else:
                w.kind = "play"
                w.regime = "light" if w.fence_ms < LIGHT_MAX else ("heavy" if w.fence_ms >= HEAVY_MIN else "mid")
            inside = [s for s in self.split if w.t - 5 <= s["t"] <= w.t + 0.5]
            if inside and w.fps > 0:
                fr = w.fps
                w.ring_kwords_per_frame = round(st.mean(s["ring"] for s in inside) / fr / 1000, 1)
                w.back_busy_ms_per_frame = round((1000 - st.mean(s["back_idle"] for s in inside)) / fr, 2)
                w.front_waited_ms_per_frame = round(st.mean(s["front_waited"] for s in inside) / fr, 2)
                sites = {}
                for s in inside:
                    for k, (ms, n, _) in s["sites"].items():
                        sites.setdefault(k, []).append((ms, n))
                w.drains = {k: [round(st.mean(x[0] for x in v) / fr, 2), round(st.mean(x[1] for x in v) / fr, 1)]
                            for k, v in sites.items()}
            ps = [p for p in self.pipelines if w.t - 5 < p[0] <= w.t]
            w.pipelines, w.pipeline_ms = len(ps), round(sum(p[1] for p in ps), 1)
        if self.gpu and self.windows:
            off = len(self.windows) - len(self.gpu)
            for k, g in enumerate(self.gpu):
                j = k + off
                if 0 <= j < len(self.windows) and self.windows[j].frames:
                    w = self.windows[j]
                    w.gpu_busy_pct = round(g[1] / g[0] * 100, 1)
                    w.gpu_ms_per_frame = round(g[1] / w.frames, 2)
                    w.gpu_submissions_per_frame = round(g[2] / w.frames, 1)

    # ---- views ---------------------------------------------------------------------------------------------
    def play(self, regime=None):
        return [w for w in self.windows if w.kind == "play" and (regime is None or w.regime == regime)]

    def hitches(self, threshold_ms=100.0):
        """Play windows with a frame over the threshold, each with its likely cause (what else happened in it)."""
        out = []
        for w in self.windows:
            if w.kind != "play" or w.worst_ms < threshold_ms:
                continue
            if w.pipeline_ms >= 50:
                cause = f"shaders built in play ({w.pipelines}, {w.pipeline_ms:.0f} ms)"
            elif w.fence_ms >= 20:
                cause = "GPU thread behind (fence wait >= 20 ms/frame)"
            else:
                cause = "unattributed"
            out.append({"t": w.t, "worst_ms": w.worst_ms, "fps": w.fps, "cause": cause})
        return out

    def summary(self):
        def agg(ws, key):
            v = [getattr(w, key) for w in ws if getattr(w, key) is not None]
            return round(st.mean(v), 2) if v else None
        play = self.play()
        out = {"run": self.name, "build": self.build, "firmware": self.firmware,
               "author": self.meta.get("author"), "route": (self.meta.get("route") or {}).get("script"),
               "play_windows": len(play), "play_fps": agg(play, "fps"),
               "worst_ms": max((w.worst_ms for w in play), default=None),
               "pipelines_in_play": sum(w.pipelines for w in play),
               "pipeline_ms_in_play": round(sum(w.pipeline_ms for w in play)),
               "regimes": {}, "hitches": self.hitches(), "has": {
                   "split": bool(self.split), "gpu_time": bool(self.gpu), "svcprof": bool(self.svcprof),
                   "guard": bool(self.guard), "back_calls": bool(self.backcalls)}}
        for r in ("light", "mid", "heavy"):
            ws = self.play(r)
            out["regimes"][r] = {
                "windows": len(ws), "share": round(len(ws) / len(play), 2) if play else None,
                "fps": agg(ws, "fps"), "frame_ms": round(1000 / agg(ws, "fps"), 1) if ws else None,
                "fence_ms": agg(ws, "fence_ms"), "back_busy_ms": agg(ws, "back_busy_ms_per_frame"),
                "front_waited_ms": agg(ws, "front_waited_ms_per_frame"),
                "ring_kwords": agg(ws, "ring_kwords_per_frame"), "gpu_ms": agg(ws, "gpu_ms_per_frame"),
                "gpu_busy_pct": agg(ws, "gpu_busy_pct")}
        if self.guard:
            g = [x for x in self.guard if x[0] > (play[0].t if play else 0)]
            if g:
                out["guard"] = {"copies_per_5s": round(st.mean(x[1] for x in g)), "pool_peak": max(x[2] for x in g),
                                "pool_size": g[0][3], "pool_full": sum(x[4] for x in g)}
        return out


def load(folder):
    return Run(folder)


# ---- CLI ---------------------------------------------------------------------------------------------------
def _fmt(v, nd=1):
    return "-" if v is None else (f"{v:.{nd}f}" if isinstance(v, float) else str(v))


def main(argv):
    if len(argv) < 2 or argv[0] not in ("summary", "windows", "json", "families"):
        print(__doc__)
        return 2
    cmd, runs = argv[0], [a for a in argv[1:] if not a.startswith("--")]
    if cmd == "summary":
        print(f"{'run':34s} {'build':10s} {'play':>5s} {'fps':>5s} | {'light':>11s} {'mid':>11s} {'heavy':>11s} | "
              f"{'back/heavy':>10s} {'gpu/heavy':>9s} {'worst':>6s} {'shaders':>8s}")
        for path in runs:
            s = load(path).summary()
            rg = s["regimes"]
            cell = lambda r: f"{_fmt(rg[r]['fps'])}x{rg[r]['windows']}"
            print(f"{s['run'][:34]:34s} {_fmt(s['build'])[:10]:10s} {s['play_windows']:5d} {_fmt(s['play_fps']):>5s} | "
                  f"{cell('light'):>11s} {cell('mid'):>11s} {cell('heavy'):>11s} | "
                  f"{_fmt(rg['heavy']['back_busy_ms']):>10s} {_fmt(rg['heavy']['gpu_ms']):>9s} "
                  f"{_fmt(s['worst_ms'], 0):>6s} {s['pipelines_in_play']:>8d}")
    elif cmd == "windows":
        run = load(runs[0])
        rows = []
        for w in run.windows:
            d = asdict(w)
            d["drains"] = ";".join(f"{k}={v[0]}ms/{v[1]}" for k, v in sorted(w.drains.items()))
            rows.append(d)
        if "--csv" in argv:
            wr = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()) if rows else ["t"])
            wr.writeheader()
            wr.writerows(rows)
        else:
            for d in rows:
                print(f"{d['t']:7.1f} {d['kind']:4s} {d['regime']:5s} fps {d['fps']:5.1f} fence {d['fence_ms']:5.1f} "
                      f"worst {d['worst_ms']:6.1f} back {_fmt(d['back_busy_ms_per_frame']):>5s} "
                      f"gpu {_fmt(d['gpu_ms_per_frame']):>5s} ring {_fmt(d['ring_kwords_per_frame']):>5s}k "
                      f"shaders {d['pipelines']}")
    elif cmd == "json":
        print(json.dumps(load(runs[0]).summary(), indent=1))
    elif cmd == "families":
        run = load(runs[0])
        for k, n in sorted(run.families.items(), key=lambda x: -x[1]):
            print(f"{n:7d} {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
