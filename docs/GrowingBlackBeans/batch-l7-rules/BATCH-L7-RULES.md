# Phase 4, batch L7: the rules

FROZEN: 2026-11-25, 19:01 UTC, before start 1 and before any folder was made. Don't edit: the hash is in every header.

Lane 7's re-opened lines (decided 25 Nov, with batch B read: of the 34 lines with weak verdicts, 9 re-opened in these 4 arms, 17 accepted, 8 moved to the picture lane and the waits). Four lines
or sets of the control whose ledger verdicts rest on 1-2 starts or an old build, and that leave the shader store as it
is, each taken out alone against this batch's own controls.

Alpha T186 (01.219.028) as installed (not a186-gbb3: put the alpha back after play8), base PS5, 13.60, handheld 1x, the
warm field route (c4fada64155f), the whole cache restored before every start (the runner's `--warm-copy`). The control
is the control env as it is. 28 starts: 12 controls and 4 of each arm, interleaved
(C w x C y z C C z y C x w C C x w C z y C C y z C w x C). Every arm has the same mean place, and no more than two arm
starts come in a row. Run on the runner (amendments 2 and 3 of batch B apply: how the runner runs a start, all starts in
one run with `--warm-copy`).

## The arms
| arm | removed | what is really off (read in T186's source) |
|---|---|---|
| w, the JIT set | JIT_TABLE, JIT_FCMP_ADC, JIT_CHECKBIT_FLAGS, JIT_FREE_MOVES, JIT_R13, JIT_PAGE_REUSE | the plain JIT paths. One arm for the set (its old verdict was for the set); it is split only if it moves |
| x, preload all pipelines | NX2_PRELOAD_ALL_PIPELINES | the boot builds only the pipelines the used list names, the rest when first needed (`vk_pipeline_cache.cpp:3222`). Store kept: scheduling only (`SkippedInSourceMode`). On the warm store the boot reads 4 records (Total Pipeline Count 4), so if the used list holds all four this arm changes nothing |
| y, code-memory reserve 256 | NX2_CRAM_RESERVE_MIB | the guest reserve targets 256 blocks (512 MiB, `ReserveBlocks`) instead of 128 (256 MiB): 256 MiB more held. The floor stays 32 |
| z, IR free at boot builds | UP_IR_FREE | a boot-time build keeps its translated IR until its driver compile returns. IR_FREE_RUNTIME (lane 4j, Vampinity's) stays on: it reads its own switch (`vk_pipeline_cache.cpp:526-527`) |

## What counts
- A start: the warm boot (80,770 known, 3 own records, Total Pipeline Count 4; an x start may read fewer than 4 and still
  counts, the store reused) and the boot lines of its own env:
  - y: `reserve N blocks (floor 32, target 128)` in a control and in w, x and z; `target 256` in a y start;
  - z: the `EDEN_UP_IR_FREE: ... freed before its driver compile` lines in `eden_log.txt` (6 in each of batch A's 12
    controls), present except in a z start;
  - w and x print no line of their own: the env that ran is checked against the folder's by the runner import.
- A control: that, completed, and control_eligible in the scorer. An arm start: that, and completed. A bad quit after
  script_end keeps an arm start's count.
- Read against this batch's eligible controls only. **Fewer than 10: rerun controls, or the batch is called short.**
  No controls from another batch.
- A runner start without the whole-cache restore (no `warm.log` / `warm-note.json`) doesn't count and is rerun at the
  end. A hang stops the runner; the rest is planned from the next number, with the hung start rerun at the end.
- A start that doesn't count and didn't crash is rerun at the end, its first files kept aside. A crash in an arm is a
  result and isn't rerun.

## Numbers
As batches A and B: survival read apart; six tested (graphics refusals to script_end, largest block at the black,
seconds under 16 MiB, worst frame after the black, load length, field-walk fps; scorer 10); distinct failed image
shapes beside the tries. Reported per arm and not tested:
- x: `cached graphics pipelines are built when first needed` lines and the Total Pipeline Count;
- y: lines with the reserve at or under 32 blocks;
- z: the IR frees (count and MiB);
- every start: VMA dumps left on the console.

## The calls
- **Moved:** a crash in an arm when no warm control crashed, or a two-sided permutation p < 0.01 on any of the six.
  Either direction. What moves is split where it can be (w into its six lines, as AS did for A's drain).
- **Retries moved, not memory moved:** refusals are the only number that moved and the distinct shapes don't.
- **Quiet**, best verdict by arm:
  - w and x: "removed, no harm seen", at best (no line of their own shows they acted). For x, if no x start shows a
    pipeline left for first use, it reads "removed, no change at the boot" beside that.
  - y and z: "removed, no change seen (handheld, field)" when their proof line is in every control and in no arm
    start; else "removed, no harm seen".
  Never "cleared".
- **Hold:** fewer than 4 arm starts count and it isn't moved.
- **Stop:** two crashes in an arm end that arm; a start of that arm the runner runs after its second crash is not read.

## Expected, written before any start (inferred, not measured)
- w: field-walk fps down about 1-2 (the old +2 fps); the old flashes can't be seen by these numbers.
- x: no change if the used list holds the four boot records; else a shorter boot and pipelines built in play.
- y: 256 MiB more held by the reserve: less room at the black and more seconds under 16 MiB, unless the pool gives it back.
- z: up to ~50 MiB more at the peak of the boot builds near 78 s; little at the black, which comes about 70 s later.

## What this can and can't see
As batches A and B: identical controls give a false move in about 3-4% of arms, so with four arms about 1 batch in 7
shows one. It speaks for the gate load on this route, handheld, from a fresh start; not for long play, docked, another
firmware, or the picture (the JIT set's flashes need captures). Nothing is adopted or removed: phase 4 explains the
control.
