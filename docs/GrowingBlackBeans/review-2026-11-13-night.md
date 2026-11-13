# Review, regroup, rethink, replan — 13 Nov 2026, night

GrowingBlackBeans. Third cycle of the day. Previous: `review-2026-11-13-evening.md`.
New direction from the user: **stop chasing the two-ahead flicker, finish the toolkit, and find out what
the game is actually asking the emulator for.** Keep Fable's measurements at the front.

**Goal (M2):** Kokiri route, 95% of walking windows at 30 fps or better, p99 under 45 ms.
**Standing rules:** post nothing without approval; a collaborator's private work stays private; no story spoilers; never commit a log holding a console user number.

## 1. What happened since the evening cycle

No new console runs. Three inputs, all analysis:

- **Fable's independent cycle** rejected the 0934 prefetch design on source ordering and found three
  further errors. I verified all four myself: they hold. Recorded in
  `archive/posts/d2-correction-2-2026-11-13.md`, posted 17:57Z.
- **A full review of a collaborator's private work-in-progress**, newly shared with us.
- **Two checks of my own**, below, which are the reason the flicker chase should stop.

## 2. The finding that justifies parking the flicker

**Our flashing runs already carry waveydude's two-slot guard, and the guard says it is working.**

Every two-ahead run we have — `runRX1/2`, `runDX1-3`, `runDXS1-3`, `runGR1` — sets
`EDEN_UP_AHEAD_TWO=1`, `EDEN_UP_AHEAD_GUARD_SLOTS=2`, `EDEN_UP_AHEAD_GUARD=3`. In every window of
`runRX2`, the arm that flashes: **`armed 300 (0 while one was still armed)`** — zero unguarded frames,
zero writes waited, zero lifted early, and the second slot in use (23-136 armed beside another).

Then the guard's page-level risk counter, across every arm we have, by eye-rating:

| arm | runs | pages read with a guard up | not in the guard | at risk | unguarded frames |
|---|---|---|---|---|---|
| one ahead, no read sync — **flashes** | DC1-3 | 4.6-4.9 M | 249-266 k | 5.40-5.49% | 0 |
| two ahead, no read sync — **flashes** | DX1-3 | 6.6-7.7 M | 327-368 k | 4.76-5.04% | 0 |
| two ahead, no read sync — **flashes** | RX1/2 | 6.0-6.8 M | 198-211 k | 3.10-3.30% | 0 |
| one ahead + read sync — **clean** | DS1-3 | 4.3-5.1 M | 233-291 k | 5.41-5.71% | 0 |
| two ahead + read sync — **clean** | DXS1-3 | 4.1-5.0 M | 247-288 k | 5.71-5.96% | 0 |
| + once per frame — **clean** | RO1/2 | 4.8 M | 167-175 k | 3.47-3.59% | 0 |
| + escape 250 us — **flashes** | RE1/2 | 5.5-6.5 M | 194-210 k | 3.23-3.55% | 0 |

**The counter does not separate flashing from clean. It separates builds.** DC/DX/DS/DXS (01.219.918)
sit at 5-6%; RX/RO/RE (.920-.921) at 3-3.6%. Within each build the clean arms are *higher* than the
flashing ones. RE (flashes) and RO (clean) are indistinguishable.

So: the copy guard is not the mechanism behind our forest flashes, and this has been in all 110 run logs
since 9 Nov, unread. The flicker chase has been pointed at a hazard that was already at zero.

## 3. What the toolkit review found

### Our own STK: three pieces designed on 11 Nov and never built

| Piece | What it would have prevented today |
|---|---|
| `EDEN_GBB_WHERE` (scene/room per second) | both route confounds — GA1 vs GA3 (17 s apart, headline moved 9x), RE1's door at 160 s vs RX2's at 72 s |
| Scripted Kokiri route | the 3.6 fps hand-played spread that makes every 2-a-side comparison a screen |
| Per-session log folders | the "183 files not from this session" note on every `checkrun` |

And `LOGS.md` blind spot #1, written by me on 11 Nov: *"per-frame order of events across the game, the
front, the back, the host GPU and fences."* We wrote down that we were blind to the whole pipeline and
then spent three days optimising one stage of it.

### waveydude already has most of the tooling we were going to build

Reviewed with his permission; the detail is his to describe, not mine, so this note stays general.

