#!/usr/bin/env python3
"""count_flashes.py: counts the short dark flashes in a capture recording (sunlit ground losing its sun for a frame).

  count_flashes.py <video> [--from s] [--to s] [--fps 30] [--mark door=79.9] [--json out.json]

What the glitch looks like: for one game frame (~50 ms) the direct sun drops out of a big part of the scene.
Stones, ground, water and the player go flat and 10-30% darker, sun shafts vanish, the hazy sky stays. Falling
leaves (small, dark, slow) are the main thing that must NOT count. This meter counts dark dips only; bright
glitches (white discs, blown-out highlights) are counted by bright_scan.py.

How: every sampled frame goes to a 32x18 grid of cell means (ffmpeg's area scaler). A cell dips when it is 10%
below the median of its own previous 0.2 s and below the median of 0.2 s that starts 0.15 s later, while those
two medians agree within 12% (so it came back). A frame is a flash frame when 10 or more cells dip at once;
consecutive flash frames are one flash; a flash longer than 200 ms is a fade and is dropped. All numbers live
in rule.py.

Only gameplay counts: with no --from/--to, lit stretches (mean >= 18) of at least 20 s, so black loading and
menus are left out; with --from/--to, every lit frame in that span. The grid is laid over the game's picture,
not the recording: a picture that sits smaller in the canvas is found and cropped first.

Prints flashes per minute, full-scene flashes (100 cells or more) per minute, and one line per flash with the
video frame number and time. --mark NAME=SECONDS switches on the game's own light stretches in game_light.json.
Needs Python 3.8+ and ffmpeg/ffprobe on the PATH, nothing else.
"""
import argparse, json, pathlib, statistics, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rule as R  # noqa: E402


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,avg_frame_rate:format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    info = json.loads(out)
    s = info["streams"][0]
    top, bottom = s["avg_frame_rate"].split("/")
    rate = float(top) / max(float(bottom), 1)
    return int(s["width"]), int(s["height"]), float(info["format"]["duration"]), rate


def picture_box(path):
    """[x, y, width, height] of the game's picture in the recording, None when it fills the frame. Twelve frames
    spread over the video at 192x108: the box of every sample brighter than black in any of them."""
    width, height, duration, _ = probe(path)
    small_w, small_h = 192, 108
    lit = bytearray(small_w * small_h)
    for k in range(12):
        at = duration * (k + 0.5) / 12
        data = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{at:.3f}", "-i", str(path), "-frames:v", "1", "-an", "-vf",
                               f"scale={small_w}:{small_h}:flags=area,format=gray", "-f", "rawvideo", "-"],
                              capture_output=True).stdout
        if len(data) == len(lit):
            lit = bytearray(max(a, b) for a, b in zip(lit, data))
    rows = [y for y in range(small_h) if max(lit[y * small_w:(y + 1) * small_w]) > R.DARK_FRAME]
    cols = [x for x in range(small_w) if max(lit[x::small_w]) > R.DARK_FRAME]
    if not rows or not cols:
        return None
    x0, x1, y0, y1 = cols[0], cols[-1] + 1, rows[0], rows[-1] + 1
    if x0 <= 0.03 * small_w and x1 >= 0.97 * small_w and y0 <= 0.03 * small_h and y1 >= 0.97 * small_h:
        return None
    even = lambda value: int(round(value / 2)) * 2
    box = [even(x0 * width / small_w), even(y0 * height / small_h),
           even((x1 - x0) * width / small_w), even((y1 - y0) * height / small_h)]
    return box if box[2] >= 64 and box[3] >= 64 else None


