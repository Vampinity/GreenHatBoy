# 2026-11-13-Play3

- **Build:** 01.219.920 (Nov 12 2026 22:10:46) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** Free play (not the benchmark route)
- **What the player saw:** Two ahead, two slots, no read sync.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** `EDEN_NX2_FRAMES_AHEAD=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_GBB_TRUST_COPY=1`, `EDEN_NX2_RESNAPSHOT=0`, `EDEN_UP_SHADER_PREP=1`, `EDEN_NX2_DMA_SNAPSHOT=1`, `EDEN_GPU_TIME=1`, `EDEN_NX2_SPLIT_WAITS=1` (99 env lines)

## Speed

285 play windows of 5 s, 34.6 fps mean; worst frame 487 ms. Era: ahead-1. Standing 34.5 fps (8 windows), walking 34.6 fps (275 windows, heavy share 0.13); door at 75 s.

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 217 | 0.76 | 34.3 | 29.1 | 0.2 | 16.3 | 10.0 | 78 | 13.1 | 45% |
| queued | 0 | 0.00 | – | – | – | – | – | – | – | – |
| mid | 30 | 0.11 | 35.0 | 28.6 | 2.9 | 15.5 | 9.5 | 72 | 13.0 | 43% |
| heavy | 38 | 0.13 | 35.6 | 28.1 | 9.6 | 13.0 | 7.7 | 62 | 11.8 | 41% |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned one window before the end of the session.

## Front waits on the back, heavy windows

| Site | ms per frame | waits per frame | µs each |
|---|---|---|---|
| list writers | 3.2 | 154 | 21 |
| dma snapshot miss | 2.1 | 26 | 79 |
| acquire check | 1.7 | 101 | 17 |
| acquire poll | 0.6 | 130 | 5 |

## Textures and memory

Texture churn per 600 frames (walking): 482 images created, 486 deleted, 377 uploads, 203 MiB.
Memory margins: out of memory in 0 of 1870 lines (max 0 MiB).

## Copy guard

54091 page copies per 5 s; pool peak 954 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

| Log s | Worst ms | fps | Likely cause |
|---|---|---|---|
| 91 | 306 | 22.6 | shaders built in play (10, 152 ms) |
| 116 | 163 | 43.9 | unattributed |
| 126 | 164 | 43.7 | unattributed |
| 131 | 105 | 27.2 | unattributed |
| 156 | 359 | 23.6 | shaders built in play (11, 517 ms) |
| 161 | 115 | 29.9 | unattributed |
| 166 | 144 | 29.3 | shaders built in play (3, 61 ms) |
| 181 | 110 | 31.8 | unattributed |
| 186 | 218 | 29.4 | shaders built in play (4, 152 ms) |
| 201 | 109 | 37.6 | unattributed |
| 237 | 190 | 27.6 | shaders built in play (4, 118 ms) |
| 242 | 103 | 29.9 | shaders built in play (12, 106 ms) |
| 277 | 242 | 31.3 | shaders built in play (7, 171 ms) |
| 302 | 115 | 35.0 | unattributed |
| 328 | 178 | 34.7 | shaders built in play (10, 115 ms) |
| 343 | 128 | 35.1 | unattributed |
| 363 | 175 | 33.6 | unattributed |
| 393 | 171 | 32.7 | shaders built in play (5, 305 ms) |
| 403 | 298 | 27.1 | shaders built in play (19, 365 ms) |
| 408 | 126 | 30.4 | shaders built in play (12, 87 ms) |
| 444 | 221 | 32.2 | shaders built in play (3, 112 ms) |
| 449 | 117 | 32.3 | shaders built in play (5, 52 ms) |
| 459 | 215 | 31.0 | shaders built in play (12, 182 ms) |
| 474 | 211 | 29.2 | shaders built in play (14, 130 ms) |
| 524 | 106 | 29.5 | shaders built in play (12, 281 ms) |
| 529 | 174 | 31.9 | shaders built in play (4, 267 ms) |
| 549 | 212 | 32.3 | shaders built in play (17, 181 ms) |
| 579 | 140 | 32.2 | shaders built in play (12, 172 ms) |
| 584 | 101 | 32.4 | shaders built in play (23, 205 ms) |
| 594 | 113 | 34.7 | shaders built in play (2, 102 ms) |
| 620 | 172 | 40.9 | unattributed |
| 630 | 164 | 33.1 | unattributed |
| 640 | 176 | 37.6 | unattributed |
| 695 | 240 | 29.0 | unattributed |
| 700 | 226 | 19.7 | unattributed |
| 730 | 321 | 27.9 | unattributed |
| 740 | 200 | 28.3 | unattributed |
| 745 | 172 | 29.4 | unattributed |
| 750 | 222 | 27.1 | unattributed |
| 755 | 112 | 29.9 | unattributed |
| 795 | 186 | 28.6 | unattributed |
| 800 | 130 | 30.5 | unattributed |
| 820 | 134 | 37.8 | unattributed |
| 825 | 196 | 27.8 | unattributed |
| 845 | 197 | 29.6 | unattributed |
| 855 | 102 | 32.7 | unattributed |
| 860 | 127 | 31.7 | unattributed |
| 885 | 253 | 33.5 | unattributed |
| 911 | 115 | 35.8 | unattributed |
| 916 | 308 | 34.2 | unattributed |
| 931 | 388 | 30.8 | unattributed |
| 946 | 159 | 32.1 | unattributed |
| 966 | 115 | 34.7 | unattributed |
| 976 | 120 | 29.6 | unattributed |
| 1021 | 160 | 37.6 | unattributed |
| 1036 | 114 | 36.6 | unattributed |
| 1066 | 127 | 30.6 | unattributed |
| 1151 | 155 | 37.0 | unattributed |
| 1156 | 160 | 34.7 | unattributed |
| 1211 | 137 | 30.1 | unattributed |
| 1221 | 101 | 31.2 | unattributed |
| 1261 | 117 | 30.8 | unattributed |
| 1271 | 204 | 29.4 | unattributed |
| 1276 | 103 | 33.6 | unattributed |
| 1307 | 145 | 32.7 | unattributed |
| 1327 | 204 | 33.4 | unattributed |
| 1372 | 165 | 38.1 | unattributed |
| 1382 | 487 | 32.9 | unattributed |
| 1387 | 359 | 32.6 | unattributed |
| 1392 | 102 | 38.1 | unattributed |
| 1442 | 119 | 38.0 | unattributed |
| 1447 | 103 | 36.6 | unattributed |
| 1468 | 179 | 34.2 | unattributed |
| 1473 | 147 | 33.5 | unattributed |
| 1505 | 119 | 36.6 | unattributed |
| 1565 | 129 | 35.9 | unattributed |
| 1595 | 104 | 37.4 | unattributed |
| 1610 | 115 | 37.9 | unattributed |
| 1620 | 103 | 38.0 | unattributed |
| 1630 | 104 | 36.2 | unattributed |
| 1640 | 241 | 38.3 | unattributed |

Shaders built while playing: 290 (4660 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
