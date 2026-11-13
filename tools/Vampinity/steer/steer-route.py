#!/usr/bin/env python3
"""Turn a stretch of recorded play into a STEER line: the path the player walked on the minimap, as
points the test harness can walk again (script command STEER, headless/test_harness.h). A path someone
really walked is open ground. Reads a video file only; never talks to the console.

  steer-route.py VIDEO --from S --to S --headless DIR [--step 12] [--back] [--radius 6] [--fps 5]
                 [--picture auto|WxH+X+Y]

  VIDEO          a recording with the game picture in it. The picture is found by itself (--picture auto:
                 the part of the frame that is ever lit), whether it fills the recording or sits unscaled
                 in a corner. Give WxH+X+Y to say it yourself.
  --from/--to    the stretch, in the video's seconds
  --headless DIR the folder that holds minimap_steer.h (headless/ of the Eglantine-PS5- source). Or set
                 STEER_HEADLESS.
  --step N       points at least N per mille of the picture's width apart (default 12; raised by itself
                 when the path would need more than 64 points)
  --back         walk the same path back as well: a loop that ends where it started
  --radius N     a point counts as reached within N per mille (default 6, the harness's own default)

Prints how well the minimap was read, the path's length and the player's speed on the map, and the
script line with a timeout of twice the time the walk took in the recording. The detector is the
harness's own (minimap_steer.h), built next to this file as steer-cli-bin on first use.
Needs python3, ffmpeg and ffprobe on PATH, and a C++20 compiler (c++).
"""
import argparse
import json
import math
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
BINARY = HERE / "steer-cli-bin"
MAX_POINTS = 64
DARK_FRAME = 18     # mean luma under this = black


def cli(headless):
    """The detector as a program, built when it is missing or older than its sources."""
    sources = [HERE / "steer_cli.cpp", headless / "minimap_steer.h"]
    if not all(s.exists() for s in sources):
        sys.exit(f"need steer_cli.cpp next to this file and minimap_steer.h in {headless}")
    if not BINARY.exists() or BINARY.stat().st_mtime < max(s.stat().st_mtime for s in sources):
        done = subprocess.run(["c++", "-std=c++20", "-O2", "-I", str(headless), str(sources[0]), "-o", str(BINARY)],
                              capture_output=True, text=True)
        if done.returncode:
            sys.exit("could not build the detector:\n" + done.stderr[-800:])
    return BINARY


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    info = json.loads(out)
    s = info["streams"][0]
    return int(s["width"]), int(s["height"]), float(info["format"]["duration"])


def picture_box(path):
    """[x, y, width, height] of the game's picture in the recording, None when it fills the frame (or
    nothing is ever lit). Twelve frames spread over the video, at 192x108: the box of every sample that is
    brighter than black in any of them. A box within 3% of the frame on every side is the whole frame."""
    width, height, duration = probe(path)
    small_w, small_h = 192, 108
    lit = bytearray(small_w * small_h)
    for k in range(12):
        at = duration * (k + 0.5) / 12
        data = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{at:.3f}", "-i", str(path), "-frames:v", "1", "-an", "-vf",
                               f"scale={small_w}:{small_h}:flags=area,format=gray", "-f", "rawvideo", "-"],
                              capture_output=True).stdout
        if len(data) == len(lit):
            lit = bytearray(max(a, b) for a, b in zip(lit, data))
    rows = [y for y in range(small_h) if max(lit[y * small_w:(y + 1) * small_w]) > DARK_FRAME]
    cols = [x for x in range(small_w) if max(lit[x::small_w]) > DARK_FRAME]
    if not rows or not cols:
        return None
    x0, x1, y0, y1 = cols[0], cols[-1] + 1, rows[0], rows[-1] + 1
    if x0 <= 0.03 * small_w and x1 >= 0.97 * small_w and y0 <= 0.03 * small_h and y1 >= 0.97 * small_h:
        return None
    even = lambda value: int(round(value / 2)) * 2
    box = [even(x0 * width / small_w), even(y0 * height / small_h),
           even((x1 - x0) * width / small_w), even((y1 - y0) * height / small_h)]
    return box if box[2] >= 64 and box[3] >= 64 else None


