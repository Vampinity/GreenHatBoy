# GrowingBlackBeans: notes

Base PS5, firmware 13.60, one standard route: Continue, through Link's house, out into Kokiri Village, a walking loop back to the water. About 3 minutes; standing ~76-130 s, walking after. Faster CPU emulation on.

- Runs: `runs/GrowingBlackBeans/` (132 runs since 7 Nov). Each `run.json` has the usual fields plus a `gbb` block with every 5 s window and the heavy/light split.
- Envs: `envs/GrowingBlackBeans/` (`everyday.env.txt` is what every unlabeled run starts from).
- Patches: `patches/GrowingBlackBeans/`. Tools: `tools/GrowingBlackBeans/` (`pack-gbb.py` packs a run into this layout with this repo's redaction).
- Builds: releases `gbb-t120-*`.

## Where we are (11 Nov)

**Everyday setup:** T120 + our patches, `everyday.env.txt` (includes `EDEN_UP_AHEAD_GUARD=3`, the NaN guard and invariant position, mask components/unwritten, trust copy trio, shader prep). Standing ~33 fps, walking ~24-25.

**What keeps the route below a stable 30** (all 128 runs, 2,403 play windows; regimes by the present's fence wait: light < 1 ms, heavy ≥ 5 ms):

1. **Heavy views, 54% of walking at ~21.6 fps: the GPU thread's per-frame work.** Frame time tracks GPU-thread ring words almost 1:1 (frame ≈ 15.7 ms + 0.213 ms per 1k words; back busy ≈ 0.229 ms per 1k words; 161k words per heavy frame vs 115k light). A heavy frame ≈ back busy (37.7 ms) + ~12 ms not overlapped with the front. The front waits ~23 ms per heavy frame in ~570 short handshakes (DMA snapshot misses 89/frame, list writers 192, acquire checks 125). Removing the present's full wait changes nothing (A3).
2. **Light views and standing: the game's own CPU chain sits at ~33 ms.** Frame time is flat at ~33.7 ms whatever the GPU work; no single guest thread is busy (main 8.6-10 ms/frame, workers 6-11), the frame is a chain of short jobs. JIT memory callbacks for GPU-tracked pages cost ~1 ms/frame each on main and pool A.
3. **Stutter:** 66% of play windows with a ≥100 ms frame have ≥50 ms of pipeline builds on the GPU thread; T120 runs build 11-50 pipelines in play and prep never converges (few hashes repeat between runs).
4. **Host GPU:** 15.8 ms per light frame, 25.7 per heavy (p90 31): the next wall after (1).
5. **Flashes:** near-gone with the guard; 0919 (`EDEN_GBB_GUARD_EARLY`) removes the stale reads left in heavy views; visual A/B pending.

**Next:** B2 (`EDEN_GBB_BACK_CALLS`, patch 0921) to name the back's cost per ring word; then cut back cost per draw (47% of 3D register writes are same-value) and improve front/back overlap; Path B for the game chain; guard-fix A/B.
