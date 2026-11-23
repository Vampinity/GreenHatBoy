# Phase 4, batch A: the rules

FROZEN: 2026-11-22 16:37 UTC, before start 1 and before any folder was made. Don't edit: the hash is in every header.

Alpha T186 (01.219.028) as installed, base PS5, 13.60, handheld 1x, the warm field route, whole cache restored before
every start. 24 starts in one sitting: 12 controls and 4 of each arm, interleaved
(C x C y C z C z C y C x C x C y C z C z C y C x).

## The arms
| arm | removed | what is really off (read in T186's source) |
|---|---|---|
| x, load hold | LOAD_HOLD, LOAD_HOLD_FREE_MIB | the hold, with everything it asks for: images, swap, heap trim, drain, the spare's refill |
| y, heap hold at load | HEAP_HOLD_AT_LOAD, its SPARE_MIB and REFILL_MIB | the hold, the spare and its refill. The two tuning lines act only with their parent |
| z, drain | PRESSURE_DRAIN, its PENDING_MIB, DRAIN_AT_AREA | pressure drain, drain at area (runs only inside it) and load hold's drain step. Counting stays on |

z is named and reported as "drain, with load hold's drain step". x and z overlap there: their effects are not added up.
If z moves, the only split there is: drain at area out alone. Pressure drain can't come out without the other two.

## What counts
- A start: the warm boot (80,770 known, 3 own records, Total Pipeline Count 4) and the boot lines of its own env
  (each unit's on-line present, or absent for the unit that is out).
- A control: that, completed, and control_eligible in the scorer. An arm start: that, and completed. A bad quit after
  script_end keeps an arm start's count.
- Read against this batch's eligible controls only. Fewer than 10: rerun controls in the same sitting, or the batch is
  called short. No controls from another day.
- A start that doesn't count and didn't crash is rerun at the end of the same sitting, its first files kept aside.
  A crash in an arm is a result and isn't rerun.

## Numbers
Survival, read apart. Six tested: graphics refusals to script_end (tries), largest block at the black, seconds under
16 MiB, worst frame after the black, load length, field-walk fps (scorer 10).
Reported beside the tries and not among the six: distinct failed image shapes (no repeats, buffers left out).

## The calls
- **Moved:** a crash in an arm when no warm control crashed, or a two-sided permutation p < 0.01 on any of the six.
  Either direction. What moved is split (#27, condition 2) where it can be.
- **Retries moved, not memory moved:** refusals are the only number that moved and the distinct shapes don't (p >= 0.01).
- **Quiet, "removed, no change seen (handheld, field)":** nothing moved, the unit's count line is in every control and
  in no arm start. Without that proof: "removed, no harm seen". Never "cleared".
- **Hold:** fewer than 4 arm starts count and it isn't moved.
- **Stop:** two crashes in an arm end that arm. The controls go on.

## What this can and can't see
From 22 Nov's four controls, about 1.8 sd: ~10 refusals, ~200 MiB at the black, ~38 s under 16 MiB, ~1.5 s of in-load
frame, ~4 s of load, ~0.25 fps of walk. Use the batch's own spread when reading. Identical controls give a false move in
about 3-4% of arms, so about 1 batch in 9 shows one. It speaks for the gate load on this route, not for long play.
Nothing is adopted.
