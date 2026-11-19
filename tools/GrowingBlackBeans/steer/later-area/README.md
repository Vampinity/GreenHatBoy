# The later-area route: a lap of a village and out to the field (18 Nov 2026)

The fifth scope of breadth, "a later area", for the cold and warm floors on the alpha control (T186 + play settings
v4.0, swap-ahead 2048 on 13.x). Fully steered: no replayed input anywhere.

| file | what |
|---|---|
| `later-area-village-lap.v2.txt` | **the route.** The field route's checked menus; the village's minimap check; a STEER lap (51 points, r=6); an exit leg (8 points, r=3) round the short fence in the gatehouse; the field's own map check; 2 minutes standing in the field; then the pause menu back to the title screen, every step gated by a check |
| `later-area-village-lap.v1.txt` | v1, kept for the record: one STEER leg, no menu tail. runLV1 met 53 of 54 points, then stood against the fence |

**Start:** a save just below the village's entrance stairs, newest entry (make your own: walk down the stairs a few
steps and save; the player's arrow must be at y 748 per mille or lower). Always with `EDEN_TEST_DISCARD_SAVE=1`.
**End:** the script ends 2 s after the title screen is back; wait 10 s after the title shows, then quit (`test-quit`). A start quit before the END does not count.
**Scoring windows** (`tools/stk/windows.json`, `later-area-village-lap-v2`): the lap (village check + 8 s to the exit
leg's last point) and the field stand (30-115 s after the field check).

## What we learned making it

- **The harness looks for the player's arrow only in x 742-992, y 743-993 per mille** (`kRegion*` in
  `headless/minimap_steer.h`), sized for the opening areas' minimaps. A minimap that reaches higher up the screen
  can't be steered there: in our first attempt (a route down from a mountain area) the arrow sat at y ~611 at the
  start, and the STEER saw it 0 times in 296 looks. That route had to replay recorded input for its top half, and a
  rolling obstacle threw a replay off the path, so it was retired.
- **Where the arrow is outside the box, the detector can read map icons as the player.** At this village's entrance
  (arrow at y 721-736) it reported a fixed point on a building icon for 20 s. A STEER started there would steer a
  phantom. Start a route inside the box.
- **A short detour needs its own leg with a small radius.** With r=6 the bottom of the user's 5-per-mille detour round
  the gatehouse fence counted as reached from the wrong side, and the straight line to the next point hit the fence.
- **Picture checks cut from PS5 captures work for minimaps and menus** (bright HUD and menu screens: every check here
  scored 91-100 on the console). They failed for a dark interior before (baseline v8).
- **`EDEN_TEST_RECORD=1` records nothing in a game opened by hand while `EDEN_TEST_BOOT` is set** (only a game the app
  booted itself gets a test session). Leave `EDEN_TEST_BOOT` out of a recording env.

## Results so far

Cold, on the alpha control (scored with `tools/stk/stk_score.py`; the gate's numbers):

| start | status | lap fps | field stand fps | lowest free block, census / driver (MiB) |
|---|---|---|---|---|
| runLV1 | v1: STEER timeout at the gatehouse fence (point 53/54), LOST | - | - | 2 / 48 |
| runLV2 | eligible | 8.56 | 12.9 | 17 / 61 |
| runLV3 | eligible | 8.71 | 12.8 | 18 / 26 |
| runLV4 | eligible | 8.87 | 13.1 | 3 / 3 |
| runLV5 | every leg met; quit 2 s before the END: INVALID, not in the floor | 8.84 | 13.0 | 5 / 12 |
| runLV6 | eligible | 8.76 | 12.7 | 9 / 17 |

The cold floor is LV2, LV3, LV4 and LV6: lap 8.73, field stand 12.88 (`tools/stk/floors-cold-2026-11-18.json`).
