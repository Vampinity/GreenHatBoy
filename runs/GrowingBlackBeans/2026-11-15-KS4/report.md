# 2026-11-15-KS4

- **Build:** 01.219.925 (Nov 13 2026 20:08:50) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark route with four standing stops (A-D, docs/GrowingBlackBeans/kokiri-stops.md), scripted (tools/GrowingBlackBeans/steer/kokiri-four-stops)
- **What the player saw:** Scripted start 4, and the control arm for the frame-ahead-off comparison (everyday settings, frame ahead on). All 12 STEER lines met, no timeouts, script_done at 408 s. Four 62 s stands; facing fingerprints at stand start A 87, B 69, C 88, D 67.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (102 env lines)

## Speed

70 play windows of 5 s, 25.3 fps mean; worst frame 139 ms. Era: ahead-1. Standing 24.4 fps (10 windows), walking 25.6 fps (57 windows, heavy share 0.00); door at 99 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 22 | 0.31 | 31.9 | 31.3 | 0.2 | 21.3 | 11.6 | 101 | 17.8 | 55% |
| queued | 48 | 0.69 | 22.2 | 45.0 | 0.4 | 38.4 | 18.5 | 169 | 27.0 | 60% |
| mid | 0 | 0.00 | – | – | – | – | – | – | – | – |
| heavy | 0 | 0.00 | – | – | – | – | – | – | – | – |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned at the end of the session.

## Textures and memory

Texture churn per 600 frames (walking): 1481 images created, 1474 deleted, 1228 uploads, 766 MiB.
Memory margins: out of memory in 272 of 342 lines (max 3072 MiB).

## Copy guard

95959 page copies per 5 s; pool peak 1044 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 104 | 139 | 18.2 | unattributed |
| 109 | 111 | 26.3 | unattributed |
| 290 | 121 | 21.5 | unattributed |
| 355 | 124 | 20.6 | unattributed |
| 375 | 101 | 19.1 | unattributed |
| 380 | 117 | 21.3 | unattributed |
| 390 | 114 | 20.6 | unattributed |

Shaders built while playing: 0 (0 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
