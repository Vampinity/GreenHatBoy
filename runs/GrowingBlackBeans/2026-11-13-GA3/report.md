# 2026-11-13-GA3

- **Build:** 01.219.923 (Nov 13 2026 17:07:58) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark: Continue, house, out, walk loop to the water
- **What the player saw:** t134-gbb7 patch 0933 with the audit naming its misses.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (102 env lines)

## Speed

23 play windows of 5 s, 18.5 fps mean; worst frame 101 ms. Era: ahead-1. Standing 19.3 fps (10 windows), walking 18.0 fps (10 windows, heavy share 0.00); door at 92 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 23 | 1.00 | 18.5 | 54.1 | 0.4 | 32.3 | 19.1 | 149 | 21.7 | 40% |
| queued | 0 | 0.00 | – | – | – | – | – | – | – | – |
| mid | 0 | 0.00 | – | – | – | – | – | – | – | – |
| heavy | 0 | 0.00 | – | – | – | – | – | – | – | – |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned at the end of the session.

## Textures and memory

Texture churn per 600 frames (walking): 2775 images created, 2650 deleted, 2042 uploads, 1322 MiB.
Memory margins: out of memory in 71 of 164 lines (max 768 MiB).

## Copy guard

13350 page copies per 5 s; pool peak 477 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 103 | 101 | 18.7 | unattributed |

Shaders built while playing: 0 (0 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
