# Scripted routes

Pad scripts that walk the same path on every start, for measurements that need a fixed place and a
fixed path. The test harness in the PS5 front end plays them. All starts below are on our dev builds,
handheld 1x, from our own saves on one console: the field and house routes on 13 Nov 2026 (T160-T181),
the two village routes on 11-12 Nov (T120-T130).

| File | What it does | Result on 13 Nov |
|---|---|---|
| `field-to-past-field.txt` | Field save, steered along the dirt path to the bridge and through the gate into the load to the area after the field, then 300 s there | 34 of 34 starts reached the load (T162-T181) |
| `field-to-past-field-stand.txt` | The same route with a 33 s stand on the road before the bridge | 10 of 10 reached the load (T175, T177) |
| `house-door-village.txt` | House save, walk to the door and open it, then a short unsteered walk in the village | 16 of 18 starts that reached the house got through the door (same door lines, T144-T177) |

| File | What it does | Result on 11-12 Nov |
|---|---|---|
| `village-tunnel-mouth.txt` | Hill save in the village, steered down the ravine and through the tunnel to its mouth (13 points), then 132 s standing there. Our run1076 | 27 of 27 starts reached all 13 points (19 with this file, 8 with the same lines and a 252 s stand) |
| `village-exit.txt` | Same save, the tunnel path and on across the village to the exit passage (32 points), up to the one standing there (1 point), a talk, into the passage (5 points), a push into the area change, then 35 s. Our run1110 | 38 of 47 starts reached all 38 points. in 6 the app crashed during the load, before the hearts showed (all in one batch, on a test build); 3 stopped at point 2 of the last 5, in the passage |

"Reached the load" means the route did its job. 17 of those 44 field starts then crashed inside the
load. That crash is the bug these runs were testing, not the route.

## What you need

