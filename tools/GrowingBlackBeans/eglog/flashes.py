#!/usr/bin/env python3
"""flashes.py: read the flash counter (patch 0928, EDEN_GBB_FLASH).

  flashes.py log  RUN [RUN ...]            per-run totals and a 10 s timeline from the eden_log lines; v25 and v40
                                           count flashes as big as Vampinity's 25+ and 40+ cells of a 32 x 18 grid
                                           (4.3% and 6.9% of the screen), so the two counters compare
  flashes.py vamp RUN|FILE [...] [--events]  count exactly by Vampinity's rule (their tools/Vampinity/flash-counter
                                           code), from our grids resampled to what a capture card records
  flashes.py grids RUN|FILE [...] [--threshold 24] [--min-cells 4] [--min-share 0.043] [--pictures DIR]
                                           re-run the detector on the saved grids (EDEN_GBB_FLASH=2): a table per
                                           run at Vampinity's sizes, the flashes of at least --min-share of the
                                           screen, and optionally their frames as PGM pictures (the frame before,
                                           the flash, the frame after; 4x enlarged). The headline numbers: v25/v40.

The detector is the same as video_core/gbb_flash.h, line for line: a cell flashes when its brightness jumps by at
least THRESHOLD for one frame (or two) away from both neighbours, the same way, while the neighbours agree to within half
that jump. A frame is a flash when at least MIN_CELLS cells flash; a "still" flash when at least MIN_CELLS of them are also
outside the range of the 3x3 cells around them in both neighbouring frames (no motion of up to a cell explains them). Standard library only.
"""
import argparse
import gzip
import os
import re
import struct
import sys
from collections import deque

EVENT = re.compile(r"\[\s*([\d.]+)\].*EDEN_GBB_FLASH event present=(\d+) t_s=([\d.]+) kind=(\d)f (dark|bright) "
                   r"cells=(\d+) of (\d+)(?: still=(\d+))? jump=(\d+) box=(\d+),(\d+)-(\d+),(\d+)")
FIVE = re.compile(r"\[\s*([\d.]+)\].*EDEN_GBB_FLASH5 t_s=([\d.]+) frames=(\d+) flashes=(\d+)(?: still=(\d+))? large=(\d+) full=(\d+) "
                  r"cells=(\d+) dark=(\d+) bright=(\d+) skipped=(\d+)")


def find_log(run):
    for p in (os.path.join(run, "eden_log.txt"), os.path.join(run, "logs", "eden_log.txt"),
              os.path.join(run, "eden_log.txt.gz"), run):
        if os.path.isfile(p):
            return p
    raise SystemExit(f"{run}: no eden_log.txt")


def read_log(run):
    events, fives = [], []
    log = find_log(run)
    with (gzip.open(log, "rt", errors="replace") if log.endswith(".gz") else open(log, errors="replace")) as fh:
        for line in fh:
            if "EDEN_GBB_FLASH" not in line:
                continue
            m = EVENT.search(line)
            if m:
                g = m.groups()
                events.append({"log_s": float(g[0]), "present": int(g[1]), "t_s": float(g[2]), "kind": int(g[3]),
                               "dark": g[4] == "dark", "cells": int(g[5]), "of": int(g[6]), "still": int(g[7] or 0), "jump": int(g[8]),
                               "box": tuple(int(x) for x in g[9:13])})
                continue
            m = FIVE.search(line)
            if m:
                g = m.groups()
                fives.append({"log_s": float(g[0]), "t_s": float(g[1]), "frames": int(g[2]), "flashes": int(g[3]),
                              "still": int(g[4] or 0), "large": int(g[5]), "full": int(g[6]), "cells": int(g[7]),
                              "dark": int(g[8]), "bright": int(g[9]), "skipped": int(g[10])})
    return events, fives


