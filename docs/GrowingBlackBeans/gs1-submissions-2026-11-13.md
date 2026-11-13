# runGS1: the counts run as specified — and which stops are actually repeatable (13 Nov)

GrowingBlackBeans. t134-gbb9 (01.219.925), `EDEN_GBB_GPFIFO=1` plus `EDEN_UP_SUBMIT_STATS=1`, which is
the counts run as the plan agreed with the independent review specified it (`runGP1` left the second
switch out). Same four stops, except stop C: anywhere near the cliff edge, pressing target pans the
camera down, so C moved to a stable spot further back. `checkrun` OK, 25.55 fps.

## Which stops are repeatable

Ring words per frame at each stop, across all three runs of the night:

| stop | runGP1 | runGT1 | runGS1 | spread | |
|---|---|---|---|---|---|
| A outside the house | 160,033 | 160,727 | 160,482 | **0.4%** | repeatable |
| B back of the forest | 92,883 | 92,609 | 91,815 | **1.2%** | repeatable |
| C cliff | 142,047 | 167,100 | 155,595 | 17.6% | panned in GP1/GT1; moved on purpose in GS1 |
| D shop sign | 189,075 | 176,710 | 168,853 | **12.0%** | **not repeatable** |

**A and B are fixed places. D is not**, and it fell in every run (189k, 177k, 169k); the logs cannot
say whether that is how the sign was faced or something in the scene. That does not touch `runGT1`'s
per-draw result, which compared places *within* one run. It does mean D is not a stop to compare
across runs until it is pinned down — which is what a scripted route would do.

## The GPFIFO result repeats

Ring words against GPFIFO words per stop: **0.74, 0.85, 0.75, 0.73** (`runGP1`: 0.74, 0.86, 0.75, 0.73).
Median 0.75 over 38 windows. The demand is the game's own; on two runs now.

## What `EDEN_UP_SUBMIT_STATS` costs: almost nothing

Against clean `runGP1` at the two repeatable stops: **A -2.0% fps, B 0.0%**; back thread +2.1% and
+0.6%. Unlike `EDEN_GBB_BACK_CALLS` (+25%), its numbers are close to clean.

## Submissions and waits on the GPU, per stop

Every window's per-site counts add up to its own total (37 of 37).

| per frame | A | B | C (new spot) | D |
|---|---|---|---|---|
| fence: waits for the GPU | 8.2, **11.4 ms** | 5.6, **7.6 ms** | 9.2, **15.8 ms** | 8.7, **11.8 ms** |
| idle: waits for the GPU | 17.7, 6.5 ms | 21.4, 5.1 ms | 22.4, 5.8 ms | 15.3, 4.6 ms |
| list copy: waits for the GPU | 0.9, 1.9 ms | 0.9, 1.0 ms | 0.9, 3.9 ms | 0.9, 1.3 ms |
| draw submissions | 11.6 | 0.9 | 10.0 | 12.2 |
| waits that gave up after 20 ms | 0 | 0 | 0 | 0 |

**Who does the biggest wait.** The fence waits are not on the back thread. From the source,
`InnerFence::Wait`: *"Only the split's back may submit; other threads (the fencing thread) ask it to and
wait."* So the 7.6-15.8 ms a frame belongs to `GPUFencingThread`, a dedicated thread whose job is to wait
for the GPU and then pop fences. It is not in the back thread's busy time, so **the M2 target from
`runGP1` and `runGT1` — the back thread's cost per draw — stands.**

The fence waits also track the GPU's own busy time: about half of it at every stop (A 11.4 of 23.9 ms,
B 7.6 of 14.2, C 15.8 of 25.9, D 11.8 of 25.1). That is the fencing thread waiting for a GPU that is
working, which is what it is for. **I first read this as the same "stages waiting on each other" that
the area after the field shows, and I withdraw that** until something puts these waits on the critical
path. The "idle" waits (4.6-6.5 ms) I have not traced to a thread.

One thing worth noting from the draws row: 10-12 draw-triggered submissions a frame at the heavy stops
against 0.9 at B. That is GPU submissions, not draws — `runGT1` counted 11,583-14,461 draws a frame — so
it is a submission policy, not a draw count.
