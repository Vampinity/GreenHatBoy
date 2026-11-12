# Frame-ahead glitches, frame by frame

> **Found:** The glitches when running a frame ahead are per-frame numbers, not textures: a whole layer or the whole frame is drawn with one frame's wrong values (flat light, white discs, blown-out highlights).
>
> **So:** The fix is to protect per-frame data while a frame is in flight; this led to the copy guard (EDEN_UP_AHEAD_GUARD).

9 Nov 2026, 23:40. Batch t85-i (gbb-everyday: runs i2, i3, i5) against t85-a (D5: runs a2, a3, a5) and six control runs.
Side check, videos only: no PS5, no OBS, no build, nothing else changed.

## Answer

**It is per-frame numbers, not textures.** Every glitch I opened is a whole layer, or the whole frame, drawn wrong for
one game frame (about 50 ms) while shapes and surface detail stay sharp and in place:

- the sunlight and the haze in the light beams go flat (dark glitch),
- the dust particles swell into white discs (bright glitch),
- highlights on water, path and wood blow out into white or golden streaks, leaves turn white (bright, or both),
- once per run, at the cut to Link's house: one frame over-bright with the camera in another spot, then 0.7 s too bright.

Nothing looked like a texture or mip glitch: no blocky or blurred surface, no wrong picture on an object, no object
that keeps a wrong look for several frames.

By the rule in the job this points to **the per-frame uniform copy**, not to DownloadLanding.

The clearest single piece of evidence is not a flash at all: the fade to black before the cut. That fade is one number
the game sends each frame. In 6 of 6 control runs it falls steadily. In 3 of the 6 trust-copy runs it arrives out of
order (for example 82, 95, 37, 62, 0, 3, 0): the picture is drawn with the number of a later frame. A texture cannot
do that.

Words: *uniform / constant data* = the small block of numbers the game hands the graphics chip for each frame and each
object (where the camera is, how bright the sun is, how big a particle is, how far the fade is). *Texture* = the
picture painted on a surface; *mip* = its smaller copy for far away.

Limits, in short (more under "Not checked"):

1. Frames show what goes wrong, not why. No log line ties a glitch frame to a cause yet.
2. Particle size may sit in per-frame vertex data, not in a uniform block. If the copy covers only uniform blocks, the
   white discs may stay. (My inference from the pictures, not something I read in the code.)
3. One sign of an old picture: run i2 showed two frames of the previous scene after the black at the cut. One run only.

## Counts

Picture grid 32 x 18 = 576 cells. "Village view" = the wide view 3 to 10 s after the door. Short = 400 ms or less.

| Run | 40+ cells, village view | dark / bright / both | 25-39 cells | Cut to Link's house |
|---|---|---|---|---|
| i2 gbb-everyday | 4 | 2 / 1 / 1 | 7 | wrong frame, 0.7 s too bright, two old frames first |
| i3 gbb-everyday | 6 | 5 / 1 / 0 | 4 | wrong frame, 0.7 s too bright |
| i5 gbb-everyday | 2 | 1 / 1 / 0 | 2 | wrong frame, 0.7 s too bright |
| i1 control | 0 | | 0 | clean fade-in |
| i4 control | 0 | | 0 | clean fade-in |

The card's flash meter said 3 / 4 / 1. It sees dark dips only, so it missed every bright one.

Where they fall: all between +3.2 and +10.1 s (wide village view), then nothing of 25+ cells during the fly-over
(+10.2 to +20.4 s) in any run, then the cut at +20.5 to +21.0 s. After the cut only Saria's greeting moves, as in the
controls.

## Every flash, per run

Time is seconds after the door line. 25 cells and up; the smaller ones are under the tables. "Not opened" = judged by
size and brightness only.

### i2 (run718, door at 79.9 s in the video)

| After door | Cells | Kind | Lasts | What changed |
|---|---|---|---|---|
| +4.70 s | 27 | dark | 117 ms | not opened |
| +5.05 s | 119 | bright | 50 ms | highlights blow out: golden sparkling streaks over fence, planks and stream, leaves white, haze thinner. Picture 1 |
| +5.45 s | 35 | dark | 50 ms | not opened |
| +6.35 s | 35 | dark | 50 ms | not opened |
| +6.50 s | 79 | both (47 dark, 29 bright) | 50 ms | as +5.05 but milder: white streaks on path and water, leaves white, haze thinner |
| +6.72 s | 26 | bright | 100 ms | not opened |
| +6.92 s | 100 | dark | 50 ms | sunlight on trees and ground goes flat and grey |
| +7.80 s | 35 | dark | 117 ms | sun and haze a little dimmer |
| +9.10 s | 176 | dark | 100 ms | sunlight and the haze in the beams drop out, whole picture. Picture 2 |
| +9.27 s | 36 | bright | 100 ms | not opened |
| +10.10 s | 38 | dark | 117 ms | not opened |
| +20.85 s | 84 | bright | 250 ms | the cut, see below |

