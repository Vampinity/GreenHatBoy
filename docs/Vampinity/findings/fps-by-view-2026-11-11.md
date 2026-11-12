# FPS by view, 11 Nov 2026 (build T120, fast mode)

> **Found:** In the village the frame rate falls from about 33 to 17-19 fps when the water and stepping stones fill the view; frame time follows the number of command-list entries a frame, and the extra time is a wait on the GPU fence.
>
> **So:** The village slowdown follows the amount of GPU command traffic per frame; speed work should cut that traffic or its cost per entry.

Two recorded tries, one video. What makes the frame rate follow the view?

## Short answer

- **Kokiri Forest:** the frame rate drops at one spot. Coming out of the short tunnel into the village, fps goes from 33 to 21 within 2 seconds, then to 17-19 while the water and the stepping stones fill the view. Getting back up is slower: 21 → 24 → 28 → 33 over about 10 seconds as he walks off the water onto the stone path and then the wooded stairs.
- **What moves with the fps:** how much GPU command traffic the game sends each frame. The heavy view has about 2.7x the command-list entries, about 1.6x the Vulkan command words and about 1.2x the submissions per frame.
- **Where the extra time goes:** the frame waits on the GPU fence, about 20 ms of a 53 ms frame. In the light view that wait is 0-2 ms. The rest of the frame stays about 30 ms in both views.
- **Fit:** frame time ≈ 22 ms + 3.3 ms per 1000 command-list entries a frame (5 Kokiri windows, r = 0.99). Across all 10 play and cutscene windows of both tries it is 20 ms + 3.5 ms per 1000 (r = 0.98).
- **Area after the forest exit:** looking down the misty path runs at 26-28 fps, facing the bank at 35 fps. The fence wait stays near 0 here, so this difference is not the GPU-wait pattern seen in the village. No logged line explains it.
- **What the logs cannot say:** whether the GPU-side wait in the village belongs to the GPU thread (front or back), the Vulkan submission thread, or the GPU itself. No front/back idle line was logged, and no GPU time (EDEN_GPU_TIME was off).

## Material and alignment

| Try | Video span | Log | Input file | Game start (app s) |
|---|---|---|---|---|
| 1 | 0-161 s | eden_log.session1.txt, stderr.session1.log, heap.session1.log | recording-baae9b0888.txt (last 136.3) | 24.62 |
| 2 | 200-405 s | eden_log.run2.txt, stderr.run2.log, hand-20261111-0537/heap.log (same run) | recording-8f2dc615e4.txt (last 175.97) | 21.72 |

- **Try 1:** video s = app s − 2.0; game s = video s − 22.6. Anchors: the first present at app 40.15 matches the overlay first showing at video 38. The load stall at app 86.2-88.8 matches the overlay "F--" at video 86-88. The fps drop at app 104.4-105.6 (from the 30-frame ticks) matches the overlay drop at video 103-105. The log runs about 3 s past the last video frame of play (home screen at video 161, last log line at app 164).
- **Try 2:** video s = app s + 200.3; game s = video s − 221.9. Anchors: the first present at app 37.5 matches the overlay at video 238. The load stall at app 79-82 matches the overlay "F--" and "F7" at video 279-282. The end of the log at app 205.7 matches the home screen at video ~405.
- **Accuracy:** about ±1 s. The overlay F figure behaves like a 1-second average, so it lags a step by about 1 s.
- **Not the same walk:** try 2 continues from a save made in try 1's pause menu (video 134-141). Try 2 starts at night by Mido on the exit path, goes through the Saria bridge cutscene, then the area after the exit. Only try 1 crosses the village.

## Periodic lines found (what each gives)

