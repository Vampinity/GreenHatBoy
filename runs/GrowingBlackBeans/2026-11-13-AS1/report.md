# 2026-11-13-AS1

- **Build:** 01.219.920 (Nov 12 2026 22:10:46) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark: Continue, house, out, walk loop to the water
- **What the player saw:** Two frames ahead, two guard slots, no read sync.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (99 env lines)

## Speed

22 play windows of 5 s, 26.8 fps mean; worst frame 265 ms. Era: ahead-1. Standing 28.3 fps (10 windows), walking 26.1 fps (9 windows, heavy share 0.00); door at 77 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 5 | 0.23 | 26.5 | 37.8 | 0.3 | 28.1 | 18.2 | 126 | 22.4 | 61% |
| queued | 16 | 0.73 | 27.1 | 36.9 | 0.3 | 31.1 | 19.3 | 150 | 20.9 | 56% |
| mid | 1 | 0.05 | 22.5 | 44.4 | 4.7 | 34.2 | 22.8 | 134 | 23.6 | 53% |
| heavy | 0 | 0.00 | – | – | – | – | – | – | – | – |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned one window before the end of the session.

## Textures and memory

Texture churn per 600 frames (walking): 2719 images created, 2611 deleted, 1946 uploads, 1312 MiB.
Memory margins: out of memory in 41 of 168 lines (max 1024 MiB).

## Copy guard

108037 page copies per 5 s; pool peak 1081 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 82 | 265 | 22.5 | unattributed |
| 142 | 128 | 20.1 | unattributed |

Shaders built while playing: 0 (0 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