### i3 (run719, door at 80.0 s)

| After door | Cells | Kind | Lasts | What changed |
|---|---|---|---|---|
| +3.20 s | 40 | dark | 367 ms | weak dimming while the camera still moves; hard to call |
| +3.65 s | about 259 | bright | about 100 ms | dust particles swell into white discs, one big white blob mid-picture, small dark specks. Picture 5. Time and length by hand: the scanner glued it to the camera move |
| +4.20 s | 32 | dark | 267 ms | not opened |
| +4.60 s | 29 | dark | 133 ms | not opened |
| +4.87 s | 44 | dark | 50 ms | haze a little dimmer |
| +5.85 s | 120 | dark (95 dark, 23 bright) | 50 ms | haze thinner, white blown-out streaks on path and water, leaves white. Picture 4 |
| +6.45 s | 61 | dark | 50 ms | sun and haze dimmer |
| +7.07 s | 36 | dark | 117 ms | not opened |
| +8.05 s | 107 | dark | 50 ms | sunlight on trees and ground drops out |
| +9.05 s | 32 | dark | 117 ms | not opened |
| +20.50 s | 75 | bright | 100 ms | the cut, see below |

### i5 (run721, door at 80.8 s)

| After door | Cells | Kind | Lasts | What changed |
|---|---|---|---|---|
| +5.28 s | 25 | dark | 100 ms | not opened |
| +5.53 s | 46 | dark | 117 ms | slight dimming |
| +5.80 s | 162 | bright | 50 ms | dust particles swell into white discs, haze brighter. Picture 3 |
| +5.93 s | 25 | dark | 50 ms | not opened |
| +20.97 s | 63 | bright | 150 ms | the cut, see below |

Smaller ones (10-24 cells, same window): i2 4 dark and 3 bright, i3 3 and 4, i5 5 and 1. Control runs have 0-3 dark and
1-5 bright of that size (moving leaves, the camera), so these cannot be told from the game's own motion. Full lists:
`python3 list.py 10 t85-i-i2-everyday` in the folder below.

How long: 50 ms is one game frame at 18 fps (three video frames). Most last one game frame, a few two. None lasts
longer except the settling after the cut.

## The pictures

Before, during, after. One game frame each.

**1. i2, +5.05 s: highlights blow out.** Golden sparkling streaks on fence, planks and stream; falling leaves white;
a patch of sky shows top left where the haze is missing. Trees, rocks and their detail are unchanged.

![i2 golden streaks](frame-ahead-glitches-2026-11-09/1-i2-golden-streaks.jpg)

**2. i2, +9.10 s: sun drop.** The warm light and the haze in the beams are gone for two game frames; a brown patch
where the haze was.

![i2 sun drop](frame-ahead-glitches-2026-11-09/2-i2-sun-drop.jpg)

**3. i5, +5.80 s: particles swell.** The tiny dust motes become soft white discs.

![i5 particle blobs](frame-ahead-glitches-2026-11-09/3-i5-particle-blobs.jpg)

**4. i3, +5.85 s: haze thinner plus white streaks.** Dark and bright in the same frame.

![i3 haze drop with white streaks](frame-ahead-glitches-2026-11-09/4-i3-haze-drop-white-streaks.jpg)

**5. i3, +3.65 s: particles swell, two game frames.** Big white blob in the middle, discs and dark specks all over.

![i3 particle blobs](frame-ahead-glitches-2026-11-09/5-i3-particle-blobs-2-frames.jpg)

**7 and 8. The same two kinds in D5 (t85-a, run a3).** The white-out at +5.77 s is the particle layer covering the
whole picture (409 of 576 cells); the discs at +4.33 s are the same as in picture 3.

![D5 a3 white-out](frame-ahead-glitches-2026-11-09/7-d5-a3-white-out.jpg)

![D5 a3 particle blobs](frame-ahead-glitches-2026-11-09/8-d5-a3-particle-blobs.jpg)

## The cut to Link's house (new in t85-i)

About 20.5 to 21 s after the door the fly-over fades to black and the game cuts to Link at his house.

