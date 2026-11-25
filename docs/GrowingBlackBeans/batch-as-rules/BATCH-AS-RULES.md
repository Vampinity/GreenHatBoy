# Phase 4, batch A split: drain at area alone, the rules

FROZEN: 2026-11-23 15:03 UTC, before start 1 and before any folder was made. Don't edit: the hash is in every header.

Why: batch A's z (drain) moved: with pressure drain, drain at area and load hold's drain step out together, less room
at the load (largest free block at the black p 0.0016, s under 16 MiB p 0.0022; #43). Under batch A's rules what moved
is split where it can be, and the only split is drain at area out alone. The user chose to run it before batch B (23 Nov).
Vampinity's ledger: "never tested alone; on in about 530 runs, never on and off apart".

Alpha T186 (01.219.028) as installed, base PS5, 13.60, handheld 1x, the warm field route, whole cache restored before
every start. 12 starts in one sitting: 8 controls and 4 of the arm, interleaved (C w C C w C C w C C w C).

## The arm
| arm | removed | what is really off (read in T186's source) |
|---|---|---|
| w, drain at area | DRAIN_AT_AREA | the drain at an area change and its 20 s window of eager drains. Pressure drain and load hold's drain step stay on |

## What counts
As batch A (BATCH-A-RULES.md, sha1 ffbf5cface7f), with these changes for the size:
- A start: the warm boot (80,770 known, 3 own records, Total Pipeline Count 4) and its own env's boot line: drain at
  area's on-line (`EDEN_UP_DRAIN_AT_AREA on:`) present in a control, absent in an arm start.
- A control: that, completed, and control_eligible in the scorer. An arm start: that, and completed. A bad quit after
  script_end keeps an arm start's count.
- Read against this batch's eligible controls only. **Fewer than 7: rerun controls in the same sitting, or the batch is
  called short.** No controls from another day, and none from batch A.
- A start that doesn't count and didn't crash is rerun at the end of the same sitting, its first files kept aside.
  A crash in the arm is a result and isn't rerun.

## Numbers
As batch A: survival read apart; six tested (graphics refusals to script_end, largest block at the black, seconds under
16 MiB, worst frame after the black, load length, field-walk fps; scorer 10); distinct failed image shapes reported
beside the tries. Drain at area's count line, `EDEN_UP_DRAIN_AT_AREA drain`, is the proof (33-35 a control in batch A).

## The calls
- **Moved:** a crash in the arm when no warm control crashed, or a two-sided permutation p < 0.01 on any of the six.
  Either direction. With 4 against 7 the smallest p is 0.006, so a move is still reachable with one control lost.
- **Retries moved, not memory moved:** refusals are the only number that moved and the distinct shapes don't.
- **Quiet, "removed, no change seen (handheld, field)":** nothing moved, the count line is in every control and in no
  arm start. Without that proof: "removed, no harm seen". Never "cleared".
- **Hold:** fewer than 4 arm starts count and it isn't moved. **Stop:** two crashes in the arm end it.

## What each answer means (written before start 1)
- **Moved:** drain at area carries some or all of z's effect at the load.
- **Quiet:** z's effect comes from pressure drain itself or load hold's drain step, which can't be told apart on this
  build. Either way pressure drain stays on: nothing is adopted or removed in phase 4.
- It speaks for the gate load on this route, handheld, from a fresh start; not for long play or docked.
