# GrowingBlackBeans core patches on T134 (t134-gbb2)

Apply after T134's own patches (`source/T134`, 0550-0591), in number order, to the Eglantine core at 0ca2032. Every switch is off unless its line is in env.txt. The front-end side of 0922/0923 is `../headless-0922-0923.diff` (unchanged from T120).

How they were moved from T120: a 3-way merge, with T120's patch set as the common base and T134's 0550-0591 as the other side. That means git placed every hunk by context; nothing was applied with fuzz.

| Patch | Change from the T120 version |
|---|---|
| 0901-0904, 0907, 0909, 0910, 0912, 0913, 0921, 0922, 0923, 0928 | re-based only |
| 0917 | include line beside T134's |
| 0918, 0920 | the audit hooks in `GPU::OnCPURead` sit beside T134's 0568 early-read trace; 0920's preemptive count is at the top of the preemptive branch, before 0567's read-sync return |
| **0927** (waveydude, `EDEN_UP_AHEAD_TWO` + `EDEN_UP_AHEAD_GUARD_SLOTS=2`) | hand merge with T134's 0569 (`EDEN_UP_AHEAD_GUARD_HELD_AGE`). With one slot, `GatherForApply` is T134's code unchanged. With two, held writes use 0927's per-frame release, with their frames in `ahead_held_frames` beside `ahead_held_writes`. `GuardNow()` reads the frame of the slot with the newest serial (0927 replaced `armed_frame` with per-slot state). |
| 0916 (Lichii #1199) | **dropped**: T134's 0578 `EDEN_UP_STALE_BACKING_FIX` is the same port plus the release half of #1236 |

Tested on a console (12 Nov): t134-gbb1 (without 0927) passed a gate against t120-gbb9 (3 against 3, walking 23.9 against 23.5); t134-gbb2 ran 13 runs of one and two frames ahead, with and without read sync. Results: `docs/GrowingBlackBeans/read-back-race-2026-11-12.md`.