Control (i1), one picture per 50 ms: black, then a fade-in from dark to normal.

![cut, control i1](frame-ahead-glitches-2026-11-09/6a-cut-control-i1.jpg)

gbb-everyday (i2): black, two frames of the old fly-over forest, one dim frame, one washed-out over-bright frame, then
the scene too bright and settling.

![cut, gbb-everyday i2](frame-ahead-glitches-2026-11-09/6b-cut-everyday-i2.jpg)

Whole-picture brightness after the black (0-255), from `cut.py`:

| Run | Highest in the first second | Settled | |
|---|---|---|---|
| 6 controls | 46-49 | 46-49 | clean |
| a2, a3, a5 (D5) | 43-47 | 43-47 | clean |
| i2 | 157 | 48 | over-bright |
| i3 | 154 | 48 | over-bright |
| i5 | 89 | 46 | over-bright |

- 3 of 3 gbb-everyday runs, 0 of 6 controls, 0 of 3 D5 runs. So it comes with what t85-i added (submit thread, GPU
  transcode 256, the v2.4 env); which of those, I cannot tell from these runs.
- In the over-bright frame **the camera is also in another spot** (closer to Link) in all three runs; the frame before
  and the frame after have the normal camera, and the control's camera does not move. A late texture cannot move the
  camera. So this frame was drawn with a whole set of numbers that belong to another moment.
- After that one frame the picture is too bright and settles over about 0.65 s (i2 per 50 ms: 84, 74, 70, 65, 63, 61,
  60, 57, 57, 56, 55, 54, then a step to 48; i3 and i5 the same shape). Probably the game's own brightness adaptation
  recovering from that one frame (my reading, not shown). It is the only effect that lasts several frames.
- Only i2 shows the old forest picture for two frames (100 ms) after the black.

## The fade to black: numbers from another frame

Brightness per game frame as the fly-over fades out, just before that cut:

| Run | Fade | |
|---|---|---|
| a1 control | 122, 110, 94, 74, 48, 12, 0 | falls steadily |
| i1 control | 122, 110, 94, 74, 48, 10, 0 | falls steadily |
| 4 more controls | same shape | falls steadily |
| a2 D5 | 122, 112, 99, 83, 63, 39, 0 | falls steadily |
| i2, i3 gbb-everyday | 122, 112, 98, 64, 38, 0 | falls steadily |
| **a3 D5** | 122, **82, 95, 37, 62, 0, 3**, 0 | out of order |
| **a5 D5** | 122, **83, 99**, 83, 63, 40, 0 | out of order |
| **i5 gbb-everyday** | 121, **83, 97**, 83, **0, 6**, 0 | out of order |

In a3 every second frame carries the value that belongs two frames later (82 before 95, 37 before 62, 0 before 3).
That is what a race looks like when the game runs a frame ahead and the emulator reads its numbers after the game has
already written newer ones. 3 of 6 trust-copy runs, 0 of 6 controls.

## Compared with t85-a D5

Same fix without submit thread and GPU transcode, on the v2.3 env. Window +3 to +24 s, one direction, short. Each
cell is dark / bright.

| Run | 10-24 cells | 25-39 | 40-99 | 100+ |
|---|---|---|---|---|
| 6 controls | 0-3 / 1-5 | 0 / 0 (one run 0 / 2) | 0 / 0 | 0 / 0 |
| a2 D5 | 4 / 0 | 3 / 1 | 0 / 1 | 1 / 2 |
| a3 D5 | 3 / 2 | 3 / 1 | 2 / 1 | 1 / 3 |
| a5 D5 | 3 / 3 | 2 / 0 | 3 / 0 | 4 / 6 |
| i2 gbb-everyday | 4 / 3 | 5 / 2 | 0 / 1 | 2 / 1 |
| i3 gbb-everyday | 3 / 4 | 4 / 0 | 3 / 1 | 2 / 0 (+1 by hand) |
| i5 gbb-everyday | 5 / 1 | 2 / 0 | 1 / 1 | 0 / 1 |

- **Same kinds of glitch in both**: sun drop, swollen particles, blown-out highlights, all one game frame, all in the
  wide village view (D5: +3.5 to +9.2 s).
- D5 had 4 / 7 / 13 glitches of 40+ cells (dark 1 / 3 / 7, bright 3 / 4 / 6), the biggest a full white-out of 409 cells.
  gbb-everyday had 4 / 6 / 2 in the village view, mostly dark, biggest 176 (and the 259-cell particle frame). No full
  white-out seen in t85-i.