| Line (file) | Cadence | Fields used |
|---|---|---|
| `nx2:vi2 5 s:` (eden_log) | 5 s | frames, fps, mean ms, 1% low, worst, **fence** = mean ms a present waited on the GPU fence |
| `nx2:vi2 last 600 presents` (eden_log) | every 600 presents | mean frame, fence, vblank pacing, "N ran a frame ahead" |
| `Memory margins` (eden_log, texture_cache TickFrame) | every ~30 frames | texture-cache "out of memory" MiB; the spacing gives fps at ~1 s resolution |
| `FETCH_COUNT differ/compared/seen` (eden_log, dma_pusher) | every ~1.03 M "submit copy" seen | cumulative **command-list entries copied at submit**, resumed entries, empty-at-submit; the spacing gives per-frame rates |
| `radv/ps5 submissions: window count kwords claim_ms copy_ms flush_ms agc_ms suspend_ms` (stderr) | about every 10 s (the window length is not printed; placed with the EDEN_AREA_EVICT frame numbers) | submissions, command kwords, time in the AGC submit and in "suspend" |
| `RADV_PS5_MEMORY t_s=` (stderr) | about 10 s, own clock | driver memory pools (did not move with the view) |
| `EDEN_AREA_EVICT frame N` (stderr) | on eviction bursts | frame counter, used to place the radv windows in time |
| `Runtime pipelines in the last 10 s` / `Kept translations in the last 10 s` (eden_log) | 10 s, only when non-zero | pipelines built on the GPU thread and their ms |
| `MeshPipelineSkipped … first draw (#n) … N workgroups` (eden_log) | first use of a mesh pipeline only | new mesh pipelines, no per-frame mesh count |
| `radv/ps5: mesh draw dropped: pipeline … not run as compute` (stderr) | per event | 32 lines in try 1 (one pipeline) |
| `CreateImage … over the memory budget` (eden_log) | per event | images allocated over budget |
| `Buffer cache: N buffers M MiB` (eden_log) | ~1 s | buffer count and size (grows as new places load; no upload volume) |
| `DMA snapshot` (eden_log) | rare, cumulative | front DMA read counts |
| `EDEN_VULKAN_FRAME` (heap) | 5 s | duplicates vi2 |
| `EDEN_GUEST_WAKE c0..c5=a/b/0/0` (heap) | 5 s | guest CPU core wakeups |
| `EDEN_JIT_PAGE_REUSE`, `MKW_*_STATE` (heap) | per 120 frames / 5 s | flat, not used |

**Not in these logs:**
- No GPU-split idle or wait line. There is only the start line "GPU thread split: engine methods run on a second thread, macros on the first".
- No draws-a-frame line.
- No query or zpass report line.
- No GPU time.
- No per-frame upload volume.
- No per-frame mesh-draw count.

## 1. FPS along the route

`fence` = ms per frame the present waited on the GPU. Kind: play, MENU, CUT (cutscene or dialogue), LOAD (load or black), HITCH (a single long stall that skews the window).

### Try 1 (Kokiri Forest, daylight)

| Game s | Video s | fps | fence ms | What is on screen | Kind |
|---|---|---|---|---|---|
| 20.6-60.6 | 38-83 | 54-60 | 0-1.8 | logo, title, file select | MENU |
| 65.7 | 83-88 | 22.6 | 3.6 | load, then a grassy hill with sunbeams, "Kokiri Forest" title | LOAD |
| 70.7 | 88-93 | 25.7 | 0.0 | hill into the dark ravine path (Navi line) | play |
| 75.7 | 93-98 | 31.6 | 0.2 | dark ravine path, rock walls, mist on the floor | play, light |
| 80.7 | 98-103 | 32.2 | 1.9 | ravine into a short tunnel, bright exit ahead | play, light |
| 85.8 | 103-108 | 18.7 | 19.6 | tunnel exit: village opens, water channel, stepping stones, houses | play, **heavy** |
| 90.8 | 108-113 | 17.8 | 17.0 | on the stepping stones over the water, village centre | play, **heavy** |
| 95.8 | 113-118 | 20.3 | 25.1 | stepping stones, water, signpost, big tree | play, **heavy** |
| 100.9 | 118-123 | 22.9 | 17.6 | last stones, leaving the water | play, easing |
| 105.9 | 123-128 | 28.4 | 2.2 | stone-paved path past houses ("It can't be true…") | play, middle |
| 110.9 | 128-133 | 32.0 | 0.0 | narrow wooded path, stone stairs up, dark path to Mido | play, light |
| 115.9-120.9 | 133-143 | 46-48 | 0.4-0.6 | pause menu, save | MENU |
| 125.9 | 143-148 | 17.2 | 20.5 | 1 s of play, a 549 ms stall, Mido talk prompt | HITCH |
| 130.9-135.9 | 148-158 | 31-33 | 0.0 | Mido dialogue scene (dark) | CUT |

