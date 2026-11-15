# Where the command reader waits in the area after the field (T186), 15 Nov 2026

> **Found:** In the area after the field, with frame ahead off, the command reader (the emulator thread that reads the game's drawing commands) waits on the graphics chip about 18 ms a frame (18.4 and 18.0 ms in two starts). Nearly all of it is one wait a frame (17.95 and 17.62 ms), always for a grid list: a few numbers the chip writes itself that set the size of a compute job, read by macro 0xe74. On the field walk the reader waits 12.6 and 12.5 ms a frame.
>
> **So:** The next speed work starts with the grid lists. If that wait went away completely, the area after the field could go from about 13.5 to 14 fps to about 18 at most.

Summary of the checked reading of test 2 on T186 (scripted, handheld, 1x, frame ahead off, two starts), with the
measurements of 14 Nov it builds on. Read twice, the second time as a check against the logs.

## Before T186 (14 Nov, T185)

- A frame in the area after the field takes about 71.6 ms. The game's own part is about 16.5 ms of it. The two
  emulator threads that read the commands and record them for the chip mostly take turns instead of working side
  by side. The chip works about 41 ms a frame and stands idle about 31.
- With an older counter (`EDEN_UP_L1094_STATS=1`, two starts) the reader stood still 18.5 and 18.4 ms a frame in
  that area, blocked while reading a list the chip had written, and 12.2 and 12.5 ms on the field walk. Which list
  it was could not be told.
- T186 adds counters by kind of list: `EDEN_UP_LISTWAIT_STATS=1` (patch 1090, see
  [`source/T186`](../../../source/T186/)).

## What T186's counters show

- **The reader's chip waits:** 18.4 and 18.0 ms a frame in the area after the field, nearly all of it one wait a
  frame (17.95 and 17.62 ms) for a grid list (macro 0xe74). In the waits that were sampled it was the frame's last
  chip-written entry before the present.
- **Lists with mesh counts** (macro 0xe62) almost never wait.
- **The recording thread** stands still for that time too (read from its gaps, not measured directly).
- **The thread that waits for fences** waits 29.9 and 28.9 ms a frame; on 14 Nov that waiter could not be named.
- **Field walk:** 12.6 and 12.5 ms a frame.

## Limits

- The counters may cost 1 to 2.5 ms a frame. That cannot be told apart from the normal spread between nights.
- Two starts, frame ahead off only. There is no figure with frame ahead on.
- Upstream, a change in this direction was taken back because of white flashes (zortos293/Lichii
  #1651 reverting #1486). So any change here has to show that it adds no flicker before it counts.