- Fewer and milder in gbb-everyday is a hint, not a result: three runs each, and D5 alone ranges from 4 to 13.
- New in gbb-everyday: the wrong frame at the cut. Not in D5.
- Speed, from the card: gbb-everyday 18.1 fps against 15.5 for the control.

## What this says for the two fixes

1. **Per-frame uniform copy: fits everything seen.** Whole layers go wrong for one frame, the camera jumps for one
   frame, the fade arrives out of order. All of that is numbers, none of it is a texture.
2. **DownloadLanding: nothing seen that needs it.** No texture or mip glitch in any frame opened. The one thing it could
   still explain is the two old frames in i2 and the 0.7 s settling, if the game's brightness adaptation reads a value
   back from the graphics chip. The camera jump in that same frame makes numbers the simpler reading.
3. **Where the glitches sit fits a race on reused memory** (inference): they come where a lot changes per frame, the
   wide view full of moving particles, and at fades and cuts, and not in the calm fly-over. A late read would then get
   another draw's numbers. If so, the copy has to be taken before the game writes its next frame, for everything in
   that memory, per-frame vertex data included.

A check that would settle it without looking at pictures: T86's VERIFY counter with `EDEN_UP_UBO_AHEAD=0`. If the
frames where the trusted copy differs from live memory line up with the glitch times in the tables above, it is the
race.

Pass mark for T86 on this route, same tools:

```
python3 scan.py <name> <video> <door second> # door second = flicker.not_counted.spans[1][0] + 1 in runs.jsonl
python3 list.py 25 <name> # clean = counted 0, like the six controls
python3 cut.py <name> # clean = ratio 1.0 and no "lit frames inside the black"
```

## One command per batch (10 Nov 00:05)

```
python3 check.py batch-t86-a # any part of the batch folder name
```

It scans the batch's door-walk videos (about 5 s a run) and gives one table: glitches dark / bright / both per run,
the cut to Link's house, the fade to black, and one line per test group that ends in **Clean.** or **Glitches.**
No hand work, videos only. Pass mark for T86's frame-ahead group: "glitches 0 / 0 / 0; wrong frame at the cut in
0 of 3; fade out of order in 0 of 3", like its control.

All nine door batches of T85, 45 runs (tables in `frame-ahead-glitches-2026-11-09/checks/`):

| Batch | Test group | Glitches per run | Wrong frame at the cut | Fade out of order | Result |
|---|---|---|---|---|---|
| t85-a | gbb-d5 (frame-ahead) | 4 / 7 / 13 | 0 of 3 | 2 of 3 | glitches |
| t85-i | gbb-everyday (frame-ahead + submit thread + GPU transcode) | 4 / 6 / 2 | 3 of 3 | 1 of 3 | glitches |
| t85-e | submit thread alone | 0 / 0 / 0 | 0 of 3 | 0 of 3 | clean |
| t85-f | GPU transcode alone | 0 / 0 / 0 | 0 of 3 | 0 of 3 | clean |
| t85-g | listskip | 0 / 0 / 0 | 0 of 3 | 0 of 3 | clean |
| t85-d | wide compute | 0 / 0 / 0 | 0 of 3 | 0 of 3 | clean |
| t85-b | l1056 back-macros | 0 / 0 | 0 of 2 | 0 of 2 | clean |
| t85-b | l1056 verify | 0 | 0 of 1 | 0 of 1 | clean |
| t85-h | l1028 verify | 0 | 0 of 1 | 0 of 1 | clean |
| t85-h | l1028 read-back | 1 / 0 | 0 of 2 | 0 of 2 | one glitch |
| t85-c | cold prep | 0 / 1 | 0 of 2 | 0 of 2 | one glitch |
| t85-c | cold prep verify | 0 | 0 of 1 | 0 of 1 | clean |
| all nine | controls, 18 runs | 0 in every run | 0 of 18 | 0 of 18 | clean |

What this adds:

- **Submit thread alone and GPU transcode alone are clean**, and so are their controls on the v2.4 env. So the
  over-bright frame at the cut to Link's house comes from none of the three on its own; it needs the frame-ahead path
  together with at least one of them. Frame-ahead alone (gbb-d5) has the glitches in the view but not that frame.
- **h3, async read-back (already parked): one real glitch.** At +8.50 s thick grey fog patches swell for one game
  frame, 61 cells, dark and bright together. 1 of 2 runs.

  ![h3 fog patches](frame-ahead-glitches-2026-11-09/9-h3-readback-fog-patches.jpg)
