# Phase 4, batch B: the rules

FROZEN: 2026-11-24 14:35 UTC, before start 1 and before any folder was made. Don't edit: the hash is in every header.

Batch A's twin for the other three memory parts of the control (D2, 22 Nov: us A and B; approved by Vampinity with the
reserve floor's off value). Drafted 22 Nov (BATCH-B-DRAFT.md), challenged by an independent review the same day, and
frozen after batch A (#43) and its split (#47) were read. The user kept y, capped (24 Nov).

Alpha T186 (01.219.028) as installed, base PS5, 13.60, handheld 1x, the warm field route (c4fada64155f), whole cache
restored before every start. The control is the control env as it is: no refusal fit. 24 starts: 12 controls and 4 of
each arm, interleaved (C x C y C z C z C y C x C x C y C z C z C y C x).

## The arms
| arm | removed | what is really off (read in T186's source) |
|---|---|---|
| x, reserve floor | GUEST_RESERVE_FLOOR | the floor goes 32 -> 128 blocks, which is the target (CRAM_RESERVE_MIB=256): nothing above the floor. While the pool is short nothing is spared to writes above it (guest_memory_service.inc:359), the keeper refills to 256 MiB instead of 64 (:3363), and the caches call memory short below 128 MiB held instead of 32 (:2181, performance.h ViewOfPool). Reserve lend and buffer lend have nothing to give. JIT lend under floor still lends, down to 16 blocks |
| y, reserved tables | UP_RESERVE_TABLES | six texture tables and the buffer table (15.2 MiB, 14,912 + 672 KiB) are not reserved; they grow by doubling instead, and can ask about 10 MiB at the worst moment |
| z, DMA scratch | UP_DMA_SCRATCH_MIB | four engines' read and write scratch, 11 MiB each, 88 MiB in all, not reserved; each grows to the largest copy instead. A copy whose scratch can't grow goes through in stripes (0920, always on) |

x is named and reported as "reserve floor out: shedding off, with the caches' short-memory signal". JIT reserve lend is
screened with it (it can lend nothing with x out). x's off value is the target, as Vampinity agreed.

## What counts
- A start: the warm boot (80,770 known, 3 own records, Total Pipeline Count 4) and the boot lines of its own env:
  - x: `EDEN_UP_JIT_LEND_UNDER_FLOOR mode 2: a code cache piece ... (floor 32)` in a control and in y and z;
    the same line with `(floor 128)` in an x start;
  - y: the two `EDEN_UP_RESERVE_TABLES` lines (texture cache, buffer cache), present except in a y start;
  - z: the four `EDEN_UP_DMA_SCRATCH_MIB:` lines, present except in a z start.
- A control: that, completed, and control_eligible in the scorer. An arm start: that, and completed. A bad quit after
  script_end keeps an arm start's count.
- Read against this batch's eligible controls only. **Fewer than 10: rerun controls, or the batch is called short.**
  No controls from another day's batch, and none from batch A or its split.
- A start that doesn't count and didn't crash (a hang included: no script_done, no crash file) is rerun at the end of
  the sitting, its first files kept aside and its hang reported. A crash in an arm is a result and isn't rerun.
- A launch that sat in the launcher (`boot_skipped reason=not_armed`) is not a start. `.prev.*` files are matched by
  pid before they are named.

## Sittings (written before start 1, as #43 asked)
- One or two sittings. A second sitting picks up the order where the first stopped, with any reruns at its end.
- Before reading a batch run in two sittings, each sitting's eligible controls are compared on the six numbers (two-sided
  permutation, `sitting_check.py`, as batch A's amendment 1): p < 0.01 on any of them and every arm is **hold**.
- **Called short** if, after at most two sittings, there are fewer than 10 eligible controls or an arm has fewer than 4
  counted starts (that arm is hold; the others are read). Starts already back are kept, packed and posted either way.

## Numbers
As batch A: survival read apart; six tested (graphics refusals to script_end, largest block at the black, seconds under
16 MiB, worst frame after the black, load length, field-walk fps; scorer 10); distinct failed image shapes reported
beside the tries. Reported per arm and not tested:
- x: lines with the reserve at or under 32 blocks (`reserve N blocks (floor `), arm against controls;
- y: `EDEN_UP_TABLE_REFUSED` lines (0 in 18 earlier controls);
- z: `EDEN_UP_DMA_STRIPE` lines, `EDEN_UP_GPU_BADALLOC` lines, and the census heap's live MiB at the last census line
  before the black;
- every start: VMA dumps (`mkw-vma-*`) left on the console.

## The calls
- **Moved:** a crash in an arm when no warm control crashed, or a two-sided permutation p < 0.01 on any of the six.
  Either direction. What moved is split where it can be.
- **Retries moved, not memory moved:** refusals are the only number that moved and the distinct shapes don't.
- **Quiet**, best verdict by arm:
  - x: "removed, no change seen (handheld, field)" only if its reserve-at-or-under-32 counts don't overlap the
    controls'; else "removed, no harm seen". The count isn't required absent: the reserve can drain that far with
    the floor out too.
  - y: "removed, no harm seen", at best. 4 starts miss the risky growth (tables doubling with memory at the bottom)
    about 1 time in 5, so y can show harm and can't show its absence.
  - z: "removed, no change seen (handheld, field)" when the four scratch lines are in every control and in no z start;
    else "removed, no harm seen".
  Never "cleared".
- **Hold:** fewer than 4 arm starts count and it isn't moved.
- **Stop:** two crashes in an arm end that arm. The controls go on.

## Expected, written before any start (inferred, not measured)
- x: harm after the black: more refusals, more seconds under 16 MiB; a higher crash risk.
- y: medians flat; a small risk of a long frame, a missing image or a crash when a table grows at the bottom.
- z: 50-88 MiB less live heap; at the black +0 to +60 MiB, under what this batch can see; a longer worst frame possible.

## What this can and can't see
As batch A: identical controls give a false move in about 3-4% of arms, so about 1 batch in 9 shows one. Use the batch's
own spread when reading. It speaks for the gate load on this route, handheld, from a fresh start; not for long play,
docked, or another firmware. Nothing is adopted or removed: phase 4 explains the control.
