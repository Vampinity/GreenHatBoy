# Phase 4, batch CR: batch C's w repeated, table reserve out alone, the rules

FROZEN: 2026-11-27 04:50 UTC (26 Nov evening, local), before start 1 and before any folder was made. Don't edit: the
hash is in every header.

Why: batch C's w (table reserve out) moved: more room at the black, median 1,290 against 1,118 MiB, p 0.0011, and the
move held with any one start dropped (Vampinity's recount, PR 49). It rests on one batch, and two things make it worth
repeating before it goes on the map as moved:
- the gain (~170 MiB) is about 10 times the reserve itself (8 blocks of 2 MiB);
- C's controls sat low against B's (B's ran 1,088-1,296 MiB at the black, C's 1,056-1,270).
The 25 Nov brief proposed this repeat for after L7; the user chose it for the evening of 26 Nov. Nobody else runs it
(checked 26 Nov: PR 49, D2, the report-backs, the ledger).

Alpha T186 (01.219.028) as installed, base PS5, 13.60, handheld 1x, the warm field route (c4fada64155f), the whole
cache restored before every start (the runner's `--warm-copy`). Batch C's control env, unchanged. 12 starts in one
sitting on the runner: 8 controls and 4 of the arm, interleaved as AS (C w C C w C C w C C w C). Batch B's amendments
2 and 3 apply (how the runner runs a start; all starts in one run).

## The arm
| arm | removed | what is really off (read in T186's source) |
|---|---|---|
| w, table reserve | UP_TABLE_RESERVE (8 in the control) | as batch C: the sparse tables' own reserve of 8 blocks is gone (`guest_memory_service.inc:5347`); a table then takes from the guest reserve like any write, and waits up to 10 s before the session ends |

## What counts
As batch AS, with batch C's proof line:
- A start: the warm boot (80,770 known, 3 own records, Total Pipeline Count 4) and its own env's boot line,
  `EDEN_UP_TABLE_RESERVE on:`, present in a control and absent in an arm start.
- A control: that, completed, and control_eligible in the scorer. An arm start: that, and completed. A bad quit after
  script_end keeps an arm start's count.
- Read against this batch's eligible controls only. **Fewer than 7: rerun controls before the read, or the batch is
  called short.** No controls from batch C or any other batch in the test.
- A runner start without the whole-cache restore doesn't count and is rerun at the end. A hang stops the runner: the
  rest is planned from the next number, with the hung start rerun at the end. A start that doesn't count and didn't
  crash is rerun at the end, its first files kept aside. A crash in the arm is a result and isn't rerun.
- A freeze (L7 amendment 1's rule): rerun; it counts as a crash for the calls only if a second arm start freezes or
  crashes.

## Numbers
- **The one this batch is for:** the largest free block at the black (the last `RADV_PS5_MEMORY available_mib` before
  `wait_met line=92`), arm against this batch's controls, two-sided permutation.
- **The other five, as batch C:** graphics refusals to script_end, seconds under 16 MiB, worst frame after the black,
  load length, field-walk fps (scorer 10); distinct failed image shapes beside the tries. Survival read apart.
- **Reported per start, not tested** (the 25 Nov brief's step 3a: where the extra room comes from): the census at the
  black (the last `EDEN_MEM_CENSUS_POOL` before line 92: out, guest, reserve, tables, heap live, fragmented; and the
  allocator's largest piece, `census_black.py`), table waits and table refusals, VMA dumps left on the console.
- **Reported, not tested:** this batch's controls at the black beside batch C's 12 and batch B's 11, to show whether
  C's controls sat low.

## The calls
- **Repeated:** the arm's largest block at the black is higher than the controls', p < 0.01. Then C's w reads
  "moved" on the map, and the question goes to Vampinity's source reading (why ~10 times the reserve).
- **Moved the other way:** lower, p < 0.01. Then C's w and CR disagree: reported as a hold, not a move.
- **Not repeated:** p ≥ 0.01 at the black. C's w becomes a hold ("moved once, not repeated"), not quiet: a hold can
  be re-asked with more starts, and no line is said to be harmless on a split result.
- **Any of the other five at p < 0.01, or a crash in the arm when no control crashed:** moved on that number, either
  direction, as in batch C.
- **Hold:** fewer than 4 arm starts count and none of the above. **Stop:** two crashes in the arm end it.
- With 4 against 8 the smallest two-sided p is 0.004, and 0.006 with one control lost, so a repeat is reachable.

## Expected, written before start 1 (inferred, not measured)
- If C's move is real: the arm at about 1,250-1,330 MiB at the black against controls at about 1,060-1,300, the
  census showing the difference outside the tables' own 16 MiB.
- If it came from C's low controls: this batch's controls at the black like B's (about 1,090-1,300) and no gap.

## What this can and can't see
As batch C: identical controls give a false move on one of six numbers in about 3-4% of arms. It speaks for the gate
load on this route, handheld, from a fresh start; not for long play, docked or another firmware. Nothing is adopted or
removed: phase 4 explains the control.
