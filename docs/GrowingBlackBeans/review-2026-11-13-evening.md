# Review, regroup, rethink, replan — 13 Nov 2026, evening

GrowingBlackBeans. Previous cycle: `review-2026-11-13.md`, this morning. This one covers only what
happened after it: patch 0933, builds gbb6 and gbb7, and runs GA1, GR1, GA3.

**Goal (M2):** Kokiri route, 95% of walking windows at 30 fps or better, p99 under 45 ms.
**Constraint from the user:** two frames ahead is wanted; it is what makes the game feel right.
**Standing rules:** post nothing without approval; the user copies files to the console; no story
spoilers; never commit a log holding a console user number.

## 1. What happened

| run | build | arm | result | by eye |
|---|---|---|---|---|
| `runGA1` | .922 | region list + audit (syncs everything) | 18.77, light 22/22 | clean — but audit mode syncs everything, so it could not flash |
| `runGR1` | .922 | region list only | 19.00, light 21/22 | no flashes, worst frame 158 ms |
| `runGA3` | .923 | same as GA1, audit now names its misses | 18.49, light 23/23 | not rated (measurement run) |

Every run `checkrun`-verified: env against the log's own `EDEN_GBB_ENV` dump, build from the boot
trace. All three are light-regime throughout, so none of this is a heavy-window mix artefact.

- **0933, region-limited read sync** (sync only inside the hot regions) → syncs 78.9 → 33.3 a frame
  (−58%), fps 18.77 → 19.00 → **rejected**.
- **The region list's completeness** → `runGA1` 6 misses of 1,586; `runGA3` **52** → **rejected as a
  fixed list**.

## 2. What we learned

### Read sync's cost is a wait for an event, so no predicate can reach it

`runGA1` and `runGR1`: same build, route and env, one switch apart.

| | syncs/frame | fence waits/frame | summed wait/frame | us per wait | fps |
|---|---|---|---|---|---|
| `runGA1` all reads | 78.9 | 30.3 | 77.65 ms | 2561 | 18.77 |
| `runGR1` list only | **33.3** | **28.7** | **72.31 ms** | **2520** | **19.00** |

- `runGA1`: 30.3 of 78.9 synced reads actually waited — **38%**.
- `runGR1`: 28.7 of 33.3 — **86%**.

The filter removed the free reads: the ones that arrived after the fence had already passed. The rest
wait for the same fence at the same wall-clock moment, so the total is unchanged.

On noise: one run a side, so `abcompare` calls the fps "noise" either way, and it is right to. The
evidence is not the 0.23 fps — it is the counters, and the fact that a **pre-registered +4.4 fps**
(3.7x the noise floor, and impossible to miss) did not appear.

Three patches, three levers, one reason: 0930 (syncs −28%), 0932 (per wait −77%), 0933 (syncs −58%),
all flat. **Anything of the form "sync fewer reads" or "sync them more cheaply" is now ruled out.**

### A fixed address list does not work, because the hot set moves

`runGA3` against `runGA1`: same list, same env, same route, 17 s longer.

| run | log length | changed OUTSIDE |
|---|---|---|
| `runGA1` | 195 s | 6 |
| `runGA3` | 211 s | **52** |

All **52 of 52** misses sit immediately *below* the listed regions — 51 in `0x30300000` (under the
listed `0x30400000`), 1 in `0x2b500000` (under `0x2b600000`) — and 51 of them fall in a burst between
200 and 220 s, territory the earlier runs never reached.

So the records live in an arena that extends downward as play goes on, and which part is hot depends on
where and how long you have played. The consolation is the shape: the drift is one direction, adjacent,
in two clusters. **Hardcoding is dead; a set learned at runtime is not.**

### The route keeps confounding us

`runGA1` and `runGA3` differ by 17 s of play and that moved the headline number nine-fold. Earlier the
same day `runRE1`'s door was at 160 s against `runRX2`'s 72 s. Two conclusions bent by route length in
one session. 0923's `EDEN_GBB_MARK` (touchpad route markers) is written and still untested.

## 3. Corrections

1. **"A targeted list is enough for correctness"** (written this evening after `runGR1`'s clean
   rating). Wrong. `runGR1`'s log ends at 194 s and 51 of GA3's 52 misses are after 200 s: GR1 never
   reached the part of the route where the list leaks. A clean rating from a run that stopped short of
   the problem is not a clean rating. **Retracted in the findings doc.**
2. **"GR1 should land near 23.4 fps"** (pre-registered). It landed at 19.00. The model behind it —
   cost scaling with the number of synced reads — is what this cycle retires.
3. **"The region list is cross-validated, `runDV1` and `runRC1` agree region for region"** (said this
   afternoon). True and misleading: both are the same route and the same save, and both ended before
   200 s. They agreed because they stopped in the same place.

## 4. Where things stand

