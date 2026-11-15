# A load window at the load from the field (T184, T185), 14 Nov 2026

> **Found:** Letting the graphics side read packed game memory straight through only while a load is going on (a load window) stops the graphics thread from waiting for memory at the load from the field into the next area. With frame ahead off and a window that closes after 10 quiet seconds (arm CB), 6 of 6 scripted starts got through over two rounds, the graphics thread never waited, and the speed after the load matched the control. The same settings without the window got through 0 of 2, 2 of 2 and 3 of 4 in three rounds.
>
> **So:** CB became the candidate play settings v4.0 for the scripted gate. It is not cleared: in one of the six starts a game thread still waited 4.0 s inside the black screen, and with 384 MiB or more taken away before the load it crawls.

Summary of the checked readings of the load rounds of 14 Nov. All scripted starts, handheld, 1x. Each count was
read twice, the second time as a check against the logs and the recordings.

## Why a window

- At this load the graphics memory pool is empty 10 to 14 s in. The deaths there were a thread that waited 10 s for
  one 2 MiB block while no frame was drawn, and small driver requests (a descriptor pool, a command buffer) refused
  at 0 MiB.
- **T184, v3.9 with the wait reclaim of T181, 12 starts in one round:** 12 of 12 through, but the graphics thread
  waited for memory in every start (longest wait 1.3 to 7.4 s), and none of the reclaim passes it asked for came
  in time.
- **T184, read-through all the time (`EDEN_UP_GPU_READ_THROUGH=2`), 4 starts:** the graphics thread never waited,
  but the area after the field ran 4 to 6 fps slower for the whole stay.
- So T185 allows read-through only inside a window (`EDEN_UP_GPU_READ_THROUGH_LOADS=1`, see
  [`source/T185`](../../../source/T185/)): it opens when the largest free block falls through 256 MiB, and closes
  after 30 quiet seconds unless `_CLOSE_S` says otherwise.

## Frame ahead on, first round (8 starts)

- Control: 2 of 2 through, the graphics thread waited 3 and 5 times (longest 3.5 and 3.4 s).
- Window, and window plus the driver reserve and retry: 4 of 4 through, the graphics thread never waited. The
  window opened 10.8 to 12.8 s into the load, before the control's first graphics-thread wait (16.1 to 17.1 s in).
- The cost: from 45 to 70 s after the load began, 9.0 to 10.9 fps against 14.3 for the control. Inside a window a
  read of a packed piece is unpacked and thrown away, nothing is brought back, and the window stayed open 20 to
  30 s after the picture was back. One start unpacked about 89 GiB to deliver 3.7 GiB.
- Read-through all the time: one start through at 11.4 fps, one crashed on a refused descriptor pool.

## Frame ahead off, the window closing after 10 quiet seconds (CB)

- **Round 1 (6 starts):** control without the window 2 of 2 through, its graphics thread waited 9 and 1 times;
  window with a 30 s close 2 of 2, no waits, but 9.7 and 11.4 fps from 45 to 70 s after the load began; CB 2 of 2,
  no waits, 14.1 and 13.8 fps against 13.9 and 13.8 for the control. CB's first window shut 17 to 25 s after the
  picture was back, never inside the load.
- **Round 2 (8 starts):** CB 4 of 4 through, the graphics thread never waited; control 3 of 4 (one ran out of
  graphics memory 17 s into the load), its graphics thread waited in 3 of 4. Black screen: CB 21.1 to 27.0 s,
  control 22.5 to 32.9 s. From 45 to 70 s after the load began: CB 13.9 to 14.1 fps, control 13.8 to 14.0. CB is
  still about 2 fps under the control at 37 to 50 s.
- Earlier that day the same settings without the window died 2 of 2 at this load.
- The driver reserve served once (256 KiB) and the retry never ran, so there is no evidence yet that either one
  saves a start.

## Not cleared yet

- In one CB start a game thread (not the graphics thread) waited 4.0 s inside the black. The gate's line is 3 s.
  The control shows waits of that kind too (3.3 and 4.8 s).
- A broken first picture after the black: 2.2 s in one CB start, about 0.9 s in another.
- **With less memory free** (memory taken away before the load, as a stand-in for a long session; one start
  each): 256 MiB through, 384 and 448 MiB through but under 1 fps for about a minute, 576 MiB crashed. With 512 MiB:
  in one batch 2 of 2 through but under 1 fps for 129 and 237 s, in another 1 of 2. With `EDEN_UP_DRAIN_TO_POOL=1`
  added, 2 of 2 in both batches, under 1 fps for 9 to 47 s.
- There is no checked docked result with these settings yet.
