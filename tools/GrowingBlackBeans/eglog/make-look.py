#!/usr/bin/env python3
"""make-look.py: cut a LOOK grid out of a picture, for the test harness's screen-synchronised waits.

    make-look.py PICTURE --region X,Y,W,H [--cells COLSxROWS] [--at SECONDS] [--min SCORE]
    make-look.py PICTURE --probe                  print the picture's size and a 8x8 brightness map
    make-look.py --selftest                       check the cell arithmetic against known images

The harness waits for a region of the screen to look a certain way:

    <seconds> WAIT <timeout> LOOK <x> <y> <w> <h> <cols>x<rows>:<hex> [<min>]

x, y, w and h are in per mille of the picture, so the line survives a resolution change. The hex is
each cell's mean brightness, two digits a cell, row by row. This script produces that line from a
screenshot, which is the piece the harness needs and does not ship: without it nobody can author a
WAIT ... LOOK by hand.

**The arithmetic is deliberately identical to the harness's own `GridOf`**, so a line made here matches
what the app computes at run time:

  - the region is x0 = x*width/1000, y0 = y*height/1000, and x1/y1 likewise from x+w and y+h, each at
    least one pixel past its start;
  - each cell spans xa..xb and ya..yb cut from that region by integer arithmetic on col/cols and
    row/rows, again at least one pixel wide;
  - a cell's value is the mean of (29*B + 150*G + 77*R) / 256 over its pixels, which is the same
    integer luma the harness uses;
  - the division is integer, floor, over the cell's pixel count.

Scoring at run time is by correlation, so brightness and contrast do not count, only shape. That means
a LOOK made at one time of day still matches at another, and also that **a LOOK cannot see a flash** --
for that, use a brightness meter, not this.

Reads PPM (what the harness's shot switch writes) and PNG. PNG needs no third-party module: it is
decoded here with zlib, for the colour types a screenshot actually uses.
"""

import argparse
import io
import os
import struct
import sys
import zlib


# ---------------------------------------------------------------- picture reading

class Picture:
    def __init__(self, width, height, rgb):
        self.width = width
        self.height = height
        self.rgb = rgb  # bytes, 3 per pixel, row-major, top row first

    def luma(self, x, y):
        i = (y * self.width + x) * 3
        r, g, b = self.rgb[i], self.rgb[i + 1], self.rgb[i + 2]
        return (29 * b + 150 * g + 77 * r)


def read_ppm(data):
    """P6 binary PPM, the format the harness's shot switch writes."""
    if not data.startswith(b"P6"):
        return None
    fields, i = [], 2
    while len(fields) < 3:
        while i < len(data) and data[i : i + 1].isspace():
            i += 1
        if data[i : i + 1] == b"#":
            while i < len(data) and data[i] != 0x0A:
                i += 1
            continue
        j = i
        while j < len(data) and not data[j : j + 1].isspace():
            j += 1
        fields.append(int(data[i:j]))
        i = j
    i += 1  # the single whitespace after maxval
    w, h, maxval = fields
    if maxval != 255:
        raise SystemExit(f"only 8-bit PPM is supported, this one has maxval {maxval}")
    need = w * h * 3
    if len(data) - i < need:
        raise SystemExit("PPM is truncated")
    return Picture(w, h, data[i : i + need])


