#!/usr/bin/env python3
"""bright_scan.py: every short picture glitch in a stretch of a recording, dark AND bright (count_flashes.py sees dark only).

  bright_scan.py <video> [--from s] [--to s] [--mark door=79.9] [--all] [--json out.json]

One decode of the stretch at 60 fps to a 32x18 grid of cell colours (ffmpeg area scaler). A cell is off in a frame
when it differs 10% or more from the median of its own 0.2 s before AND from the median of 0.2 s that starts a
little later (0.15 s or 0.4 s later, either), while those two medians agree within 12%: so it came back, and cuts,
fades and lasting changes do not count. Off cells are 'd' dark (darker), 'b' bright (brighter) or 'c' colour
(same brightness, other colour). 10 or more off cells in a frame = a glitch frame; glitch frames up to two frames
apart are one flash. A flash is called dark, bright or colour when that kind has at least twice the cells of the
other two together, otherwise mixed. Left out: the outer ring of cells and a 7x3-cell corner top-left (where a
performance overlay sits). The rule for what counts as a glitch (40 cells, length) is in rule.py.

Prints the counts per minute and one line per flash (frame number, time, cells, kind, length); --all also lists
flashes under 40 cells. Long recordings take a while: keep --to - --from to a few minutes.
Needs Python 3.8+ and ffmpeg on the PATH, nothing else.
"""
import argparse, json, pathlib, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rule as R  # noqa: E402

FPS = 60
PRE = round(R.PRE_S * FPS)               # frames in a median window (0.2 s)
GAPS = (round(R.GAP_S * FPS), 24)        # frames between the frame and the after-window (0.15 s, 0.4 s)
FLOOR = 40                               # brightness floor for the 10% reference


def med(v):
    s = sorted(v)
    return s[len(s) // 2]


def video_rate(video):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=avg_frame_rate",
                          "-of", "json", str(video)], capture_output=True, text=True, check=True).stdout
    top, bottom = json.loads(out)["streams"][0]["avg_frame_rate"].split("/")
    return float(top) / max(float(bottom), 1)


