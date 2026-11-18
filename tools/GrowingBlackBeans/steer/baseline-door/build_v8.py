#!/usr/bin/env python3
"""build_v8.py V6_SCRIPT BC1_VIDEO > v8: the baseline route with the house door steered by the picture.

Why (17 Nov 2026): on the control, 2 of 12 cold starts missed the house door (CC4, BD1). v6 swings the camera
right then left for 1.5 s each (RSTICK), presses ZL and pushes forward 4 s: open loop, and how far a timed swing
turns depends on the frame rate. There is no minimap inside the house, so it cannot be steered by minimap.
BC1's capture shows Link standing after "Saving..." already facing the door with the camera behind him.

v8 replaces v6 lines 110-114 (the swing, ZL, the push, the A Open MAYBE) with:
  ZL (camera behind Link), then a closed-loop check against BC1's door-ahead view (video 466.5 s, region
  0 80 780 840, 16x9, need 85: BC1's frames score 95-100 facing the door and <55 once the camera has swung);
  if it does not match, 15 deg turns, each followed by ZL, until it does (as kokiri-four-stops stop D);
  then the same 4 s push and the same A Open MAYBE, now counted from the moment the door view was met.
Everything else is v6, byte for byte, including the fallback and the 60 s END.
"""
import importlib.util, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ml", os.path.join(HERE, "../../eglog/make-look.py"))
ml = importlib.util.module_from_spec(spec); spec.loader.exec_module(ml)

REF_T, REGION, CELLS, NEED = 466.5, (0, 80, 780, 840), (16, 9), 85
STEP, TAP_MS, EVERY, TAPS, SETTLED = 15, 120, 1.4, 24, 6.0

def stick(turn):
    r = math.radians(turn)
    return 128 + round(127 * math.sin(r)), 128 - round(127 * math.cos(r))

def ref_grid(video):
    import subprocess, tempfile
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "ref.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{REF_T}", "-i", video, "-frames:v", "1", p], check=True)
        g = ml.grid_of(ml.load(p), *REGION, *CELLS)
    return f"LOOK {' '.join(map(str, REGION))} {CELLS[0]}x{CELLS[1]}:" + "".join(f"{v:02x}" for v in g)

def main(v6, video):
    lines = open(v6).read().split("\n")
    assert lines[109].startswith("5.5 RSTICK 255 128 1500") and lines[113].startswith("9.5 MAYBE 5 LOOK 568 782"), "not v6"
    aopen = lines[113].split(" ", 3)[3]          # "LOOK 568 782 75 48 12x3:..."
    look = ref_grid(video)
    x, y = stick(STEP)
    new = ["# v8 (17 Nov 2026): no camera swing. ZL puts the camera behind Link, then the view is checked against",
           f"# BC1's door-ahead view (need {NEED}); if it is off, {STEP} deg turns, each followed by ZL, until it matches.",
           "5.0 ZL 200"]
    for k in range(TAPS):
        t = SETTLED + 0.7 + k * EVERY
        new += [f"{t:.1f} LSTICK {x} {y} {TAP_MS}", f"{t + 0.6:.1f} ZL 200"]
    new += [f"{SETTLED} MAYBE {SETTLED + 1 + TAPS * EVERY:.0f} {look} {NEED}",
            "# Door ahead: the same push and A Open check as v6, counted from the moment the door view was met.",
            "0.3 LSTICK 128 0 4000",
            f"0.3 MAYBE 5 {aopen}"]
    head = ["# zelda-first-start-watch-wait-30s.v8.txt: v6 with the house door steered by the picture (build_v8.py)."]
    out = head + lines[:108] + [lines[108].replace("then the camera swing, ZL behind the player, run to the door (as the old route) [G].",
                                                     "then (v8) ZL, the door-view check, run to the door.")] + new + lines[114:]
    sys.stdout.write("\n".join(out))

if __name__ == "__main__":
    main(*sys.argv[1:3])
