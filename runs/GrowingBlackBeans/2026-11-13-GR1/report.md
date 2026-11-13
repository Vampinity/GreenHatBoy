# 2026-11-13-GR1

- **Build:** 01.219.922 (Nov 13 2026 16:40:33) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark: Continue, house, out, walk loop to the water
- **What the player saw:** t134-gbb6 patch 0933: region-limited read sync. No flashes seen; below 20 fps most of the run.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (100 env lines)

## Speed

22 play windows of 5 s, 19.0 fps mean; worst frame 158 ms. Era: ahead-1. Standing 19.7 fps (9 windows), walking 19.1 fps (9 windows, heavy share 0.00); door at 80 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 21 | 0.95 | 19.2 | 52.2 | 0.3 | 31.2 | 19.2 | 148 | 21.6 | 41% |
| queued | 0 | 0.00 | – | – | – | – | – | – | – | – |
| mid | 0 | 0.00 | – | – | – | – | – | – | – | – |
| heavy | 1 | 0.05 | 15.4 | 64.9 | 5.9 | 38.3 | 24.8 | 168 | 20.4 | 32% |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned at the end of the session.

## Front waits on the back, heavy windows

| Site | ms per frame | waits per frame | µs each |
|---|---|---|---|
| dma snapshot miss | 9.5 | 133 | 72 |
| acquire check | 6.5 | 140 | 46 |
| list writers | 6.3 | 223 | 28 |
| acquire poll | 1.3 | 212 | 6 |
| map | 1.0 | 5 | 192 |
| acquire recheck | 0.2 | 8 | 21 |

## Textures and memory

Texture churn per 600 frames (walking): 4010 images created, 3899 deleted, 2530 uploads, 2151 MiB.
Memory margins: out of memory in 20 of 136 lines (max 512 MiB).

## Copy guard

20623 page copies per 5 s; pool peak 535 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 85 | 158 | 15.4 | unattributed |
| 100 | 102 | 19.4 | unattributed |

Shaders built while playing: 0 (0 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