def cmd_log(a):
    print(f"{'run':<16} {'frames':>7} {'flashes':>7} {'per 1k':>6} {'still':>5} {'v25':>4} {'v40':>4} {'large':>5} {'full':>4} {'dark':>5} "
          f"{'bright':>6} {'skipped':>7}")
    timelines = {}
    for run in a.runs:
        ev, fv = read_log(run)
        tot = {k: sum(f[k] for f in fv) for k in ("frames", "flashes", "still", "large", "full", "dark", "bright", "skipped")}
        per = 1000 * tot["flashes"] / tot["frames"] if tot["frames"] else 0
        name = os.path.basename(os.path.normpath(run))
        # Vampinity's sizes (docs/Vampinity/findings/frame-ahead-glitches-2026-11-09.md): 25+ and 40+ cells of a
        # 32 x 18 grid, i.e. at least 25/576 and 40/576 of the screen. From the logged events (capped at 10 a second).
        v25 = sum(1 for e in ev if e["cells"] * 576 >= 25 * e["of"])
        v40 = sum(1 for e in ev if e["cells"] * 576 >= 40 * e["of"])
        print(f"{name:<16} {tot['frames']:>7} {tot['flashes']:>7} {per:>6.1f} {tot['still']:>5} {v25:>4} {v40:>4} "
              f"{tot['large']:>5} {tot['full']:>4} "
              f"{tot['dark']:>5} {tot['bright']:>6} {tot['skipped']:>7}")
        bins = {}
        for e in ev:
            b = int(e["log_s"] // 10) * 10
            bins[b] = bins.get(b, 0) + 1
        timelines[name] = bins
    print("\nflash events per 10 s, by log time (the [seconds] at the start of each eden_log line; lines are capped "
          "at 10 a second, the 5 s totals above are not):")
    for name, bins in timelines.items():
        if not bins:
            print(f"  {name}: none")
            continue
        row = "  ".join(f"{b}s:{n}" for b, n in sorted(bins.items()))
        print(f"  {name}: {row}")
    if a.events:
        for run in a.runs:
            ev, _ = read_log(run)
            print(f"\n{run}:")
            for e in ev:
                print(f"  log {e['log_s']:8.2f}s  present {e['present']:6}  {e['kind']}f "
                      f"{'dark' if e['dark'] else 'bright':6} {e['cells']:5} cells ({e['still']} still)  jump {e['jump']:3}  "
                      f"box x {e['box'][0]}-{e['box'][2]}% y {e['box'][1]}-{e['box'][3]}%")


class Detector:
    """video_core/gbb_flash.h Detector, in Python."""

    def __init__(self, t, min_cells):
        self.t, self.min_cells, self.hist, self.size = t, min_cells, deque(maxlen=4), None

    def reset(self):
        self.hist.clear()

    def push(self, grid, w, h):
        if (w, h) != self.size:
            self.size = (w, h)
            self.hist.clear()
        self.hist.append(grid)
        r = None
        if len(self.hist) >= 3:
            r = self.one(self.hist[-3], self.hist[-2], self.hist[-1], w)
        if (r is None or r["cells"] < self.min_cells) and len(self.hist) >= 4:
            r = self.two(*self.hist, w)
        if r is None or r["cells"] < self.min_cells:
            return None
        return r

    def _add(self, r, i, darker, jump, w):
        x, y = i % w, i // w
        if r["cells"] == 0:
            r["box"] = [x, y, x, y]
        b = r["box"]
        b[0], b[1], b[2], b[3] = min(b[0], x), min(b[1], y), max(b[2], x), max(b[3], y)
        r["cells"] += 1
        r["dark"] += 1 if darker else 0
        r["sum_jump"] += jump
        r["where"].append(i)

    def outside(self, v, g, i, darker, w):
        """v at least t darker (brighter) than every cell of the 3x3 block around i in g (motion-proof)."""
        h, x, y, t = len(g) // w, i % w, i // w, self.t
        for yy in range(max(0, y - 1), min(h - 1, y + 1) + 1):
            for xx in range(max(0, x - 1), min(w - 1, x + 1) + 1):
                n = g[yy * w + xx]
                if (n - v < t) if darker else (v - n < t):
                    return False
        return True

    def one(self, a, b, c, w):
        t, r = self.t, {"kind": 1, "cells": 0, "dark": 0, "sum_jump": 0, "still": 0, "box": None, "where": []}
        for i in range(len(b)):
            da, dc = b[i] - a[i], b[i] - c[i]
            if (da > 0) != (dc > 0):
                continue
            jump = min(abs(da), abs(dc))
            if jump < t or abs(a[i] - c[i]) * 2 > jump:
                continue
            self._add(r, i, da < 0, jump, w)
            if self.outside(b[i], a, i, da < 0, w) and self.outside(b[i], c, i, da < 0, w):
                r["still"] += 1
        return r

    def two(self, a, b, c, d, w):
        t, r = self.t, {"kind": 2, "cells": 0, "dark": 0, "sum_jump": 0, "still": 0, "box": None, "where": []}
        for i in range(len(b)):
            ba, cd = b[i] - a[i], c[i] - d[i]
            if (ba > 0) != (cd > 0):
                continue
            jump = min(abs(ba), abs(cd))
            if jump < t or abs(b[i] - c[i]) * 2 > jump or abs(a[i] - d[i]) * 2 > jump:
                continue
            self._add(r, i, ba < 0, jump, w)
            if self.outside(b[i], a, i, ba < 0, w) and self.outside(c[i], d, i, ba < 0, w):
                r["still"] += 1
        return r


def read_grids(path):
    with (gzip.open(path, "rb") if path.endswith(".gz") else open(path, "rb")) as fh:
        if fh.read(8)[:6] != b"GBBFL1":
            raise SystemExit(f"{path}: not a flash grid file")
        while True:
            head = fh.read(24)
            if len(head) < 24:
                return
            w, h, present, ns = struct.unpack("<IIQQ", head)
            data = fh.read(w * h)
            if len(data) < w * h:
                return
            yield w, h, present, ns, data


def write_pgm(path, grid, w, h, scale=4, mark=()):
    marked = set(mark)
    rows = []
    for y in range(h):
        row = bytearray()
        for x in range(w):
            v = grid[y * w + x]
            if (y * w + x) in marked and (x + y) % 2 == 0:
                v = 255 if v < 128 else 0  # checker the flashing cells so they show in the picture
            row += bytes([v]) * scale
        rows.append(bytes(row) * 1)
    with open(path, "wb") as fh:
        fh.write(f"P5 {w * scale} {h * scale} 255\n".encode())
        for row in rows:
            for _ in range(scale):
                fh.write(row)


def grid_file(arg):
    """A gbb-flash-*.bin, or a run folder holding one in logs/ (the newest)."""
    if os.path.isfile(arg):
        return arg
    # The console's logs/ folder keeps earlier sessions' grids too: take the file this run's eden_log names.
    for log in (os.path.join(arg, "eden_log.txt"), os.path.join(arg, "logs", "eden_log.txt"),
                os.path.join(arg, "eden_log.txt.gz")):
        if os.path.isfile(log):
            with (gzip.open(log, "rt", errors="replace") if log.endswith(".gz") else open(log, errors="replace")) as fh:
                for line in fh:
                    m = re.search(r"writing every grid to \S*/(gbb-flash-\d+\.bin)", line)
                    if m:
                        for d in (os.path.join(arg, "logs"), arg):
                            for name in (m.group(1), m.group(1) + ".gz"):
                                if os.path.isfile(os.path.join(d, name)):
                                    return os.path.join(d, name)
                        raise SystemExit(f"{arg}: the log names {m.group(1)}, which isn't in the folder")
    for d in (os.path.join(arg, "logs"), arg):
        if os.path.isdir(d):
            found = sorted((os.path.getmtime(os.path.join(d, f)), f) for f in os.listdir(d)
                           if f.startswith("gbb-flash-") and f.endswith((".bin", ".bin.gz")))
            if found:
                return os.path.join(d, found[-1][1])
    raise SystemExit(f"{arg}: no gbb-flash-*.bin")


def scan(path, a):
    det = Detector(a.threshold, a.min_cells)
    recent = deque(maxlen=6)
    first_ns, last_present, n, events = None, None, 0, []
    for w, h, present, ns, data in read_grids(path):
        if first_ns is None:
            first_ns = ns
        if last_present is not None and present != last_present + 1:
            det.reset()
            recent.clear()
        last_present = present
        recent.append((present, ns, data))
        n += 1
        r = det.push(list(data), w, h)
        if not r:
            continue
        cells = w * h
        back = 1 if r["kind"] == 1 else 2
        p, pns, _ = recent[-1 - back]
        b = r["box"]
        e = {"still": r["still"], "present": p, "t_s": (pns - first_ns) / 1e9, "kind": r["kind"],
             "cells": r["cells"], "share": r["cells"] / cells, "still_share": r["still"] / cells,
             "dark": r["dark"] * 2 >= r["cells"], "jump": r["sum_jump"] // r["cells"],
             "box": (b[0] * 100 // w, b[1] * 100 // h, (b[2] + 1) * 100 // w, (b[3] + 1) * 100 // h)}
        events.append(e)
        if a.pictures and e["share"] >= a.min_share and sum(x["share"] >= a.min_share for x in events) <= a.around:
            out = os.path.join(a.pictures, os.path.basename(path).replace(".bin", ""))
            os.makedirs(out, exist_ok=True)
            frames = list(recent)[-(back + 2):]
            for k, (fp, _, fd) in enumerate(frames):
                role = "before" if k == 0 else ("after" if k == len(frames) - 1 else "flash")
                write_pgm(os.path.join(out, f"t{e['t_s']:07.2f}-{k}-{role}-p{fp}.pgm"), fd, w, h,
                          mark=r["where"] if role == "flash" else ())
    return n, events


def cmd_grids(a):
    v25, v40 = 25 / 576, 40 / 576
    print(f"Sizes as Vampinity counts them (25+ / 40+ cells of a 32 x 18 grid = {100 * v25:.1f}% / {100 * v40:.1f}% "
          f"of the screen); 'still' = of those, flashes whose motion-proof cells alone reach {100 * v25:.1f}%. "
          f"Small flashes (any size, at least {a.min_cells} cells) are mostly the game's own motion.")
    print(f"{'run':<22} {'frames':>7} {'small':>6} {'v25':>4} {'v40':>4} {'still':>5} {'v25 dark/bright':>16}")
    per_run = []
    for arg in a.files:
        path = grid_file(arg)
        n, events = scan(path, a)
        big = [e for e in events if e["share"] >= v25]
        name = os.path.basename(os.path.normpath(arg)) if os.path.isdir(arg) else os.path.basename(arg)
        dark = sum(e["dark"] for e in big)
        print(f"{name:<22} {n:>7} {len(events):>6} {len(big):>4} {sum(e['share'] >= v40 for e in big):>4} "
              f"{sum(e['still_share'] >= v25 for e in big):>5} {f'{dark}/{len(big) - dark}':>16}")
        per_run.append((name, events))
    for name, events in per_run:
        listed = [e for e in events if e["share"] >= a.min_share]
        print(f"\n{name}: {len(listed)} flashes of {100 * a.min_share:.1f}% of the screen or more "
              f"(seconds after the first counted frame)")
        for e in listed:
            print(f"  t {e['t_s']:8.2f}s  present {e['present']:6}  {e['kind']}f {'dark' if e['dark'] else 'bright':6} "
                  f"{100 * e['share']:5.1f}% ({100 * e['still_share']:.1f}% still)  jump {e['jump']:3}  "
                  f"box x {e['box'][0]}-{e['box'][2]}% y {e['box'][1]}-{e['box'][3]}%")


def vamp_dir(arg):
    """Vampinity's tools/Vampinity/flash-counter: --vampinity, else found next to this toolkit in the repo."""
    cands = [arg] if arg else []
    here = os.path.dirname(os.path.abspath(__file__))
    cands += [os.path.join(here, "..", "..", "Vampinity", "flash-counter"),
              os.path.expanduser("~/Desktop/work/GreenHatBoy/tools/Vampinity/flash-counter")]
    for c in cands:
        if c and os.path.isfile(os.path.join(c, "count_flashes.py")):
            return os.path.abspath(c)
    raise SystemExit("can't find Vampinity's flash-counter (tools/Vampinity/flash-counter); pass --vampinity DIR")


def to_grid(data, w, h, gx, gy):
    """Area average of a w x h brightness grid onto gx x gy cells (fractional overlaps weighted)."""
    out = []
    for cy in range(gy):
        y0, y1 = cy * h / gy, (cy + 1) * h / gy
        for cx in range(gx):
            x0, x1 = cx * w / gx, (cx + 1) * w / gx
            tot = wt = 0.0
            for y in range(int(y0), min(h, int(y1) + 1)):
                fy = min(y + 1, y1) - max(y, y0)
                if fy <= 0:
                    continue
                row = y * w
                for x in range(int(x0), min(w, int(x1) + 1)):
                    fx = min(x + 1, x1) - max(x, x0)
                    if fx > 0:
                        tot += data[row + x] * fx * fy
                        wt += fx * fy
            out.append(int(round(tot / wt)) if wt else 0)
    return bytes(out)


def video_like(path, fps, gx, gy):
    """What a capture card at fps would have recorded, on Vampinity's grid: at each 1/fps the frame last presented.
    Returns (frames, first_ns)."""
    small, times = [], []
    for w, h, present, ns, data in read_grids(path):
        small.append(to_grid(data, w, h, gx, gy))
        times.append(ns)
    if not small:
        return [], 0
    frames, k, step = [], 0, 1e9 / fps
    t = times[0]
    while t <= times[-1]:
        while k + 1 < len(times) and times[k + 1] <= t:
            k += 1
        frames.append(small[k])
        t += step
    return frames, times[0]


def cmd_vamp(a):
    import importlib.util
    d = vamp_dir(a.vampinity)
    sys.path.insert(0, d)
    spec = importlib.util.spec_from_file_location("vamp_count_flashes", os.path.join(d, "count_flashes.py"))
    cf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cf)
    R = cf.R
    print(f"Counted by Vampinity's rule ({d}/rule.py): {R.GX}x{R.GY} grid, outer ring left out, a cell off by "
          f"{100 * R.DROP:.0f}% against the medians of {R.PRE_S} s before and after, {R.MIN_CELLS}+ cells a flash, "
          f"{R.GLITCH_CELLS}+ a glitch, {R.FULL_SCENE}+ full-scene. Our grids are resampled to what a capture card "
          "would have recorded (the frame on screen at each tick). Dark: their own count_flashes code at 30 fps. "
          "Bright: their bright_scan rule at 60 fps on brightness only (our grids hold no colour, so no colour "
          "flashes).")
    print(f"{'run':<22} {'minutes':>7} {'dark':>5} {'/min':>5} {'dark40':>6} {'bright':>6} {'/min':>5} "
          f"{'bright40':>8} {'full':>4}")
    detail = []
    for arg in a.files:
        path = grid_file(arg)
        name = os.path.basename(os.path.normpath(arg)) if os.path.isdir(arg) else os.path.basename(arg)
        frames, _ = video_like(path, 30, R.GX, R.GY)
        keep = cf.gameplay([sum(f) / len(f) for f in frames], 30, False)
        dark = [f for f in cf.flashes(cf.dips(frames, keep, 30), 30, 0.0, 30) if not f["too_long"]]
        mins = sum(keep) / 30 / 60
        frames60, _ = video_like(path, 60, R.GX, R.GY)
        keep60 = cf.gameplay([sum(f) / len(f) for f in frames60], 60, False)
        bright = bright_scan_luma(frames60, keep60, R)
        per = lambda n: n / mins if mins else 0
        full = sum(f["cells"] >= R.FULL_SCENE for f in dark) + sum(f["cells"] >= R.FULL_SCENE for f in bright)
        print(f"{name:<22} {mins:>7.1f} {len(dark):>5} {per(len(dark)):>5.1f} "
              f"{sum(f['cells'] >= R.GLITCH_CELLS for f in dark):>6} {len(bright):>6} {per(len(bright)):>5.1f} "
              f"{sum(f['cells'] >= R.GLITCH_CELLS and f['ms'] <= R.GLITCH_MS for f in bright):>8} {full:>4}")
        detail.append((name, dark, bright))
    if a.events:
        for name, dark, bright in detail:
            print(f"\n{name}: seconds after the first counted frame")
            for f in sorted([dict(x, k="dark") for x in dark] + [dict(x, k="bright") for x in bright],
                            key=lambda x: x["t"]):
                print(f"  t {f['t']:8.2f}s  {f['k']:6} {f['cells']:4} cells  {f['ms']:4} ms")


def bright_scan_luma(frames, keep, R, fps=60):
    """Vampinity's bright_scan rule (dark and bright cells; no colour), on 60 fps brightness grids."""
    pre = round(R.PRE_S * fps)
    gaps = (round(R.GAP_S * fps), 24)
    floor = 40
    gx, gy = R.GX, R.GY
    n = len(frames)
    cells = [(x, y) for y in range(R.EDGE, gy - R.EDGE) for x in range(R.EDGE, gx - R.EDGE) if not (y < 3 and x < 7)]
    off = [dict() for _ in range(n)]
    med = lambda v: sorted(v)[len(v) // 2]
    for (x, y) in cells:
        i0 = y * gx + x
        Y = [f[i0] for f in frames]
        for i in range(pre, n - gaps[0] - pre):
            if not keep[i]:
                continue
            py = med(Y[i - pre:i])
            for gap in gaps:
                j = i + gap
                if j + pre > n:
                    continue
                qy = med(Y[j:j + pre])
                ref = max((py + qy) / 2, floor)
                if abs(py - qy) > R.RECOVER * ref:
                    continue
                if Y[i] < py * (1 - R.DROP) and Y[i] < qy * (1 - R.DROP) and py >= R.MIN_PRE:
                    off[i][(x, y)] = "d"
                    break
                if Y[i] > py + R.DROP * ref and Y[i] > qy + R.DROP * ref:
                    off[i][(x, y)] = "b"
                    break
    events, cur = [], None
    for i in range(n):
        k = len(off[i])
        if k >= R.MIN_CELLS:
            if cur and i - cur["last"] <= 2:
                cur["last"] = i
                if k > cur["cells"]:
                    cur["cells"], cur["peak"] = k, i
            else:
                cur = {"first": i, "last": i, "peak": i, "cells": k}
                events.append(cur)
    out = []
    for e in events:
        f = off[e["peak"]]
        nb = sum(v == "b" for v in f.values())
        nd = len(f) - nb
        if nb < 2 * nd:  # bright_scan calls it bright only when bright cells dominate; dark ones are count_flashes'
            continue
        out.append({"t": round(e["peak"] / fps, 3), "ms": round((e["last"] - e["first"] + 1) * 1000 / fps),
                    "cells": e["cells"]})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    lg = sub.add_parser("log")
    lg.add_argument("runs", nargs="+")
    lg.add_argument("--events", action="store_true", help="also list every logged event")
    gr = sub.add_parser("grids")
    gr.add_argument("files", nargs="+", help="gbb-flash-*.bin files or run folders")
    gr.add_argument("--min-share", type=float, default=25 / 576,
                    help="list (and draw) flashes covering at least this share of the screen (default 25/576)")
    gr.add_argument("--threshold", type=int, default=24)
    gr.add_argument("--min-cells", type=int, default=4)
    gr.add_argument("--pictures")
    gr.add_argument("--around", type=int, default=40, help="pictures for the first N listed flashes per run")
    vp = sub.add_parser("vamp", help="count by Vampinity's rule (tools/Vampinity/flash-counter)")
    vp.add_argument("files", nargs="+", help="gbb-flash-*.bin files or run folders")
    vp.add_argument("--vampinity", help="path to tools/Vampinity/flash-counter")
    vp.add_argument("--events", action="store_true")
    a = ap.parse_args()
    return {"log": cmd_log, "grids": cmd_grids, "vamp": cmd_vamp}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