### Try 2 (exit path at night, Saria bridge, area after the exit)

| Game s | Video s | fps | fence ms | What is on screen | Kind |
|---|---|---|---|---|---|
| 20.8-55.9 | 238-278 | 54-60 | 0-2 | title, file select | MENU |
| 60.9 | 278-283 | 9.1 | 17.8 | load (678 ms stall) | LOAD |
| 65.9 | 283-288 | 27.8 | 0.0 | Mido dialogue at night, "Kokiri Forest" title | CUT |
| 70.9-81.0 | 288-303 | 29.5-34.1 | 0.0 | dark path past Mido, dark tunnel | play, light |
| 86.0-121.1 | 303-343 | 36-40 | 0.0-0.2 | Saria bridge cutscene, ocarina | CUT |
| 126.1-131.1 | 343-353 | 47-57 | 0.0 | black screen, area change | LOAD |
| 136.1-148.2 | 353-370 | 13-23 | 6-36 | cave mouth, ocarina tutorial, song, "Saving…", stalls of 0.7-3.1 s | LOAD / HITCH |
| 153.3 | 370-375 | 27.1 | 0.3 | out of the cave onto the misty path | play |
| 158.3 | 375-380 | 21.4 | 0.0 | crossing the stream (944 ms stall) | play + HITCH |
| 163.3 | 380-385 | 25.8 | 4.0 | up the path; stops at video 383.4 (last LSTICK at game 161.5) | play |
| 168.3 | 385-390 | 27.6 | 4.1 | **standing still, looking down the path**: rock arch in the mist ahead, cliff on the right | play, path |
| 173.3 | 390-395 | 27.2 | 2.9 | same, still | play, path |
| 178.3 | 395-400 | 11.8 | 9.8 | camera turned right (RSTICK, game 174.2-176.0), then a 2.5 s stall | HITCH |
| 183.3 | 400-405 | 34.8 | 0.0 | **standing still, facing the bank/slope**, short view | play, wall |

### The steps

- **Kokiri, down (sharp):** 32-33 → 18 fps, about −14 fps.
  - Seen in the video as 33 → 26 → 21 → 19 → 17 over video 103-107, and in the 30-frame ticks as 34 → 26 → 21 → 18 at app 104.4-108.7.
  - It is a boundary: the moment he leaves the tunnel and the village with the water comes into view.
- **Kokiri, up (gradual):** 18 → 33 fps over about 12 s (ticks 17, 18, 19, 20, 21, 22, 23, 24, 27, 29, 30, 31, 33 at app 110-134). It follows how much of the water and village stays in view as he walks away from it. This fits his "as soon as I pass the big open area/the water, the fps rises".
- **Area after the exit:** 26-28 fps looking down the path, 35 fps facing the bank. That is +7 to +8 fps, about −8 ms a frame (36.5 → 28.8 ms). The turn itself is hidden behind a 2.5 s stall.

## 2. Windows and every quantity the logs give

