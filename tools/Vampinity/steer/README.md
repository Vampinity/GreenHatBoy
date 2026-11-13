# steer-route.py: a recorded walk to STEER points

`steer-route.py` reads a stretch of a recording of your own play, finds the player's marker and the
camera wedge on the minimap in each frame, and prints a STEER line for the test harness: the path you
walked, as minimap points the harness can walk again. A path someone really walked is open ground, so
it is a good start for a route. All the scripts in `../routes` got their points this way.

It uses the harness's own detector, `steer::Find` in `headless/minimap_steer.h`, so what it reads is
what the console reads during a STEER. It only reads the video file; it never talks to a console.

## Files

| File | What it is |
|---|---|
| `steer-route.py` | the tool |
| `steer_cli.cpp` | a small program that runs `minimap_steer.h` over raw frames on stdin, one line per frame. `steer-route.py` builds it on first use (as `steer-cli-bin` next to itself) |
| `steer_test.cpp` | our host test of `minimap_steer.h`: drawn minimaps in all directions, an orange map icon that must not count, and a small world where the stick and camera move the player, to see a walk reach its points |

## What you need

- python3, ffmpeg and ffprobe on the PATH, and a C++20 compiler as `c++` (clang or gcc).
- `headless/minimap_steer.h` from the Eglantine-PS5- source, public on the `ocarina-dev-t120` branch of
  [Vampinity/Eglantine-PS5-](https://github.com/Vampinity/Eglantine-PS5-/tree/ocarina-dev-t120).
  It has no dependencies of its own and is unchanged up to T181.
- A recording of the game with the minimap on screen (default HUD). Ours are 1920x1080 captures,
  handheld 1x. The picture may fill the recording or sit unscaled in a corner; the tool finds it.

## How to run it

    python3 steer-route.py VIDEO --from 88.5 --to 108 --step 4 --radius 4 --headless <path to headless/>

`--from` and `--to` are seconds in the video. Instead of `--headless` you can set `STEER_HEADLESS`.
Other options: `--step N` (points at least N per mille apart, default 12), `--radius N` (a point counts
as reached within N per mille, default 6, as in the harness), `--back` (add the way back, a loop),
`--fps` (frames read per second, default 5), `--picture WxH+X+Y` (say where the game picture is).

It prints how many frames it could read, the path length and speed, and a line like

    1 STEER 40 920,839 915,841 911,840 ... 884,876 r=4

The timeout is twice the time the walk took in the recording. Put the line after a WAIT that has the
player standing at the first point (in our scripts, the WAIT for the hearts after the load).

To run the host test:

    c++ -std=c++20 -Wall -Wextra -Werror -I <path to headless/> steer_test.cpp -o steer_test && ./steer_test

## What it was checked on

- This copy, on the owner's 11 Nov recording that the village scripts came from: 88.5-108 s with
  `--step 4 --radius 4` gives the same 13 points as `village-tunnel-mouth.txt`, marker and wedge read
  in 88 of 98 frames (90%). 294-301.2 s gives the five passage points of `village-exit.txt` (plus one
  more, see below).
- The detector, on the owner's play of 9 Nov (village stretches): the marker in 100% of frames with the
  map on screen, marker and wedge in 98-100%. On a night walk: 99% and 97%. On the launcher screen
  (a red logo on black): 0 of 400 frames taken for the player.
- The C++ detector and our first prototype of it agreed on all 2,448 frames we compared (place within
  1.5 pixels, angle within 3 degrees).
- `steer_test.cpp` passes (this copy, against the T181 `minimap_steer.h`).
- The routes made from its points: see the results in `../routes/README.md`.

## Known limits

- **Check the points by eye.** A misread that jumps less than 30 per mille is not dropped. On the
  88.5-133.5 s stretch the tool printed one stray point (867,840) between 880,875 and 878,873; we
  took it out by hand for `village-exit.txt`. We also dropped the last passage point (780,818) by
  hand, to stay short of the area change.
- **Only the village and the field were tried.** The detector's limits were set on the village map.
  In a later area whose map is a boxed floor plan the marker and the wedge are read far less often.
- **A path walked one way may not work the other way.** A ledge you jumped down cannot be walked up.
  `--back` does not know that.
- **Up to 64 points.** If the path needs more, the step is raised by itself. Long walks are better
  cut into several STEER lines.
- **No map, no points.** Menus, loading, talks and indoor rooms without the minimap give nothing.
- Most of our recordings and test starts are at night in the game. The daylight frames we tried read
  well, but there were few of them.
