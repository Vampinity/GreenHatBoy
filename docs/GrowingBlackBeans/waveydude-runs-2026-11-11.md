# waveydude's runs, read with the toolkit

GrowingBlackBeans, 11 Nov 2026. waveydude's four 13.60 runs and two 9.40 boots (`runs/waveydude/`), set against our T120 Kokiri runs (R120a/b, g1/g2). Their settings: 0.75× resolution, Faster CPU emulation off, Handheld; FSR 3 frame generation 2× in runs 2-4 (fps counts native frames). Ours: 1×, Faster CPU on, no frame generation. Different areas, routes and builds, so read this as comparisons across conditions, not A/Bs.

| Run | Minutes | Heavy share | Queued share | Light fps | Queued fps | Heavy fps | Back per heavy frame (ms) | Ring k words per heavy frame | Shaders built per minute | of them on disk | Least free memory | Heap peak |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| wd astc-crash (Lon Lon, no frame gen) | 7.6 | 73% | 3% | 27.2 | 27.6 | 17.5 | 43.1 | 148 | 49 | 30% | 1 MiB | 992 MiB |
| wd lost-woods (frame gen) | 19.7 | 61% | 14% | 32.7 | 26.9 | 20.6 | 44.8 | 79 | 18 | 42% | 1 MiB | 1,184 MiB |
| wd kakariko (frame gen) | 3.6 | 79% | 9% | 30.1 | 30.0 | 18.9 | 48.9 | 94 | 70 | 53% | 1 MiB | 960 MiB |
| wd dodongos-cavern (frame gen) | 17.7 | 47% | 24% | 34.2 | 31.6 | 22.3 | 41.2 | 92 | 22 | 44% | 1 MiB | 1,184 MiB |
| ours R120a/b, g1/g2 (Kokiri) | ~2 each | 20-38% | 0% | 30.5-32.7 | - | 20.1-22.5 | 34.0-38.5 | 151-162 | 6-23 | 48-81% | 177-288 MiB | 1,120-1,152 MiB |

"Minutes" is play time (5 s windows). Heavy = present fence wait ≥ 5 ms; queued = no wait but the back over 80% busy (see `tools/GrowingBlackBeans/eglog/LOGS.md`).

## What they show

1. **Heavy views aren't a Kokiri quirk.** Lon Lon Ranch, Lost Woods, Kakariko and Dodongo's Cavern spend 47-79% of play in heavy windows, at 17.5-22.3 fps. That's the same band as our Kokiri walk (20-22.5). The GPU-side cost per frame is the game-wide problem.
2. **The "queued" regime is real.** No present wait, but the back over 80% busy: 3-24% of their play windows (Dodongo's Cavern 24%), at 27-32 fps. It never shows on our Kokiri route. Classifying by present wait alone would have filed these as game-CPU-bound.
3. **Faster CPU emulation off didn't sink the light windows.** They run 27-34 fps light at 0.75× with it off, against our 30.5-32.7 with it on. That fits our earlier +0.5-2.5 fps for the switch. It still matters for comparisons, but it isn't a large lever.
4. **The back costs more per unit of work in the frame-generation runs.** The ratio of back busy per heavy frame to ring words per heavy frame comes out as:

   | Runs | Back time per ring word |
   |---|---|
   | waveydude, frame generation on (2-4) | 0.45-0.57 µs |
   | waveydude, no frame generation (1) | 0.29 µs |
   | ours, no frame generation | 0.22-0.24 µs |

   It's confounded: the frame-generation runs are also in other areas with fewer words per frame. But if frame generation's work lands on the split's back thread, or on its core, it costs native fps in exactly the heavy views. Worth one A/B in the same place: frame generation on against off.
5. **Shaders built while playing are worse in new areas.** They build 18-70 per minute of play, and only 30-53% of those were on disk; the rest are new or mesh pipelines met for the first time. Preload and Vampinity's T129 fix remove the on-disk part. First visits still stall, which only background translation (or a pre-seeded cache) avoids.
6. **They live at the memory wall.** Every 13.60 run touched 1 MiB free, with the heap peaking at 0.96-1.18 GB and driver memory at 3.3-3.5 GB (lower than our 3.5-3.8 at 1×). The crashes were single big requests (32 MiB ASTC scratch, 62 MiB JIT table), which matches the arena finding: free room in other threads' arenas, and big requests that never ask them.

## Update: frame generation tested, and heap.log added

waveydude ran the same spot both ways (Kakariko, same build and settings, 0.75×, only frame generation changed). Two short sessions:

| | Frame gen on (2×) | Frame gen off |
|---|---|---|
| Native fps | 11-12 | 22-28 |
| Wait at present | 41-64 ms | 0-4 ms |

Frame generation roughly halves native fps in a heavy view, and with it on, old frames reached the screen at 12-20 native fps. That fits point 4 (the back's cost per unit of work doubling in the frame-generation runs).

`heap.log` (with `EDEN_GPU_TIME`) is now in each 13.60 run (`heap.log.gz`). Host GPU time per heavy frame, from the emulator's own submissions:

| Run | Host GPU per heavy frame | Host GPU busy (heavy) |
|---|---|---|
| Lon Lon, no frame gen | 27.0 ms | 45% |
| Lost Woods, frame gen | 15.7 ms | 31% |
| Kakariko, frame gen | 19.6 ms | 31% |
| Dodongo's Cavern, frame gen | 16.6 ms | 33% |

So in the frame-generation runs the host GPU sits about a third busy: the halving isn't GPU throughput, at least not in what the probe counts. Frame generation's own GPU work may not go through these submissions. The present wait grows instead, which points at the frame-generation path holding up the present or the GPU side's thread.

waveydude also tried preloading every pipeline: 8,657 built at boot against 4,681, and the heap grew 416 MiB in blocks under 256 KiB against 128 MiB. Preloading everything scales with the size of the shader cache, so it gets costlier the further a player gets. A narrower fix (Vampinity's refused-translation fix, a longer used-list life) ages better.

## Toolkit notes

- These builds write `EDEN_GPU_TIME` to `heap.log`, which wasn't in the bundle. The checker now looks in `heap.log` too and only notes the lines as missing, instead of failing the run (fix in `eglog.py` / `checkrun.py`).
- The door-based standing and walking phases and the era guess are for our hand-played Kokiri route. On long hand-played sessions through other areas they're meaningless, so use the regimes instead.
