# Title logo stutter: independent check (12 Nov 2026)

> **Found:** The title screen stutter is the background movie decoder dropping up to a third of its frames after the cut to the dark shot; the emulator's own fps meter cannot see it because the game redraws the same picture.
>
> **So:** Test more decoder threads and a frame delay for the movie (done in title-movie-test-2026-11-12.md).

Second check: a re-measure of the first report. I re-measured two runs myself: run1255 (cold prepared store, new game) and run1256 (warm, new game), both in `eglantine-logs-2026-11-05/auto-20261112-033108-batch-door-wall-t134/`. I also read the movie lines of run1257, run1243 (Continue) and run1233 (cold first start). READ means measured from a video or a log. INFERRED means my reasoning.

## Verdict

The first read has the right moment: the title screen's background movie. The stutter is real and shows in every run. Two of the first read's main points are wrong, though: how long it lasts, and the likely cause.

## What Vampinity sees (moment 1, title screen)

- READ, run1256 video: the movie is smooth in the bright rider shot. Over the 4 s before the cut, 3-7 of 60 frames per second are unchanged. From the cut to the dark grass shot (video 53.5 s), 27-45 of 60 frames per second are unchanged. The worst still lasts 31 frames (0.52 s), right after the cut. The first read reported at most 12 frames for this run.
- READ, run1255 video: for this I measured a strip on the right edge, which the logo and the menu never cover, so their fades can't hide or fake motion. Before the cut, 4-8/60 frames are unchanged. From the cut until the title movie ends, 18-38/60 are unchanged, and the longest stills are 12, 19 and 17 frames. This goes on for **at least 11 s**: through the grass shot, the logo fade-in and the menu.
- READ, logs: between movie time ~10.5 s and ~26 s the decoder threw away a third of the frames as late: run1255 309 (frame 600 to 1200), run1257 275. In run1256 the movie ran 27.5 s but only 1072 frames were handed out, where 60 a second would give ~1650.
- **Correction 1:** this is not a 3-4 s window that ends when the logo is in. The movie runs at about 35-45 pictures a second from the cut until it stops. It just shows most on the dark grass shot, because nothing else on screen moves there.
- **Correction 2:** the first read said "the title loop movie that follows is smooth". In these runs the movie that follows is the New Game opening, which is a different movie. In Continue runs (run1243) no second movie plays. Nothing tonight shows the title movie playing smoothly a second time.
- READ: the emulator's own present meter shows 60 fps here (run1256 52-57 s: 300 frames, worst 19.7 ms). The game redraws the same movie picture, so the meter can't see this stutter. This part of the first report is correct and it matters.
- READ: the single ~0.1 s frame when the logo appears is also there (run1256: 101.1 ms in the 57-62 s window). It is a separate, small hitch.

## Moment 2 (end of the opening)

- READ: run1256 has a worst present of 1584.9 ms right after the opening movie ends (log 223.5 s), then **another 801.5 ms** in the next 5 s window. run1255: 1445.3 ms, and 569.4 ms in the window before. **Correction 3:** it is a big freeze plus a second 0.6-0.8 s one, not one freeze per run. There is no movie on screen there, so it isn't what Vampinity means.

## What the emulator is doing (moment 1)

- READ: shader preparation finished long before the movie starts (run1255: done at 24.9 s, movie at 54.1 s; run1256: 75 left, done at 11.9 s). No pipeline builds happen in the window. Cold and warm runs look the same. The first read is right on this.
- READ: run1256 loaded 75 new images between 52.9 s and 62.9 s (the logo and the menu). After that, texture loading is quiet, **yet the dropping goes on** (run1255 until its movie stops at 82.4 s).
- READ, from the source (`nx2_gsv.h` 3886-3957): one thread decodes a frame, waits for the game to hand back one of its only **two** decoder images, and copies the frame in. It keeps at most 2 frames decoded ahead (`MaxDecodedAhead = 2`). Pacing (`EDEN_UP_MOVIE_PACE`) throws away any frame whose time has already passed. dav1d runs with 4 threads in every run.
- READ: the input queue fills up and refuses packets (102-105 refusals per title movie, "input queue full (24 packets)" at the start). So at least at times the feed is ahead of the decoder. The logs don't say when, though.
- **Correction 4 (INFERRED, about 60%):** the dropping starts exactly at a cut in the picture and keeps going after the logo files have loaded. That points to the decoder being too slow on the detailed grass footage: AV1 on 4 threads, a single serial decode-and-copy thread, and only 2 images to rotate. A busy file thread (the first read's top pick, 55%) would not switch on at a cut in the picture, and it would ease off once the logo and menu files were in. On 8 Nov the movie was too *slow* because of the feed. That was fixed (it is in sync now). What's left is a different limit.

## Why it was never fixed

READ, the project log: 8 Nov fixed the movie being 23 s **behind** its sound, and wrote down that "the title movie at boot stays choppy with pacing" without following it up. On 9 Nov the "logo stutter" was measured as the single ~0.1 s frame, blamed on the game, and parked. Every meter since then has counted presents, which stay at 60 fps, so none of them could see dropped movie frames. The first read is right on this.

## Quick test (corrected)

- The first read's arm C (`EDEN_UP_MOVIE_PACE=0`) does not tell feed from decoder. Both causes make frames late, and C only turns late frames into drift. It is still worth one run to see what Vampinity would get (smooth but up to ~4 s behind the music), but it is not a diagnosis.
- Arms, three title starts with **no button presses**, so the title movie runs to its own end (needed for the frame 1200 log line):
  - A: Vampinity's env (control).
  - B: + `EDEN_NX2_AV1_THREADS=8`.
  - D: + `EDEN_NX2_AV1_THREADS=8 EDEN_NX2_AV1_FRAME_DELAY=4`.
  - Optional: C for the drift trade-off.
- Score from the cut to the grass until the movie stops, not just 6 s. Use the logo-free right-edge strip (frames unchanged per second, longest still), plus the "late dropped" count at frame 600 and frame 1200.
- If B or D cuts the drops to the opening movie's level (1-6 per 10 s), the cause is the decoder being short of CPU, and the setting goes into the env. If not, add the ~20-line per-frame timing log (decode ms, wait for a free image, copy ms) and then do the code change: more decoder images or frames banked ahead, or the copy moved off the decode thread. That log is the real tie-breaker; the settings test alone is not.

## In plain words (written for the project owner) (short)

1. The stutter is real. It's the title movie dropping about a third of its frames from the grass shot until the movie ends (10+ s), not just around the logo.
2. The game still draws 60 times a second, so our meters always said "fine". That's why it kept getting missed.
3. It isn't the shader cache or a cold start. It looks like the movie decoder can't keep up with the detailed grass footage.
4. Next: three title starts (normal, more decoder threads, more threads + more frames ahead), about 15 min. If that doesn't fix it, it needs a small code change.