| Quantity | Kokiri light (try 1, app 95-105) | Kokiri heavy (try 1, app 105-120) | Field: path (try 2, app 185-195) | Field: bank (try 2, app 200-205) |
|---|---|---|---|---|
| View | dark ravine path, then tunnel | village with water and stepping stones | still, looking down the misty path | still, facing the bank |
| fps (vi2) | 31.6 / 32.2 | 18.7 / 17.8 / 20.3 | 27.6 / 27.2 | 34.8 |
| mean frame ms | 31.6 / 31.0 | 53.5 / 56.0 / 49.2 | 36.2 / 36.7 | 28.8 |
| fence wait ms a frame | 0.2 / 1.9 | 19.6 / 17.0 / 25.1 | 4.1 / 2.9 | 0.0 |
| frame minus fence, ms | ~31 / 29 | ~34 / 39 / 24 | ~32 / 34 | ~29 |
| last-600 summary | (98.98, incl. load) fence 0.75 ms, vblank pacing 8.5 ms, 268 ahead | (125.2) frame 43.8, fence 13.8, vblank pacing 2.0, 441 ahead | (193.7) frame 39.0, fence 2.3, vblank pacing 0.6, 569 ahead | none |
| command-list entries a frame (FETCH_COUNT "submit copy") | 3672 (app 97.7-107.2, includes ~2 s heavy); 3210 at the later light path (126-136) | 10482 (107.2-112.7), 8657 (112.7-118.9); 6071 easing (118.9-126.3) | 4261 (181.0-190.1, walking + still) | no clean window (190.1-202.0 straddles the stall: 3923) |
| resumed / empty-at-submit a frame | 7.1 / 50 | 5.9-6.9 / 47-50 | 7.0 / 58 | none |
| radv submissions a frame | 53.2 (90.0-99.3) | 65.5 (109.0-119.4) | ~57 (assumes a 10 s window, ~270 frames) | no clean window |
| radv kwords a frame | 200 | 361 | ~200 (same assumption) | no clean window |
| radv submissions a second | 1495 | 1238 | ~1500 | no clean window |
| agc_ms / suspend_ms a frame | 9.0 / 16.9 | 11.0 / 24.0 | ~13 / ~17 (same assumption) | no clean window |
| (agc + suspend) per submission | 0.49 ms | 0.53 ms | ~0.52 ms | no clean window |
| pipelines built on the GPU thread (10 s line) | 15 built, 56 ms (mesh 11), at 103.0 | 8 built, 211 ms (mesh 7), at 122.6 | 52 built, 683 ms (new 22, mesh 11), at 190.9 | none logged |
| kept translations (10 s) | 9, 23.8 ms | 3, 6.8 ms | 19, 16.1 ms (at 196.9) | none |
| new mesh pipelines (first draw) | 3 + 3 | 2 + 0 + 1 | 0 | 0 |
| texture cache "out of memory" | 0 MiB | 0 MiB | **3072 MiB** (over budget the whole time) | 3072 MiB |
| over-budget image allocations / 5 s | 0 | 0 | 0-2 | 0 |
| guest core wakeups / 5 s (c4, c5) | 16.5k, 15-16k | 6-10k, 7-9k | 14k, 14k | none (window has the stall) |
| draws a frame, query reports, uploads, front wait, back idle, GPU time | **not logged** | **not logged** | **not logged** | **not logged** |

Notes:
- The radv windows are placed in time with the EDEN_AREA_EVICT frame numbers that bracket each line, ±16 to ±22 frames for the Kokiri windows. The Kokiri light radv window starts 1 s after the load, so it is slightly mixed.
- In the area after the exit the bracket is loose, so those radv figures assume a 10 s window.
- The bank window is only ~5 s and follows a 2.5 s stall. Only the vi2 line and the 30-frame ticks (35-36 fps) cover it cleanly.

## 3. What moves with the fps

**Moves with fps (Kokiri):**
- Command-list entries a frame: ×2.7.
- radv command words a frame: ×1.6-1.8.
- radv submissions a frame: ×1.2.
- Fence wait: 0-2 → 17-25 ms.
- agc and suspend ms a frame: up about 9 ms together.
- Guest core wakeups: down (the guest waits more).

**Does not move:**
- The frame time minus the fence wait (~30 ms in both views).
- Submissions a second (1240-1500 everywhere, cutscenes included).
- agc + suspend per submission (~0.5 ms).
- Texture memory margins (0).
- New mesh pipelines and pipeline builds (small, not larger in the heavy view).
- Resumed and empty entries a frame.

**Reading, using the rules set before the test:**
- **Kokiri heavy view.** The extra ~20 ms is all fence wait: the present waits for the GPU side to finish frame N while the CPU side keeps its usual ~30 ms. So the limit in the village is on the GPU side of the hand-over, and it scales with the command traffic of the view.
  - Whether that is the GPU thread's back (recording Vulkan for the extra draws), the radv submission thread, or the GPU itself (water, mist, resolution), the log cannot tell. There is no back-idle or front-wait line and no GPU time.
  - The "front's waits grow" case and the "back idle vanishes" case cannot be tested.
  - The rise in suspend ms a frame (17 → 24) points the same way (the submit side waiting longer), but the line does not define "suspend".
