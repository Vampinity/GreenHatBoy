# 2026-11-14-KW2

- **Build:** 01.219.925 (Nov 13 2026 20:08:50) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark route with four standing stops (A-D, docs/GrowingBlackBeans/kokiri-stops.md), recorded for the scripted route
- **What the player saw:** Recorded walk for the scripted route: GS1 counts (EDEN_GBB_GPFIFO=1 + EDEN_UP_SUBMIT_STATS=1) plus EDEN_TEST_RECORD=1, EDEN_TEST_DISCARD_SAVE=1, EDEN_GBB_LOG_SESSION=1. Capture video kept locally (STEER points from it). At stop C a false start: the first L2 (input clock 234.1 s) turned Link round, the second (237.8 s) set the view; count C from the second. recorded-input.txt is the player's input.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (103 env lines)

## Speed

70 play windows of 5 s, 24.8 fps mean; worst frame 226 ms. Era: ahead-1. Standing 24.0 fps (8 windows), walking 25.1 fps (59 windows, heavy share 0.00); door at 87 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 20 | 0.29 | 32.5 | 30.7 | 0.2 | 21.7 | 11.4 | 106 | 17.6 | 55% |
| queued | 48 | 0.69 | 21.8 | 45.8 | 0.4 | 39.1 | 19.2 | 169 | 27.2 | 59% |
| mid | 2 | 0.03 | 19.9 | 50.3 | 1.7 | 43.6 | 20.0 | 192 | 30.2 | 60% |
| heavy | 0 | 0.00 | – | – | – | – | – | – | – | – |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned at the end of the session.

## Textures and memory

Texture churn per 600 frames (walking): 1584 images created, 1568 deleted, 1325 uploads, 780 MiB.
Memory margins: out of memory in 307 of 390 lines (max 3072 MiB).

## Copy guard

95830 page copies per 5 s; pool peak 914 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 92 | 185 | 16.9 | unattributed |
| 284 | 104 | 21.2 | unattributed |
| 299 | 103 | 21.6 | unattributed |
| 374 | 128 | 19.1 | unattributed |
| 384 | 109 | 20.7 | unattributed |
| 394 | 149 | 20.4 | unattributed |
| 404 | 131 | 20.4 | unattributed |
| 444 | 122 | 20.5 | unattributed |
| 449 | 226 | 19.4 | unattributed |

Shaders built while playing: 0 (0 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
