# Two-frame guard (0927) on my console, and the title freeze (12 Nov 2026)

> **Found:** two frames ahead with both guard slots ran with no flicker I could see in a later area, at 24.9 fps against 17.2 on W-10. The title-screen freeze happens with two slots too; `EDEN_UP_AHEAD_LOAD_WAIT=1` fixes it.
>
> **But:** the second slot was used once in the run (my limit there is CPU-side), and part of the fps gain is a warm shader cache.

waveydude. Base PS5 13.60, my T120 hybrid. W-10 = hybrid with `EDEN_NX2_FRAMES_AHEAD=0`; W-11 = W-10 + 0927. One run each, about 7 minutes of play in the same later area, different paths. Envs on `waveydude/Eglantine-PS5-` branch `w11-two-frame-guard`, `docs/presets/env-w11-0400486024dec000.txt`.

## Why two slots

GrowingBlackBeans' 0924 runs (12 Nov) showed two frames in flight gives about +2 fps walking and a third off the slowest frames, but flickers. The copy guard (0491-0504) has one slot: a present that finds it still up for the frame before only counts an overlap and leaves its own frame unguarded (9-15% of his presents). 0927 gives each frame in flight its own slot. Details in `patches/waveydude/README.md` and the patch header.

Host tests (`tools/experiments/ahead-guard-slots` on the branch): a threaded stress with the game, back and fence on their own threads, 400 frames, two in flight: two slots 0 wrong reads in 5 runs, one slot about 66% wrong.

## The title-screen freeze

- First W-11 start, **two slots**: hung at the title-screen load. Presents stop, the front polls an acquire about 8,000 times a second, the back is idle. GrowingBlackBeans saw it with one slot (2 of 3 starts).
- `EDEN_UP_AHEAD_LOAD_WAIT=1`: presents during loads and for 700 ms after wait for their own frame. The next start went straight through. GrowingBlackBeans' Play2 had no title freeze with it either.

## A later area, W-10 against W-11

| | W-10 (`FRAMES_AHEAD=0`) | W-11 (two ahead, two slots) |
|---|---|---|
| fps overall / median | 17.2 / 18.5 | **24.9 / 26.7** |
| 5 s windows under 15 fps | 48% | 19% |
| Present wait (median) | 37 ms | 1.2 ms |
| Pipeline builds on the GPU thread | 35.5 s | 5.2 s |

- No flicker or flashes seen by eye. No flash counter on my side.
- Guard counters: 0 frames unguarded, 0 writes waited, the pool peaked at 543 of 2048, never full, second slot used once.

## Left over

Stretches of ~1 s frames in both builds. Followed up in `stalls-driver-cache-2026-11-13.md`.