def read_png(data):
    """Enough PNG for a screenshot: 8-bit RGB or RGBA, no interlace, no palette."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    pos, idat, w = 8, bytearray(), None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        kind = data[pos + 4 : pos + 8]
        body = data[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            w, h, depth, colour, _comp, _filt, interlace = struct.unpack(">IIBBBBB", body)
            if depth != 8 or colour not in (2, 6) or interlace != 0:
                raise SystemExit(f"unsupported PNG: depth {depth}, colour type {colour}, "
                                 f"interlace {interlace}")
            channels = 3 if colour == 2 else 4
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
    if w is None:
        raise SystemExit("PNG has no header")
    raw = zlib.decompress(bytes(idat))
    stride = w * channels
    out = bytearray(w * h * 3)
    prev = bytearray(stride)
    at = 0
    for row in range(h):
        filt = raw[at]
        at += 1
        line = bytearray(raw[at : at + stride])
        at += stride
        if filt == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif filt == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif filt == 3:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif filt == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 0xFF
        elif filt != 0:
            raise SystemExit(f"unknown PNG filter {filt}")
        for px in range(w):
            out[(row * w + px) * 3 : (row * w + px) * 3 + 3] = line[px * channels : px * channels + 3]
        prev = line
    return Picture(w, h, bytes(out))


def load(path):
    data = io.open(path, "rb").read()
    for reader in (read_ppm, read_png):
        pic = reader(data)
        if pic is not None:
            return pic
    raise SystemExit(f"{path}: not a P6 PPM or a PNG")


# ---------------------------------------------------------------- the grid, as GridOf computes it

def grid_of(pic, x, y, w, h, cols, rows):
    """Byte-for-byte the harness's GridOf: per-mille region, integer cell cuts, integer luma mean."""
    width, height = pic.width, pic.height
    if not width or not height or not cols or not rows:
        return []
    x0, y0 = x * width // 1000, y * height // 1000
    x1 = max(x0 + 1, (x + w) * width // 1000)
    y1 = max(y0 + 1, (y + h) * height // 1000)
    out = []
    for row in range(rows):
        ya = y0 + (y1 - y0) * row // rows
        yb = min(height, max(ya + 1, y0 + (y1 - y0) * (row + 1) // rows))
        for col in range(cols):
            xa = x0 + (x1 - x0) * col // cols
            xb = min(width, max(xa + 1, x0 + (x1 - x0) * (col + 1) // cols))
            total = count = 0
            for yy in range(ya, yb):
                for xx in range(xa, xb):
                    total += pic.luma(xx, yy)
                count += xb - xa
            out.append((total // (256 * max(count, 1))) & 0xFF)
    return out


def grid_text(grid):
    return "".join(f"{v:02x}" for v in grid)


# ---------------------------------------------------------------- commands

def cmd_look(a):
    pic = load(a.picture)
    try:
        x, y, w, h = (int(v) for v in a.region.split(","))
    except ValueError:
        raise SystemExit("--region wants four per-mille numbers: X,Y,W,H")
    for name, v in (("x", x), ("y", y), ("w", w), ("h", h)):
        if not 0 <= v <= 1000:
            raise SystemExit(f"--region {name}={v} is outside 0..1000 per mille")
    if x + w > 1000 or y + h > 1000:
        raise SystemExit("--region runs past the edge of the picture (x+w or y+h over 1000)")
    try:
        cols, rows = (int(v) for v in a.cells.lower().split("x"))
    except ValueError:
        raise SystemExit("--cells wants COLSxROWS, for example 8x4")
    if cols < 1 or rows < 1 or cols * rows > 4096:
        raise SystemExit("--cells must be at least 1x1 and at most 4096 cells")
    grid = grid_of(pic, x, y, w, h, cols, rows)
    print(f"# {os.path.basename(a.picture)}  {pic.width}x{pic.height}  "
          f"region {x},{y},{w},{h} per mille  {cols}x{rows} cells")
    line = f"{a.at} WAIT {a.timeout} LOOK {x} {y} {w} {h} {cols}x{rows}:{grid_text(grid)}"
    if a.min is not None:
        line += f" {a.min}"
    print(line)
    span = max(grid) - min(grid)
    if span < 12:
        print(f"# WARNING: the cells span only {span} of 255. A flat region scores well against almost")
        print(f"#          anything, because the run-time score is a correlation. Pick a region with")
        print(f"#          structure in it, or this WAIT will pass on the wrong screen.")
    return 0


def cmd_probe(a):
    pic = load(a.picture)
    print(f"{os.path.basename(a.picture)}: {pic.width}x{pic.height}")
    print("8x8 brightness map of the whole picture (hex, row by row):")
    grid = grid_of(pic, 0, 0, 1000, 1000, 8, 8)
    for row in range(8):
        print("   " + " ".join(f"{grid[row * 8 + c]:02x}" for c in range(8)))
    print("\nPick a region with variation in it, then rerun with --region X,Y,W,H in per mille.")
    return 0


def cmd_selftest(_a):
    """The cell arithmetic against images whose means are known by hand."""
    fails = 0

    def check(ok, what):
        nonlocal fails
        print("ok   " + what if ok else "FAIL " + what)
        if not ok:
            fails += 1

    # a 4x4 picture, left half black, right half white
    w = h = 4
    rgb = bytearray()
    for y in range(h):
        for x in range(w):
            v = 0 if x < 2 else 255
            rgb += bytes((v, v, v))
    pic = Picture(w, h, bytes(rgb))
    g = grid_of(pic, 0, 0, 1000, 1000, 2, 1)
    # white luma = (29+150+77)*255/256 = 255 (integer: 256*255//256)
    check(g == [0, 255], f"two cells over a black/white split give {g}, expected [0, 255]")

    g = grid_of(pic, 0, 0, 1000, 1000, 1, 1)
    check(g == [127], f"one cell over the whole thing gives {g}, expected [127] (floor of 127.5)")

    # a region covering only the right half
    g = grid_of(pic, 500, 0, 500, 1000, 1, 1)
    check(g == [255], f"a per-mille region over the white half gives {g}, expected [255]")

    # more cells than pixels: every cell must still be at least one pixel, none out of range
    g = grid_of(pic, 0, 0, 1000, 1000, 8, 8)
    check(len(g) == 64 and all(0 <= v <= 255 for v in g),
          "asking for more cells than pixels still returns in-range values")

    # channel weighting: pure green is much brighter than pure blue
    # integer floors: 77*255//256 = 76, 150*255//256 = 149, 29*255//256 = 28
    for name, colour, want in (("red", (255, 0, 0), 76), ("green", (0, 255, 0), 149),
                               ("blue", (0, 0, 255), 28)):
        p = Picture(1, 1, bytes(colour))
        v = grid_of(p, 0, 0, 1000, 1000, 1, 1)[0]
        check(v == want, f"pure {name} reads {v}, expected {want}")

    check(grid_text([0, 255, 16]) == "00ff10", "hex text is two digits a cell, in order")

    print("\nall passed" if not fails else f"\n{fails} FAILED")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("picture", nargs="?")
    ap.add_argument("--region", help="X,Y,W,H in per mille of the picture")
    ap.add_argument("--cells", default="8x4", help="COLSxROWS (default 8x4)")
    ap.add_argument("--at", default="0", help="the script time to print on the WAIT line")
    ap.add_argument("--timeout", default="20", help="the WAIT timeout in seconds")
    ap.add_argument("--min", help="minimum score (the harness defaults to 85)")
    ap.add_argument("--probe", action="store_true", help="print the size and an 8x8 brightness map")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return cmd_selftest(a)
    if not a.picture:
        ap.error("a picture is needed (or --selftest)")
    if a.probe:
        return cmd_probe(a)
    if not a.region:
        ap.error("--region is needed; run with --probe first to find one")
    return cmd_look(a)


if __name__ == "__main__":
    sys.exit(main())
