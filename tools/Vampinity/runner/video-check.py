#!/usr/bin/env python3
"""Scans a capture frame by frame for what timed screenshots miss, and writes a report and a picture sheet.

  video-check.py <video> [--out <folder>] [--name <prefix>] [--max 16]

Looks at every frame of a small copy of the video (64x36, top-left and bottom-right corners left out:
the overlay and the map stay still and would hide changes):
  pop      one or two frames unlike the frames on both sides: a flash, dropout or wrong image
  black    the picture goes mostly black
  white    the picture goes mostly white
  noise    many bright, saturated pixels: speckle or wrong memory
  patch    part of the picture jumps and jumps back, the rest stays: tile holes
  freeze   no change for over 1.5 s: a stall, or simply nothing moving on screen
Scores are only pointers. Look at the sheet before believing one. Needs ffmpeg and ffprobe.
"""
import argparse, json, pathlib, subprocess, sys

W, H = 64, 36
CELLS_X, CELLS_Y = 8, 6


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=avg_frame_rate:format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    info = json.loads(out)
    top, bottom = info["streams"][0]["avg_frame_rate"].split("/")
    return float(top) / max(float(bottom), 1), float(info["format"]["duration"])


def usable():
    """Pixels that count: not the overlay corner, not the map corner."""
    keep = []
    for y in range(H):
        for x in range(W):
            if (x < 12 and y < 6) or (x >= 42 and y >= 22):
                continue
            keep.append(y * W + x)
    return keep


def read_frames(path):
    process = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"scale={W}:{H}:flags=neighbor",
                                "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    size = W * H * 3
    while True:
        data = process.stdout.read(size)
        if len(data) < size:
            break
        yield data
    process.wait()


def measure(data, keep):
    luma, black, white, noisy = [], 0, 0, 0
    for i in keep:
        r, g, b = data[i * 3], data[i * 3 + 1], data[i * 3 + 2]
        value = (r * 3 + g * 6 + b) // 10
        luma.append(value)
        black += value < 24
        white += value > 225
        # Speckle: a bright saturated pixel unlike the pixel beside it. Plain bright colours don't count.
        j = (i + 1) * 3 if (i + 1) % W else (i - 1) * 3
        noisy += (max(r, g, b) - min(r, g, b) > 150 and max(r, g, b) > 170
                  and abs(r - data[j]) + abs(g - data[j + 1]) + abs(b - data[j + 2]) > 220)
    n = len(keep)
    return luma, sum(luma) / n, black / n, white / n, noisy / n


