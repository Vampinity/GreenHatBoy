# 2026-11-14-KS3

- **Build:** 01.219.925 (Nov 13 2026 20:08:50) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark route with four standing stops (A-D, docs/GrowingBlackBeans/kokiri-stops.md), scripted (tools/GrowingBlackBeans/steer/kokiri-four-stops)
- **What the player saw:** Scripted start 3 of 3: same script as KS2. All 12 STEER lines met; facing fingerprints at stand start A 95, B 80, C 86, D 60 (D after four search taps). Stand windows run from the start fingerprint (wait_skipped) to the end one.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (102 env lines)

## Speed

83 play windows of 5 s, 24.8 fps mean; worst frame 464 ms. Era: ahead-1. Standing 24.0 fps (10 windows), walking 25.1 fps (70 windows, heavy share 0.00); door at 97 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 22 | 0.27 | 32.1 | 31.2 | 0.2 | 22.1 | 11.7 | 107 | 17.8 | 55% |
| queued | 55 | 0.66 | 22.3 | 44.8 | 0.4 | 38.4 | 17.8 | 174 | 27.1 | 61% |
| mid | 3 | 0.04 | 20.9 | 47.8 | 2.7 | 40.6 | 22.8 | 156 | 25.6 | 53% |
| heavy | 3 | 0.04 | 20.4 | 48.9 | 9.5 | 41.4 | 24.7 | 151 | 24.4 | 48% |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned at the end of the session.

## Front waits on the back, heavy windows

| Site | ms per frame | waits per frame | µs each |
|---|---|---|---|
| dma snapshot miss | 12.4 | 93 | 133 |
| list writers | 6.5 | 197 | 33 |
| acquire check | 3.7 | 126 | 29 |
| map | 1.1 | 4 | 321 |
| acquire poll | 0.8 | 94 | 8 |
| acquire recheck | 0.2 | 7 | 26 |

## Textures and memory

Texture churn per 600 frames (walking): 774 images created, 763 deleted, 590 uploads, 499 MiB.
Memory margins: out of memory in 315 of 417 lines (max 3072 MiB).

## Copy guard

97214 page copies per 5 s; pool peak 1091 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 102 | 333 | 14.1 | unattributed |
| 107 | 464 | 25.5 | unattributed |
| 127 | 271 | 21.7 | unattributed |
| 353 | 174 | 19.0 | shaders built in play (9, 149 ms) |
| 358 | 233 | 22.9 | shaders built in play (15, 317 ms) |
| 368 | 144 | 22.7 | shaders built in play (6, 95 ms) |
| 378 | 163 | 20.9 | shaders built in play (4, 220 ms) |
| 388 | 111 | 20.7 | unattributed |
| 519 | 120 | 20.8 | unattributed |

Shaders built while playing: 43 (953 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
