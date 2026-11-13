# 2026-11-12-Play2Alt

- **Build:** 01.219.920 (Nov 12 2026 22:10:46) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** Free play (not the benchmark route)
- **What the player saw:** Two ahead, two slots, read sync with the pending check.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (100 env lines)

## Speed

9 play windows of 5 s, 20.2 fps mean; worst frame 413 ms. Era: ahead-1. Standing 23.4 fps (6 windows), walking – fps (0 windows, heavy share –); door at 72 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 5 | 0.56 | 20.2 | 49.5 | 0.3 | 28.7 | 17.5 | 122 | 18.5 | 35% |
| queued | 0 | 0.00 | – | – | – | – | – | – | – | – |
| mid | 3 | 0.33 | 22.6 | 44.3 | 3.8 | 22.0 | 13.9 | 90 | 16.0 | 35% |
| heavy | 1 | 0.11 | 12.8 | 78.1 | 15.2 | 41.0 | 31.3 | 104 | 27.4 | 35% |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned one window before the end of the session.

## Front waits on the back, heavy windows

| Site | ms per frame | waits per frame | µs each |
|---|---|---|---|
| dma snapshot miss | 16.5 | 43 | 386 |
| list writers | 8.2 | 223 | 37 |
| acquire check | 4.3 | 142 | 30 |
| acquire poll | 1.7 | 212 | 8 |
| map | 0.6 | 5 | 118 |

## Textures and memory

Texture churn per 600 frames (whole run): 747 images created, 555 deleted, 846 uploads, 981 MiB.
Memory margins: out of memory in 21 of 116 lines (max 1024 MiB).

## Copy guard

20550 page copies per 5 s; pool peak 659 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 77 | 413 | 12.8 | shaders built in play (4, 213 ms) |
| 88 | 115 | 25.4 | unattributed |
| 93 | 269 | 20.4 | shaders built in play (11, 179 ms) |
| 123 | 264 | 21.9 | shaders built in play (7, 227 ms) |
| 128 | 223 | 21.0 | shaders built in play (3, 66 ms) |
| 138 | 102 | 12.6 | unattributed |

Shaders built while playing: 28 (704 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