He has, already built and in use: a live-switch schedule that compares a switch on and off **at one
spot in a single start**, with a settle window and A,B,B,A counterbalancing; **frame-indexed input
replay**, so a faster build does not desync a recorded route; a **per-frame position reader**, which is
what our designed-never-built `EDEN_GBB_WHERE` was for; a host-side deterministic stress test of the
real copy-guard code; per-read records carrying the scheduler state our ordering question turns on; and
named Vulkan timers that would attribute read sync's cost directly.

Between them these cover three of our four designed-not-built toolkit pieces. **The plan is therefore to
adopt rather than build**, and the most useful thing we can contribute back is the two helper scripts
his harness references and does not ship — without them nobody but him can author a screen-synchronised
wait. (`make-look.py`, one of the two, was written on 13 Nov.)

### And he named a mechanism we never tested

His own notes on the cut-from-black symptom say: whole-picture brightness after a cut runs 9, 91, 81, 74, 72, 62 … 47 against
9, 18, 33, 40, 43, 45 in a clean run, and points at **the exposure meter — a sum the GPU writes and the
game reads and clears every frame. Its download lands at the frame's fence, and a frame ahead the game
reads before that.** He then built a landing trace to find it: per-landing lines with kind **`k`** =
bytes kept off because the guest CPU wrote there first. *"A value that follows the picture's brightness
through the fade to black and the cut is the meter; a `k` line on it at the cut is the reading lost."*

**No commit anywhere reports running it.** It is a one-run experiment, the switch is in our build, and
it fits every oddity in our data: it is a *download landing late*, not a copy-guard page hazard (so the
guard reads zero); it is timing-dependent (so 2 ms is clean and 250 us flashes); and it does not care
which reads sync (so all three predicates measured flat).

## 4. Corrections

1. **"Collaborators: no overlap"** (evening cycle, and implied in the posted correction). Wrong twice
   over: L1028 early read-back, and now most of the toolkit.
2. **"The two-slot guard covers both frames but the flicker stayed, so something outside the buffer
   guard flickers"** (roadmap M1, 12 Nov). Right, and we then spent three days inside the buffer guard's
   neighbourhood anyway.
3. **The guard's own counters were never read.** Zero unguarded frames in 110 runs, and we were still
   treating "are both frames guarded" as an open question.
4. I should also record what the review of waveydude's repo says about his own numbers, so we do not
   repeat them: his W-11 "24.9 against 17.2 fps" is confounded by a warm shader cache *by his own
   admission in the same commit*, and his two-slot flicker verdict is one person, one run, by eye. The
   `0 unguarded frames` counter is the strong part; the fps and flicker claims are not established.

## 5. Where things stand

| # | Problem | Cost against M2 | Certainty | Evidence |
|---|---|---|---|---|
| 1 | **We have never characterised the game's demand** | unknown, and it bounds every other number | measured gap | no run has ever had the demand-side counters on together: BACK_CALLS on 4 of 113 runs, COST/TIMELINE/GPU_PROFILE on 1 each |
| 2 | The route is back-thread bound at about 27 fps | 3.4 fps short of M2 | measured | RX1/2 queued-dominated, back busy ~32 ms of a 37.5 ms frame |
| 3 | No objective flicker measure, and the one we thought we had does not discriminate | blocks M1 | measured | section 2; the flash counter saturates |
| 4 | Runs cannot be compared by place | bent two conclusions in one day | measured | GA1 vs GA3; RE1 vs RX2 |
| 5 | Read sync costs 7-8 fps and cancels the lookahead gain | 7-8 fps | measured | DX vs DXS, DS vs DXS |

**Ruled out, with the run that did it:** every read-sync predicate (0929/0930/0933), escape tuning
(0932), the fixed region list (GA3), the copy-guard hazard as our flicker mechanism (section 2), ASTC
decode backlog (AS1/RE1/RE2), 0934 as designed (source ordering).

## 6. Rethink

**Is the current path the one most likely to give a certain, meaningful result?** No, and the user is
right about why. Three days went into one symptom, with no model of what the emulator is being asked to
do. The one piece of topsight we ever built — the light/queued/mid/heavy regime taxonomy — has done more
work than every patch since, and it is the only reason we know problem 2 at all.

**The assumption that, if wrong, changes the plan most:** that the back thread's ~96,000 GPU methods per
frame (2.2 M/s, 226 ns each, 21.7 ms of a 43 ms frame in `runRD1`) is honest work. If the game really
issues that many command-stream methods a frame, the back is doing its job and M2 needs a faster back.
If it is inflated — macro expansion, list replay, state churn, resubmission — then we have an
amplification problem and the fix is a different class of thing entirely. **Nothing in our record
distinguishes those two worlds**, and the difference is the whole M2 gap. Cheapest decisive test:
`EDEN_UP_SUBMIT_STATS` plus `EDEN_NX2_GPU_PROFILE` on one run, which attribute submissions and methods
by call site without needing the ELF.

