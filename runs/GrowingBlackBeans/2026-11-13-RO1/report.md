# 2026-11-13-RO1

- **Build:** 01.219.920 (Nov 12 2026 22:10:46) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark: Continue, house, out, walk loop to the water
- **What the player saw:** Read sync once (2 ms escape). Clean by eye.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (100 env lines)

## Speed

22 play windows of 5 s, 19.3 fps mean; worst frame 285 ms. Era: ahead-1. Standing 19.6 fps (10 windows), walking 18.9 fps (10 windows, heavy share 0.00); door at 72 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 21 | 0.95 | 19.4 | 51.5 | 0.3 | 31.1 | 18.5 | 145 | 21.0 | 41% |
| queued | 0 | 0.00 | – | – | – | – | – | – | – | – |
| mid | 0 | 0.00 | – | – | – | – | – | – | – | – |
| heavy | 1 | 0.05 | 17.3 | 57.8 | 6.1 | 36.2 | 23.9 | 134 | 21.1 | 37% |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned at the end of the session.

## Front waits on the back, heavy windows

| Site | ms per frame | waits per frame | µs each |
|---|---|---|---|
| dma snapshot miss | 9.0 | 106 | 84 |
| list writers | 6.1 | 175 | 35 |
| acquire check | 5.5 | 110 | 50 |
| map | 1.9 | 6 | 342 |
| acquire poll | 1.1 | 163 | 7 |
| acquire recheck | 0.1 | 6 | 22 |

## Textures and memory

Texture churn per 600 frames (walking): 2352 images created, 2390 deleted, 1684 uploads, 1116 MiB.
Memory margins: out of memory in 0 of 141 lines (max 0 MiB).

## Copy guard

24596 page copies per 5 s; pool peak 558 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 82 | 285 | 17.3 | unattributed |
| 142 | 102 | 14.8 | unattributed |

Shaders built while playing: 0 (0 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
