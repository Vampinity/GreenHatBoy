# Read sync's cost is a fence wait, not work — so syncing less can never help

GrowingBlackBeans, 13 Nov 2026. Base PS5 13.60, t134-gbb4 to gbb7, Kokiri benchmark, Handheld 1x,
Faster CPU on, two frames ahead with waveydude's two-slot guard. Every run verified with
`checkrun.py` (env against the log's own `EDEN_GBB_ENV` dump, build from the boot trace).

## The finding

`EDEN_UP_AHEAD_READ_SYNC` (Vampinity's 0567) makes a guest read of a GPU-written range wait for the
presented frame's fence. **That wait is for an event, not for work.** The fence lands when the GPU
gets there. Changing how many reads queue up for it does not make it land sooner, so every patch that
reduces the number of synced reads leaves the cost where it was.

Three patches tried three different levers and all three measured flat:

| patch | lever | measured | fps change |
|---|---|---|---|
| 0930 `EDEN_GBB_READ_SYNC_ONCE` | sync once per present | syncs 76 -> 53 a frame (-28%) | +0.2 (`runRC1` 19.1 -> `runRO1/2` 19.30/19.35) |
| 0932 `EDEN_GBB_READ_SYNC_ESCAPE` | give up after 250 us instead of 2 ms | per wait 2.585 -> 0.590 ms (-77%) | +0.68, **and the flicker came back** |
| 0933 `EDEN_GBB_READ_SYNC_REGIONS` | sync only inside the hot regions | syncs 78.9 -> 33.3 a frame (-58%) | **+0.23** (`runGA1` 18.77 -> `runGR1` 19.00); the -0.35 printed here earlier was GR1 against RO, a different pair |

## The run that makes it unambiguous

`runGA1` and `runGR1` are the same build (01.219.922), same route, same env but one switch: GA1 syncs
every read (audit mode), GR1 syncs only those inside the two listed regions.

| | syncs/frame | fence waits/frame | summed wait/frame | us per wait | fps |
|---|---|---|---|---|---|
| `runGA1` | 78.9 | 30.3 | 77.65 ms | 2561 | 18.77 |
| `runGR1` | **33.3** | **28.7** | **72.31 ms** | **2520** | **19.00** |

A 58% cut in synced reads removed 1.6 fence waits a frame and 5 ms of summed wait. Nothing.

The ratio says why:

- `runGA1`: 30.3 waits of 78.9 syncs — **38%** of synced reads had to wait at all.
- `runGR1`: 28.7 waits of 33.3 syncs — **86%**.

**The reads the filter removed were the free ones.** They arrived after the fence had already passed
and cost nothing. The ones left are the ones that genuinely race, and they wait for the same fence at
the same wall-clock moment, so the total waiting is unchanged.

The same mechanism read from the other side, in the escape-dial runs: a long give-up lets the GPU
catch up, so later reads find the fence already passed; a short one never lets anything catch up, so
nearly every read waits.

| arm | escape | share of lookups taking a fence wait |
|---|---|---|
| `runDS1-3` | 2 ms | 38.7 / 38.3 / 38.3% |
| `runRO1`/`RO2` | 2 ms | 34.5 / 34.8% |
| `runRE1`/`RE2` | 250 us | **74.8 / 78.6%** |
| `runGR1` (region list) | 2 ms | **86.2%** |

Both the dial and the region list drive the same number up, and both leave the fps where it was.

## What this rules out

Any further patch of the form "sync fewer reads" or "sync them more cheaply". That is 0929, 0930, 0932
and 0933, and anything else that narrows the predicate. The predicate is not the cost.

## What is left

1. **Make the fence land sooner.** Submit the producing work when a read traps, instead of waiting for
   the normal submit point. Turns a wait into a submit.
2. **Do not wait at all.** Keep a CPU-side copy of the GPU-written ranges and answer the read from it.
3. **Do not be in the situation.** No lookahead: `runFW1-3` with `EDEN_NX2_FRAMES_AHEAD=0` ran
   21.65 / 21.33 / 20.85, which is *faster* than read sync's clean configuration and needs no patch.
   Different build and session, so that is a lead; the blinded `runZ1-9` set settles it.

## Where 0933 does earn its place

It is the wrong fix and the right foundation. A CPU-side shadow of the whole GPU-written address space
is absurd; a shadow of **two 4 MiB regions**, refreshed once a frame, is small and bounded, and those
regions hold 86% of the reads that currently block. The region list makes option 2 tractable.

Two conditions on that:

- **The list must be complete.** `runGA1`'s audit found **6 changed reads outside the list** of 1,586
  (99.6% coverage, not 100%). A shadow that misses a region is stale there, which is the flicker back
  again with nothing in the log. gbb7 (01.219.923) makes the audit name every miss by address;
  `runGA3` re-runs it.
- **The list must travel.** Both validations (`runDV1` 12 Nov, `runRC1` 13 Nov) are the same route and
  the same save. `runGA2` runs the audit on a different area to find out whether a fixed list scales at
  all. If it does not, the set has to be learned at runtime rather than written down (0929's granule
  table already has the machinery; key it on the flush area's base, which `RasterizerDownloadArea`
  already carries, and promote a granule when a sampled verify finds it changed).

## Corrections this supersedes

- **"About 77% of read sync's wait is the 2 ms escape, so the escape is the cost"** (posted in
  Discussion #2, 13 Nov). The arithmetic was right; the inference was wrong. That is summed wait across
  concurrent threads, and `runRC1` spent 72 ms of it inside a 52 ms frame, which cannot be serial.
- **"The cost is a per-read check paid by every read"** (13 Nov, after `runRD1`/`runRD2`). Over-stated.
  `runGR1` removed 58% of the syncs and the cost did not move, which a per-read check would not do
  either.
- **"GR1 should land near 23.4 fps"** (pre-registered before the run, from cost scaling with synced
  reads). It landed at 19.00. The model behind the prediction is what this document retires.

## By eye

`runGR1`, with only 44% of reads synced: **no flashes seen**, and smoother than `runRO`
(worst frame 158 ms against RO's 276 and 285).

**Retracted the same evening.** I wrote here that this showed a targeted list is enough for
correctness. `runGA3` shows it does not, and that `runGR1` simply did not reach the part of the route
where the list leaks: GR1's log ends at 194 s, and 51 of GA3's 52 misses happened after 200 s. A clean
rating from a run that stopped short of the problem is not a clean rating.

## `runGA3`: a fixed list does not work, and now we know why

Same build family, same env, same list, same route as `runGA1`, 17 s longer:

| run | log length | changed OUTSIDE |
|---|---|---|
| `runGA1` | 195 s | 6 |
| `runGA3` | 211 s | **52** |

Where the misses are is the point. All **52 of 52** sit immediately *below* the two listed regions:

| 1 MiB region of the miss | count | listed region it sits under |
|---|---|---|
| `0x30300000` | 51 | `0x30400000` |
| `0x2b500000` | 1 | `0x2b600000` |

And when: 1 miss at 172 s, then **40 in the 200-210 s window and 11 in 210-220 s** — a burst, in
territory the earlier runs never reached.

So the records are not at fixed addresses. They sit in an arena that extends *downward* as play goes
on, and which part of it is hot depends on where and how long you have played. A written-down list
will always be chasing it, which is a direct answer to the scaling question: **it does not scale, and
not because of a coverage percentage - because the hot set moves.**

The consolation is the shape. The misses are not scattered across the address space; they are 1 MiB
below, in one direction, in two clusters. A set learned at runtime, or simply a region that extends to
cover its own neighbours, has an easy target. Hardcoding is what is dead, not the idea.

## A second route confound in one day

`runGA1` vs `runGA3` differed only by 17 s of play, and that changed the headline number nine-fold.
Earlier the same day, `runRE1`'s door was at 160 s against `runRX2`'s 72 s. Two conclusions this
session have been bent by where and how long the route ran. 0923's `EDEN_GBB_MARK` (touchpad route
markers) is written and still untested; it should be tested before the next comparison, not after.

---

## Postscript, 13 Nov evening: what the anatomy found in an hour

The frame anatomy (`eglog/anatomy.py`, new today) run over `runRD1` and `runRD2` — runs that already
existed, no console time — put the week in proportion:

| | ms/frame | share of the 33.3 ms budget at 30 fps |
|---|---|---|
| Issuing `draw` (e0:0x585, 13,294 a frame at 1.182 us) | 15.69 | **47%** |
| All other back-thread commands | 11.86 | 36% |
| Everything else, including the host GPU's own 18.6 ms | 5.78 | 17% |

Read sync, which took three days and three rejected patches, was worth 7-8 fps and cancelled the
lookahead gain while doing it. **Draw issuing is 47% of the frame.** The lesson is not about read sync;
it is that we were optimising a stage we had never measured against a demand we had never counted.

Posted to GHB Discussion #5 (the measurement programme thread), 13 Nov.
