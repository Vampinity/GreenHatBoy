#!/usr/bin/env python3
"""steer-route.py: STEER points for the test harness, from a capture video of a walk.

    steer-route.py track  VIDEO [-o track.txt] [--fps 4]   Link's position and camera bearing per frame
    steer-route.py stops  TRACK                            where Link stood still, with times
    steer-route.py route  TRACK [--names A,B,C,D]          a script fragment: one STEER leg per stop
    steer-route.py places TRACK                            one line a second, for joining onto a run's log

`track` runs the harness's own finder (`minimap_steer.h`, unchanged, built into `steer_cli`) over the
video through ffmpeg, so the numbers are the ones STEER will see on the console. Nothing here
re-implements Find. The harness header names a `steer-route.py` that "prints them from a recording";
that tool isn't public, so this one was written to the same description (13 Nov 2026).

Units are the harness's own: x, y in per mille of the picture; distances in per mille of the picture's
WIDTH (a per mille of height is 9/16 of one of width), as minimap_steer::Distance measures them.

What `route` does with a track:
  - stops: stretches of at least --stand seconds where Link moved less than --still per mille;
  - a leg: the track from leaving one stop to arriving at the next, with frames where the finder lost
    Link dropped (and reported, because they are where STEER can't steer either);
  - points: the leg simplified (Ramer-Douglas-Peucker, --tolerance), then filled in so no two points
    are more than --spacing apart, then an approach point --approach before the stop, so the last
    stretch always runs the same way and ZL leaves the camera facing the same way every run;
  - at each stop: ZL, a one-look fingerprint of the whole screen (a MAYBE that can never match, so its
    wait_skipped line prints the grid it saw), a plain gap of --hold seconds (no WAIT, so no frame
    readbacks while measuring), and a second fingerprint.
It does NOT write the opening (title, Continue, load, door): take Vampinity's house-door lines.
"""

import argparse
import math
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_POINTS = 64  # test_harness.h kMaxSteerPoints
# A grid no screen can match: one brightness has no shape, and test_harness.h scores a shapeless grid 0.
# So the MAYBE always times out, and its wait_skipped line prints the 16x9 grid it actually saw.
FINGERPRINT = "0 0 1000 1000 16x9:" + "80" * (16 * 9)


def dist(a, b):
    return math.hypot(b[0] - a[0], (b[1] - a[1]) * 9.0 / 16.0)


def read_track(path):
    rows = []
    with open(path) as fh:
        for line in fh:
            p = line.split()
            if len(p) != 8 or line.startswith("#"):
                continue
            t, m, f, v = float(p[0]), int(p[1]), int(p[2]), int(p[3])
            rows.append({"t": t, "map": m, "found": f, "view": v, "x": float(p[4]), "y": float(p[5]),
                         "angle": float(p[6])})
    return rows


def cmd_track(a):
    cli = os.path.join(HERE, "steer_cli")
    if not os.path.exists(cli):
        print("build steer_cli first: clang++ -std=c++17 -O2 -o steer_cli steer_cli.cpp")
        return 1
    if not shutil.which("ffprobe") or not shutil.which("ffmpeg"):
        print("ffmpeg and ffprobe are needed")
        return 1
    size = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                           "stream=width,height", "-of", "csv=p=0:s=x", a.video],
                          capture_output=True, text=True, check=True).stdout.strip().split("x")
    w, h = int(size[0]), int(size[1])
    out = a.o or os.path.splitext(a.video)[0] + ".track.txt"
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.video, "-vf", f"fps={a.fps}", "-f", "rawvideo",
                           "-pix_fmt", "bgra", "-"], stdout=subprocess.PIPE)
    with open(out, "w") as fh:
        fh.write(f"# steer-route track of {os.path.basename(a.video)}: {w}x{h}, {a.fps} frames a second\n")
        fh.write("# t map found view x y angle area\n")
        fh.flush()
        subprocess.run([cli, str(w), str(h), str(a.fps)], stdin=ff.stdout, stdout=fh, check=True)
    ff.wait()
    rows = read_track(out)
    seen = sum(1 for r in rows if r["found"] and r["view"])
    onmap = sum(1 for r in rows if r["map"])
    print(f"{out}: {len(rows)} frames, {rows[-1]['t'] if rows else 0:.0f} s; map on screen {onmap}, "
          f"Link and camera found {seen} ({100 * seen / max(onmap, 1):.0f}% of map frames)")
    return 0


