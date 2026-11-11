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
    regime        by the present's fence wait per frame AND the back's idle time:
                    light   fence < 1 ms and the back idle >= 20% (the game's CPU sets the pace)
                    queued  fence < 1 ms but the back busy > 80%: the GPU side throttles the game through the
                            command queue without a present wait (seen at heavy stands)
                    mid     fence 1-5 ms
                    heavy   fence >= 5 ms (the GPU side sets the pace)
                  (windows without split data: light/mid/heavy by fence only)
    phase         door = first play-ish window after 35 s with a frame >= 300 ms; standing = door+10..door+60 s,
                  walking = door+70 s on. Hand-played routes only: scripted routes keep phase "".
    era           "full-wait" (EDEN_NX2_FRAMES_AHEAD not 1, or standing fence > 15 ms) or "ahead-1"; never pool them.
    back busy     1000 - "back idle" from the split's per-second line, per frame (no profiler needed)
    split         "GPU split per second" lines come every 10 s with per-second averages; a window takes the line whose
                  10 s interval holds the window's midpoint.
    GPU time      EDEN_GPU_TIME lines on stderr have no timestamps; aligned at the session end, or one window earlier
                  when that correlates better (GPU busy against fps): right in about 60% of runs at end-1.
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
TC_CREATED = re.compile(r"Texture cache last 600 frames: created (\d+) images, deleted (\d+)")
TC_UPLOADS = re.compile(r"Texture cache last 600 frames: (\d+) uploads from guest memory, (\d+) MiB")
MARGINS = re.compile(r"Memory margins: base (\d+) MiB, out of memory (\d+) MiB, block slack (\d+) MiB")
LIVE_END = re.compile(r"Live switches: phase (\d+) '([^']*)' ended after ([\d.]+) s: (\d+) frames in ([\d.]+) s = ([\d.]+) fps, "
                      r"mean ([\d.]+) ms, 1% low ([\d.]+) ms, worst ([\d.]+) ms")
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
    back_idle_ms_s: float | None = None
    phase: str = ""           # standing / walking / "" (see module docstring)


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
        self.tc_created: list[tuple] = []         # (t, images created, deleted) per 600 frames
        self.tc_uploads: list[tuple] = []         # (t, uploads, MiB) per 600 frames
        self.margins: list[tuple] = []            # (t, out of memory MiB, block slack MiB)
        self.live_phases: list[dict] = []         # in-run live-switch phases (EDEN_UP_LIVE_SWITCHES)
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
                m2 = TC_CREATED.search(line)
                if m2:
                    self.tc_created.append((t, int(m2[1]), int(m2[2])))
                    continue
                m2 = TC_UPLOADS.search(line)
                if m2:
                    self.tc_uploads.append((t, int(m2[1]), int(m2[2])))
                    continue
                m2 = MARGINS.search(line)
                if m2:
                    self.margins.append((t, int(m2[2]), int(m2[3])))
                    continue
                m2 = LIVE_END.search(line)
                if m2:
                    tail = line.split(" | ", 1)[1].strip() if " | " in line else ""
                    self.live_phases.append({"t": t, "phase": int(m2[1]), "label": m2[2], "frames": int(m2[4]),
                                             "fps": float(m2[6]), "mean_ms": float(m2[7]), "low1_ms": float(m2[8]),
                                             "worst_ms": float(m2[9]), "switches": tail})
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
            mid = w.t - 2.5
            inside = [sp for sp in self.split if sp["t"] - 10 < mid <= sp["t"]]
            if inside and w.fps > 0:
                sp = inside[0]
                fr = w.fps
                w.back_idle_ms_s = sp["back_idle"]
                w.ring_kwords_per_frame = round(sp["ring"] / fr / 1000, 1)
                w.back_busy_ms_per_frame = round((1000 - sp["back_idle"]) / fr, 2)
                w.front_waited_ms_per_frame = round(sp["front_waited"] / fr, 2)
                w.drains = {k: [round(ms / fr, 2), round(n / fr, 1)] for k, (ms, n, _) in sp["sites"].items()}
            if w.fps >= 45:
                w.kind = "menu"
            elif w.frames < 40 or w.worst_ms >= 500:
                w.kind = "load"
            else:
                w.kind = "play"
                if w.fence_ms >= HEAVY_MIN:
                    w.regime = "heavy"
                elif w.fence_ms >= LIGHT_MAX:
                    w.regime = "mid"
                elif w.back_idle_ms_s is not None and w.back_idle_ms_s < 200:
                    w.regime = "queued"
                else:
                    w.regime = "light"
            ps = [p for p in self.pipelines if w.t - 5 < p[0] <= w.t]
            w.pipelines, w.pipeline_ms = len(ps), round(sum(p[1] for p in ps), 1)
        # phases (hand-played routes): door, then standing and walking
        self.door_t = None
        script = ((self.meta.get("route") or {}).get("script") or "")
        if not script.endswith(".txt"):
            for w in self.windows:
                if w.t > 35 and w.worst_ms >= 300 and w.fps < 45:
                    self.door_t = w.t
                    break
            if self.door_t is not None:
                for w in self.windows:
                    if w.kind == "play":
                        if self.door_t + 10 <= w.t <= self.door_t + 60:
                            w.phase = "standing"
                        elif w.t >= self.door_t + 70:
                            w.phase = "walking"
        # era
        stand = [w.fence_ms for w in self.windows if w.phase == "standing"]
        fa = self.env.get("EDEN_NX2_FRAMES_AHEAD")
        self.era = "full-wait" if (fa is not None and fa != "1") or (stand and st.median(stand) > 15) else (
            "ahead-1" if fa == "1" else "unknown")
        # GPU time: end-aligned, or one window earlier when that fits better
        self.gpu_offset = None
        if self.gpu and self.windows:
            def corr(off):
                pairs = [(self.gpu[k][1] / self.gpu[k][0], self.windows[k + off].fps) for k in range(len(self.gpu))
                         if 0 <= k + off < len(self.windows) and self.windows[k + off].kind == "play"]
                if len(pairs) < 6:
                    return 0.0
                xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]
                mx, my = st.mean(xs), st.mean(ys)
                sx = sum((x - mx) ** 2 for x in xs) ** .5
                sy = sum((y - my) ** 2 for y in ys) ** .5
                return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy) if sx and sy else 0.0
            end = len(self.windows) - len(self.gpu)
            off = min((end, end - 1), key=corr)          # GPU busy goes down as fps goes up: most negative wins
            self.gpu_offset = off - end
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
        out = {"run": self.name, "build": self.build, "firmware": self.firmware, "era": self.era,
               "door_s": self.door_t, "gpu_align": self.gpu_offset,
               "author": self.meta.get("author"), "route": (self.meta.get("route") or {}).get("script"),
               "play_windows": len(play), "play_fps": agg(play, "fps"),
               "worst_ms": max((w.worst_ms for w in play), default=None),
               "pipelines_in_play": sum(w.pipelines for w in play),
               "pipeline_ms_in_play": round(sum(w.pipeline_ms for w in play)),
               "regimes": {}, "hitches": self.hitches(), "has": {
                   "split": bool(self.split), "gpu_time": bool(self.gpu), "svcprof": bool(self.svcprof),
                   "guard": bool(self.guard), "back_calls": bool(self.backcalls)}}
        for ph in ("standing", "walking"):
            ws = [w for w in play if w.phase == ph]
            out[ph] = {"windows": len(ws), "fps": agg(ws, "fps"),
                       "heavy_share": round(sum(w.regime == "heavy" for w in ws) / len(ws), 2) if ws else None}
        if self.tc_created:
            walk_t = [w.t for w in play if w.phase == "walking"]
            sel = [x for x in self.tc_created if walk_t and walk_t[0] - 5 <= x[0]] or self.tc_created
            up = [x for x in self.tc_uploads if walk_t and walk_t[0] - 5 <= x[0]] or self.tc_uploads
            out["texture_churn_per_600_frames"] = {
                "created": round(st.mean(x[1] for x in sel)), "deleted": round(st.mean(x[2] for x in sel)),
                "uploads": round(st.mean(x[1] for x in up)) if up else None,
                "upload_mib": round(st.mean(x[2] for x in up)) if up else None,
                "scope": "walking" if walk_t else "whole run"}
        if self.margins:
            out["memory"] = {"out_of_memory_events": sum(1 for x in self.margins if x[1] > 0),
                             "out_of_memory_max_mib": max(x[1] for x in self.margins),
                             "lines": len(self.margins)}
        if self.live_phases:
            groups = {}
            for ph in self.live_phases:
                groups.setdefault(ph["label"], []).append(ph["fps"])
            out["live_phases"] = {k: {"phases": len(v), "fps": round(st.mean(v), 2)} for k, v in groups.items()}
        for r in ("light", "queued", "mid", "heavy"):
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
        print(f"{'run':30s} {'build':10s} {'era':9s} {'stand':>5s} {'walk':>5s} | {'light':>9s} {'queued':>9s} "
              f"{'mid':>9s} {'heavy':>9s} | {'back/hv':>7s} {'gpu/hv':>6s} {'worst':>5s} {'shaders':>7s}")
        for path in runs:
            s = load(path).summary()
            rg = s["regimes"]
            cell = lambda r: f"{_fmt(rg[r]['fps'])}x{rg[r]['windows']}"
            print(f"{s['run'][:30]:30s} {_fmt(s['build'])[:10]:10s} {s['era'][:9]:9s} "
                  f"{_fmt(s['standing']['fps']):>5s} {_fmt(s['walking']['fps']):>5s} | "
                  f"{cell('light'):>9s} {cell('queued'):>9s} {cell('mid'):>9s} {cell('heavy'):>9s} | "
                  f"{_fmt(rg['heavy']['back_busy_ms']):>7s} {_fmt(rg['heavy']['gpu_ms']):>6s} "
                  f"{_fmt(s['worst_ms'], 0):>5s} {s['pipelines_in_play']:>7d}")
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
                print(f"{d['t']:7.1f} {d['kind']:4s} {d['phase'][:5]:5s} {d['regime']:6s} fps {d['fps']:5.1f} fence {d['fence_ms']:5.1f} "
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
