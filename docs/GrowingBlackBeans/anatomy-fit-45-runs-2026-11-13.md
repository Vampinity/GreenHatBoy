# The anatomy fit across 45 runs, and a correction to the first table (13 Nov, desk)

GrowingBlackBeans. No console. Tool: `eglog/anatomy.py fitall` (new). Data: every local run with the
`EDEN_GBB_VITALS` line, minus the instrumented ones and the read-sync ones, which both distort frame
time. **45 clean runs, 43 with enough play to use, 7,543 seconds.** The shared repo's runs were checked
too and add none: vitals arrived with patch 0922 on 12 Nov, and every run since is already local.

## The fit replicates the one from 11 Nov

Split by who sets the pace — on 11 Nov frame time tracked GPU-thread work only while the back thread set
the pace, and sat flat at about 33.7 ms while the game's own CPU did, so pooling the two blurs both.

**Back sets the pace** (back busy at least 80% of the frame): 1,589 seconds, 39 runs.

| | per frame, mean | upper-bound us per unit | R^2 alone |
|---|---|---|---|
| ring words | 141,839 | 0.196 | **0.754** |
| host GPU submissions | 55 | 507 | 0.715 |
| fence pops | 104 | 283 | 0.568 |
| front drains | 448 | 59 | 0.476 |

**One point per run, ring words only: frame = 11.75 ms + 0.203 ms per 1,000 words, R^2 0.792.**
The 11 Nov fit, on 128 older runs across all regimes: 15.7 ms + **0.213** ms per 1,000 words. The slope
agrees to within 5% on independent data from newer builds. That is the per-unit cost of the GPU
thread's work, and it is now measured twice.

**Back does not set the pace:** 5,954 seconds, 43 runs. Ring words explain R^2 0.287 on their own;
the joint fit leaves **27% of frame time unexplained**, which trips the plan's own decision rule (over
25%: the demand classes are wrong or something unmeasured dominates). The unmeasured thing is known
from 11 Nov — the game's own CPU chain — and vitals does not carry it.

## Only one demand class is identified

In the joint fit, host GPU submissions correlate with ring words at **r = 0.985** and are dropped; fence
pops and front drains come out **negative**, which means not identified. So with this data, ring words
are the one demand class with a real cost, and the others are proxies for the same quantity. Separating
them needs the per-method counts (`EDEN_GBB_BACK_CALLS`) or the GPFIFO counter, at the fixed spots.

## The correction: the back is not the pace-setter "in every window"

I posted to Discussion #5 that the back thread is **87-90% of every walking frame**, from `runRD1` and
`runRD2`. Both carry profiling switches. On clean runs it is not true:

| | back busy as a share of the frame | seconds where it is 80% or more |
|---|---|---|
| instrumented `runRD1`/`runRD2` | median **84%**, p90 89% | **54%** |
| **45 clean runs** | median **71%**, p90 85% | **21%** |

The ~12% instrument cost I flagged in that post understated it: instrumentation does not just add 12%
to the frame, it moves the back from the pace-setter half the time to the pace-setter a fifth of the
time. The back is still the busiest single stage, and the draw finding stands as a proportion — `draw`
is still most of the back's work — but **"the back owns the frame" is a claim about heavy walking
windows, not about the route.** For the other four-fifths, the game's CPU chain sets the pace, which is
what 11 Nov said and what the 27% residual says again.

## A tooling note

`anatomy.py` raised "divide by zero" and "overflow encountered in matmul" warnings on finite data. They
are spurious: numpy 2.0.2 uses Apple's Accelerate, the same three warnings fire on synthetic finite
input, and the product agrees with a pure-numpy einsum to 1.4e-14. They are silenced around the solves
only, with the reason in the code.

## runV1, the third run the plan named

`runV1` (12 Nov, build 01.219.914) carries `EDEN_GBB_BACK_CALLS` and nothing else; `runRD1` carried it
**plus** the twelve-thread `EDEN_GBB_SVC_PROFILE`. Same method breakdown, independently:

| | runRD1 | runV1 |
|---|---|---|
| `draw` (e0:0x585) per call | 1.245 us | 1.113 us |
| `draw` share of all back-thread command time | 57% | 58% |
| top four by time | draw, transform_feedback, inline_data, report_semaphore | identical |

So the draw finding holds across sessions and builds. The ~12% difference in per-call cost matches the
one thing that differs between the runs, so the thread profiler adds about 12% **on top of** the
back-call timer.

> **Corrected after `runGT1`:** I first wrote this as "the thread profiler is the expensive instrument,
> not the back-call timer". That does not follow — the comparison says nothing about the back-call
> timer's own cost. Measured against `runGP1`, `EDEN_GBB_BACK_CALLS` alone adds about **25%** to the back
> thread's time. Both instruments are expensive. See `findings-2026-11-13-gt1-cost-per-draw.md`.
