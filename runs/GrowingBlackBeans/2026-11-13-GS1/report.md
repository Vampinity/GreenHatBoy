# 2026-11-13-GS1

- **Build:** 01.219.925 (Nov 13 2026 20:08:50) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark route with four standing stops (A-D, docs/GrowingBlackBeans/kokiri-stops.md)
- **What the player saw:** Counts: EDEN_GBB_GPFIFO=1 + EDEN_UP_SUBMIT_STATS=1; stop C moved back from the edge. See gs1-submissions-2026-11-13.md
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (100 env lines)

## Speed

62 play windows of 5 s, 25.6 fps mean; worst frame 281 ms. Era: ahead-1. Standing 23.6 fps (10 windows), walking 26.2 fps (49 windows, heavy share 0.02); door at 121 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 22 | 0.35 | 30.2 | 33.1 | 0.3 | 22.8 | 12.1 | 110 | 17.8 | 52% |
| queued | 36 | 0.58 | 23.5 | 42.6 | 0.4 | 35.7 | 17.3 | 161 | 24.7 | 58% |
| mid | 3 | 0.05 | 17.5 | 57.0 | 1.7 | 46.0 | 24.8 | 179 | 32.3 | 57% |
| heavy | 1 | 0.02 | 21.3 | 46.9 | 6.7 | 36.9 | 21.2 | 149 | 23.2 | 50% |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned one window before the end of the session.

## Front waits on the back, heavy windows

| Site | ms per frame | waits per frame | µs each |
|---|---|---|---|
| dma snapshot miss | 9.8 | 98 | 100 |
| list writers | 5.8 | 198 | 29 |
| acquire check | 3.7 | 126 | 30 |
| acquire poll | 0.8 | 90 | 9 |
| map | 0.7 | 3 | 285 |
| acquire recheck | 0.2 | 7 | 24 |

## Textures and memory

Texture churn per 600 frames (walking): 1327 images created, 1325 deleted, 1081 uploads, 648 MiB.
Memory margins: out of memory in 277 of 428 lines (max 3072 MiB).

## Copy guard

91342 page copies per 5 s; pool peak 1135 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 126 | 173 | 15.7 | unattributed |
| 302 | 116 | 23.0 | unattributed |
| 317 | 110 | 22.2 | unattributed |
| 327 | 117 | 22.6 | unattributed |
| 352 | 113 | 22.2 | unattributed |
| 357 | 281 | 21.3 | shaders built in play (14, 301 ms) |
| 362 | 100 | 25.6 | shaders built in play (6, 70 ms) |
| 367 | 138 | 18.0 | shaders built in play (13, 274 ms) |
| 372 | 145 | 18.9 | shaders built in play (8, 254 ms) |

Shaders built while playing: 43 (928 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