| # | Problem | Costs | Certainty | Evidence |
|---|---|---|---|---|
| 1 | Read sync's fence wait, and nothing that narrows the read set can touch it | 7-8 fps, and it cancels the lookahead gain | **measured** | GA1/GR1 counters; 0930, 0932, 0933 all flat |
| 2 | We still cannot measure flicker | blocks M1's exit and every flicker call | measured | the flash counter saturates and fails its FW/RX control |
| 3 | Route alignment: runs are hand-played and not comparable by place | bends conclusions, twice today | measured | GA1 vs GA3; RE1 vs RX2 |
| 4 | Frame-ahead flicker itself | blocks two ahead, worth +1.6 fps and the pacing | by eye only | DC/DX vs DS/DXS |
| 5 | Benchmark route is queued-dominated at 26.65 | the ceiling without read sync | measured | RX1/RX2 regime split |

**Ruled out and not to be retried without a new reason:** 0929 (pending predicate, 1.5% skip), 0930
(once per present, +0.2), 0932 (short escape, +0.68 and flicker back), 0933 as a filter (−58% syncs,
flat), a fixed region list (GA3), ASTC decode backlog (AS1/RE1/RE2).

## 5. Rethink

**The one lever left that nothing has tried: change *when* the download is requested, not who waits
for it.**

Today's code asks for the download at the moment of the guest read — the worst possible moment, because
the frame it needs has only just been submitted. But the present thread already knows, at the present,
both that the frame ran ahead and what its fence is (`nx2_gsv.h`, where `g_ahead`, `g_present` and
`g_fence` are stored). And the GPU thread's queue is **already ordered behind the frame's work**.

So a flush enqueued on the GPU thread at the present runs after that frame completes by construction —
nobody waits for a fence to do it. A guest read a whole frame later finds the bytes already in guest
memory. The read still has to check that the prefetch landed, but it is checking work issued a frame
earlier instead of microseconds earlier, which is the entire difference.

This is distinct from everything that failed: it does not reduce the number of synced reads (0930,
0933) or shorten the wait (0932). It moves the request a frame earlier.

**Which ranges?** Not an address list — GA3 killed that. 0930 already tracks exactly the right set:
*the ranges read via read sync in the previous present*. Reuse it and the scaling problem disappears,
because the set is observed, not written down.

**The assumption that, if wrong, changes the plan most:** that the prefetch can be enqueued without the
present thread blocking. If it cannot, the cost moves to present pacing and we have made things worse.
Cheapest decisive test: a counter-only build that enqueues the flush and measures present-thread time,
with no behaviour change to reads.

**What an independent reviewer said this morning**, given the data and not my conclusion, included
exactly this: "turn the wait into a submit — flush the producing work the moment a read traps — or keep
a CPU-side copy of the hot GPU-written ranges so the read is answered without waiting". It also flagged
a confound I still cannot close: the five pool threads each gained nearly the same 4.0-5.8 ms a frame,
which is the signature of a shared serialisation point rather than independent per-thread work. If
there is one lock behind this, the prefetch helps anyway, but it is worth a targeted measurement.

**Collaborators:** no overlap. Vampinity is on memory, the driver cache and `guard=1` for flicker;
waveydude is on the memory wall (W-20 works). Vampinity's `EDEN_UP_AHEAD_READ_SYNC_AUTO` (0583) arms
read sync around a cut from black — a time axis, untested, and asked about in the drafted post.

## 6. Plan

**Off-console, no console needed:**

1. **Write 0934: prefetch the previous present's read-sync ranges at the present.** Enqueue 0930's
   batch flush on the GPU thread from the present site in `nx2_gsv.h`, behind
   `EDEN_GBB_READ_SYNC_PREFETCH=1`, off by default. Counters: ranges prefetched per present, reads
   answered with no wait, reads that still had to wait, and present-thread time spent enqueuing.
   **Decision rule:** if present-thread time per present rises by more than ~0.5 ms, stop and
   reconsider — that is the failure mode.
2. **Test 0923's `EDEN_GBB_MARK`** so runs can be compared by place. Two conclusions have been bent by
   route length today; this is cheap and overdue.

**Console runs, in order:**

3. **`runGA2`** — the audit on a different area, on gbb7, which now names its misses. Tells us how far
   the arena drifts, which sizes the prefetch set. One run.
4. **0934's three runs against `runRX`** (26.65, 26.65) for speed and `runRO` (19.30, 19.35) for
   flicker. **Decision rule:** within ~2 fps of RX and clean → this is the answer, and read sync stops
   being a tax. Still near 19 → the prefetch is not landing before the read, and the counters say so
   directly. Fast but flashing → the prefetch is racing the read; widen to two presents of lookahead.
5. **`runZ1-9`**, the blinded `FW`/`RX`/`RO` decider — the fallback, and still the only clean answer to
   "is read sync worth having at all". Worth running regardless once 0934 is settled, because
   `runFW1-3` at 21.65 / 21.33 / 20.85 is still faster than read sync's clean configuration.

**Parked:** every read-sync predicate variant; further escape tuning; the fixed region list; ASTC.

## 7. Decisions needed

1. **Build 0934 next, or run the blinded `runZ` set first?** Recommend 0934 — it is the only untried
   lever and the `runZ` set is a fallback that does not expire.
2. **0933 stays in the tree behind its switch, unset.** Its audit mode is the measurement that found
   all of this; the filter half should not be used. Recommend keeping it and saying so in the notes.
3. **Post the two drafts?** They now carry the fence-wait finding, which saves Vampinity and waveydude
   from trying the same three dead levers.
