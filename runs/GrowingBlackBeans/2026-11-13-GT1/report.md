# 2026-11-13-GT1

- **Build:** 01.219.925 (Nov 13 2026 20:08:50) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark route with four standing stops (A-D, docs/GrowingBlackBeans/kokiri-stops.md)
- **What the player saw:** Timers only: EDEN_GBB_BACK_CALLS=1. See gt1-cost-per-draw-2026-11-13.md
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GBB_BACK_CALLS=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (99 env lines)

## Speed

64 play windows of 5 s, 23.0 fps mean; worst frame 400 ms. Era: ahead-1. Standing 20.3 fps (10 windows), walking 23.7 fps (51 windows, heavy share 0.00); door at 76 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 14 | 0.22 | 31.8 | 31.4 | 0.2 | 22.7 | 15.0 | 92 | 15.3 | 49% |
| queued | 47 | 0.73 | 20.9 | 47.9 | 0.4 | 45.0 | 30.7 | 163 | 25.1 | 52% |
| mid | 1 | 0.02 | 18.8 | 53.2 | 1.0 | 49.9 | 33.9 | 178 | 28.3 | 53% |
| heavy | 2 | 0.03 | 13.1 | 76.3 | 15.8 | 71.0 | 52.2 | 200 | 36.0 | 47% |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned one window before the end of the session.

## Front waits on the back, heavy windows

| Site | ms per frame | waits per frame | µs each |
|---|---|---|---|
| dma snapshot miss | 25.7 | 117 | 219 |
| acquire check | 11.8 | 140 | 84 |
| list writers | 10.1 | 221 | 46 |
| acquire poll | 2.2 | 61 | 36 |
| map | 2.1 | 8 | 262 |
| acquire recheck | 0.3 | 8 | 34 |

## Textures and memory

Texture churn per 600 frames (walking): 1422 images created, 1402 deleted, 1188 uploads, 540 MiB.
Memory margins: out of memory in 255 of 323 lines (max 3072 MiB).

## Copy guard

94460 page copies per 5 s; pool peak 1235 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 81 | 400 | 14.4 | unattributed |
| 86 | 238 | 11.8 | unattributed |
| 101 | 141 | 21.5 | unattributed |
| 247 | 103 | 19.2 | unattributed |
| 332 | 107 | 16.5 | unattributed |
| 342 | 130 | 18.7 | unattributed |
| 352 | 130 | 18.7 | unattributed |
| 383 | 129 | 18.8 | unattributed |
| 398 | 118 | 17.9 | unattributed |

Shaders built while playing: 2 (16 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE).