**Are we measuring the right thing?** No, and for the first time today the honest answer is that the
instruments already exist — in our own eboot and in waveydude's tree — and we have not used them.

**Collaborators:** everything in section 3.

## 7. Plan, as the user framed it

### (a) What measurements to make

In order, cheapest and most decisive first. None needs a new build.

1. **Workload census.** One run with every demand-side counter on: `EDEN_GBB_BACK_CALLS`,
   `EDEN_NX2_GPU_PROFILE`, `EDEN_UP_SUBMIT_STATS`, `EDEN_GPU_TIME`, `EDEN_NX2_TC_LOG`,
   `EDEN_GBB_SVC_PROFILE`, `EDEN_GBB_COST`, `EDEN_PERF_REPORT` with `cost-run.txt`. Derived table per
   5 s window: **what the game asked for** (methods, calls, draws, submissions, uploads, bytes, decodes,
   SVCs) against **what each stage spent supplying it** (front, back, host GPU, guest threads). Then the
   number that has never existed for this project: **cost per unit of demand, per stage.**
2. **The landing trace through the forest.** `EDEN_UP_LANDING_TRACE=1` with `EDEN_NX2_OVERWRITE_CHECK`,
   two ahead, no read sync. Look for a `k` line on a value that tracks picture brightness.
3. **Fable's ordering probe**, with his tool rather than a new patch: `EDEN_UP_SUBMIT_STATS` plus
   his per-read trace analyser, whose records already carry `pending_channels`, `fence` and
   `sequence` per read.
4. **`EDEN_PERF_COST` on a read-sync on/off pair**, to put the 7-8 fps in one of 24 named buckets.

### (b) What direction those measurements imply

