# steer: STEER points from a capture video (13 Nov 2026)

| file | what it does | tested |
|---|---|---|
| `minimap_steer.h` | the test harness's minimap finder, copied **unchanged** from `headless/` (Vampinity, GPL-3.0) | it's the console's code |
| `steer_cli.cpp` | runs `steer::Find` over raw BGRA frames from ffmpeg; one line a frame | 4/4 synthetic frames: position within 1 per mille, bearing within 0.3 deg (`make_test_frames.py`) |
| `steer-route.py` | `track` (video → per-frame fixes), `stops`, `route` (script fragment: a STEER leg per stop, approach point, ZL, fingerprints, a plain hold), `places` (one line a second, for joining onto a log) | `stops` and `route` on a synthetic track; **not yet on a real video** |

    clang++ -std=c++17 -O2 -o steer_cli steer_cli.cpp
    python3 steer-route.py track walk.mp4            # writes walk.track.txt
    python3 steer-route.py stops walk.track.txt
    python3 steer-route.py route walk.track.txt --names A,B,C,D > legs.txt

Why the real header and not a Python port: the points must be what STEER will see on the console, so
the finder runs the same code. The harness names a `steer-route.py` that "prints them from a recording"
but it isn't public; this one is written to that description.

Unverified until the first real video: whether PS5 capture video (compressed, possibly a different
picture size) gives the 99-100% marker rate the harness notes measured on Vampinity's recordings.
`track` prints the rate.
