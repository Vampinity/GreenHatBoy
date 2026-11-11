# How well can Ocarina of Time (Switch 2) ever run on a base PS5?

GrowingBlackBeans, 11 Nov 2026. Revised after the second-opinion review (`review-2026-11-11-second-opinion.md`). Read it skeptically. The hardware figures for the PS5 are solid; the Switch 2 figures are approximate; the emulation ratios are estimates, and the "what would change this" list says how to check each one.

## The two machines

| | Base PS5 | Switch 2 (approximate) | Ratio |
|---|---|---|---|
| CPU | 8 × Zen 2, up to 3.5 GHz, SMT; a game gets about 6.5-7 cores | 8 × Cortex-A78C, about 1 GHz in games, about 6 cores for the game | about 3.5× clock per core, similar work per clock |
| GPU | RDNA2, 36 CUs, 2.23 GHz, about 10.3 TFLOPS | Ampere, 1536 CUDA cores, about 1 GHz docked, about 3 TFLOPS on paper | about 3-4× raw |
| Memory | 16 GB GDDR6 shared, 448 GB/s; a title gets about 12.5 GB | 12 GB LPDDR5X, about 100 GB/s; most of it for the game | about 1×, no headroom |
| GPU command processing | must be emulated on the CPU | dedicated hardware | pure added cost |

On paper the PS5 is the bigger machine. Emulation costs differ by subsystem, though.

## CPU: probably already near the real console's speed per thread

- Translating ARM code to x86 at run time typically costs about 2-4× per instruction. The 3.5× clock advantage roughly cancels it, so each emulated core runs at roughly 0.9-1.7× real Switch 2 speed (an estimate, not a measurement).
- Measured: in light views the game's own chain takes about 31-34 ms per frame, whatever the GPU work. No guest thread is busy on its own; guest cores are about 55% used. The frame is a chain of short jobs handed between threads.
- The game's frame pacing settles at about 33 ms and 50 ms (two and three 60 Hz refreshes), which fits a game built for 30 fps with a fall-back to 20. This is inference, and the first thing to check (see the list at the end).
- Cores: 6 emulated cores, plus the GPU front, back and fencing threads, shader builders, decoding and audio, adds up to 10 or more busy threads on about 7 cores. SMT siblings compete, typically 20-30% each. There's no spare core budget.
- Realistic CPU headroom: about 10-25% (JIT memory callbacks about 2 ms per frame, about 130 short yields per frame per thread, thread placement). Doubling isn't realistic: it means running the game's logic twice as fast as the real Switch 2 does, on a Zen 2.

## GPU: plenty of theoretical headroom, overhead in practice

- Measured at 1080p internal (both datasets render 1920×1080 and scale to 1440p): about 15.3-15.8 ms of host GPU time per light frame and about 26 ms per heavy one (p90 31). The host GPU is never more than 67% busy in any 5 s window.
- For a GPU 3-4× faster on paper, that is inefficient. The costs: texture formats the PS5 can't sample decoded or converted, mesh shading emulated with compute, about 60 GPU-to-CPU copy-backs per frame, dozens of submissions, and synchronisation the real hardware doesn't need. All of these are engineering, not physics.

## GPU command processing: our biggest cost, and not a physical limit

- On the Switch 2, dedicated hardware processes the command lists. Here the split GPU thread's front and back do it in software: about 1,000-2,500 draws per frame at roughly 20 µs each on the back.
- Well-tuned PC drivers spend about 1-5 µs per draw; a PS5 core is perhaps 60-70% of a current desktop core. A realistic floor here is roughly 6-10 µs per draw: 12-20 ms for a 2,000-draw heavy frame. That fits 30 fps comfortably and only just fits 60.
- In heavy views nothing is saturated: back about 77% busy, front about 45%, host GPU about 56%. They run one after another behind a present that keeps only one frame in flight. That is a pipeline-depth and per-draw-cost problem, which the emulator can change.

## Memory: the immovable wall for "everywhere"

- The Switch 2 gives the game up to about 12 GB; the PS5 gives a title about 12.5 GB. The emulator must hold the game's memory, plus host copies of textures and buffers (decoded textures are larger), plus its own code and caches.
- Memory margins already dip into "out of memory" in about half the runs in both datasets, Kokiri included. Bigger areas (Castle Town, the field) already crash for testers.
- Swap, streaming and eviction push the wall back, at the cost of hitches. RAM is the one constraint no engineering removes.

## Expectations

| Target | Expectation | Confidence | Why |
|---|---|---|---|
| Stable 30 in Kokiri | Achievable | Moderately high, a little higher after the review | Every stage has measured headroom against 33 ms and nothing is saturated in heavy views. The work: cheaper draws on the back, a deeper present, about 10% off the game chain, boot prep that builds what's on disk. |
| 30 in most of the game (field, villages, dungeons) | Likely, with dips | Medium | Draw counts and memory rise. The PS5 Pro (same CPU at 3.85 GHz, bigger GPU) reportedly averages 29-34 in the house: a hint, not proof. |
| 30 everywhere, including Castle Town and set pieces | Uncertain | Low to medium, slightly lower after the review | Memory is the wall, and we already touch it in Kokiri. |
| 60 in gameplay | Very unlikely | High | Needs the game chain at 16.7 ms, faster than the real Switch 2 if the game targets 30, and likely a game patch. A deeper pipeline overlaps frames but can't shorten the game's own 33 ms. |
| 60 in cutscenes and menus | Already happens | Measured | The intro is paced at 60. |

A trade-off to keep in mind: every extra frame in flight adds about 33 ms of input lag at 30 fps. A two-frames-ahead present buys fps in heavy views with some responsiveness.

## What would change this assessment

1. **What frame rate the Switch 2 version targets.** If it's 60 on Switch 2, the pacing reading is wrong, its native budget per frame is half, and our ceiling rises.
2. **How many cores and SMT threads the PS5 gives this process,** and where our threads land. Measurable with a thread-placement log.
3. **The real JIT ratio** (host time per guest instruction). A sampler run can estimate it and replace the 2-4× guess.
4. **How much memory the process can actually use,** and how close Kokiri already is. The memory census in stderr has much of this.
