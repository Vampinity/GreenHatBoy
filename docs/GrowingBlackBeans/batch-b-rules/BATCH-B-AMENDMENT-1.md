# Phase 4, batch B: amendment 1, a restart under the runner

FROZEN: 2026-11-25, 12:12 UTC, after try 1's start 4 and before the restart's start 1. Amends
BATCH-B-RULES.md (sha1 9e13ca644841), which stays unchanged. Decided by the user; reported with the batch's result in
its D2 line.

## Why
Try 1 (25 Nov, by hand) was stopped after start 4 of 24 (C1, X1, C2, Y1, all four counted) so that batch B can run
automated. Finishing it under the runner would mix two ways of running in one batch, and the sitting check would have
only 2 controls on the hand-run side, too few to see a difference. So the batch starts again from start 1, run one way
throughout.

## What changes
1. **Try 1 is set aside.** Its four starts are not read, not pooled and not used in the sitting check. They are kept,
   and they are packed and posted under their own ids (`runM1B-01-C1-try1` .. `runM1B-04-Y1-try1`), as the rules ask
   for starts already back.
2. **The restart runs all 24 starts** in the rules' order, with the same envs (unchanged since 24 Nov) and the same
   route, on the runner. The runner does each start's steps as written: the whole cache restored, the logs folder set
   aside, the game booting itself, the quit 6-8 minutes after the black, and the files copied back flat. Any start done
   by hand instead is named in the report.
3. **Start 1 of the restart is checked alone** before start 2, as before.
4. **Reported with the result:** that try 1 existed and why it stopped, its four starts (not used), and the runner and
   its commit.

Everything else in BATCH-B-RULES.md applies unchanged, the sittings and the calls included.