- **c4, cold prep: one real glitch.** At +16.68 s a diagonal shaft of light for one game frame in the fly-over,
  50 cells. 1 of 2 runs, no frame-ahead in that run. Where it comes from is not known.
- **Late runs.** c1 and c5 (cold starts) and b1 play 1.8 to 2.8 s later than the script line says. Counting by
  script time gave control c5 a false alarm at +3.93 s: Link was still in the doorway. The rule now takes its window
  from the picture (the 17.4 s before the fade to black) and the table names every run that is off the usual
  timing. All other counts stayed the same.

## Clips for the eye (10 Nov 00:25)

Vampinity, on the pictures above: "i do not see any visual glitches ... I simply can't tell on screenshots except for
when it is very clear the foliage that becomes BRIGHT white for a frame or two." A still cannot show a change that
lasts one game frame, and without the normal picture next to it nobody can tell game light (sun, Navi, Saria's
fairy) from a wrong frame. So the proof is now a clip, not a picture:

    python3 reel.py batch-t86-a # after check.py batch-t86-a; one clip per flagged test group -> watch/

Top: the normal build. Below: the test run at the same camera position (lined up on the fade to black, then on the
picture itself; the leftover is 0.1 to 0.3 s over 7 s). A number lights up in the strip around each flagged moment
and a yellow bar shows on the exact frames. Each part plays at real speed, then 4x slower. **A real glitch is in
the lower picture only, for a frame or two, and gone again; light that is in both pictures is the game's own.**

| Clip in `watch/` | What it shows |
|---|---|
| `frame-ahead-a3.mp4` | D5 run a3 against control a1, numbers 1-7: white dust discs (1, 2), the full white-out (4), blue sky with golden streaks (6), flat light (3, 5, 7) |
| `everyday-i2.mp4` | gbb-everyday run i2 against control i1, 1-4 in the village view (1 = the golden streaks of picture 1), 5 = the over-bright frame at the cut to Link's house |
| `frame-ahead-a5.mp4` | D5 run a5 against a1, the first 8 of its 13 |
| `batch-t85-h-run714-...mp4` | l1028 read-back h3: grey fog patches for 2 frames |
| `batch-t85-c-run690-...mp4` | cold prep c4: one light shaft across the Kokiri Forest card for 1 frame |

Each clip has a `.txt` beside it that says which number is which event. Looked at by me at the flagged frame,
against the normal picture: the big bright ones are unmistakable and in the lower picture only: white dust discs
and white blobs (a3 1, 2; a5 5, 7), the full white-out (a3 4, a5 3), a blue sky with golden streaks (a3 6, a5 6),
golden streaks (i2 1) and the over-bright cut (i2 5). So are the two singles (h3, c4) called "least certain" above:
both are real one-frame errors. The dark ones (i2 3, 4; a3 3, 5, 7; a5 2, 4, 8), i2 2 and a5 1 are another matter:
the sun haze goes flat for a frame, which the scan measures (46 to 252 cells change and change back within 50 to
200 ms; no such event in the 18 control runs), but in a still beside the normal picture they are faint and I would
not swear to each one by eye. a5's last five are not in its clip. Sent to Vampinity: the first two clips. His verdict
per number was the open point, most of all for the dark ones.

**Vampinity's verdict (00:35), after watching both clips:** "many of the ones you caught are correct, but some in between ones where everything dims a few times only get labeled as a single one. not the worst thing, since it's often all or nothing with the glitches, so getting the exact number right seems to matter less than just catching them in the first place". So the numbered moments are right (many, he did
not name one that is wrong), the dimming is visible to him in motion, and a run of dims in a row is one number where
he sees several. What that changes:

- **Judge a group by how many of its runs glitch**, not by the number of moments. `check.py` now leads each group
  with "glitches in 3 of 3 runs" and has a column "In all": the added length of a run's glitches, which grows when
  wrong frames come in a row. T85: gbb-d5 3 of 3 runs (4 / 7 / 13 moments, 584 / 650 / 1784 ms in all), gbb-everyday
  3 of 3 (4 / 6 / 2, 250 / 1184 / 167 ms), 0 of the 18 control runs. The moments are a lowest count.
- **Nothing is missed by the joining.** In the 45 T85 runs no event of 40+ cells is dropped for being too long; 12
  counted ones last 150 to 617 ms (several wrong frames in a row), two of them in the clips he watched (a3 number 2
  and number 7).
