# Phase 4, batch C: the rules

FROZEN: 2026-11-25, 18:21 UTC, before start 1 and before any folder was made. Don't edit: the hash is in every header.

Batch C was Vampinity's in the 22 Nov split. On 25 Nov they handed it to us: their console's drive is too full for its
cache copies, and it is busy with the depth recheck gate. Their words: "D only if C's waits probe shows active waits,
like in the split." So this batch is run on our console, under our conditions from the split (the control env, the whole
cache restored before every start, 12 controls of its own, rules frozen before start 1, read by one of the other two).

Alpha T186 (01.219.028) as installed, base PS5, 13.60, handheld 1x, the warm field route (c4fada64155f), the whole cache
restored before every start (the runner's `--warm-copy`). The control is the control env as it is. 28 starts: 12
controls and 4 of each arm, interleaved (C w x C y z C C z y C x w C C x w C z y C C y z C w x C), each arm with the same
mean place and no more than two arm starts in a row. Then **start 29, the waits probe**, in the same runner run. Run on
the runner (batch B's amendments 2 and 3 apply).

## The arms
| arm | removed | what is really off (read in T186's source) |
|---|---|---|
| w, table reserve | UP_TABLE_RESERVE | the sparse tables' own reserve of 8 blocks, filled before every other reserve, is gone (`guest_memory_service.inc:5347`). A table then takes from the guest reserve like any write, and waits up to 10 s before the session ends |
| x, scratch release | AREA_CHANGE_SCRATCH_RELEASE | a scratch buffer that grows destructively keeps its old buffer until the new one is allocated, so both are held at once for a moment (`scratch_buffer.h:81`) |
| y, keep arenas | HEAP_KEEP_ARENAS | empty heap arenas are given back instead of staying with their thread records (`heap_arenas.inc:302`) |
| z, report thread | MEMORY_REPORT_THREAD | the low-memory burst report and the heap trim run on the GPU thread again (`performance.cpp:933`) |

y overlaps Vampinity's own arenas kit (their play settings, 12.40 docked: v4.0b with and without the line, 6 against 6).
That kit asks about their play file, this batch about our control; the two are reported side by side, not pooled.

## The probe (start 29)
The control env plus `EDEN_UP_FAULT_LOG=1`. On this control it only logs: `GPU_READ_THROUGH=2` and `FAULT_RESERVE=1`
already turn the fault path on (`GpuReadSwitchesOn`, `guest_memory_service.inc:2992`), so the switch adds the capped
`EDEN_UP_FAULT_WAIT` lines and nothing else. It isn't in the store's stamp. It is not a control and is not read with C.

**Batch D's decision, written now** (`waits.py`, beside these rules):
- a guest-write wait is active if the probe shows at least one `EDEN_UP_FAULT_WAIT end`;
- block wait trim acts only inside a guest-write wait, so it is active with them;
- a JIT commit or new-handler wait is active if its line shows in the probe or in any of C's 12 controls (they print
  without the fault log).

Each active wait gets an arm in batch D, one at a time, with 12 controls of its own. A wait never seen is reported as
"never acted on this route (handheld, field)" and gets no arm. No wait active: batch D isn't run.
If the probe start doesn't count (no restore, a hang), it is rerun at the end; one start, not read for numbers.

## What counts
- A start: the warm boot (80,770 known, 3 own records, Total Pipeline Count 4) and the boot lines of its own env:
  - w: the two `EDEN_UP_TABLE_RESERVE on: 8 blocks for the sparse tables` lines in a control and in x, y and z, absent
    in a w start;
  - x, y and z print no line of their own: the env that ran is checked against the folder's by the runner import.
- A control: that, completed, and control_eligible in the scorer. An arm start: that, and completed. A bad quit after
  script_end keeps an arm start's count.
- Read against this batch's eligible controls only. **Fewer than 10: rerun controls, or the batch is called short.**
- A runner start without the whole-cache restore (no `warm.log` / `warm-note.json`) doesn't count and is rerun at the
  end. A hang stops the runner; the rest is planned from the next number, the hung start rerun at the end.
- A start that doesn't count and didn't crash is rerun at the end, its first files kept aside. A crash in an arm is a
  result and isn't rerun.

## Numbers
As batches A and B: survival read apart; six tested (graphics refusals to script_end, largest block at the black,
seconds under 16 MiB, worst frame after the black, load length, field-walk fps; scorer 10); distinct failed image
shapes beside the tries. Reported per arm and not tested:
- w: table waits and `EDEN_UP_TABLE_REFUSED` lines;
- y: the heap's `given_back` (its last `EDEN_HEAP_GROWTH` line) and its idle-arena page lines;
- every start: VMA dumps left on the console.

## The calls
- **Moved:** a crash in an arm when no warm control crashed, or a two-sided permutation p < 0.01 on any of the six.
  Either direction.
- **Retries moved, not memory moved:** refusals are the only number that moved and the distinct shapes don't.
- **Quiet**, best verdict by arm:
  - w: "removed, no change seen (handheld, field)" when its line is in every control and in no w start, and no w start
    shows a table wait or refusal; else "removed, no harm seen". The reserve was taken in 1 of 9 controls on 21 Nov.
  - x, y and z: "removed, no harm seen", at best (no line of their own shows they acted).
  Never "cleared".
- **Hold:** fewer than 4 arm starts count and it isn't moved.
- **Stop:** two crashes in an arm end that arm; a start of that arm the runner runs after its second crash is not read.

## Expected, written before any start (inferred, not measured)
- w: medians flat; a small risk of a table wait or a crash when a table grows with the pool at the bottom.
- x: a little less room for a moment at an area change; nothing the six numbers are sure to see.
- y: more room at the black if arenas come back (T51: 878 against 623 MiB largest block, one run each); or nothing,
  if the heap holds them anyway (T188, 2 against 2: nothing given back).
- z: the GPU thread does the report and the trim again: a longer worst frame possible after the black.
- The probe: guest-write waits likely (their 7 field starts on 12.40: 6 of 7); JIT commit waits rare (1 of 18 ours).

## What this can and can't see
As batches A and B: identical controls give a false move in about 3-4% of arms, so with four arms about 1 batch in 7
shows one. It speaks for the gate load on this route, handheld, from a fresh start; not for long play, docked or another
firmware. Nothing is adopted or removed: phase 4 explains the control.
