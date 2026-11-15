# Frame ahead on against off: the flicker (T185), 14 Nov 2026

> **Found:** With frame ahead on, the ground near Link loses its direct sunlight for one game frame, again and again, and the flags, pennants and cloth in the area after the field go dark for one frame 2 to 2.5 times a second. With frame ahead off, both were gone in our scripted starts: 0 and 0 ground flashes at the field edge against 187 and 191, and 0 and 0 cloth blinks at the gate view against 117 and 138 a minute.
>
> **So:** Frame ahead is off in the candidate play settings v4.0 and in every test since 14 Nov. It costs about 3 fps in the field fights, 1.5 to 2 fps walking across the field, and under 1 fps in the area after the field.

Summary of the checked readings of five scripted batches on T185 (handheld, 1x), two starts a side unless a line
says otherwise. Each count was read twice, the second time as a check against the logs and the recordings.

## What was run

- **Field edge:** frame ahead on (`EDEN_NX2_FRAMES_AHEAD=1` with `EDEN_UP_AHEAD_GUARD=3` and `EDEN_GBB_GUARD_EARLY=2`,
  as in play settings v3.9) against off (those three lines removed). Counted over the first 150 s after the save loads.
- **Gate view in the area after the field** (a still camera): on against off, both with the load window and the
  driver reserve of T185.
- **Two ways to keep running ahead:** read sync (`EDEN_UP_AHEAD_READ_SYNC=1`: the game's reads of data the chip
  wrote wait for that data) and a frame wait capped at 40 ms (`EDEN_UP_OOT_FRAME_CAP=1`, 40 ms: it runs ahead only
  on slow frames).

## What we know

- **Ground flashes at the field edge, first 150 s:** on 187 and 191, off 0 and 0. Three meters and a look by eye
  agree. Per game frame that is about 100 to 116 in 1,000 against 0, so the lower fps with it off does not explain it.
- **What the flash is:** for one game frame the near ground and the player lose their direct sunlight. Most of
  them come in the first 150 s after the save loads at the field edge: 187 and 191 of the 195 and 203 over the
  whole route.
- **Cloth at the gate view:** on 138 and 117 blinks a minute (about one game frame in seven), off 0 and 0 (none
  in about 1,250 game frames each). The cloth is not stuck dark with it off: its brightness is the same in all four.
  Whole-scene dark flashes over the same recordings: on 13 and 19, off 0 and 0.
- **Read sync** took the ground flashes from 166 and 190 to 0 and 0 at the field, and the cloth blink at the gate
  view from about 126 a minute to 0 and 0 (one start with frame ahead on against two with read sync), although it
  still ran ahead on about a third of the frames. So the flashes come from the game reading results that are one
  frame old. Read sync is slower than frame ahead off (about 19 fps against 20 on the field after the first 150 s).
- **The 40 ms cap** cut the ground flashes only to 39 and 42 (on: 210 and 192). The bar set before the test was
  10%, so it was dropped.
- **Cost of off:** field fights 22.3 to 23.0 fps on, 19.1 to 19.3 off; walking the field before the load 19.6 and
  20.6 on, 18.1 and 18.4 off; standing in the area after the field 14.1 and 14.1 on, 13.95 and 13.95 off.
- **Pacing at the field edge:** frames over 100 ms 1,170 and 1,137 on, 91 and 96 off. But 5-second stretches with
  a hitch of 0.45 s or more: 3 and 2 on, 13 and 8 off, at the pause menu opening and closing.

## What this does not show

- Off is three changes at once: frame ahead goes, the copy guard goes, and the `EDEN_UP_SKIP_STALE_UPLOADS=1` line
  starts to act. The test shows frame ahead or something that comes with it, not which part.
- Rarer kinds of flicker (trees or the far view going dark for a moment) were not seen in either arm on these short
  routes. Not seen is not the same as removed; they are judged in longer play.
- Plants blinking at the field edge: no clear change either way.
- Two starts a side: a count, not a verdict.
