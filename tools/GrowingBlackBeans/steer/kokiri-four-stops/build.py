#!/usr/bin/env python3
"""Build kokiri-four-stops.txt, the scripted benchmark route (house, stops A-D), from the runKW2 walk.

Inputs, all from runKW2 (14 Nov 2026, t134-gbb9):
  - the PS5 capture video (passed on the command line),
  - the STEER points Vampinity's tools/Vampinity/steer/steer-route.py printed for each leg
    (--step 4 --radius 4 --picture 1920x1080+0+0; the capture's header says 1088 rows, the frames have 1080),
  - the four stands, read off our own track (steer-route.py track/stops) and the L2 presses in
    logs/recorded-input.txt (log time = video time + 36.3 s).

Each stop is pinned by:
  position  STEER to an approach point P on the walked path (r=4, then r=2), then to the stand S (r=3);
  facing    L2 (camera behind Link, who faces P->S), one short stick tap turning him by the difference
            between that and the facing of the KW2 stand, L2 again (camera behind the new facing, default
            pitch: this also fixes the tilt);
  check     a fingerprint of the KW2 view cut from the video at the start and the end of the stand. The
            MAYBE never needs to match (min 100); its wait_skipped line says best= (how alike the view is
            to KW2's: 93-98 on the right facing, ~70 at 10 degrees off, ~65 at 25, below 0 turned round)
            and seen= (the grid itself, for comparing starts).
  stand     a plain 62 s gap with no input and no picture reads between the two fingerprints.

Run: python3 build.py VIDEO  (writes kokiri-four-stops.txt and points.png next to this file)
"""
import math, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080

# Vampinity's steer-route.py output for the four legs (video seconds in the comment).
LEGS = {
    "A": "829,900 833,896 837,896 841,894 843,887 843,879",                       # 25.4-39.9
    "B": "843,869 839,866 836,862 832,857 829,852 826,846 823,841 819,837 815,833 812,828 808,825",  # 104.0-117.2
    "C": "806,823 808,816 810,808 813,805 817,800 821,798 825,797 829,800 834,803 838,806",  # 180.6-197.6
    "D": ("841,806 844,811 848,815 851,821 854,826 857,831 862,829 867,827 871,831 873,838 874,845 "
          "874,853 872,860 867,864 863,867 859,865 858,858"),                      # 281.0-304.3
}
# The stands: position (mean after the L2 that set the view), camera bearing (0 = up, clockwise), the
# video seconds the fingerprints are cut at, and the seconds walked on the leg before it.
STOPS = {
    "A": dict(s=(843.4, 869.1), cam=338, fp=(43.0, 103.0), walk=14, what="out of the house, hopped down, facing down the main path"),
    "B": dict(s=(806.4, 822.7), cam=286, fp=(119.0, 179.0), walk=13, what="the back of the forest, facing the Kokiri blocking the path"),
    "C": dict(s=(841.0, 804.2), cam=160, fp=(204.0, 280.0), walk=17, what="after the ivy wall, at the large rock, looking out over the cliff"),
    "D": dict(s=(858.1, 857.8), cam=258, fp=(311.0, 379.0), walk=23, what="the shop sign, facing it"),
}
APPROACH = 9.0       # per mille of width: P is the last walked point at least this far before S
CUT = 2.0            # per mille of width: how far the line P->S may leave the walked path
TURN_MIN = 8         # degrees: a smaller difference is left alone
TAP_MS = 150         # the turning tap; tune on the console if the fingerprints say the facing is off
HOLD = 62            # seconds between the two fingerprints
SEARCH_STEP = 15     # degrees a search turn
SEARCH_MS = 120      # its tap (KS1: a 150 ms tap turned C the full +59 deg)
SEARCH_EVERY = 1.4   # seconds a search turn takes: tap, L2 0.6 s later, two looks at the settled view
SEARCH_TAPS = 24     # a full circle
SEARCH_MIN = 60      # KS1 scored the right view 77-87 against KW2's capture; D's view scores <=27 off by 45
                     # deg and at most 80 anywhere else in KW2
REGION = (0, 80, 780, 840)   # the fingerprint's region: no hearts, no minimap, no overlay text
COLS, ROWS = 16, 9

HEARTS = "44 56 63 26 9x3:45553b4c56325356296f80617680567f8046356e293b6b2046691a 80"
TITLE = "403 848 194 42 24x3:0111010102010101010101010101010101010101010101013233454a4d43421c1e61343e622954453d5828513e444223092d372627231c1f0c221f1f0f140f1f0a211220181d291f"
LOAD = "400 0 200 75 16x4:3634333437373737393b3b3b3a3939394745454748484f494d554d4b49494b4b5d5c5e5e5d5e8091a78763636262626378787c7b7b7c817c7c827d7d7d7e7c7f"


