# flash-counter

Counts short flashes in a capture-card recording. Needs only Python 3.8+ and ffmpeg.

- `count_flashes.py`: dark dips (the sun dropping out for a frame).
- `bright_scan.py`: dark, bright and colour flashes.
- `rule.py`: every threshold. `game_light.json`: light the game makes itself.

## How it measures

The picture becomes a 32 x 18 grid of cell averages; the outer ring is skipped (480 cells). A cell is off when it is 10% darker (or brighter) than the median of its own last 0.2 s AND of 0.2 s starting 0.15 s later, while those two medians agree within 12%. So cuts, fades and camera turns never count. Cells darker than 30/255 are skipped.

`bright_scan.py` differs a little: a bright cell must sit 10% of the medians' average (at least 40/255) above both, a colour cell is the same brightness with 15% other colour, the after-window may also start 0.4 s later, and it skips a 6 x 2 corner top-left where a performance overlay sits (468 cells).

10+ off cells in a frame is a flash; neighbouring flash frames are one flash. 100+ cells is full-scene. A glitch is 40+ cells lasting up to 1 s (0.4 s when no kind dominates). Leaves and dust give under 40.

Game's own light (a door opening into daylight, leaves in a fly-over, a glow): mark the moment, `--mark door=79.9`, and flashes under 40 cells in those stretches are not counted. There it stayed at 26 cells or under in 100 runs; the glitch gave 60-190.

## Run

    python3 count_flashes.py video.mov --from 0 --to 90
    python3 bright_scan.py video.mov --from 0 --to 90 --all

Output: counts per minute, then per flash: seconds, frame number, cells, drop % or kind, length.

## Limits

- Needs a 60 fps capture of gameplay. The opening movie's firelight flickers and counts.
- Heavy compression smears one-frame flashes.
- `count_flashes.py` sees dark dips better than bright ones.

## Same count inside the emulator

Per cell, take full-range luma (0-1) of the presented frame. Dark = under 0.9 x each median; the medians within 12% of each other; cells whose before-median is under 0.12 skipped. Windows in seconds: 0.2 s before, 0.2 s after starting 0.15 s on. Flash = 10+ of 480 cells (2%), full-scene 100+ (21%), glitch 40+ (8%). Flash frames up to two frames apart are one flash; the dark count drops flashes over 200 ms. Average several pixels per cell.