- **Kokiri light view and the field path.** The fence is near 0, so these frames (31-37 ms) are limited on the CPU side: the game thread, or its hand-over to the GPU thread front. Frame time still rises with command traffic here: Saria cutscene 2.2k entries → 25-27 ms, light Kokiri 3.2-3.7k → 31-34 ms, field path 4.3k → 37 ms. That suggests the per-entry cost sits partly on the CPU side too.
- **Field path vs bank (8 ms).** No logged quantity separates the two views (the windows straddle the stall), and the fence does not move. The field also runs with the texture cache 3 GiB over budget and builds pipelines (683 ms in 10 s), which Kokiri does not. These are extra costs that do not depend on view direction.
- **Needed to settle it:**
  1. A per-5 s GPU-split line: front busy/wait ms, back busy/idle ms, and draws recorded a frame.
  2. EDEN_GPU_TIME (GPU ms a frame).
  3. The radv window length printed in the submissions line.

## 4. Milliseconds per unit (Kokiri heavy minus light)

Assumption: all of the extra frame time comes from the extra command traffic of the village view, and everything else per frame is unchanged. This is a correlation. "More on screen" also means more pixels of water and mist, which these logs cannot separate.

| Unit | Light → heavy a frame | Δ frame ms | ms per unit |
|---|---|---|---|
| command-list entries (FETCH_COUNT "submit copy") | ~3.4k → ~9.6k | +21.6 | **~3.3 ms per 1000** (fit over 5 Kokiri windows: 22.2 ms + 3.25 ms/1000, r = 0.99; all 10 windows of both tries: 20.3 + 3.51 ms/1000, r = 0.98) |
| radv command kwords | 200-237 → 361 | +21.6 | ~0.13-0.17 ms per 1000 words |
| radv submissions | 53-54.5 → 65.5 | +21.6 | ~1.9 ms per extra submission (much more than the 0.5 ms agc + suspend a submission costs, so heavier submissions, not more of them, carry the cost) |

## 5. Bench spots (load the Kokiri Forest autosave)

The autosave starts on the grassy hill with sunbeams at the forest edge. Walk straight ahead (the only path).

- **Light (31-33 fps):** about 6-10 s after load, in the **dark ravine path** before the tunnel. Rock walls on both sides, mist on the floor, dark with fireflies. Face forward along the path, away from the hill. See still 01. The narrow wooded stone stairs on the far side of the village (still 06) is a second light spot at 33 fps.
- **Heavy (17-19 fps):** about 15-20 s after load, go through the short tunnel and stop **2-3 steps past the tunnel mouth**, facing straight into the village. The water channel with flat stepping stones is in front, the big tree and the shop/house with a sign are upper right, mist all over. See still 03. Standing on the stepping stones in the middle of the water, facing the village centre, also gives 18-19 fps (still 04).

The two spots are about 10 s apart on one straight walk, so one load covers both. For the area after the exit, the path/bank pair (stills 07 and 08) is usable but sits behind a cutscene, loads and stalls.

## Stills (fps-by-view-2026-11-11/)

01 dark ravine path (F32) · 02 tunnel to the village (F35) · 03 tunnel exit, village and water (F18) · 04 stepping stones over the water (F19) · 05 stone path past the water (F28) · 06 wooded path and stairs (F33) · 07 field, looking down the path (F27) · 08 field, facing the bank (F35)

## Uncertainty

- The 5 s lines are coarse.
- The video-to-log offset is ±1 s.
- The radv windows have no printed length.
- FETCH_COUNT "submit copy" is the best stand-in for draws in these logs, but it is not a draw count.
- Menus, cutscenes and loads are marked and left out of all figures above.

## Correction, 11 Nov 09:27 (profile at the heavy spot, run1076)

Draw counts in this note were derived from flush counts. The profiler's own count: about 3,970 draws a frame at the heavy spot (not 3,030) and 860 at a wall view in the ravine. Per draw the back thread's zoned work is about 8.7 us (bind stage buffers 2.0, configure 1.05, update buffers 0.97, read handles 0.94, draw 0.92, fill image views 0.77, flush work 0.69). The driver's submit runs on the VulkanWorker thread, so agc time is not part of the back thread's 87%. Both 17.6 and 36.5 fps were taken without the usage tracker. Details: `the the project log`, 11 Nov 09:27.
