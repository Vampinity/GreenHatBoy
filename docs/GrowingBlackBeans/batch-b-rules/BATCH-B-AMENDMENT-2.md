# Phase 4, batch B: amendment 2, how the runner runs a start

FROZEN: 2026-11-25, 12:50 UTC, before the restart's start 1. Amends BATCH-B-RULES.md (sha1 9e13ca644841)
and amendment 1 (dbf66e3), which stay unchanged except where this says so. Decided by the user; reported with the
batch's result in its D2 line.

## The runner
Vampinity's runner (PR 38) at 31ace18, with 634a2b0's `restore-save.py` beside it, unused (no save is imported). It was
proven on 25 Nov with one warm field control: control eligible, boot 80,770 / 80,770 / 3 own / count 4, and the same env
hash and fps median as our hand-run control RC-5-C3.

## Where it differs from the written steps
Amendment 1 said the runner does each start's steps as written. In four places it does them differently:
1. **Logs.** The console's `logs` folder is not renamed before a start. The runner follows the new process's
   `eden_log.txt`, `stderr.log` and `heap.log` as they are written, and copies them, the boot trace and any crash and
   VMA files into that start's own folder. The step's purpose, each start's files kept apart, holds.
2. **The quit.** It comes 10 s after `script_done`, about 5 minutes after the black on this route, not 6 to 8 minutes
   after it. Every number the batch reads ends at `script_done` + 10 s, so the quit's timing doesn't change any of them.
3. **A hang** stops the whole batch. Nothing launches after it, so its main log is kept in its own folder (no `hang-try/`
   folder). It is rerun at the end, as the rules say.
4. **The stop rule** (two crashes in an arm end that arm). The runner doesn't apply it: after a crash the app restarts
   and the next start goes on. **An arm start that runs after that arm's second crash is not read.** The arm ended there.
   The start is kept, packed and reported.

## Unchanged
The field save is the console's newest entry before the batch (the user's step, as before). The whole cache is restored
before every start, from a copy checked against runWS2's 27 checksums. Start 1 is checked alone. The order, the envs
(apart from the two test lines the runner writes, the boot and the script's name), the route (c4fada64155f), the
counting and the calls are as in the rules.