def find_stops(rows, stand, still):
    good = [r for r in rows if r["found"] and r["view"]]
    stops, i = [], 0
    while i < len(good):
        j = i
        while j + 1 < len(good) and dist((good[i]["x"], good[i]["y"]), (good[j + 1]["x"], good[j + 1]["y"])) <= still:
            j += 1
        if good[j]["t"] - good[i]["t"] >= stand:
            seg = good[i:j + 1]
            stops.append({"t0": seg[0]["t"], "t1": seg[-1]["t"],
                          "x": sum(r["x"] for r in seg) / len(seg), "y": sum(r["y"] for r in seg) / len(seg),
                          "angle": sorted(r["angle"] for r in seg)[len(seg) // 2], "n": len(seg)})
            i = j + 1
        else:
            i += 1
    return stops


def cmd_stops(a):
    rows = read_track(a.track)
    stops = find_stops(rows, a.stand, a.still)
    print(f"{len(stops)} stops (at least {a.stand:.0f} s within {a.still} per mille)")
    for k, s in enumerate(stops):
        print(f"  {k + 1}. t {s['t0']:7.1f}-{s['t1']:7.1f} s ({s['t1'] - s['t0']:5.1f} s)  "
              f"at {s['x']:.1f},{s['y']:.1f}  camera {s['angle']:.0f} deg")
    return 0


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    base = dist(a, b)

    def off(p):
        if base == 0:
            return dist(a, p)
        ax, ay, bx, by, px, py = a[0], a[1] * 9 / 16, b[0], b[1] * 9 / 16, p[0], p[1] * 9 / 16
        return abs((bx - ax) * (ay - py) - (ax - px) * (by - ay)) / base

    k, worst = 0, -1.0
    for i in range(1, len(pts) - 1):
        d = off(pts[i])
        if d > worst:
            k, worst = i, d
    if worst <= eps:
        return [a, b]
    return rdp(pts[:k + 1], eps)[:-1] + rdp(pts[k:], eps)


def fill(pts, spacing):
    out = [pts[0]]
    for p in pts[1:]:
        q = out[-1]
        n = int(dist(q, p) // spacing)
        for s in range(1, n + 1):
            f = s / (n + 1)
            out.append((q[0] + (p[0] - q[0]) * f, q[1] + (p[1] - q[1]) * f))
        out.append(p)
    return out


def approach_point(path, stop, back):
    """The point on the walked path `back` per mille before the stop (measured along the path)."""
    run = 0.0
    for i in range(len(path) - 1, 0, -1):
        run += dist(path[i], path[i - 1])
        if run >= back:
            return path[i - 1]
    return None


def cmd_route(a):
    rows = read_track(a.track)
    stops = find_stops(rows, a.stand, a.still)
    names = a.names.split(",") if a.names else [chr(ord("A") + k) for k in range(len(stops))]
    if len(stops) != len(names):
        print(f"# WARNING: {len(stops)} stops found, {len(names)} names given; check `stops` first")
    good = [r for r in rows if r["found"] and r["view"]]
    print(f"# Made by steer-route.py from {os.path.basename(a.track)}. Paste after the opening (door, hearts).")
    print(f"# Fingerprint at each stop: {FINGERPRINT[:24]}... never matches; its wait_skipped seen= grid is the view.")
    prev_t = rows[0]["t"] if rows else 0.0
    for k, s in enumerate(stops):
        name = names[k] if k < len(names) else str(k + 1)
        leg_rows = [r for r in rows if prev_t < r["t"] < s["t0"]]
        leg = [(r["x"], r["y"]) for r in leg_rows if r["found"] and r["view"]]
        lost = [r for r in leg_rows if r["map"] and not (r["found"] and r["view"])]
        nomap = [r for r in leg_rows if not r["map"]]
        stop_pt = (s["x"], s["y"])
        if not leg:
            print(f"# stop {name}: no tracked frames before it (in the house, or the map was off). "
                  f"Walk to it open loop.")
            pts = [stop_pt]
        else:
            pts = fill(rdp(leg + [stop_pt], a.tolerance), a.spacing)[1:]
            ap = approach_point(leg + [stop_pt], stop_pt, a.approach)
            if ap is not None and dist(ap, stop_pt) > a.radius + 1:
                pts = [p for p in pts[:-1] if dist(p, stop_pt) > dist(ap, stop_pt)] + [ap, stop_pt]
        if len(pts) > MAX_POINTS:
            print(f"# WARNING: {len(pts)} points, the harness takes {MAX_POINTS}; raise --spacing or --tolerance")
        walk_s = s["t0"] - prev_t
        print(f"\n# --- leg to stop {name}: video {prev_t:.1f}-{s['t0']:.1f} s ({walk_s:.0f} s walked), "
              f"{len(pts)} points; map off {len(nomap) / a.fps:.1f} s, Link lost {len(lost) / a.fps:.1f} s")
        for gap in spans(lost + nomap, a.fps):
            print(f"#     not steerable at video {gap[0]:.1f}-{gap[1]:.1f} s: take this stretch from recorded-input.txt")
        timeout = max(60, int(walk_s * 3))
        print(f"0.5 STEER {timeout} " + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) +
              (f" r={a.radius}" if a.radius != 6 else ""))
        print(f"# stop {name}: at {s['x']:.1f},{s['y']:.1f}, camera {s['angle']:.0f} deg in the recording")
        print("0.3 ZL 150")
        print(f"2.0 MAYBE 1 LOOK {FINGERPRINT} 100")
        print(f"{a.hold:g} MAYBE 1 LOOK {FINGERPRINT} 100")
        prev_t = s["t1"]
    print("\n5 END")
    return 0


def spans(rows, fps):
    ts = sorted(r["t"] for r in rows)
    out = []
    for t in ts:
        if out and t - out[-1][1] <= 1.5 / fps:
            out[-1][1] = t
        else:
            out.append([t, t])
    return [g for g in out if g[1] - g[0] >= 1.0]


def cmd_places(a):
    rows = read_track(a.track)
    print("# second map found x y angle")
    sec = {}
    for r in rows:
        sec.setdefault(int(r["t"]), []).append(r)
    for s in sorted(sec):
        g = [r for r in sec[s] if r["found"] and r["view"]]
        if g:
            m = g[len(g) // 2]
            print(f"{s} 1 1 {m['x']:.1f} {m['y']:.1f} {m['angle']:.0f}")
        else:
            print(f"{s} {int(any(r['map'] for r in sec[s]))} 0 - - -")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("track"); t.add_argument("video"); t.add_argument("-o"); t.add_argument("--fps", type=float, default=4)
    t.set_defaults(fn=cmd_track)
    for name, fn in (("stops", cmd_stops), ("route", cmd_route), ("places", cmd_places)):
        q = sub.add_parser(name); q.add_argument("track")
        q.add_argument("--stand", type=float, default=40, help="seconds still to count as a stop")
        q.add_argument("--still", type=float, default=2.0, help="per mille of width Link may drift in a stop")
        q.add_argument("--names")
        q.add_argument("--tolerance", type=float, default=2.0, help="RDP tolerance, per mille of width")
        q.add_argument("--spacing", type=float, default=25.0, help="most per mille of width between points")
        q.add_argument("--approach", type=float, default=12.0, help="approach point, per mille before a stop")
        q.add_argument("--radius", type=int, default=6, help="STEER r=, per mille of width")
        q.add_argument("--hold", type=float, default=65.0, help="seconds between the two fingerprints")
        q.add_argument("--fps", type=float, default=4, help="the track's frame rate")
        q.set_defaults(fn=fn)
    a = ap.parse_args()
    return a.fn(a) or 0


if __name__ == "__main__":
    sys.exit(main())
