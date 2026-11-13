# GrowingBlackBeans: notes

Base PS5, firmware 13.60, one standard route: Continue, through Link's house, out into Kokiri Village, a walking loop back to the water. About 3 minutes; standing ~76-130 s, walking after. Faster CPU emulation on.

- Runs: `runs/GrowingBlackBeans/` (132 runs since 7 Nov). Each `run.json` has the usual fields plus a `gbb` block with every 5 s window and the heavy/light split.
- Envs: `envs/GrowingBlackBeans/` (`everyday.env.txt` is what every unlabeled run starts from).
- Patches: `patches/GrowingBlackBeans/`. Tools: `tools/GrowingBlackBeans/` (`pack-gbb.py` packs a run into this layout with this repo's redaction).
- Builds: releases `gbb-t120-*`.
- Where the split back thread spends its time (sampler, 9 Nov) and ports from other forks: `back-thread-profile.md`.
- Session plans: `session-plan-2026-11-11.md`, `session-plan-2026-11-12.md`. Review of the 11-12 Nov night: `review-2026-11-12-night.md`.
- How close Kokiri is to the memory wall (1,055 runs): `memory-wall.md`.
- waveydude's runs (Lon Lon, Lost Woods, Kakariko, Dodongo's Cavern; 9.40 boots) read against ours: `waveydude-runs-2026-11-11.md`.
- Builds t120-gbb4 to gbb7 (untested), switches and how to test them: `builds-t120-gbb4-7.md`.
- Technical limits (what a base PS5 can ever do with this game): `technical-limits.md`. Second-opinion review: `review-2026-11-11-second-opinion.md`.

- **13 Nov, read sync:** why its cost cannot be narrowed away (`read-sync-is-a-fence-wait-2026-11-13.md`), the escape dial (`read-sync-escape-2026-11-13.md`), and why the saved frame grids hold no flicker signal (`flicker-is-not-brightness-2026-11-13.md`, **corrected** -- Vampinity's `tools/Vampinity/flash-counter/` is the real meter).
- **13 Nov, three review cycles:** `review-2026-11-13.md` (morning), `-evening.md`, `-night.md`. The night one carries the frame-anatomy plan and an addendum where an independent review rejected most of it.
- **13 Nov builds:** `build-t134-gbb5-escape-dial.md`, `build-t134-gbb6-region-list.md`, `build-t134-gbb8-gpfifo.md`.
- **Tools:** `tools/GrowingBlackBeans/eglog/` gains `anatomy.py` (demand against supply, per-method cost, the fit, a 30 fps budget), `guard.py` (the copy guard's own counters, unread in 77 runs until 13 Nov) and `flashdet.py` (**superseded** by Vampinity's flash-counter).

## Where we are (13 Nov)

**The frame is back-thread bound and draws dominate it.** From `runRD1`/`runRD2` with `anatomy.py`: the
back thread is 87-90% of every walking frame, and `draw` (register `e0:0x585`) runs **13,294 times a
frame at 1.182 us**, which is **15.69 ms -- 47% of a 33.3 ms budget at 30 fps** -- before the host GPU
draws anything. All other commands are 11.86 ms. Both runs carry about 12% of instrument overhead, so
treat the milliseconds as proportions.

**Two independent levers:** 13,294 draws a frame is the game's demand; 1.182 us each is ours. Whether
that count is the game's or inflated by our front end is what patch 0934 answers, and it has not run.

**Read sync is closed as a line of work.** Three patches, three levers, all flat: syncs -28% (0930),
per-wait -77% (0932), syncs -58% (0933). The cost is a wait for the frame's fence, which is an event,
so the predicate is not the lever. And the guard counters show read sync removes the second frame in
flight entirely, so its cost and the lost lookahead gain are one fact rather than two.

**Flicker is parked, and the instrument question is settled:** Vampinity's capture-video flash meter is
the only working one, it has run on 418 runs, and **none of them is a two-frames-ahead arm**. The
measurement nobody has taken is the one the argument needs.

**Still open:** `EDEN_UP_AHEAD_GUARD_ALL_WRITES=1` has never been set in any run, and it is the direct
test of whether the copy guard's exposure is harm. `runGW1` is prepared for it.

**Note on the 11 Nov section below:** its point 5 ("flashes near-gone with the guard") is wrong, and its
ring-word fit is the ancestor of `anatomy.py`. We had this topsight on 11 Nov and then stopped using it.

## Where we were (11 Nov)

**Everyday setup:** T120 + our patches, `everyday.env.txt` (includes `EDEN_UP_AHEAD_GUARD=3`, the NaN guard and invariant position, mask components/unwritten, trust copy trio, shader prep). Standing ~33 fps, walking ~24-25.

**What keeps the route below a stable 30** (all 128 runs, 2,403 play windows; regimes by the present's fence wait: light < 1 ms, heavy ≥ 5 ms):

1. **Heavy views, 54% of walking at ~21.6 fps: the GPU thread's per-frame work.** Frame time tracks GPU-thread ring words almost 1:1 (frame ≈ 15.7 ms + 0.213 ms per 1k words; back busy ≈ 0.229 ms per 1k words; 161k words per heavy frame vs 115k light). A heavy frame ≈ back busy (37.7 ms) + ~12 ms not overlapped with the front. The front waits ~23 ms per heavy frame in ~570 short handshakes (DMA snapshot misses 89/frame, list writers 192, acquire checks 125). Removing the present's full wait changes nothing (A3).
2. **Light views and standing: the game's own CPU chain sits at ~33 ms.** Frame time is flat at ~33.7 ms whatever the GPU work; no single guest thread is busy (main 8.6-10 ms/frame, workers 6-11), the frame is a chain of short jobs. JIT memory callbacks for GPU-tracked pages cost ~1 ms/frame each on main and pool A.
3. **Stutter:** 66% of play windows with a ≥100 ms frame have ≥50 ms of pipeline builds on the GPU thread; T120 runs build 11-50 pipelines in play and prep never converges (few hashes repeat between runs).
4. **Host GPU:** 15.8 ms per light frame, 25.7 per heavy (p90 31): the next wall after (1).
5. **Flashes:** near-gone with the guard; 0919 (`EDEN_GBB_GUARD_EARLY`) removes the stale reads left in heavy views; visual A/B pending.

**Next:** B2 (`EDEN_GBB_BACK_CALLS`, patch 0921) to name the back's cost per ring word; then cut back cost per draw (47% of 3D register writes are same-value) and improve front/back overlap; Path B for the game chain; guard-fix A/B.