- **The 40-cell line stays.** Smaller events (8 to 39 cells) in the village view are as common in normal runs as in
  frame-ahead runs: 8 to 16 a run in the 18 controls, 11 to 19 in the 6 frame-ahead runs. They are the game's own
  light (door, camera swing, Navi), so counting them would not catch more.

Old tables: `checks-before-perrun/`; old tool: `check.py.bak-live-perrun`.

Seen on the way, not counted by the rule: in a3 the foreground (walkway, bridge moss, Link) is about 20 levels of
255 darker than in the control for the first 2 s of the village view, sunlight on the walkway dim. a2 and a5 do
not show it by eye, and control against control is within 2 levels. One run, so no claim; the rule only counts
changes of up to 1 s against the run's own frames, so a longer difference like this needs the side-by-side.

## How it was measured

- `scan.py`: 60 pictures a second on a 32 x 18 grid. A cell is off when it is 10% or more darker, brighter or another
  colour than both the 0.2 s before and the 0.2 s after. 10+ cells off = a glitch frame. One direction at least twice
  the rest = dark, bright or colour; otherwise "mixed", which is usually motion.
- Counted = 40+ cells, one direction, 400 ms or less, +3 to +24 s after the door. Six control runs give 0. Before +3 s
  the door swing and the cut to the village move in every run (up to 66 cells); after +24 s Saria's greeting does.
- Two glitches were added by hand because the rule missed them: i3 +3.65 s (glued to the camera move) and i2 +6.50 s
  ("mixed", dark and bright in one frame).
- Since 23:55 one rule gives the same counts with nothing added by hand, and `check.py` and `list.py` both use it
  (`rule.py`): 40+ cells, in the view, and either one direction up to 1 s long or "mixed" up to 0.4 s. The door
  swing and the cut to the village are "mixed" and last 1.6 to 2.8 s, so they stay out; the cut to Link's house
  (+20.5 to +21 s) is judged on its own by brightness. A rise in the fade counts when it is more than 4 levels.
- "In the view" is timed from the picture since 10 Nov 00:05: the 17.4 s before the fade to black, up to 0.3 s
  before it. In a normal run that is +3 to +20 s after the door. The script's door second sits up to 1 s off the
  picture, and a cold start can play 2.5 s late. The black starts +19.4 to +21.2 s after the door line in 39 of 40
  warm runs; without frame-ahead the cut to the village sits 16.3 to 17.6 s before it.
- i4's door second (79.7) comes from lining its brightness curve up with i1's; its record has no flash data.

## Not checked

- The cause. The emulator logs of run717 and run718 have no per-frame line about copies or downloads.
- 12 of the 25 village-view glitches of 25+ cells were not opened (marked in the tables); all those of 40+ were.
- Only the door walk, three runs per set. Nothing on the pond stand or in free play.
- Which of submit thread and GPU transcode, on top of frame-ahead, brings the wrong frame at the cut. Each alone is
  clean (t85-e, t85-f); frame-ahead with only one of them was not run.
- Whether the out-of-order fade moves only the fade number or the whole frame's numbers.

## Correction to the earlier note

The 21:26 look at t85-a's D5 runs (`gbb-d5-frames-2026-11-09/`) used tools that see dark dips only. It reported
1 / 3 / 6 sun drops and missed every bright glitch. With `scan.py` the D5 runs have 4 / 7 / 13 glitches of 40+ cells,
about half of them bright. The flash meter in the cards has the same blind spot.

## Files

Folder `frame-ahead-glitches-2026-11-09/`:

- `check.py <batch>`: the whole check for one batch in one command (glitches dark / bright / both per run and per
  group, the cut, the fade); result also in `checks/<batch>.md`. See "One command per batch" above.
- `rule.py`: what counts as a glitch, in one place for `check.py` and `list.py`.
- `reel.py <batch>` (or two scan names and an output name): the side-by-side clips in `watch/`; `labels.swift`
  draws their text (this ffmpeg has no text filter). See "Clips for the eye" above.
- `scan.py`, `list.py`, `cut.py`, `triplet.py`, `strip.py`: read videos only.
- `<run>.scan.json` for all 45 runs of t85-a to t85-i (t85-a twice: `t85-a-*` from the first round, `batch-t85-a-*`
  from `check.py`; same numbers).
- Pictures 1-5, 6a, 6b, 7, 8, 9 as above.
- Videos: `eglantine-logs-2026-11-05/videos/batch-t85-<a to i>/`.