def scan(video, start=0.0, end=0.0):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}"]
    if end:
        cmd += ["-t", f"{end - start:.3f}"]
    raw = subprocess.run(cmd + ["-i", str(video), "-vf", f"fps={FPS},scale={R.GX}:{R.GY}:flags=area,format=rgb24",
                                "-f", "rawvideo", "-"], capture_output=True).stdout
    GX, GY = R.GX, R.GY
    n = len(raw) // (GX * GY * 3)
    cells = [(x, y) for y in range(R.EDGE, GY - R.EDGE) for x in range(R.EDGE, GX - R.EDGE) if not (y < 3 and x < 7)]
    off = [dict() for _ in range(n)]          # frame -> {(x, y): (kind, relative change)}
    for (x, y) in cells:
        o = (y * GX + x) * 3
        Y, CR, CB = [], [], []
        for i in range(n):
            p = i * GX * GY * 3 + o
            r, g, b = raw[p], raw[p + 1], raw[p + 2]
            Y.append(0.299 * r + 0.587 * g + 0.114 * b); CR.append(r - g); CB.append(b - g)
        for i in range(PRE, n - GAPS[0] - PRE):
            py = med(Y[i - PRE:i])
            for gap in GAPS:
                j = i + gap
                if j + PRE > n:
                    continue
                qy = med(Y[j:j + PRE])
                ref = max((py + qy) / 2, FLOOR)
                if abs(py - qy) > R.RECOVER * ref:
                    continue
                d = Y[i] - (py + qy) / 2
                if Y[i] < py * (1 - R.DROP) and Y[i] < qy * (1 - R.DROP) and py >= R.MIN_PRE:
                    off[i][(x, y)] = ("d", d / ref); break
                if Y[i] > py + R.DROP * ref and Y[i] > qy + R.DROP * ref:
                    off[i][(x, y)] = ("b", d / ref); break
                pr, qr = med(CR[i - PRE:i]), med(CR[j:j + PRE])
                pb, qb = med(CB[i - PRE:i]), med(CB[j:j + PRE])
                if abs(pr - qr) <= R.RECOVER * ref and abs(pb - qb) <= R.RECOVER * ref:
                    c = max(abs(CR[i] - (pr + qr) / 2), abs(CB[i] - (pb + qb) / 2))
                    if c >= 1.5 * R.DROP * ref:
                        off[i][(x, y)] = ("c", c / ref); break
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
        kinds = {"d": 0, "b": 0, "c": 0}
        for kind, _ in f.values():
            kinds[kind] += 1
        kind = ("dark" if kinds["d"] >= 2 * (kinds["b"] + kinds["c"]) else
                "bright" if kinds["b"] >= 2 * (kinds["d"] + kinds["c"]) else
                "colour" if kinds["c"] >= 2 * (kinds["d"] + kinds["b"]) else "mixed")
        out.append({"t": round(start + e["peak"] / FPS, 3), "ms": round((e["last"] - e["first"] + 1) * 1000 / FPS),
                    "cells": e["cells"], "kind": kind, "dark": kinds["d"], "bright": kinds["b"], "colour": kinds["c"],
                    "change_pct": round(sum(abs(v) for _, v in f.values()) / len(f) * 100, 1),
                    "map": ["".join(f[(x, y)][0] if (x, y) in f else "." for x in range(GX)) for y in range(GY)]})
    return n, out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--from", dest="start", type=float, default=0.0)
    ap.add_argument("--to", dest="end", type=float, default=0.0)
    ap.add_argument("--mark", action="append", help="NAME=SECONDS, a moment named in game_light.json")
    ap.add_argument("--all", action="store_true", help="also list flashes under 40 cells")
    ap.add_argument("--json", help="also write the full result here (with a cell map per flash)")
    a = ap.parse_args()
    video = pathlib.Path(a.video)
    rate = video_rate(video)
    frames, found = scan(video, a.start, a.end)
    if not frames:
        sys.exit(f"{video.name}: no frames read")
    own = R.game_light_spans(R.parse_marks(a.mark)) if a.mark else []
    for f in found:
        f["frame"] = round(f["t"] * rate)
        f["game_light"] = R.is_game_light(f, own)
        f["glitch"] = R.is_glitch(f) and not f["game_light"]
    mins = frames / FPS / 60
    glitches = [f for f in found if f["glitch"]]
    count = lambda kind: sum(f["kind"] == kind for f in glitches)
    print(f"{video.name}: {frames / FPS:.0f} s scanned from {a.start:g} s, video {rate:g} fps")
    print(f"glitches (40+ cells) {len(glitches)} ({len(glitches) / mins:.2f}/min): dark {count('dark')}, bright {count('bright')}, "
          f"colour {count('colour')}, mixed {count('mixed')}; full-scene (100+) "
          f"{sum(f['cells'] >= R.FULL_SCENE for f in glitches)}; all flashes 10+ cells {len(found)}")
    print("\n    time s    frame  cells  kind     ms  change%  d/b/c        note")
    for f in found:
        if not (f["glitch"] or a.all):
            continue
        note = ("glitch" if f["glitch"] else "game's own light, not counted" if f["game_light"]
                else "too long" if f["cells"] >= R.GLITCH_CELLS else "")
        print(f"  {f['t']:8.2f} {f['frame']:8d} {f['cells']:6d}  {f['kind']:6} {f['ms']:5d} {f['change_pct']:7.1f}  "
              f"{f['dark']}/{f['bright']}/{f['colour']:<8} {note}")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"video": video.name, "from": a.start, "frames": frames,
                                                    "game_light_spans": own, "flashes": found}, indent=1))


if __name__ == "__main__":
    main()