If the method count is honest, M2 is a back-thread throughput problem and the work is the draw-end path
(Lichii #1095) and method dispatch — not anything we have touched this week. If it is inflated, the work
is upstream of the back entirely. The landing trace, if it finds the meter, turns the flicker from "sync
every read" into "make one download land before one read", which costs nothing and keeps two ahead.

### (c) If that fails, what gaps the measurement must still cover

Design the census so a null result is still informative. It must be able to say, per 5 s window and per
place: which stage was the critical path; whether the back's time is methods, submissions or waits;
whether the guest threads are in SVC or in guest code; whether the host GPU was idle. If the method
count is honest *and* the back is not the critical path everywhere, the census should already show
which windows are bounded by what — that is the ranked problem list for everything after M2, and it is
the thing we have never had.

### (d) How to build the tools

**Adopt before building.** In order:

1. **Ask waveydude for `make-look.py` and `steer-route.py`** (referenced in his harness, absent from the
   repo). Without them his route harness is unusable by anyone but him; with them we get a
   scripted, screen-synchronised route. Offering to write them is probably our highest-value
   contribution and it is squarely our skill set.
2. **Take his frame-indexed replay and his per-frame position reader** instead
   of building the scripted route and `EDEN_GBB_WHERE`. Both already exist and are calibrated.
3. **Make `EDEN_UP_AHEAD_READ_SYNC` a live switch**, templated on his 0548. Small, and it converts every
   future read-sync comparison from cross-run to one-spot-on/off.
4. **A per-frame brightness logger** from `GridOf`/`GridText`, which already exist and are tested: the
   objective flicker metric both teams lack, and it reproduces his 9/91/81 series automatically.
5. **Finish our own three STK pieces only where his do not cover them** — per-session log folders is
   still ours, and a confidence interval over `EDEN_UP_LIVE_SWITCHES` phase lines is a small analyzer
   that finishes his schedule.

**Parked:** the two-ahead flicker as a target, every read-sync variant, 0934, the blinded `runZ` set
(its arms are recognisable by frame rate anyway, per Fable).

## 8. Decisions needed

1. **Does the workload census go first, or the landing trace?** Recommend the census: it is the topsight
   the user asked for and it bounds everything else. The landing trace is one run and can follow.
2. **Ask waveydude for the missing harness tools, and offer to write them?** Recommend yes.
3. **A new GHB discussion for the forensic work?** It is a different kind of thread from "who is working
   on what" and would give both the census and the toolkit a home.

---

## 9. Addendum: Fable's second review did NOT approve this cycle

It called the direction right and the plan wrong as scoped. I verified its load-bearing objections
against the logs; the ones below hold and are corrections to this document.

1. **"Zero unguarded frames in 110 runs" is false.** 77 runs have guard lines and **9 show overlaps**
   (`runFX1-3` 240-275, `runX1-3` 197-232, `runXU1` 348, two freeze runs). The claim is true only of the
   two-ahead runs with `GUARD_SLOTS=2`.
2. **"It separates builds" is wrong — it is a load-in window.** Per window, the .918 excess is one spike
   at 75-80 s (DX1 21.0%, DXS1 31.2%). In steady windows (t >= 110 s) all four arms are the same:
   DX1 3.98%, DXS1 4.12%, RX2 4.20%, RO2 3.62%. The non-discrimination survives; my explanation of the
   aggregate difference did not.
3. **Exposure is not harm.** The counter counts pages read while unprotected; it cannot tell whether a
   guest write actually raced one. So "the copy-guard hazard is not the mechanism" is **not
   established**, and it comes off the ruled-out list. The direct test, `EDEN_UP_AHEAD_GUARD_ALL_WRITES=1`,
   is in the eboot and appears in no `env.txt` we have ever run.
4. **The method count was wrong.** Steady standing windows in `runRD1` are **132-134 k methods a frame**
   at 202-206 ns, not 96 k at 226 ns; 2.2 M/s is the load-in window. And `runRD1` stands at 24.5 fps
   against `runRX1/2` at 27.8/27.9, so the instruments cost about 12% and the "43 ms frame" was inflated
   by them.
5. **Demand must be measured at the guest boundary, not at emulator internals.** Methods and draws are
   already our own counters. What the game asks for is GPFIFO entries and words per frame per channel,
   reads of GPU-written memory, writes to GPU-tracked pages, SVC waits, presents and fences. **This is a
   better framing than section 7's and replaces it.** The one open ratio is GPFIFO words against ring
   words: above about 1.2 means amplification on the front; otherwise the work is back-thread
   throughput on the draw path.
6. **"Cost per unit of demand, per stage" as a single number is a category error.** Per method cost
   ranges from 0.03 us (`0x8e3`) to 1.05 us (`0x585`) to 17.9 us (`e3:0x107`), so it must be per class;
   stages run in parallel so only the critical path buys frames; and a ratio needs a reference floor to
   mean "poorly". Marginal and fixed cost differ (draw-end is 15-37 us at 5 draws a frame and 1.05 us at
   13,300), so the right instrument is a **fit of frame time against demand across places**, not a ratio.
7. **Everything-on-at-once makes the supply half unusable.** Counts survive instrumentation; times do
   not. Split into one counts-only run and separate lightly instrumented runs.
8. **Step 3 was mis-paired.** `analyze-ordered-reads.py` reads capture files written by
   `headless/ordered_read_trace.inc`, not anything `EDEN_UP_SUBMIT_STATS` produces. Whether a capture
   can even be started on Ocarina is unverified.

### Where its review is wrong, checked against the logs

Its table gives `runDXS1-3` as **0** for "armed beside another", "copies served both slots" and "reads
took a newer frame's copy". Measured:

| run | arm | armed beside another | both-slot copies | newer-copy reads | by eye |
|---|---|---|---|---|---|
| `runDX1` | two ahead | 1332 | 6608 | 2243 | flashes |
| `runDXS1` | + read sync | **81** | **15** | **1448** | clean |
| `runRX2` | two ahead | 1065 | 3898 | 260 | flashes |
| `runRO2` | + read sync + once | 0 | 0 | 0 | clean |
| `runRE1` | + escape 250 us | 8 | 28 | 0 | flashes |

So "the clean two-ahead arms are not two-ahead" is too strong: DXS1 ran two frames in flight for 81
presents and took 1,448 newer-frame copies, and was clean. And the correlate it offers in place of mine
fails on the pair that matters most — **`runRE1` flashes with 0 newer-copy reads while `runDXS1` is
clean with 1,448.** Opposite directions on the one single-variable comparison we have.

### Standing

The gate the user set was that Fable had to approve before anything was posted. It did not, so nothing
was posted. The plan in section 7 is superseded by Fable's re-scoping (items 1-7 of its section 3),
which is better than mine: desk census from `runRD1`/`runRD2`/`runV1` first, the brightness metric
extended at the desk, a guard-line extractor for `eglog.py`, then two short console runs — counts only,
then timers only.

---

## 10. The anatomy phase (adopted at the user's direction, 13 Nov)

Fable's re-scoped plan collapses topsight to one question — GPFIFO words against ring words. That is
the right *first* question and not a sufficient one. The anatomy is adopted as a phase in its own right.

**What it answers:** for each place in the game, what the game asks the emulator for, what each stage
spends supplying it, what one unit of each kind of demand costs us, and what we can afford to spend at
30 fps.

### Method

1. **Fixed places, not windows.** Three or four standing spots on the Kokiri route (outside the house,
   the water, a forest hotspot, the village side). Standing windows repeat to within 1% — 132 k ± 1 k
   methods a frame — so a handful of spots give a clean design matrix without the scripted route.
   Walking windows are collected too but kept separate; they are the variance, not the baseline.
2. **Demand is counted at the guest boundary first, then internally.** Per frame, per place:

   | Class | Source | State |
   |---|---|---|
   | GPFIFO entries and words, per channel | **needs a counter** | blind |
   | Macro expansion ratio (GPFIFO words -> ring words) | **needs a counter** | blind |
   | Ring words | runreport, every run | have |
   | Methods by class (draw, constant-buffer word, clear, dispatch, state) | `EDEN_GBB_BACK_CALLS` + `EDEN_NX2_GPU_PROFILE` | 4 of 113 runs |
   | Host GPU submissions, fence pops | vitals (`gpu_subs_s`, `fence_pops_s`) | have, never read |
   | Images created/deleted, upload MiB, ASTC decodes | `EDEN_NX2_TC_LOG` | 113 runs |
   | Reads of GPU-written memory | read-sync lookups | 2 runs |
   | Writes to GPU-tracked pages | guard copies | 77 runs, never read |
   | Guest SVC calls and waits, presents | `EDEN_GBB_SVC_PROFILE` | 7 runs |

3. **Supply is timed in separate runs.** Counts survive instrumentation; times do not (`runRD1` stands
   at 24.5 fps against `runRX1/2` at 27.8/27.9, so the timers cost about 12%). One counts-only run and
   one timers-only run per place, the timers under live switches at a single spot.
4. **The fit.** Regress frame time on demand by class across places:
   `frame_ms ~ fixed + sum_c (count_c x marginal_cost_c)`. This is the instrument, not a ratio. It
   separates marginal from fixed cost, which a per-unit average hides — draw-end costs 15-37 us at five
   draws a frame and 1.05 us at 13,300.
5. **The budget, which is what makes "poorly" mean something.** The game targets 30 fps, so the frame
   budget is 33.3 ms. For each demand class: `affordable_cost_per_unit = share_of_budget / count_per_frame`.
   Put measured cost beside affordable cost. **The classes where measured exceeds affordable are the
   ranked problem list for the rest of the project**, and they are ranked by how much of the budget each
   one overspends — not by which bug annoyed us most recently.
6. **Critical path per place.** Stages run in parallel, so only the critical path buys frames. Each
   place gets a verdict: back-bound, guest-CPU-bound, host-GPU-bound, or submission-bound, from the
   stage whose busy time is within a few per cent of the frame.

### Decision rules

- **Any class where measured cost exceeds its 30 fps budget by 2x or more** becomes a work item with
  its own expected size in ms a frame. If no class does, the frame is fixed cost and the target is the
  dispatch loop itself.
- **If the fit's residual is over about 25% of frame time**, the demand classes are wrong or something
  unmeasured dominates, and the next step is finding it rather than optimising anything.
- **If every place returns the same verdict**, one stage owns M2 and the roadmap simplifies.
- **If places disagree**, the roadmap needs per-place work and the scripted route stops being optional.

### What it needs built

- A GPFIFO counter (entries, words, per channel, per frame) — **the one new patch this phase requires**,
  log-only, off by default.
- `eglog/anatomy.py` — reads a run and emits the per-frame demand and supply table; across runs, does
  the fit and prints the budget table. This is the tool the toolkit roadmap never had, and it subsumes
  the "workload census" idea from section 7.
- The guard-line and vitals extractors, since both already carry demand signals no tool reads.

### Where it sits

Phase 1 (desk census from `runRD1`/`runRD2`/`runV1`) is the dry run for `anatomy.py` and will already
answer the fit for the classes we have. The GPFIFO counter and the counts-only run answer Fable's first
question *inside* the anatomy rather than beside it.