def picture_of(video, picture):
    """(width, height, x, y) of the game's picture in the recording."""
    if picture != "auto":
        found = re.fullmatch(r"(\d+)x(\d+)\+(\d+)\+(\d+)", picture)
        if not found:
            sys.exit("--picture is auto, or WxH+X+Y, for example 1280x720+0+0")
        return tuple(map(int, found.groups()))
    box = picture_box(video)
    if box:
        return box[2], box[3], box[0], box[1]
    width, height, _ = probe(video)
    return width, height, 0, 0


def fixes(video, start, end, fps, picture, headless):
    """[(seconds, x, y)] in per mille of the picture, where the player's marker and the camera wedge were found."""
    w, h, x, y = picture_of(video, picture)
    print(f"the game's picture: {w}x{h} at {x},{y}")
    binary = cli(headless)
    ffmpeg = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(end - start), "-i", str(video), "-vf",
                               f"fps={fps},crop={w}:{h}:{x}:{y}", "-f", "rawvideo", "-pix_fmt", "bgra", "-"],
                              stdout=subprocess.PIPE)
    out = subprocess.run([str(binary), str(w), str(h)], stdin=ffmpeg.stdout, capture_output=True, text=True)
    ffmpeg.wait()
    rows, total = [], 0
    for line in out.stdout.splitlines():
        p = line.split()
        total += 1
        if p[2] == "1" and p[3] == "1":
            rows.append((start + int(p[0]) / fps, float(p[4]), float(p[5])))
    return rows, total


def distance(a, b):
    """Per mille of the picture's width (a per mille of the height is 9/16 of one of the width)."""
    return math.hypot(b[0] - a[0], (b[1] - a[1]) * 9 / 16)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=pathlib.Path)
    ap.add_argument("--from", dest="start", type=float, required=True)
    ap.add_argument("--to", dest="end", type=float, required=True)
    ap.add_argument("--headless", type=pathlib.Path, default=os.environ.get("STEER_HEADLESS"))
    ap.add_argument("--step", type=float, default=12)
    ap.add_argument("--back", action="store_true")
    ap.add_argument("--radius", type=int, default=6)
    ap.add_argument("--fps", type=float, default=5)
    ap.add_argument("--picture", default="auto")
    args = ap.parse_args()
    if args.end <= args.start:
        sys.exit("--to must come after --from")
    if args.headless is None:
        sys.exit("give --headless DIR (the folder with minimap_steer.h) or set STEER_HEADLESS")
    rows, total = fixes(args.video, args.start, args.end, args.fps, args.picture, args.headless.resolve())
    if total == 0:
        sys.exit("no frames in that stretch")
    print(f"{total} frames, the player's marker and the camera wedge read in {len(rows)} ({100 * len(rows) / total:.0f}%)")
    if len(rows) < 10:
        sys.exit("too few to make a path: is the minimap on screen in this stretch?")
    # a jump is a misread (or another map): the player does not move 30 per mille in a fifth of a second
    path = [rows[0]]
    jumps = 0
    for row in rows[1:]:
        if distance(path[-1][1:], row[1:]) > 30 and row[0] - path[-1][0] < 2:
            jumps += 1
            continue
        path.append(row)
    length = sum(distance(a[1:], b[1:]) for a, b in zip(path, path[1:]))
    took = path[-1][0] - path[0][0]
    step = args.step
    while True:
        points = [path[0][1:]]
        for row in path[1:]:
            if distance(points[-1], row[1:]) >= step:
                points.append(row[1:])
        if distance(points[-1], path[-1][1:]) > args.radius:
            points.append(path[-1][1:])
        walk = points + points[-2::-1] if args.back else points
        if len(walk) <= MAX_POINTS:
            break
        step *= 1.25
    straight = sum(distance(a, b) for a, b in zip(walk, walk[1:]))
    print(f"path: {length:.0f} per mille walked in {took:.0f} s ({length / took:.1f} a second, standing included), "
          f"{jumps} misread jump(s) dropped")
    print(f"points: {len(walk)} at {step:.0f} per mille or more apart, {straight:.0f} per mille along them"
          + (", out and back" if args.back else ""))
    timeout = math.ceil(2 * took * (2 if args.back else 1) / 5) * 5
    text = " ".join(f"{round(x)},{round(y)}" for x, y in walk)
    print("\nScript line (after the WAIT that puts the player at the first point; seconds count from that WAIT):\n")
    print(f"1 STEER {timeout} {text}" + (f" r={args.radius}" if args.radius != 6 else ""))


if __name__ == "__main__":
    main()
