# 2026-11-13-RX2

- **Build:** 01.219.920 (Nov 12 2026 22:10:46) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark: Continue, house, out, walk loop to the water
- **What the player saw:** Two ahead, two slots, no read sync. Flashes.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (98 env lines)

## Speed

21 play windows of 5 s, 26.6 fps mean; worst frame 396 ms. Era: ahead-1. Standing 27.9 fps (10 windows), walking 26.4 fps (8 windows, heavy share 0.00); door at 72 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 7 | 0.33 | 26.5 | 37.8 | 0.3 | 27.6 | 17.8 | 126 | 23.2 | 61% |
| queued | 13 | 0.62 | 26.9 | 37.2 | 0.4 | 31.7 | 19.6 | 152 | 21.0 | 56% |
| mid | 0 | 0.00 | – | – | – | – | – | – | – | – |
| heavy | 1 | 0.05 | 24.8 | 40.3 | 7.0 | 32.8 | 20.7 | 148 | 21.7 | 54% |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned at the end of the session.

## Front waits on the back, heavy windows

| Site | ms per frame | waits per frame | µs each |
|---|---|---|---|
| dma snapshot miss | 7.1 | 114 | 62 |
| acquire check | 5.6 | 120 | 47 |
| list writers | 5.4 | 192 | 28 |
| map | 1.6 | 4 | 370 |
| acquire poll | 0.9 | 57 | 15 |
| acquire recheck | 0.2 | 7 | 24 |

## Textures and memory

Texture churn per 600 frames (walking): 1806 images created, 1800 deleted, 1273 uploads, 984 MiB.
Memory margins: out of memory in 0 of 156 lines (max 0 MiB).

## Copy guard

108076 page copies per 5 s; pool peak 1216 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 82 | 396 | 24.8 | unattributed |
| 133 | 142 | 25.8 | unattributed |
| 138 | 101 | 19.4 | unattributed |

Shaders built while playing: 0 (0 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
