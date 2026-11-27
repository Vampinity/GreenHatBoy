# Phase 4, batch L6: lane 6c, the kernel resource cap out alone, the rules

FROZEN: 2026-11-27 05:05 UTC (26 Nov evening, local), before start 1 and before any folder was made. Don't edit: the
hash is in every header.

Why: lane 6 holds the lines the field route can't answer as it stands. 10 of its 13 change the shader store and wait
for a store lane; two picture lines need captures. Lane 6c's one line, `EDEN_KERNEL_RESOURCE_MIB=8`, leaves the store
alone (ledger), and reading T186's source on 26 Nov showed it acts from boot, not after ~9 minutes as the map said:
- `k_system_resource.cpp:52-63`: the title's kernel resource (47 MiB asked; only the kernel's memory blocks and block
  infos come out of it) is cut to N MiB, while the guest still sees the size it asked for;
- `k_dynamic_page_manager.h`, `Initialize`: the managed size is backed with host memory at boot
  (`m_backing_memory.resize`), every page zeroed, so all of it is real from the first second.
So the line saves about 39 MiB of real memory from boot. What comes after ~9 minutes is only the game's first use of
the resource: "1 MiB of 8 MiB of pages used at most" at about 531 and 541 s in Vampinity's New Game runs (PR 27), and at
98, 212 and 1,191 s in our play runs; never more than 1 MiB in any log. The field route (~465 s) never reaches that
line, so this batch has no proof line. The user chose the plain field route over a longer one (26 Nov). Vampinity's
ledger: "on in about 1,810 runs, never on and off apart"; his PR 27 note: "in heap it goes alone".

Alpha T186 (01.219.028) as installed, base PS5, 13.60, handheld 1x, the warm field route (c4fada64155f), the whole
cache restored before every start (`--warm-copy`). The control env, unchanged (as batches C, L7 and CR). 12 starts in
one sitting on the runner: 8 controls and 4 of the arm (C w C C w C C w C C w C). Batch B's amendments 2 and 3 apply.

## The arm
| arm | removed | what is really off (read in T186's source) |
|---|---|---|
| w, kernel resource cap | KERNEL_RESOURCE_MIB (8 in the control) | the title's kernel resource keeps its full managed size (about 47 MiB), all of it backed and zeroed at boot: about 39 MiB more real memory held from the first second. The guest sees the same size either way |

## What counts
As batch CR, except the proof:
- A start: the warm boot (80,770 known, 3 own records, Total Pipeline Count 4). The line prints nothing on this route,
  so the env that ran is checked against the folder's by the runner import (KERNEL_RESOURCE_MIB absent in an arm
  start, `=8` in a control).
- A control: that, completed, and control_eligible in the scorer. An arm start: that, and completed. A bad quit after
  script_end keeps an arm start's count.
- Read against this batch's eligible controls only. **Fewer than 7: rerun controls before the read, or the batch is
  called short.**
- A runner start without the whole-cache restore doesn't count and is rerun at the end. A hang stops the runner: the
  rest is planned from the next number, the hung start rerun at the end. A start that doesn't count and didn't crash is
  rerun at the end, its first files kept aside. A crash in the arm is a result and isn't rerun. A freeze: L7 amendment
  1's rule (it counts as a crash only from a second freeze or crash in the arm).

## Numbers
As batch C: survival read apart; six tested (graphics refusals to script_end, largest block at the black, seconds under
16 MiB, worst frame after the black, load length, field-walk fps; scorer 10); distinct failed image shapes beside the
tries. Reported per start, not tested: the census at the black (`EDEN_MEM_CENSUS_POOL`: out and heap), any
`EDEN_KERNEL_RESOURCE all ... pages are in use` line (the cap running out; none expected), and any `of 8 MiB` line.

## The calls
- **Moved:** a crash in the arm when no control crashed, or a two-sided permutation p < 0.01 on any of the six. Either
  direction. With 4 against 8 the smallest p is 0.004, 0.006 with one control lost.
- **Retries moved, not memory moved:** refusals are the only number that moved and the distinct shapes don't.
- **Quiet:** "removed, no harm seen (handheld, field)", at best: the line has no proof on this route. Never "cleared".
- **Hold:** fewer than 4 arm starts count and it isn't moved. **Stop:** two crashes in the arm end it.

## Expected, written before start 1 (inferred, not measured)
- About 39 MiB less room in the arm, from boot, if the host memory comes out of the same pool: below what 4 against 8
  can see at the black (the controls span about 200 MiB). So most likely quiet.
- No `pages are in use` line in any start: the most the game used in any log is 1 MiB.

## What this can and can't see
It speaks for the gate load on this route, handheld, from a fresh start. It can't see whether 8 MiB runs out in long
play (the cap would bind above 8 MiB of use; 1 MiB is the most seen, in 20 minutes of play). Nothing is adopted or
removed: phase 4 explains the control.
