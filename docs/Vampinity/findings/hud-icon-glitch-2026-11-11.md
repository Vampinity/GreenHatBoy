# HUD icon glitch, 11 Nov 2026 (fast mode, no copy guard, usage tracker on)

> **Found:** In fast mode, HUD images are sometimes drawn at the wrong place and size for one to three frames (hearts in the minimap's spot, stretched panels), in bursts at a few spots.
>
> **So:** It shows in fast mode without the copy guard; the guard at EDEN_UP_AHEAD_GUARD=3 later removed it on the walking loop.

**What it is.** For one game frame, sometimes two or three, HUD images are drawn at the wrong place and size. Examples: the hearts appear where the minimap should be, a big heart outline sits bottom right, the item or ZR icon floats next to Link's head, a panel is stretched into a huge cream or gold triangle across the picture. The draw that should be there often goes missing at the same time: the minimap or the hearts are gone for that frame. One game frame is about 50 ms (3 video frames at 60 fps). Stills: `hud-icon-glitch-2026-11-11/` (left = frame before, right = glitch frame).

## Counts (every number below is from frames I looked at)

| Session | Build / settings | HUD-visible play | Moments | Per minute | Where |
|---|---|---|---|---|---|
| 05:37 | T120/T121, fast, no guard, tracker | 1.6 min | 14 | 8.6 | all 14 at 98–147 s, first try, running through the village. None in 37 s of the second try (forest exit) |
| 05:47 | same | 2.3 min | 10 | 4.4 | 8 of 10 at 220–240 s, Link standing by the sign on the path, fog |
| 05:54 | T121, same | 1.2 min | 44 | ~36 | 43 of them at 366–382 s, standing still by the tree in a later area while the "New Event" banner and "Saving…" show, shortly before the low-memory end. Leave that stretch out and it is 1 in about 1 min |
| 06:07 | same | 0.7 min | 1 | 1.4 | forest exit (no minimap there) |
| 07 Nov 05:01 | settings unclear, see below | 7.8 min | 0 | 0 | Kokiri village, same 3-heart save |
| 07 Nov 08:06 | settings unclear | 5.2 min | 0 | 0 | village, later area |
| 07 Nov 08:48 | settings unclear | 4.7 min | 0 | 0 | village, a later area |

"HUD-visible play" counts the time the hearts show (menus, cutscenes, loading, home screen and dialogue with the HUD hidden are left out). It is a lower bound for play time.

**Length.** Most moments last 1 game frame (3 video frames). A few last 2–3 game frames: 05:47 at 222.88 and 224.38, 05:37 at 110.15, 111.45, 118.67 and 143.55, and several in the 05:54 burst.

**Which element.** 05:47: hearts drawn at the minimap's place (222.9, 224.4, 227.9, 239.3, 240.0), minimap missing (220.7, 227.5, 237.9), hearts and "Jump" prompt missing (149.1), extra copy of the minimap circle in the corner (201.2). 05:37: hearts (big outline or big red heart), item / ZR icons by Link's head, d-pad icon, white squares, one stretched gold panel. 05:54 burst: huge stretched cream/gold/red/magenta triangles, d-pad and heart icons, the "Open Threads of Time" text.

**Where it clusters.** No clear tie to rolls or camera turns: the 05:37 hits came while running, the 05:47 and 05:54 bursts while standing almost still. During dialogue the HUD is hidden, so talking cannot show it. Two things stand out: it comes in bursts at one spot (05:47 by the sign, 05:54 by the tree during "Saving…"), and the worst burst came just before the 05:54 run ran out of memory. Forest exit and later area stretches had very few (1 in 06:07, 0 in the 05:37 second try).

## Tracker against no tracker

I could not make a fair comparison. No hand-2026110* folder says it ran in fast mode: none of their logs have `EDEN_NX2_FRAMES_AHEAD` (the 07 Nov ones list their env lines without it; 09 Nov 06:17 has `EDEN_UP_OOT_FRAME_WAIT=1`, the full wait, so it is not fast mode). No hand-20261110* folders exist. The three 07 Nov sessions show 0 HUD moments in 17.7 min, same village, same kind of play. This morning shows 69 in 5.8 min (26 in 5.5 min without the 05:54 burst). So the glitch is new compared with 07 Nov, but because those runs were probably not one frame ahead, this does not show that the tracker causes it. To test the tracker you need a fast-mode, no-guard run with the tracker off, at the 05:47 sign spot or the 05:37 village route.

## Five clips for Vampinity (05:47 video, seconds)

1. 222.88 (lasts to 222.93): hearts drawn small where the minimap was, minimap gone
2. 224.38 (to 224.48): same, two game frames; top-left hearts drop to one
3. 227.88: hearts icon at the minimap spot, top-left hearts gone
4. 239.33: top-left heart turns white, minimap gone
5. 240.03: hearts at the minimap spot again

A single clip from 220 to 241 s covers 8 of the 10 moments in this session. For a more striking clip, use 05:37 at 105–113 s (big hearts and icons near Link) or 05:54 at 366–382 s (the burst).

## Detector (scripts in working folder `hud-glitch/scripts/`)

`scan3.py` keeps each new game frame (the 60 fps video repeats each one about 3 times) and saves the hearts and minimap corners plus small thumbnails. `detect.py` flags a frame when the heart-orange or minimap-gold pixel count in its corner drops below 55–60% of the frames around it, rises well above them, or the corner image changes sharply, while the frames before and after agree with each other. Frames 1–2 apart are merged into one moment. I then looked at every hit (`review.py` puts the frame before and the hit side by side).

- **Hits checked by eye:** 05:47 14 hits, 10 right, 3 wrong (bright scene, scarecrow straw, a lantern over the hearts), 1 unclear (249.32, a big dark-red shape top left that may be scene geometry; not counted). 05:37 16 hits, 14 right, 2 wrong. 06:07 3 hits, 1 right, 1 unclear (207.28), 1 white flash. 05:54: the first 4 hits were 1 right, 3 wrong (cutscene light flashes); I counted the 366–382 s burst frame by frame instead (43 moments by eye against about 30 detector groups). Old sessions: 74 hits, 0 right (lighting flashes, sparkle bursts, black frames, the minimap cone turning).
- **What it misses:** it watches only the hearts and minimap corners. It misses icons drawn elsewhere when both corners stay normal, the top-right item box, the d-pad and button prompts, and any area with no minimap (forest exit, later area: hearts only). It merges moments that are 1–2 frames apart. Recall checks by eye on thumbnails of every frame: 05:47 222–245 s, all minimap-gone frames were found. 05:37 second try (2 of 8 sheets), 06:07 forest exit (1 of 9 sheets) and 07 Nov 08:06 (2 sheets): no missed moments.
- **What it wrongly flags:** white or golden light flashes, cutscenes with the HUD hidden, gold scene objects (scarecrow, lanterns) in the minimap corner, black frames. Without an eye check its raw counts are useless in sessions with flashes.
