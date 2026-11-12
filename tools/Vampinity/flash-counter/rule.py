#!/usr/bin/env python3
"""rule.py: the numbers that decide what counts. Shared by count_flashes.py and bright_scan.py.

Both scripts lay a 32 x 18 grid over the game's picture and judge every cell against its own recent past and
near future, so a lasting change (a cut, a fade, the camera turning) never counts, only a change that comes back.

  dip / rise   a cell is 10% (DROP) darker, or brighter, than the median of its own 0.2 s before AND the median
               of 0.2 s that starts a little later, while those two medians agree within 12% (RECOVER).
  flash        10 or more cells (MIN_CELLS) off in the same frame; off frames next to each other are one flash.
  full-scene   a flash of 100 cells or more (FULL_SCENE) of the 480 inner cells: the whole sunlit scene.
  glitch       a flash of 40 cells or more (GLITCH_CELLS) that lasts 1 s or less (0.4 s when dark and bright
               cells mix). Under 40 cells the game's own motion (leaves, dust, the camera) gives the same sizes.

The game's own light: game_light.json lists stretches where the game itself changes the light (a door opening
into sunlight, an area card's fly-over, a character's glow). They are given in seconds after a moment you mark
in the video (--mark door=79.9). Inside such a stretch, plus 1 s on both sides, only a flash of 40 cells or
more counts. The game's own light there stayed at 26 cells or under in 100 runs; the real glitch gave 60-190.
Standard library only.
"""
import json, pathlib

GX, GY = 32, 18      # grid over the game's picture
EDGE = 1             # outer ring of cells left out (borders, letterbox, overscan)
PRE_S = 0.20         # median window before the frame
GAP_S = 0.15         # wait before the after-window: the longest dip it waits out
DROP = 0.10          # a cell must differ 10% from both medians
RECOVER = 0.12       # the before and after medians agree within 12%: the change came back
MIN_PRE = 30         # cells darker than this (0-255) are not judged for dips: noise in the dark
MIN_CELLS = 10       # cells off in one frame to call it a flash (falling leaves: 1-7)
MAX_MS = 200         # dark meter: a dip longer than this is a fade, not a flash
DARK_FRAME = 18      # mean brightness under this = black screen or loading
MIN_RUN = 20.0       # seconds of lit picture that count as gameplay (whole-video mode only)
FULL_SCENE = 100     # cells: a full-scene flash
GLITCH_CELLS = 40    # cells: a glitch, and the size that still counts inside the game's own light
GLITCH_MS, MIXED_MS = 1000, 400
GUARD_S = 1.0        # seconds added on both sides of a game-light stretch

HERE = pathlib.Path(__file__).resolve().parent


def is_glitch(flash):
    """flash: dict with 'cells', 'ms' and optionally 'kind' ('dark', 'bright', 'colour', 'mixed')."""
    if flash["cells"] < GLITCH_CELLS:
        return False
    return flash["ms"] <= (MIXED_MS if flash.get("kind") == "mixed" else GLITCH_MS)


def game_light_spans(marks, path=None):
    """marks: {name: video second}. Returns merged [start, end] video seconds of the game's own light."""
    entries = json.loads(pathlib.Path(path or HERE / "game_light.json").read_text())
    spans = []
    for e in entries:
        if e["mark"] in marks:
            at = marks[e["mark"]]
            spans += [[at + a - GUARD_S, at + b + GUARD_S] for a, b in e["stretches"]]
    merged = []
    for a, b in sorted(spans):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return merged


def is_game_light(flash, spans):
    """True when the flash is small and falls in a stretch of the game's own light: not counted."""
    return flash["cells"] < GLITCH_CELLS and any(a <= flash["t"] <= b for a, b in spans)


def parse_marks(items):
    marks = {}
    for item in items or []:
        name, _, value = item.partition("=")
        marks[name.strip()] = float(value)
    return marks
