# 2026-11-14-Play4a

- **Build:** 01.219.925 (Nov 13 2026 20:08:50) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** Long play, no script: end of the Deku Tree into Hyrule Field. Session A of two; ended in a SIGSEGV on a guest thread at 1032 s.
- **What the player saw:** Hitch census and memory wall; feeds the hitch and memory-wall programmes. Flight recorder at 150 ms, 64 dumps.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Flight-recorder dumps:** 371 ms frame at 85 s → gbb-flight-107-0.bin; 675 ms frame at 222 s → gbb-flight-107-1.bin; 186 ms frame at 400 s → gbb-flight-107-2.bin; 735 ms frame at 405 s → gbb-flight-107-3.bin; 823 ms frame at 412 s → gbb-flight-107-4.bin; 779 ms frame at 430 s → gbb-flight-107-5.bin; 232 ms frame at 458 s → gbb-flight-107-6.bin; 153 ms frame at 482 s → gbb-flight-107-7.bin; 183 ms frame at 514 s → gbb-flight-107-8.bin; 337 ms frame at 551 s → gbb-flight-107-9.bin; 162 ms frame at 582 s → gbb-flight-107-10.bin; 155 ms frame at 632 s → gbb-flight-107-11.bin; 168 ms frame at 654 s → gbb-flight-107-12.bin; 174 ms frame at 671 s → gbb-flight-107-13.bin; 704 ms frame at 680 s → gbb-flight-107-14.bin; 967 ms frame at 685 s → gbb-flight-107-15.bin; 1217 ms frame at 698 s → gbb-flight-107-16.bin; 1164 ms frame at 709 s → gbb-flight-107-17.bin; 1412 ms frame at 768 s → gbb-flight-107-18.bin; 343 ms frame at 861 s → gbb-flight-107-19.bin; 656 ms frame at 869 s → gbb-flight-107-20.bin; 683 ms frame at 912 s → gbb-flight-107-21.bin; 167 ms frame at 959 s → gbb-flight-107-22.bin; 166 ms frame at 1005 s → gbb-flight-107-23.bin; 173 ms frame at 1015 s → gbb-flight-107-24.bin; 164 ms frame at 1024 s → gbb-flight-107-25.bin
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (104 env lines)

## Speed

133 play windows of 5 s, 33.0 fps mean; worst frame 398 ms. Era: ahead-1. Standing 41.3 fps (10 windows), walking 32.1 fps (120 windows, heavy share 0.08); door at 86 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 81 | 0.61 | 35.2 | 28.4 | 0.3 | 19.9 | 10.5 | 97 | 14.7 | 50% |
| queued | 30 | 0.23 | 28.9 | 34.6 | 0.3 | 29.8 | 14.8 | 140 | 19.9 | 56% |
| mid | 9 | 0.07 | 29.9 | 33.4 | 3.1 | 23.6 | 12.9 | 104 | 17.3 | 49% |
| heavy | 13 | 0.10 | 30.7 | 32.6 | 10.9 | 26.0 | 12.7 | 113 | 19.3 | 48% |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned at the end of the session.

## Front waits on the back, heavy windows

| Site | ms per frame | waits per frame | µs each |
|---|---|---|---|
| dma snapshot miss | 5.0 | 52 | 97 |
| list writers | 4.0 | 168 | 24 |
| acquire check | 2.4 | 108 | 22 |
| acquire poll | 1.0 | 93 | 11 |
| map | 0.2 | 1 | 201 |

## Textures and memory

Texture churn per 600 frames (walking): 576 images created, 575 deleted, 761 uploads, 713 MiB.
Memory margins: out of memory in 358 of 1087 lines (max 3072 MiB).

## Copy guard

56144 page copies per 5 s; pool peak 1683 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 91 | 269 | 29.1 | shaders built in play (2, 148 ms) |
| 106 | 140 | 37.2 | shaders built in play (12, 82 ms) |
| 465 | 120 | 30.4 | unattributed |
| 480 | 131 | 30.9 | unattributed |
| 485 | 153 | 32.1 | shaders built in play (14, 99 ms) |
| 505 | 115 | 36.7 | unattributed |
| 515 | 183 | 31.8 | shaders built in play (13, 50 ms) |
| 520 | 398 | 31.4 | shaders built in play (9, 338 ms) |
| 555 | 337 | 34.0 | unattributed |
| 585 | 217 | 29.1 | unattributed |
| 610 | 107 | 31.7 | unattributed |
| 635 | 155 | 30.6 | unattributed |
| 655 | 168 | 33.0 | unattributed |
| 691 | 114 | 31.8 | unattributed |
| 721 | 111 | 31.8 | unattributed |
| 726 | 106 | 34.3 | unattributed |
| 866 | 119 | 29.9 | unattributed |
| 876 | 225 | 18.0 | shaders built in play (9, 287 ms) |
| 891 | 119 | 19.3 | unattributed |
| 896 | 124 | 22.6 | shaders built in play (2, 54 ms) |
| 962 | 167 | 26.9 | unattributed |
| 997 | 110 | 31.6 | unattributed |
| 1007 | 180 | 25.1 | unattributed |
| 1012 | 152 | 18.7 | unattributed |
| 1017 | 173 | 16.2 | shaders built in play (9, 214 ms) |
| 1022 | 190 | 13.8 | shaders built in play (12, 298 ms) |
| 1027 | 164 | 15.7 | unattributed |

Shaders built while playing: 137 (1887 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
