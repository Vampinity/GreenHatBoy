# 2026-11-14-KS1

- **Build:** 01.219.925 (Nov 13 2026 20:08:50) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark route with four standing stops (A-D, docs/GrowingBlackBeans/kokiri-stops.md), scripted (tools/GrowingBlackBeans/steer/kokiri-four-stops)
- **What the player saw:** Scripted start 1 of 3: GS1 counts (EDEN_GBB_GPFIFO=1 + EDEN_UP_SUBMIT_STATS=1) plus EDEN_TEST_SCRIPT=kokiri-four-stops.txt and EDEN_TEST_DISCARD_SAVE=1; no hands on the pad. First script version (one turn tap per stop, no search). All 12 STEER lines met. D faced about 45 deg off (fingerprint 15): its last approach point is inside the reach radius. Stand windows run from the start fingerprint (wait_skipped) to the end one.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (102 env lines)

## Speed

87 play windows of 5 s, 24.8 fps mean; worst frame 192 ms. Era: ahead-1. Standing 24.6 fps (10 windows), walking 24.9 fps (75 windows, heavy share 0.01); door at 99 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 25 | 0.29 | 30.7 | 32.6 | 0.3 | 23.4 | 12.2 | 113 | 19.5 | 56% |
| queued | 57 | 0.66 | 22.4 | 44.6 | 0.4 | 38.0 | 17.9 | 172 | 26.9 | 60% |
| mid | 4 | 0.05 | 23.2 | 43.1 | 2.6 | 35.7 | 19.0 | 152 | 24.0 | 54% |
| heavy | 1 | 0.01 | 20.0 | 50.0 | 5.3 | 43.5 | 22.2 | 182 | 26.6 | 54% |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned at the end of the session.

## Front waits on the back, heavy windows

| Site | ms per frame | waits per frame | µs each |
|---|---|---|---|
| dma snapshot miss | 8.9 | 95 | 93 |
| list writers | 7.4 | 196 | 37 |
| acquire check | 4.1 | 125 | 33 |
| acquire poll | 1.2 | 47 | 26 |
| map | 0.4 | 1 | 617 |
| acquire recheck | 0.3 | 7 | 39 |

## Textures and memory

Texture churn per 600 frames (walking): 1203 images created, 1195 deleted, 984 uploads, 615 MiB.
Memory margins: out of memory in 371 of 460 lines (max 3072 MiB).

## Copy guard

101622 page copies per 5 s; pool peak 1086 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 114 | 192 | 23.9 | unattributed |
| 289 | 116 | 21.0 | unattributed |
| 370 | 130 | 22.6 | shaders built in play (8, 155 ms) |
| 375 | 143 | 19.1 | shaders built in play (9, 208 ms) |
| 380 | 172 | 20.0 | shaders built in play (4, 207 ms) |
| 491 | 117 | 21.8 | unattributed |
| 541 | 126 | 21.5 | unattributed |

Shaders built while playing: 26 (615 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
