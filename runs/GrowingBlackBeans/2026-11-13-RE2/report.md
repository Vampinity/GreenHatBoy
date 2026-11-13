# 2026-11-13-RE2

- **Build:** 01.219.921 (Nov 13 2026 11:13:19) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark: Continue, house, out, walk loop to the water
- **What the player saw:** Read sync once with a 250 us escape.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (102 env lines)

## Speed

28 play windows of 5 s, 20.0 fps mean; worst frame 111 ms. Era: ahead-1. Standing 20.3 fps (10 windows), walking 19.7 fps (16 windows, heavy share 0.00); door at 79 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 28 | 1.00 | 20.0 | 50.0 | 0.3 | 32.2 | 20.3 | 147 | 21.1 | 42% |
| queued | 0 | 0.00 | – | – | – | – | – | – | – | – |
| mid | 0 | 0.00 | – | – | – | – | – | – | – | – |
| heavy | 0 | 0.00 | – | – | – | – | – | – | – | – |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned at the end of the session.

## Textures and memory

Texture churn per 600 frames (walking): 1927 images created, 1827 deleted, 1356 uploads, 985 MiB.
Memory margins: out of memory in 32 of 163 lines (max 512 MiB).

## Copy guard

90518 page copies per 5 s; pool peak 641 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 89 | 111 | 18.0 | unattributed |
| 219 | 109 | 21.5 | shaders built in play (1, 58 ms) |

Shaders built while playing: 1 (58 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
