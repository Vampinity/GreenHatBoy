# 2026-11-13-RD2

- **Build:** 01.219.921 (Nov 13 2026 11:13:19) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark: Continue, house, out, walk loop to the water
- **What the player saw:** Profiler pair: read sync once with 250 us escape + EDEN_GBB_BACK_CALLS + EDEN_GBB_SVC_PROFILE.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GBB_BACK_CALLS=1`, `EDEN_GBB_SVC_PROFILE=86,152,153,154,155,156,157,158,159,160,161,162`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (104 env lines)
- **Measurement cost in this run:** EDEN_GBB_SVC_PROFILE (per-SVC timing: small). Compare fps only with runs that have the same.

## Speed

23 play windows of 5 s, 18.3 fps mean; worst frame 185 ms. Era: ahead-1. Standing 18.8 fps (10 windows), walking 18.1 fps (10 windows, heavy share 0.00); door at 81 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 18 | 0.78 | 18.7 | 53.4 | 0.3 | 38.5 | 25.6 | 145 | 20.7 | 39% |
| queued | 4 | 0.17 | 17.3 | 57.7 | 0.4 | 48.5 | 33.5 | 166 | 26.8 | 47% |
| mid | 0 | 0.00 | – | – | – | – | – | – | – | – |
| heavy | 1 | 0.04 | 15.1 | 66.2 | 5.2 | 39.4 | 28.2 | 95 | 22.2 | 34% |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned at the end of the session.

## Front waits on the back, heavy windows

| Site | ms per frame | waits per frame | µs each |
|---|---|---|---|
| dma snapshot miss | 10.2 | 73 | 140 |
| list writers | 8.3 | 137 | 61 |
| acquire check | 7.4 | 88 | 84 |
| acquire poll | 1.3 | 115 | 11 |
| map | 0.6 | 5 | 128 |
| list flush | 0.2 | 0 | 767 |
| acquire recheck | 0.1 | 6 | 19 |

## Game threads (ms per frame outside SVCs, play)

t152 17.3, t86 16.9, t154 13.7, t153 13.5, t155 12.4, t156 11.9, t159 10.0, t157 8.7

## Textures and memory

Texture churn per 600 frames (walking): 2879 images created, 2794 deleted, 1976 uploads, 1453 MiB.
Memory margins: out of memory in 28 of 141 lines (max 2560 MiB).

## Copy guard

95781 page copies per 5 s; pool peak 1014 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 86 | 185 | 15.1 | unattributed |
| 151 | 111 | 16.0 | unattributed |
| 156 | 106 | 16.7 | unattributed |

Shaders built while playing: 0 (0 ms).

## What this run cannot tell you

Missing: nothing from the standard set.
