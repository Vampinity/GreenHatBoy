# Batch CR, the read (27 Nov 2026, desk)

Rules BATCH-CR-RULES.md (sha1 9088f44c6340, frozen 27 Nov 04:50 UTC) with L7 amendment 2's points 1, 4, 5, 6 (docs/GrowingBlackBeans/batch-l7-rules/, sha1 642c95d1b7d7, frozen 27 Nov 15:20 UTC, before this read). One runner run, 27 Nov
07:01-09:23; the 12 starts are in runs/GrowingBlackBeans/2026-11-27-runM1CR-*.
12 of 12 completed, restored, warm; 0 FAST; no crash, no freeze. 8 eligible controls (C1, C7, C8 by point 6).

## The call: not repeated, so C's w becomes a hold
- **The free block at the black** (the number this batch is for): arm 1234-1337 MiB (1313, 1234, 1268, 1337),
  controls 1021-1290 (1245, 1290, 1141, 1252, 1245, 1151, 1071, 1021), **p 0.0545**. The rule asks p < 0.01. Without
  the three controls point 6 let in, p is 0.119: the same call.
- The other five: none under 0.01. Seconds under 16 MiB p 0.024 (arm 16-28 against 24-60), refusals 1.0, worst 0.37,
  load 0.40, field walk 0.96. Failed image shapes 0-2 against 0-10.
- So by "The calls": **not repeated**. Batch C's w (table reserve out) reads "moved once, not repeated", a hold: it can
  be asked again with more starts. It isn't called quiet.

## Reported, not tested
- **Controls at the black, three batches:** B 1088-1296 (median 1244), C 1056-1270 (median 1118), CR 1021-1290
  (median 1198). C's controls sat lowest. This batch's are between, and their spread is as wide as both together.
- **Census at the black** (the last `EDEN_MEM_CENSUS_POOL` before line 92), per start: two groups show up in arms and
  controls alike (out ~10.6k / tables 172 / heap live ~795, against out ~9.2k / tables 158 / live ~690: C2, W2, W3, C6).
  They don't follow the arm. Reserve 256 everywhere but C8 (182). Idle arenas 22-100.
- Table waits and table refusals: 0 in all 12.
- The three cut closes: C1 a guest abort in a socket poll, C7 the stuck present fence, C8 a thread dump. All in the
  shutdown, after the window (batch-cr-rules/CLOSE-CUTS.md).

## What it means for the map
The arm sits a little higher, as C saw, but no more than this batch's own controls spread. The likelier reading is
that C's move came largely from C's low controls; it isn't ruled out. Nothing goes to Vampinity's source reading on
this. Phase 4 explains the control; nothing is adopted or removed.
