# 2026-11-13-RD1

- **Build:** 01.219.921 (Nov 13 2026 11:13:19) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark: Continue, house, out, walk loop to the water
- **What the player saw:** Profiler pair: two ahead + EDEN_GBB_BACK_CALLS + EDEN_GBB_SVC_PROFILE (timers inflate times about 12% on top of the back-call timer's 25%).
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GBB_BACK_CALLS=1`, `EDEN_GBB_SVC_PROFILE=86,152,153,154,155,156,157,158,159,160,161,162`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (101 env lines)
- **Measurement cost in this run:** EDEN_GBB_SVC_PROFILE (per-SVC timing: small). Compare fps only with runs that have the same.

## Speed

23 play windows of 5 s, 23.1 fps mean; worst frame 393 ms. Era: ahead-1. Standing 24.5 fps (9 windows), walking 22.4 fps (10 windows, heavy share 0.00); door at 83 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 1 | 0.04 | 19.5 | 51.3 | 0.4 | – | – | – | – | – |
| queued | 21 | 0.91 | 23.6 | 42.4 | 0.3 | 38.5 | 25.9 | 146 | 20.7 | 49% |
| mid | 0 | 0.00 | – | – | – | – | – | – | – | – |
| heavy | 1 | 0.04 | 15.5 | 64.5 | 11.3 | 55.8 | 38.0 | 190 | 31.1 | 49% |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned one window before the end of the session.

## Front waits on the back, heavy windows

| Site | ms per frame | waits per frame | µs each |
|---|---|---|---|
| dma snapshot miss | 14.6 | 149 | 98 |
| acquire check | 10.6 | 158 | 67 |
| list writers | 10.2 | 251 | 41 |
| acquire poll | 1.3 | 67 | 19 |
| map | 0.9 | 7 | 137 |
| acquire recheck | 0.3 | 9 | 31 |

## Game threads (ms per frame outside SVCs, play)

t152 11.1, t86 10.4, t159 9.6, t154 9.1, t157 8.8, t158 8.2, t155 8.1, t162 8.1

## Textures and memory

Texture churn per 600 frames (walking): 2052 images created, 2045 deleted, 1384 uploads, 1094 MiB.
Memory margins: out of memory in 0 of 154 lines (max 0 MiB).

## Copy guard

108444 page copies per 5 s; pool peak 1032 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 88 | 393 | 15.5 | unattributed |
| 93 | 105 | 21.6 | unattributed |
| 153 | 113 | 19.4 | unattributed |
| 158 | 104 | 18.4 | unattributed |

Shaders built while playing: 0 (0 ms).

## What this run cannot tell you

Missing: nothing from the standard set.
