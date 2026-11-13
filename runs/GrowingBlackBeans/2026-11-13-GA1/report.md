# 2026-11-13-GA1

- **Build:** 01.219.922 (Nov 13 2026 16:40:33) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark: Continue, house, out, walk loop to the water
- **What the player saw:** t134-gbb6 patch 0933: region-limited read sync. Clean by eye.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (102 env lines)

## Speed

22 play windows of 5 s, 18.8 fps mean; worst frame 109 ms. Era: ahead-1. Standing 19.6 fps (10 windows), walking 18.5 fps (9 windows, heavy share 0.00); door at 83 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 22 | 1.00 | 18.8 | 53.3 | 0.3 | 32.1 | 18.7 | 148 | 21.4 | 40% |
| queued | 0 | 0.00 | – | – | – | – | – | – | – | – |
| mid | 0 | 0.00 | – | – | – | – | – | – | – | – |
| heavy | 0 | 0.00 | – | – | – | – | – | – | – | – |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned at the end of the session.

## Textures and memory

Texture churn per 600 frames (walking): 2844 images created, 2704 deleted, 1953 uploads, 1393 MiB.
Memory margins: out of memory in 29 of 130 lines (max 1024 MiB).

## Copy guard

11246 page copies per 5 s; pool peak 569 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 153 | 109 | 17.8 | unattributed |

Shaders built while playing: 0 (0 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