- A build with the harness: `headless/test_harness.h` (WAIT, LOOK, GONE, MAYBE, END, STEER) plus
  `headless/minimap_steer.h`, public on the `ocarina-dev-t120` branch of
  [Vampinity/Eglantine-PS5-](https://github.com/Vampinity/Eglantine-PS5-/tree/ocarina-dev-t120).
  Both files are unchanged up to T181. We ran the field and house scripts on T160-T181 builds and
  the village scripts on T120-T130, never on a T134 build.
- Your own save at the start spot (ours stay private, see below). Make it the newest entry: the
  scripts press Continue, then A on the top entry of the load list, with no cursor moves.
- Settings as we ran them: handheld, resolution 1x, 1080p output, the minimap on screen (default
  HUD). Docked and other resolutions were not tried.
- The script file in `/data/eglantineps5/` on the console, and in `env.txt`:

      EDEN_TEST_SCRIPT=field-to-past-field.txt

- Keep your save safe. The game saves by itself during these routes. Our test builds have a switch,
  `EDEN_TEST_DISCARD_SAVE=1`, that makes the game use a throwaway copy of the save. It is patch 0547,
  in T119 and later, so it is in the public T120 source and in T134 builds too (`savedata_factory.cpp`).
  An earlier version of this README said it was not; GrowingBlackBeans found it in his t134-gbb9.
  Even with it, back up your save once and put it back before every start, or the next start may
  begin somewhere else.
- Read progress in `stderr.log`: `EDEN_TEST wait_met`, `steer_point`, `steer_met`, `wait_timeout`,
  `steer_timeout`, `script_end`, `script_done`. `line=` is the line in the script file.

The harness does not stop the game after `END`. Stop it yourself, or use the `test-quit` file that
the header of `test_harness.h` describes.

## Start positions

**Field.** An autosave on the dirt path in the field, about a minute's walk south-south-east of the
bridge and gate that lead to the area after the field. After the load the player must stand at
minimap point 936,841 (per mille of the picture, x then y). Check it on your first start: the first
`steer_point ... point=1/11` should come within a second of the STEER starting. Ours was a plain
autosave the game made while we walked that path. We have not tried anyone else's save.

**House.** A save in the house where the game starts. On Continue the player stands in the room
facing the camera, with the door behind the camera to the left.

**Village hill.** A save on the hill in the village, above the ravine that leads down to the tunnel.
After the load the player must stand at minimap point 920,839. Both village scripts start there. Check
the first `steer_point ... point=1/13` (or `1/32`) on your first start, as for the field.

## field-to-past-field.txt

Title, Continue, load, then up to 240 s waiting for the field minimap (a LOOK on its left part).
Three STEER lines walk the player by the minimap arrowhead and camera wedge: 11 points up the dirt
path, three round a stone ruin, then one aimed at the gate passage that stops 8 per mille short of
it. After that comes ZL (camera behind the player) and a 12 s straight push over the bridge and
through the gate. If the minimap is still there after that, three short sideways pushes free him
from a gate post. `WAIT GONE` on the minimap marks the start of the load. Then 120 s with no input,
a 20 s stand, 6 s forward, END.

- Walk time (all 44 starts): the 11-point STEER was met 45-72 s after the minimap showed, the last
  STEER 57-86 s. So the moment the load starts varies by about 30 s from start to start. Use the
  log lines, not script time, to line up measurements.
- Known trouble spots: small flying plant enemies near 922,803 can knock the player off line (STEER
  walks him back, 150 s timeout). A stone ruin just before the bridge (corner ~900.6,772.9) stopped
  two of three starts of the previous version. This version goes round it.
- The last ~8 per mille (the bridge and the gate) are open loop: a straight push, not steered. Gate
  posts and the stone ledges beside the bridge caught earlier versions there.
- Earlier versions, not shared: v1 missed the gate 3 of 3 (into the moat beside the bridge), v2 got
  stuck on a gate post 1 of 1, v3 reached the load 1 of 3. This one (v4) reached it in all 34 starts,
  all from the same save.
- It does not fight. The part after the load is a short unchecked walk. Nothing there is steered.

## field-to-past-field-stand.txt

Every command line is the same as above, plus one 33 s stand after the last STEER (a MAYBE that can
never match, so it always runs to its timeout). It gives a fixed standing spot on the road before
the bridge. It does not fix the arrival time: the walk's spread stays, because the harness has no
"wait until script second N" command.

## house-door-village.txt

Title, Continue, load (up to 240 s for the house), stick down-left until "(A) Open" shows (LOOK),
a short push forward if he stopped short, then A three times. After the door it waits for the hearts
and walks 6 s forward and 4 s forward-right in the village, open loop.

- Door: 16 of 18 starts that reached the house got through it (this file and earlier copies with
  the same lines). The two misses were on an older build (T144) with a cold shader store: slow frames
  left him one step short of the door, and the fallback push walked him back into the room.
- Whole script: 8 of 10 starts ran to END. The other two never saw the title within the 180 s title
  wait (a boot problem, not the walk). A copy with a 600 s title wait for a cold store ran 6 of 9 to
  END.
- The village part is not a route. Where he ends up is not checked.

## village-tunnel-mouth.txt

Title, Continue, load, up to 60 s for the hearts, then one STEER line of 13 points down the ravine and
through the tunnel (45 s timeout), and 132 s standing at the tunnel mouth with the village and the
water in view.

- The points are about 4 per mille apart and follow the owner's own walk. A first version with 5
  points 12 per mille apart cut a corner and ran into a tree. A blind replay of the same walk
  (recorded stick input) missed the spot in 2 of 3 starts.
- In run1076 the STEER was met 27 s after it started. Where the player stands after the last point
  is not checked by the script. Look at a frame of your first start.
- The `WAIT 30 GONE` on the title grid after the STEER is met at once. It only gave our runner a
  fixed line to count the stand from.

## village-exit.txt

The same start and the same first 13 points, then 19 more west across the village to just east of
the exit passage (one STEER line of 32 points, 120 s timeout). A one-point STEER walks up to the one
standing in the passage. A short push, CIRCLE every 1.5 s until the hearts go (the talk), CROSS every
0.6 s until they are back. A five-point STEER into the passage, then the stick held forward until the
screen goes black (`WAIT GONE` on the hearts), and 35 s standing while the area after the exit loads.

- The buttons are named as the PS5 pad names them (CIRCLE, CROSS), as in the owner's recording.
- The last metres of the passage are open loop: the last point is about 3 s of walking short of where
  the area change starts, so no look is asked for during the load.
- The 3 starts that stopped at point 2 of the last 5 timed out in the passage after the talk (two
  control starts and one with a switch on). We have not looked into why.
- It talks to the one in the passage on the way. If your save is at another point in the story the
  talk may be longer or shorter; the CROSS presses stop when the hearts are back, up to 55 s.

## Making your own LOOKs and STEER points

A LOOK line is a brightness grid of a screen region. A tool that cuts one from a screenshot has to
use the harness's own arithmetic (`GridOf` in `test_harness.h`). GrowingBlackBeans'
[`make-look.py`](../../GrowingBlackBeans/eglog/make-look.py) does that. STEER points are minimap
positions in per mille of the picture. We take them from a recording of our own walk with
[`steer-route.py`](../steer/README.md) in `tools/Vampinity/steer`, which runs the harness's own
detector (`minimap_steer.h`) over the video.
