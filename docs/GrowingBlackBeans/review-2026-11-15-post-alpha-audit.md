# Review, regroup, rethink, replan — 15 Nov 2026, after the alpha

> **Posted 16 Nov.** This is the 15 November cycle as it was written, left as it stood. Two things
> changed between writing and posting, both on @Vampinity's side, and both make this review's picture
> better than it describes:
>
> - **He packed eleven control starts** (`runs/Vampinity/2026-11-15-t186-control-README.md`): seven
>   T186 field starts, two T185 and two T186 new-game starts, with the scoring windows written out.
>   That closes problem 4 in section 3 ("the control has no packed baseline") and most of phase 3.
>   All eleven carry both memory line formats, so the cross-check in section 2 now has 90 runs behind
>   it rather than 79, eleven of them on the control itself.
> - **He added `--json` to `memmap.py`, `ht_split.py` and `frame_split.py`** (branch
>   `vampinity/readers-json`), which closes the last line of the "Nothing emits JSON" correction.
>
> The archive counts below are as of 15 Nov: `index.csv` held 1,321 runs then and holds 1,332 now.

**Goal:** steady 30 fps on a base PS5. **Constraints:** the project is in a code freeze since the alpha
— no new patches, test builds or fixes, with one exception agreed with @waveydude: tests already built
that only measure, run as one-line changes from the control. Previous cycle: 14 Nov morning
(`review-2026-11-14-morning.md`).

Almost no console time today. One packed run and otherwise an audit, which is unusual for this cycle
and is the point of it.

## 1. What happened

| run / build | what it is | result | status |
|---|---|---|---|
| `2026-11-15-KS4` | fourth scripted Kokiri start, control arm for frame-ahead-off | packed; `checkrun.py` flagged a stderr/window mismatch | **false positive** (load-in windows); tool bug to fix |
| `2026-11-14-Play4a/b` | the two long plays | packed; both died of memory | see below |
| `t134-gbb10` | @waveydude's W-23 guard-order probe as patch 0936, folding @Vampinity's 1038 and its checker fix 1039 | built (01.219.926) | **never installed, never run** |
| `runKF1-4` | frame ahead off at the four stops | prepared | not run |

**Two results from the long plays.** Dead gaps are **not** memory waits: 38 memory-pressure events in
the second session, **zero** inside a gap bracket against about seven expected by chance. Swap is ruled
out — the worst page-in across both sessions is **1 ms**, against gaps of 500 to 2,000 ms.

## 2. What the audit found

Every packed run in this repo was scanned, and every row of `SWITCHES.md` parsed.

**The archive, against the row we agreed:**

| number | runs that could supply it | share |
|---|---|---|
| survival, n of N | 1,244 | 94% |
| largest free block | 1,151 | 87% |
| shader builds in play | 1,140 | 86% |
| median fps / p10 / worst frame | 971 | 74% |
| crash class | 879 | 66% |
| flashes a minute | 772 | 58% |
| hitch ms a minute | 4 | 0.3% |
| game speed | 0 packed | 0% |

**No run carries all ten.** 643 — 49% — could carry eight. The two that fail are structurally absent:
no flight-recorder file and no capture video has ever been packed by anyone, and the game-speed switch
is not on in any packed run (@Vampinity has three T180 runs with it that are not packed).

**The memory column is a reader problem, not a data problem.** `anatomy/memmap.py` reads
`EDEN_MEM_CENSUS_POOL`, present in **80** runs. `RADV_PS5_MEMORY` / `available_mib` is in **1,149**.
**79 runs carry both**, which is a built-in cross-check for any second reader. One extra reader takes
that column from 6% to 87% of the archive — the largest single gain available anywhere in this work.

**`run.json` beats the crash tools by two orders of magnitude.** Crash files are packed for **6** runs;
`run.json` already carries a classified ending on 1,244 and a crash class on 879.

**The conditions were never a measurement gap.** Console is on every run, build version on 83%, named
route on 84%, settings hash on 82% — all in `run.json`, simply never carried into `index.csv`.

**The switches.** 807 rows: 709 change behaviour, and **385 have no verdict**. The control we are
adopting **sets 169 switches; 75 of them have no verdict and 17 are flagged shipped-but-never-tested-
alone**, with a median of 143 runs behind each. That is not a criticism of the table — it is a gap in
it, and 67 of the 75 already have eight or more runs, so much of it may settle without a console.

Testing all 709 one at a time at four runs a side is **5,672 starts, about 662 console hours**. Screening
the control's unexplained switches by subsystem is **nine batches plus one control arm — 40 starts,
about five hours** — then bisecting only what moves.

## 3. Where things stand

| # | problem | certainty | evidence |
|---|---|---|---|
| 1 | the control's own composition is 45% unexplained | measured | 75 of 167 control switches |
| 2 | no run has ever been scored with the agreed row | measured | 0 of 1,321 |
| 3 | the memory column is unreadable by the tool we planned to use | measured | 80 against 1,149 |
| 4 | the control has no packed baseline | measured | no run on T185–T190 in this repo |

**Ruled out today:** dead gaps as memory waits; swap as a cause.

## 4. Corrections

Stated plainly, because several of them were mine and two were unfair to @Vampinity.

- **`available_mib` is the largest free block, not the total.** We published the wrong reading twice in
  one day. Corrected on D5 (19637363). Both long-play sessions are the fragmentation pattern, not a
  drained pool.
- **@Vampinity's D7 holder tables came from his own T186/T188 starts, not from our 1,055-run census.**
  We said otherwise.
- **He pointed out that p99 was already in the index the same evening, not days earlier.**
- **"Nothing emits JSON" was false.** `eglog.py json`, `count_flashes.py --json` and
  `bright_scan.py --json` already do. Only `memmap.py`, `ht_split.py` and `frame_split.py` do not.
- **"There is no scripted route in the village" was false** — three of his exist, and the listing was
  in front of us.
- **"The capture rig has been used exactly once" was false**; it is in routine use on his bench.
- **Our switch triage summed to 631, not 709**: 78 control switches that do have a verdict were
  uncounted.
- **Our own noise figure is up to 3.6 fps between identical runs** (upstream issue 21, comment 88). Any
  gate threshold has to start there rather than from a guess.

## 5. The plan

Phases, each ending on a condition rather than a date. The first three need no console.

1. **Read the archive** — the second memory reader, then one scorer over one run checked by hand, then
   every run scored into one row each, a coverage report that is **counted rather than drawn**, and a
   list of every run-and-column that came back empty with its reason.
2. **Write the rules down** — the four rules into this repo. They are agreed between the three of us in
   chat and recorded nowhere here, which is the same failure the rules exist to fix.
3. **Make the control real** — packed control starts, @waveydude's runs of the control on both 13.60
   and 9.40, and the B/D probe capture we owe him.
4. **Explain the control** — screen the 74 unexplained control switches in nine batches, bisect what
   moves. A batch that does not move is recorded as *screened as a group*, never as *each of these was
   tested*.
5. **Build the gate** — noise floors measured from the control arm. **The freeze ends here.**
6. **Finish the regime** — capture in every start, and the three instruments nothing currently covers:
   input lag, rendering correctness, audio.

**Open, and needing an answer:** the gate is the one rule nobody has explicitly agreed to. @Vampinity's
yes named one control, one route and one scorer. It is the rule that decides what gets rejected, so it
needs its own answer.
