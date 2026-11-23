# Phase 4, batch A: amendment 1, two sittings

FROZEN: 2026-11-23, about 00:10 EST, after start 14 and before start 15. Amends BATCH-A-RULES.md (sha1 ffbf5cface7f),
which stays unchanged. Decided by the user; reported with the batch's result in its D2 line.

## Why
Sitting 1 (22 Nov, 20:33-23:45 EST) ended at start 14 of 24. The rules said "one sitting" and "no controls from another
day", so the batch would have been called short. That rule guarded against the console drifting between nights, but every
start already restores the whole cache, the settings and the field save, and the interleaving puts controls on both sides
of every arm start. The batch is finished in a second sitting instead, with the checks below.

## What changes
1. **Two sittings:** starts 1-14 on 22 Nov (done), starts 15-24 on 23 Nov in the table's order, then the two reruns
   (C4, C6) at the end of sitting 2. Nothing else runs on the console in between: no play, no launcher update, no system
   update, no change to the config, the warm restore or the field save.
2. **Start 15 (C8) is checked alone** before start 16, like start 1: warm boot (80,770 known, 3 own, count 4), settings
   as written, and firmware 13.60 in its log.
3. **Read:** the eligible controls of both sittings are pooled (10 or more needed, as before) and the calls are as
   written in the rules.
4. **Sitting check, before the calls:** sitting 1's eligible controls against sitting 2's on each of the six numbers
   (two-sided permutation). If any differs at p < 0.01, the sittings are not alike: every arm is reported **hold**
   ("sittings differ") and no call is made. Otherwise the pooled read stands.
5. **Reported with the result:** the batch ran in two sittings, which arm starts fell in each (sitting 1: X1-3, Y1-2,
   Z1-2; sitting 2: X4, Y3-4, Z3-4), and the sitting check's p values.

Everything else in BATCH-A-RULES.md applies unchanged.
