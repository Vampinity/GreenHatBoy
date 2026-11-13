# 2026-11-13-RO2

- **Build:** 01.219.920 (Nov 12 2026 22:10:46) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark: Continue, house, out, walk loop to the water
- **What the player saw:** Read sync once (2 ms escape). Clean by eye.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (100 env lines)

## Speed

24 play windows of 5 s, 19.4 fps mean; worst frame 276 ms. Era: ahead-1. Standing 19.8 fps (9 windows), walking 19.0 fps (12 windows, heavy share 0.00); door at 96 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 23 | 0.96 | 19.4 | 51.7 | 0.3 | 31.5 | 18.7 | 146 | 20.6 | 40% |
| queued | 0 | 0.00 | – | – | – | – | – | – | – | – |
| mid | 0 | 0.00 | – | – | – | – | – | – | – | – |
| heavy | 1 | 0.04 | 19.4 | 51.5 | 5.9 | 31.8 | 18.3 | 146 | 18.6 | 36% |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned at the end of the session.

## Front waits on the back, heavy windows

| Site | ms per frame | waits per frame | µs each |
|---|---|---|---|
| dma snapshot miss | 6.5 | 112 | 58 |
| acquire check | 5.5 | 119 | 46 |
| list writers | 4.6 | 190 | 24 |
| acquire poll | 1.0 | 183 | 5 |
| map | 0.6 | 5 | 102 |
| acquire recheck | 0.1 | 7 | 20 |

## Textures and memory

Texture churn per 600 frames (walking): 1827 images created, 1855 deleted, 1268 uploads, 1042 MiB.
Memory margins: out of memory in 80 of 137 lines (max 768 MiB).

## Copy guard

21828 page copies per 5 s; pool peak 599 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 106 | 118 | 18.3 | unattributed |
| 111 | 276 | 19.4 | unattributed |
| 121 | 100 | 19.9 | unattributed |
| 177 | 105 | 16.4 | unattributed |

Shaders built while playing: 0 (0 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
