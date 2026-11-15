# 2026-11-14-Play4b

- **Build:** 01.219.925 (Nov 13 2026 20:08:50) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** Long play, no script: end of the Deku Tree into Hyrule Field. Session B of two; host heap exhausted, SIGSEGV in the pipeline builder at 1186 s, inside a load that never finished.
- **What the player saw:** Hitch census and memory wall; feeds the hitch and memory-wall programmes. Flight recorder at 150 ms, 64 dumps.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Flight-recorder dumps:** 274 ms frame at 387 s → gbb-flight-108-0.bin; 400 ms frame at 418 s → gbb-flight-108-1.bin; 193 ms frame at 426 s → gbb-flight-108-2.bin; 176 ms frame at 437 s → gbb-flight-108-3.bin; 667 ms frame at 638 s → gbb-flight-108-4.bin; 4695 ms frame at 733 s → gbb-flight-108-5.bin; 625 ms frame at 738 s → gbb-flight-108-6.bin; 1869 ms frame at 747 s → gbb-flight-108-7.bin; 454 ms frame at 756 s → gbb-flight-108-8.bin; 725 ms frame at 802 s → gbb-flight-108-9.bin; 735 ms frame at 841 s → gbb-flight-108-10.bin; 253 ms frame at 848 s → gbb-flight-108-11.bin; 166 ms frame at 854 s → gbb-flight-108-12.bin; 423 ms frame at 892 s → gbb-flight-108-13.bin; 654 ms frame at 899 s → gbb-flight-108-14.bin; 786 ms frame at 905 s → gbb-flight-108-15.bin; 792 ms frame at 911 s → gbb-flight-108-16.bin; 2311 ms frame at 922 s → gbb-flight-108-17.bin; 239 ms frame at 927 s → gbb-flight-108-18.bin; 254 ms frame at 933 s → gbb-flight-108-19.bin; 1544 ms frame at 948 s → gbb-flight-108-20.bin; 722 ms frame at 955 s → gbb-flight-108-21.bin; 223 ms frame at 961 s → gbb-flight-108-22.bin; 703 ms frame at 972 s → gbb-flight-108-23.bin; 169 ms frame at 1038 s → gbb-flight-108-24.bin; 720 ms frame at 1073 s → gbb-flight-108-25.bin; 175 ms frame at 1081 s → gbb-flight-108-26.bin; 175 ms frame at 1088 s → gbb-flight-108-27.bin; 171 ms frame at 1095 s → gbb-flight-108-28.bin; 920 ms frame at 1115 s → gbb-flight-108-29.bin; 312 ms frame at 1124 s → gbb-flight-108-30.bin; 1620 ms frame at 1129 s → gbb-flight-108-31.bin; 265 ms frame at 1160 s → gbb-flight-108-32.bin; 167 ms frame at 1165 s → gbb-flight-108-33.bin; 679 ms frame at 1171 s → gbb-flight-108-34.bin; 1260 ms frame at 1177 s → gbb-flight-108-35.bin
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (104 env lines)

## Speed

104 play windows of 5 s, 32.5 fps mean; worst frame 454 ms. Era: ahead-1. Standing 27.1 fps (10 windows), walking 33.3 fps (91 windows, heavy share 0.08); door at 423 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 89 | 0.86 | 34.3 | 29.2 | 0.2 | 19.2 | 10.5 | 94 | 14.0 | 45% |
| queued | 3 | 0.03 | 20.8 | 48.1 | 0.4 | 41.4 | 20.9 | 178 | 25.6 | 53% |
| mid | 4 | 0.04 | 28.7 | 34.8 | 3.4 | 27.1 | 15.1 | 114 | 16.6 | 42% |
| heavy | 8 | 0.08 | 19.4 | 51.7 | 13.4 | 36.0 | 17.9 | 147 | 27.1 | 50% |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned at the end of the session.

## Front waits on the back, heavy windows

| Site | ms per frame | waits per frame | µs each |
|---|---|---|---|
| dma snapshot miss | 7.5 | 60 | 125 |
| list writers | 5.8 | 163 | 35 |
| acquire check | 3.1 | 104 | 30 |
| acquire poll | 1.4 | 51 | 27 |
| acquire recheck | 0.1 | 7 | 21 |
| map | 0.1 | 1 | 78 |

## Textures and memory

Texture churn per 600 frames (walking): 883 images created, 872 deleted, 747 uploads, 600 MiB.
Memory margins: out of memory in 696 of 923 lines (max 3072 MiB).

## Copy guard

54547 page copies per 5 s; pool peak 1423 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 428 | 193 | 14.6 | unattributed |
| 433 | 113 | 19.3 | unattributed |
| 438 | 176 | 18.6 | unattributed |
| 584 | 126 | 36.7 | unattributed |
| 644 | 129 | 26.8 | unattributed |
| 659 | 130 | 38.6 | unattributed |
| 694 | 107 | 36.9 | unattributed |
| 714 | 116 | 35.8 | unattributed |
| 760 | 454 | 28.3 | shaders built in play (32, 212 ms) |
| 927 | 287 | 25.2 | unattributed |
| 932 | 239 | 24.9 | unattributed |
| 937 | 254 | 24.5 | unattributed |
| 942 | 264 | 28.7 | unattributed |
| 963 | 223 | 21.5 | unattributed |
| 1008 | 111 | 33.3 | unattributed |
| 1038 | 130 | 27.4 | unattributed |
| 1043 | 169 | 14.8 | unattributed |
| 1048 | 109 | 16.1 | unattributed |
| 1058 | 103 | 31.5 | unattributed |
| 1083 | 185 | 16.7 | GPU thread behind (fence wait >= 20 ms/frame) |
| 1088 | 175 | 16.4 | GPU thread behind (fence wait >= 20 ms/frame) |
| 1098 | 171 | 15.6 | unattributed |
| 1103 | 110 | 15.9 | unattributed |
| 1108 | 116 | 15.4 | unattributed |
| 1114 | 141 | 14.5 | unattributed |

Shaders built while playing: 53 (346 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