def dist(a, b):
    return math.hypot(a[0] - b[0], (a[1] - b[1]) * 9 / 16)


def off(a, b, p):
    """How far p is from the straight line a-b, per mille of width."""
    ax, ay, bx, by, px, py = a[0], a[1] * 9 / 16, b[0], b[1] * 9 / 16, p[0], p[1] * 9 / 16
    length = math.hypot(bx - ax, by - ay)
    return abs((bx - ax) * (ay - py) - (ax - px) * (by - ay)) / length if length else 0.0


def bearing(a, b):
    return math.degrees(math.atan2((b[0] - a[0]) * W / 1000, -(b[1] - a[1]) * H / 1000)) % 360


def pts(text):
    return [tuple(float(v) for v in p.split(",")) for p in text.split()]


def fmt(p):
    """The harness reads whole per mille only (Number in test_harness.h): a 843.4 would stop the script."""
    return f"{round(p[0])},{round(p[1])}"


def frame(video, t):
    return subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-f", "rawvideo",
                           "-pix_fmt", "bgra", "-"], capture_output=True, check=True).stdout


def grid(raw):
    """As GridOf in test_harness.h (luma 29/150/77 of BGRA), sampling every 4th pixel."""
    x, y, w, h = REGION
    x0, y0, x1, y1 = x * W // 1000, y * H // 1000, (x + w) * W // 1000, (y + h) * H // 1000
    out = []
    for r in range(ROWS):
        ya, yb = y0 + (y1 - y0) * r // ROWS, y0 + (y1 - y0) * (r + 1) // ROWS
        for c in range(COLS):
            xa, xb = x0 + (x1 - x0) * c // COLS, x0 + (x1 - x0) * (c + 1) // COLS
            tot = n = 0
            for yy in range(ya, yb, 4):
                row = raw[(yy * W + xa) * 4:(yy * W + xb) * 4]
                for i in range(0, len(row), 16):
                    tot += 29 * row[i] + 150 * row[i + 1] + 77 * row[i + 2]
                    n += 1
            out.append(tot // (256 * max(n, 1)))
    return out


def look(g, least=100):
    x, y, w, h = REGION
    return f"LOOK {x} {y} {w} {h} {COLS}x{ROWS}:" + "".join(f"{v:02x}" for v in g) + f" {least}"


def plan():
    """[(name, walked points to P, P, S, heading P->S, turn)]"""
    out = []
    for name, st in STOPS.items():
        s = st["s"]
        walked = pts(LEGS[name])
        # P: the nearest walked point at least APPROACH before S whose straight line to S keeps within
        # CUT of every walked point between them (at D the walk goes round a tree: a straight line from
        # further back would cut into it). If none, the furthest point back that keeps within CUT.
        p = None
        for k in range(len(walked) - 1, -1, -1):
            q = walked[k]
            if any(off(q, s, m) > CUT for m in walked[k + 1:]):
                break
            p = q
            if dist(q, s) >= APPROACH:
                break
        before = walked[:walked.index(p)]
        heading = bearing(p, s)
        turn = (st["cam"] - heading + 180) % 360 - 180
        out.append((name, before, p, s, heading, turn))
    return out


def stick(turn):
    r = math.radians(turn)
    return 128 + round(127 * math.sin(r)), 128 - round(127 * math.cos(r))


def script(video):
    lines = [
        "# The Kokiri benchmark route: house, then stops A, B, C and D, 62 s each, by minimap steering.",
        "# Made by gbb-tools/steer/kokiri-four-stops/build.py from runKW2 (14 Nov 2026, t134-gbb9): the STEER points",
        "# are Vampinity's steer-route.py on the KW2 capture, the stands and facings are KW2's. Read build.py.",
        "# Start: your house save (the 11 Nov one, top of the load list), EDEN_TEST_DISCARD_SAVE=1 so it stays on top.",
        "# After the load Link stands on the house floor at minimap 829,900.",
        "# Opening (title, Continue, load) as Vampinity's tools/Vampinity/routes scripts. Clock: seconds count from",
        "# EDEN_GUEST_START; lines after a WAIT or STEER count from the moment it was met (test_harness.h).",
        "# Buttons: A through the game's mapping (opening, as Vampinity's), L2 = the targeting button you pressed in KW2.",
        "",
        f"0 WAIT 180 LOOK {TITLE}",
        "1.5 A 150",
        "4.5 A 150",
        f"1.0 WAIT 8 LOOK {LOAD}",
        "1.0 A 150", "3.0 A 150", "5.0 A 150", "7.0 A 150", "9.0 A 150",
        f"0.5 WAIT 15 GONE {LOAD}",
        "# Loading. No input. Up to 240 s for the hearts (a cold shader store is slow).",
        f"0 WAIT 240 LOOK {HEARTS}",
    ]
    for name, before, p, s, heading, turn in plan():
        st = STOPS[name]
        g0, g1 = grid(frame(video, st["fp"][0])), grid(frame(video, st["fp"][1]))
        timeout = max(45, 3 * st["walk"])
        lines += ["", f"# --- leg to stop {name} ({st['what']}): {len(before)} walked points, then P {fmt(p)} "
                      f"and the stand {fmt(s)} (P->S heads {heading:.0f} deg)"]
        if before:
            lines.append(f"1 STEER {timeout} " + " ".join(fmt(q) for q in before + [p]) + " r=4")
            lines.append(f"0.2 STEER 10 {fmt(p)} r=2")
        else:
            lines.append(f"1 STEER {timeout} {fmt(p)} r=2")
        lines.append(f"0.2 STEER 20 {fmt(s)} r=3")
        lines.append(f"# stop {name}: KW2 faced {st['cam']} deg; L2, turn {turn:+.0f} deg, L2")
        lines.append("0.3 L2 150")
        if abs(turn) >= TURN_MIN:
            x, y = stick(turn)
            lines.append(f"1.1 LSTICK {x} {y} {TAP_MS}")
            lines.append("1.8 L2 150")
            settled = 2.8
        else:
            settled = 1.3
        # Closed loop (added after runKS1, where D faced ~45 deg off: its approach is shorter than the
        # reach radius, so Link's heading on arrival is not set). Small turns the same way as the first,
        # each followed by L2, until the view looks like KW2's (SEARCH_MIN); then the rest are dropped.
        # A, B and C matched at 77-87 in KS1, so they pass on the first look.
        step = SEARCH_STEP if turn >= 0 else -SEARCH_STEP
        x, y = stick(step)
        lines.append(f"# then turn {step:+d} deg at a time until the view is KW2's (score {SEARCH_MIN}), at most "
                     f"{SEARCH_TAPS} turns")
        for k in range(SEARCH_TAPS):
            t = settled + 0.7 + k * SEARCH_EVERY
            lines.append(f"{t:.1f} LSTICK {x} {y} {SEARCH_MS}")
            lines.append(f"{t + 0.6:.1f} L2 150")
        lines.append(f"{settled} MAYBE {settled + 1 + SEARCH_TAPS * SEARCH_EVERY:.0f} {look(g0, SEARCH_MIN)}")
        lines.append(f"# fingerprints of KW2's view at video {st['fp'][0]:.0f} s and {st['fp'][1]:.0f} s; between them the stand")
        lines.append(f"1.0 MAYBE 1 {look(g0)}")
        lines.append(f"{HOLD} MAYBE 1 {look(g1)}")
    lines += ["", "5 END", ""]
    return "\n".join(lines)


def picture(video):
    from PIL import Image, ImageDraw
    raw = frame(video, 41.0)
    img = Image.frombytes("RGBA", (W, H), raw, "raw", "BGRA").convert("RGB")
    box = (1500, 840, 1760, 1000)
    img = img.crop(box).resize(((box[2] - box[0]) * 4, (box[3] - box[1]) * 4), Image.LANCZOS)
    d = ImageDraw.Draw(img)

    def px(q):
        return ((q[0] * W / 1000 - box[0]) * 4, (q[1] * H / 1000 - box[1]) * 4)

    colours = {"A": (230, 60, 60), "B": (60, 120, 230), "C": (160, 60, 200), "D": (20, 150, 90)}
    for name, before, p, s, heading, turn in plan():
        c = colours[name]
        chain = [px(q) for q in before + [p, s]]
        d.line(chain, fill=c, width=3)
        for q in before:
            x, y = px(q)
            d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=c)
        x, y = px(p)
        d.rectangle((x - 5, y - 5, x + 5, y + 5), outline=(0, 0, 0), width=2)
        x, y = px(s)
        d.ellipse((x - 9, y - 9, x + 9, y + 9), outline=(0, 0, 0), width=3, fill=c)
        r = math.radians(STOPS[name]["cam"])
        d.line((x, y, x + 34 * math.sin(r), y - 34 * math.cos(r)), fill=(0, 0, 0), width=4)
        d.text((x + 10, y - 22), name, fill=(0, 0, 0))
    path = os.path.join(HERE, "points.png")
    img.save(path)
    return path


if __name__ == "__main__":
    video = sys.argv[1]
    for name, before, p, s, heading, turn in plan():
        print(f"{name}: {len(before)} walked points, P {fmt(p)} ({dist(p, s):.1f} per mille), heading {heading:.0f}, "
              f"KW2 facing {STOPS[name]['cam']}, turn {turn:+.0f}" + (f" -> LSTICK {stick(turn)}" if abs(turn) >= TURN_MIN else " (none)"))
    out = os.path.join(HERE, "kokiri-four-stops.txt")
    with open(out, "w") as fh:
        fh.write(script(video))
    print("wrote", out)
    print("wrote", picture(video))
