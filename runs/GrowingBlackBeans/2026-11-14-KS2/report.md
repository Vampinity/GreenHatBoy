# 2026-11-14-KS2

- **Build:** 01.219.925 (Nov 13 2026 20:08:50) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark route with four standing stops (A-D, docs/GrowingBlackBeans/kokiri-stops.md), scripted (tools/GrowingBlackBeans/steer/kokiri-four-stops)
- **What the player saw:** Scripted start 2 of 3: as KS1 with the script that turns Link in 15 deg taps until the view matches KW2's (MAYBE, min 60). All 12 STEER lines met; facing fingerprints at stand start A 97, B 72, C 89, D 65 (D after one search tap). Stand windows run from the start fingerprint (wait_skipped) to the end one.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (102 env lines)

## Speed

77 play windows of 5 s, 24.9 fps mean; worst frame 322 ms. Era: ahead-1. Standing 24.6 fps (10 windows), walking 25.2 fps (64 windows, heavy share 0.00); door at 106 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 23 | 0.30 | 31.8 | 31.4 | 0.3 | 22.1 | 11.8 | 107 | 17.7 | 55% |
| queued | 50 | 0.65 | 22.1 | 45.3 | 0.4 | 38.2 | 17.9 | 174 | 27.6 | 61% |
| mid | 4 | 0.05 | 21.2 | 47.1 | 3.0 | 40.6 | 23.6 | 153 | 27.3 | 56% |
| heavy | 0 | 0.00 | – | – | – | – | – | – | – | – |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned one window before the end of the session.

## Textures and memory

Texture churn per 600 frames (walking): 866 images created, 854 deleted, 631 uploads, 497 MiB.
Memory margins: out of memory in 331 of 430 lines (max 3072 MiB).

## Copy guard

98149 page copies per 5 s; pool peak 1122 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 112 | 322 | 14.9 | unattributed |
| 362 | 132 | 19.4 | shaders built in play (8, 188 ms) |
| 367 | 136 | 21.9 | shaders built in play (16, 383 ms) |
| 378 | 134 | 23.1 | shaders built in play (5, 76 ms) |
| 383 | 121 | 18.9 | shaders built in play (5, 134 ms) |
| 388 | 140 | 20.0 | shaders built in play (5, 195 ms) |

Shaders built while playing: 45 (1076 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
