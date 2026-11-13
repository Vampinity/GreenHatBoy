# 2026-11-13-GP1

- **Build:** 01.219.925 (Nov 13 2026 20:08:50) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark route with four standing stops (A-D, docs/GrowingBlackBeans/kokiri-stops.md)
- **What the player saw:** Counts only: EDEN_GBB_GPFIFO=1. See docs/GrowingBlackBeans/gp1-four-stops-2026-11-13.md
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (99 env lines)

## Speed

65 play windows of 5 s, 26.2 fps mean; worst frame 383 ms. Era: ahead-1. Standing 23.4 fps (10 windows), walking 27.0 fps (52 windows, heavy share 0.00); door at 76 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 20 | 0.31 | 31.8 | 31.4 | 0.2 | 20.6 | 10.9 | 104 | 16.6 | 52% |
| queued | 41 | 0.63 | 24.1 | 41.5 | 0.4 | 35.6 | 16.6 | 165 | 25.2 | 60% |
| mid | 1 | 0.02 | 26.0 | 38.5 | 4.8 | – | – | – | – | – |
| heavy | 3 | 0.05 | 18.1 | 55.2 | 7.7 | 44.9 | 24.5 | 177 | 28.9 | 53% |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned one window before the end of the session.

## Front waits on the back, heavy windows

| Site | ms per frame | waits per frame | µs each |
|---|---|---|---|
| dma snapshot miss | 9.4 | 116 | 81 |
| list writers | 7.3 | 210 | 35 |
| acquire check | 5.0 | 132 | 38 |
| map | 1.7 | 5 | 348 |
| acquire poll | 0.9 | 69 | 13 |
| acquire recheck | 0.2 | 8 | 28 |

## Textures and memory

Texture churn per 600 frames (walking): 675 images created, 658 deleted, 488 uploads, 305 MiB.
Memory margins: out of memory in 230 of 301 lines (max 2560 MiB).

## Copy guard

93593 page copies per 5 s; pool peak 1172 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 82 | 383 | 16.7 | unattributed |
| 87 | 110 | 19.1 | unattributed |
| 92 | 354 | 18.6 | unattributed |
| 338 | 103 | 18.6 | unattributed |
| 403 | 360 | 26.0 | unattributed |

Shaders built while playing: 1 (2 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
