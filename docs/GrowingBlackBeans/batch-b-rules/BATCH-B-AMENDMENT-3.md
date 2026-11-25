# Phase 4, batch B: amendment 3, all 24 in one run

FROZEN: 2026-11-25, 13:12 UTC, before the restart's counted start 1. Amends amendment 1's point 3 ("start 1
of the restart is checked alone"). BATCH-B-RULES.md (sha1 9e13ca644841) and amendments 1 and 2 otherwise stand. Decided
by the user; reported with the batch's result in its D2 line.

## Why
The restart's first runner start (25 Nov, 07:58 local) ran without the whole-cache restore, so it doesn't count: the
rules restore the whole cache before every start. Apart from that it checked out in full. It booted warm (80,770 / 80,770
/ 3 own / count 4), ran the settings as written, finished the script, closed normally and didn't crash, and it reads as an
eligible control. So it has already done what checking start 1 alone was for: it showed that the runner, the plan and
the settings work together. The whole-cache restore itself was shown in the runner's proving start the same morning.

## What changes
1. **The restart runs all 24 starts in one run** of the runner, in the rules' order, each with the whole-cache restore
   (`--warm-copy`). No start is checked alone first.
2. **The uncounted start is not read.** It is kept and packed under its own id (`runM1B-01-C1-nowarm`), and reported
   with try 1 as a start that didn't count, with the reason.
3. **Every start is still checked** after the import and before the read, as the rules say. A start without the
   restore doesn't count, and it is rerun at the end.