def difference(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def cells(a, b, keep):
    """Share of 8x6 cells that changed a lot."""
    sums, counts = {}, {}
    for value_a, value_b, i in zip(a, b, keep):
        cell = (i % W) * CELLS_X // W + ((i // W) * CELLS_Y // H) * CELLS_X
        sums[cell] = sums.get(cell, 0) + abs(value_a - value_b)
        counts[cell] = counts.get(cell, 0) + 1
    return sum(sums[c] / counts[c] > 45 for c in sums) / len(sums)


def scan(path):
    keep = usable()
    rows, kept = [], []
    for data in read_frames(path):
        luma, mean, black, white, noisy = measure(data, keep)
        rows.append({"mean": mean, "black": black, "white": white, "noisy": noisy})
        kept.append(luma)
        if len(kept) > 5:
            kept[-6] = None
        n = len(rows) - 1
        rows[n]["diff"] = difference(luma, kept[n - 1]) if n else 0.0
        rows[n]["pop"] = rows[n]["patch"] = 0.0
        if n >= 2:
            # The frame before last against its neighbours: unlike both, while they match each other.
            before, middle, after = kept[n - 2], kept[n - 1], luma
            around = difference(before, after)
            away = min(difference(before, middle), difference(middle, after))
            rows[n - 1]["pop"] = away - around
            rows[n - 1]["patch"] = cells(before, middle, keep) if around < 8 else 0.0
    return rows


def events(rows, fps):
    found = []

    def add(kind, start, end, score):
        found.append({"kind": kind, "start": start / fps, "end": end / fps, "score": round(score, 1), "frame": (start + end) // 2})

    def spans(test, minimum, kind, score):
        start = None
        for i, row in enumerate(rows + [None]):
            on = row is not None and test(row)
            if on and start is None:
                start = i
            elif not on and start is not None:
                if i - start >= minimum:
                    add(kind, start, i - 1, score(rows[start:i]))
                start = None

    for i, row in enumerate(rows):
        if row["pop"] > 18:
            add("pop", i, i, row["pop"])
        elif row["patch"] >= 0.08:
            add("patch", i, i, row["patch"] * 100)
    spans(lambda r: r["black"] > 0.6, 2, "black", lambda s: 100 * max(r["black"] for r in s))
    spans(lambda r: r["white"] > 0.55, 2, "white", lambda s: 100 * max(r["white"] for r in s))
    spans(lambda r: r["noisy"] > 0.02, 1, "noise", lambda s: 100 * max(r["noisy"] for r in s))
    spans(lambda r: r["diff"] < 0.25, int(fps * 1.5), "freeze", lambda s: len(s) / fps)
    return sorted(found, key=lambda e: e["start"])


def sheet(path, chosen, out):
    """Picture sheet of the chosen moments: for a pop, the frame itself and the one before it."""
    if not chosen:
        return False
    inputs, labels = [], []
    for event in chosen:
        inputs += ["-ss", f"{max(event['start'], 0):.3f}", "-i", str(path)]
        labels.append(f"{event['kind']} {event['start']:.1f}s")
    columns = 4
    filters = [f"[{i}:v]trim=end_frame=1,scale=400:-2[v{i}]" for i in range(len(labels))]
    while len(labels) % columns:
        labels.append("")
        filters.append(f"[0:v]trim=end_frame=1,scale=400:-2,drawbox=c=black:t=fill[v{len(labels) - 1}]")
    rows = []
    for r in range(len(labels) // columns):
        names = "".join(f"[v{r * columns + c}]" for c in range(columns))
        filters.append(f"{names}hstack=inputs={columns}[r{r}]")
        rows.append(f"[r{r}]")
    final = rows[0] if len(rows) == 1 else "out"
    if len(rows) > 1:
        filters.append("".join(rows) + f"vstack=inputs={len(rows)}[out]")
    else:
        final = "r0"
    command = ["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(filters), "-map",
                                                          f"[{final}]", "-frames:v", "1", str(out)]
    ok = subprocess.run(command).returncode == 0
    if ok:  # This ffmpeg has no text filter, so the order goes in a file: left to right, top to bottom.
        out.with_suffix(".order.txt").write_text("\n".join(l for l in labels if l) + "\n")
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video")
    parser.add_argument("--out")
    parser.add_argument("--name", default="video-check")
    parser.add_argument("--max", type=int, default=16)
    args = parser.parse_args()
    path = pathlib.Path(args.video)
    out = pathlib.Path(args.out) if args.out else path.parent
    out.mkdir(parents=True, exist_ok=True)
    fps, duration = probe(path)
    rows = scan(path)
    if not rows:
        sys.exit("no frames could be read")
    fps = len(rows) / duration if duration else fps
    found = events(rows, fps)
    count = {}
    for event in found:
        count[event["kind"]] = count.get(event["kind"], 0) + 1
    share = lambda key, limit: 100 * sum(r[key] > limit for r in rows) / len(rows)
    lines = [f"{path.name}: {len(rows)} frames, {duration:.1f} s, {fps:.1f} fps",
             f"black {share('black', 0.6):.0f}% of frames, white {share('white', 0.55):.0f}%, noise {share('noisy', 0.02):.0f}%",
             "events: " + (", ".join(f"{k} {v}" for k, v in sorted(count.items())) or "none"), ""]
    for event in found[:200]:
        lines.append(f"{event['start']:8.2f} to {event['end']:8.2f} s  {event['kind']:6} {event['score']}")
    (out / f"{args.name}.txt").write_text("\n".join(lines) + "\n")
    (out / f"{args.name}.json").write_text(json.dumps({"fps": fps, "duration": duration, "events": found}, indent=1))
    # The sheet: a spread of kinds, strongest first, freezes last as they are usually harmless.
    order = {"noise": 0, "patch": 1, "pop": 2, "white": 3, "black": 4, "freeze": 5}
    chosen, seen = [], []
    for event in sorted(found, key=lambda e: (order[e["kind"]], -e["score"])):
        if all(abs(event["start"] - t) > 1.0 for t in seen):
            chosen.append(event)
            seen.append(event["start"])
        if len(chosen) == args.max:
            break
    made = sheet(path, sorted(chosen, key=lambda e: e["start"]), out / f"{args.name}.jpg")
    print("\n".join(lines[:3]))
    print(f"report {out / (args.name + '.txt')}" + (f", sheet {out / (args.name + '.jpg')}" if made else ""))


if __name__ == "__main__":
    main()
