# t134-gbb8: the GPFIFO counter (patch 0934)

GrowingBlackBeans, 13 Nov 2026. **01.219.924**, in `EglantinePS5-package/t134-gbb8`, commit `18aa687`.
Symbols at `/work2/keep/t134-gbb8-llvm-pie.elf`. Built the documented development way with
`EDEN_SKIP_SOURCE_CHECKS=1`, as gbb1-gbb7 were. BUILD-EXIT=0; both the switch and the report line are
confirmed in the eboot.

| Switch | What |
|---|---|
| `EDEN_GBB_GPFIFO=1` | Log only, off by default. Per channel, every 10 s: GPFIFO entries parsed, the words those entries declare (`CommandListHeader::size`), and the command headers the parser produced from them, with words per entry and words per header. Unset: one relaxed load of a function-local static per parsed entry — no clock read, no atomics. |

## Why

The frame anatomy of 13 Nov found the back thread spending **27.55 ms of a 33.3 ms budget** on command
methods, **15.69 ms of it on `draw` alone** at 13,294 draws a frame. Every one of those numbers is
counted *inside* the emulator. Nothing we have counts what the game submitted, so there has been no way
to say whether that demand is the game's or ours.

This is the demand boundary, and it is the one counter the anatomy needs that the tree does not provide.

## The overlap check (standing rule, step 3)

Fetched `Vampinity/GreenHatBoy` (no new commits since `de83e37`), read the newest Discussion #2 comments,
searched `SWITCHES.md`, `BUILDS.md`, `CHANGELOG.md` and the source.

**Nearest prior art: `EDEN_NX2_FETCH_COUNT` (patch 0238, Vampinity, after kraibse's 2c9263140d).** It
walks the same entries through the same `RecordParsedEntry` hook, but it counts *where each entry's
words came from* and how often they differ from the words at submit — a correctness trace, reported at
a dump or a dropped word rather than periodically. It does not count entries or words per frame. So
0934 is new, and it sits deliberately next to 0238 in the same function and reuses its hook rather than
adding a second one. `EDEN_NX2_FETCH_RECHECK` and `EDEN_NX2_LIST_FAST` touch the same file for
unrelated reasons.

## What it answers

**GPFIFO words per frame against ring words per frame.** `EDEN_GBB_VITALS` already reports
`ring_kwords_s` on the back side. If the two are close, the game really is asking for about 130,000
commands a frame and M2 is a back-thread throughput problem on the draw path. If GPFIFO words are well
below ring words, something on the front is inflating them, and the work is somewhere none of us has
looked.

Ring words are about 1.11x methods today, so there is no amplification between the ring and the back.
The front is the only place left.

## Runs

`runGP1` to `runGP4`, one per fixed standing spot, each differing from the `runRX2` control by this one
switch. **Counts only: no `EDEN_GBB_BACK_CALLS`, no `EDEN_GBB_SVC_PROFILE`.** Counts survive
instrumentation and times do not, so the timers come in their own run later.

Stand still for at least 60 s at each spot. Standing windows repeat to within 1% (132 k ± 1 k methods a
frame), which is what makes places comparable and what the fit needs to separate marginal from fixed
cost — two runs on one route could not, and said so.

Decision rules:
1. **GPFIFO words within about 20% of ring words:** the demand is the game's. M2 is back-thread
   throughput, and the draw path is the work.
2. **GPFIFO words well below ring words:** the front is expanding them. Find where before anything else.
3. **Entries or words differ a lot between spots:** demand is a scene property, the per-place anatomy
   is required, and a single benchmark number was never going to be enough.
4. **The counter costs measurable fps:** it should not — it is three relaxed adds per entry — but if it
   does, the anatomy's counts-only runs need rethinking and that is worth knowing early.

## Not tested on a console

Host build only. The report path is exercised by the build, not by a run.