def read_grid(path, fps, start, end, box=None):
    crop = f"crop={box[2]}:{box[3]}:{box[0]}:{box[1]}," if box else ""
    cmd = ["ffmpeg", "-v", "error"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    if end:
        cmd += ["-to", f"{end:.3f}"]
    cmd += ["-i", str(path), "-an", "-vf",
            f"fps={fps},{crop}scale=320:180:flags=area,scale={R.GX}:{R.GY}:flags=area,format=gray", "-f", "rawvideo", "-"]
    data = subprocess.run(cmd, capture_output=True, check=True).stdout
    n = R.GX * R.GY
    return [data[i:i + n] for i in range(0, len(data) - n + 1, n)]


def gameplay(means, fps, exact):
    lit = [m >= R.DARK_FRAME for m in means]
    if exact:
        return lit
    keep, i = [False] * len(lit), 0
    while i < len(lit):
        j = i
        while j < len(lit) and lit[j] == lit[i]:
            j += 1
        if lit[i] and (j - i) / fps >= R.MIN_RUN:
            keep[i:j] = [True] * (j - i)
        i = j
    return keep


def dips(frames, keep, fps):
    """Per frame: list of (x, y, relative drop) for the cells that dip."""
    P = max(2, round(R.PRE_S * fps))
    G = max(2, round(R.GAP_S * fps))
    n = len(frames)
    cells = [(x, y, y * R.GX + x) for y in range(R.EDGE, R.GY - R.EDGE) for x in range(R.EDGE, R.GX - R.EDGE)]
    out = [[] for _ in range(n)]
    for t in range(P, n - G - P):
        if not all(keep[t - P:t + G + P]):
            continue
        for x, y, i in cells:
            v = frames[t][i]
            if v >= max(frames[k][i] for k in range(t - P, t)) * (1 - R.DROP):
                continue
            pre = statistics.median(frames[k][i] for k in range(t - P, t))
            if pre < R.MIN_PRE or v >= pre * (1 - R.DROP):
                continue
            post = statistics.median(frames[k][i] for k in range(t + G, t + G + P))
            if v >= post * (1 - R.DROP) or abs(post - pre) > R.RECOVER * pre:
                continue
            out[t].append((x, y, 1 - v / pre))
    return out


def flashes(per_frame, fps, t0, rate):
    found, t, n = [], 0, len(per_frame)
    while t < n:
        if len(per_frame[t]) < R.MIN_CELLS:
            t += 1
            continue
        s = t
        while t < n and len(per_frame[t]) >= R.MIN_CELLS:
            t += 1
        peak = max(range(s, t), key=lambda k: len(per_frame[k]))
        cells = per_frame[peak]
        at = t0 + peak / fps
        found.append({"t": round(at, 3), "frame": round(at * rate), "ms": round(1000 * (t - s) / fps),
                      "cells": len(cells), "drop_pct": round(100 * sum(c[2] for c in cells) / len(cells), 1),
                      "too_long": 1000 * (t - s) / fps > R.MAX_MS})
    return found


def measure(path, fps, start, end, marks=None):
    _, _, _, rate = probe(path)
    box = picture_box(path)
    frames = read_grid(path, fps, start, end, box)
    if not frames:
        sys.exit(f"{path.name}: no frames read")
    keep = gameplay([sum(f) / len(f) for f in frames], fps, bool(start or end))
    found = flashes(dips(frames, keep, fps), fps, start, rate)
    own = R.game_light_spans(marks) if marks else []
    for f in found:
        f["game_light"] = R.is_game_light(f, own)
    real = [f for f in found if not f["too_long"] and not f["game_light"]]
    mins = sum(keep) / fps / 60.0
    per_min = lambda k: round(k / mins, 2) if mins else None
    return {"video": path.name, "video_fps": round(rate, 3), "fps_sampled": fps, "picture": box,
            "gameplay_s": round(mins * 60, 1), "flashes": len(real), "flashes_per_min": per_min(len(real)),
            "full_scene": sum(f["cells"] >= R.FULL_SCENE for f in real),
            "full_scene_per_min": per_min(sum(f["cells"] >= R.FULL_SCENE for f in real)),
            "glitches_40": sum(f["cells"] >= R.GLITCH_CELLS for f in real),
            "cell_events_per_min": per_min(sum(f["cells"] for f in real)),
            "game_light_spans": own, "all": found,
            "params": {k: getattr(R, k) for k in ("GX", "GY", "EDGE", "PRE_S", "GAP_S", "DROP", "RECOVER", "MIN_PRE",
                                                  "MIN_CELLS", "MAX_MS", "DARK_FRAME", "MIN_RUN", "FULL_SCENE")}}


def report(r):
    if not r["gameplay_s"]:
        return [f"{r['video']}: no gameplay found (only black, loading or menus), nothing measured"]
    lines = [f"{r['video']}: {r['gameplay_s']:.0f} s gameplay, video {r['video_fps']:g} fps, sampled at {r['fps_sampled']:g} fps",
             f"dark flashes {r['flashes']} ({r['flashes_per_min']}/min), full-scene {r['full_scene']} "
             f"({r['full_scene_per_min']}/min), 40+ cells {r['glitches_40']}, {r['cell_events_per_min']} cell-events/min",
             "", "    time s    frame  cells  drop%    ms  note"]
    for f in r["all"]:
        note = ("fade, not counted" if f["too_long"] else "game's own light, not counted" if f["game_light"]
                else "full-scene" if f["cells"] >= R.FULL_SCENE else "")
        lines.append(f"  {f['t']:8.2f} {f['frame']:8d} {f['cells']:6d} {f['drop_pct']:6.1f} {f['ms']:5d}  {note}")
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--from", dest="start", type=float, default=0.0, help="start second in the video")
    ap.add_argument("--to", dest="end", type=float, default=0.0, help="end second in the video")
    ap.add_argument("--fps", type=float, default=30.0, help="frames sampled per second (30 matches published counts)")
    ap.add_argument("--mark", action="append", help="NAME=SECONDS, a moment named in game_light.json")
    ap.add_argument("--json", help="also write the full result here")
    a = ap.parse_args()
    path = pathlib.Path(a.video)
    r = measure(path, a.fps, a.start, a.end, R.parse_marks(a.mark))
    print("\n".join(report(r)))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
