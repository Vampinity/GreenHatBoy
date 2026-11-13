# waveydude

Base PS5 on 13.60 (and a 9.40 Digital). I build on Vampinity's T120 with my hybrid series; builds are `W-<n>`, branches on `waveydude/Eglantine-PS5-`. My patches and switches: `patches/waveydude/README.md`. My runs: `runs/waveydude/`.

| Date | Note | Status |
|---|---|---|
| 12 Nov | [Two-frame guard (0927) on my console, and the title freeze](two-frame-guard-2026-11-12.md) | Done: works, no flicker seen; load wait fixes the title freeze |
| 13 Nov | [The ~1 s stall stretches: the driver pipeline cache write](stalls-driver-cache-2026-11-13.md) | Fix built (0931, W-13), not run yet |
| 13 Nov | [The memory wall: the pool was not full, it was full of holes (in-place packing)](pool-holes-in-place-pack-2026-11-13.md) | Fix built and installed (W-20, `EDEN_GUEST_SWAP_PACK_IN_PLACE=2`), not run yet |
