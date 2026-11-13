# 2026-11-13-RX1

- **Build:** 01.219.920 (Nov 12 2026 22:10:46) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark: Continue, house, out, walk loop to the water
- **What the player saw:** Two ahead, two slots, no read sync. Flashes.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (98 env lines)

## Speed

24 play windows of 5 s, 26.6 fps mean; worst frame 358 ms. Era: ahead-1. Standing 27.8 fps (10 windows), walking 25.5 fps (11 windows, heavy share 0.00); door at 72 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 6 | 0.25 | 27.1 | 36.8 | 0.3 | 28.3 | 18.2 | 128 | 21.3 | 57% |
| queued | 17 | 0.71 | 26.6 | 37.6 | 0.4 | 32.1 | 20.1 | 151 | 21.3 | 56% |
| mid | 0 | 0.00 | – | – | – | – | – | – | – | – |
| heavy | 1 | 0.04 | 24.9 | 40.2 | 6.7 | 33.0 | 20.9 | 147 | 19.1 | 48% |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned at the end of the session.

## Front waits on the back, heavy windows

| Site | ms per frame | waits per frame | µs each |
|---|---|---|---|
| dma snapshot miss | 6.9 | 112 | 62 |
| list writers | 6.3 | 191 | 33 |
| acquire check | 5.9 | 120 | 49 |
| acquire poll | 0.9 | 54 | 16 |
| map | 0.7 | 4 | 157 |
| acquire recheck | 0.2 | 7 | 26 |

## Textures and memory

Texture churn per 600 frames (walking): 1850 images created, 1691 deleted, 1280 uploads, 909 MiB.
Memory margins: out of memory in 110 of 168 lines (max 1024 MiB).

## Copy guard

111212 page copies per 5 s; pool peak 1074 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 82 | 358 | 24.9 | unattributed |

Shaders built while playing: 0 (0 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
