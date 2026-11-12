# Fresh install, cycle v7: nine new-game starts, three settings groups (T134, 12 Nov 2026, 09:22-10:57)

> **Found:** Nine new-game starts on a fresh install (T134), three settings groups: 7 of 9 reached the village. With two pipeline builders, the memory gate and the hand-backs (g2) a true first start reached the village for the first time, as a near miss (pool at 0 MiB for ~6 s, 85 s black screen). Two builders removed the door burst on warm starts (0 of 4), not on cold ones.
>
> **So:** Two builders are worth keeping for restarts. A first start still dies at the door when the file service asks for a 0.9 MB buffer while the pool is empty, so g2 needs more cold starts before it counts.

Read-only check, 12 Nov ~11:00-12:00. No console touched, no test started, nothing posted, no file changed
except this note. READ = seen in a log, frame, video check or source. INFERRED = my reasoning.
Method as in `fresh-install-v6-2026-11-12.md` and `door-burst-source-2026-11-12.md` (census lines in
stderr, script marks placed by their position in stderr; app clock = EDEN_GUEST_START + script time).
Control = v6 G1 (run1271-1273, same build, script and cache handling). One group of three is no verdict.

## Answer first

- **7 of 9 starts got through** (script_end line=126 + script_done, no crash file). Both deaths were cold starts,
  both at the house door, both the same request: the file service asked for a 902,912-byte reply buffer and the
  pool said no.
- **Both changes move the first-start death out of the house.** Control cold starts: 0 of 3 left the house.
  v7: 3 of 3 cold starts reached the door (g1, g2, g3). g2's cold start reached the village and stood out its
  60 s: **the first true first start to get through in any cycle.** (second check: for g3 "out of the house" is
  ~4 s of progress. The control died ~10 s after the house control; g3 died 2 s after the door's A, which is
  ~14 s after it. Same stretch of the walk, a different request. B alone is no clear gain.)
- **Two builders remove the door burst on warm starts (0 of 4), not on cold ones (2 of 2 still burst).** With
  8 builders, 5 of 6 warm starts burst (v6 4 of 4, g3 1 of 2). The memory gate barely acted in g1 (1 wait per
  run), so this is the builder count, not the gate.
- **g2's cold pass was a near miss, not a margin:** pool at 0 MiB for ~6 s on arrival, 64 driver refusals, a
  ~12 s near-frozen picture there, and the longest first-scene black screen seen so far: **85 s** (control 47 s).
  (second check: the pool **never came back** in the village. Its largest free block was 0-46 MiB for the whole
  60 s, median 32 MiB (warm runs: median 95-284). 22 images found no memory, 20 of them screen-size render
  targets, from 577 s to 625 s (after the script's end too). All that time the heap held ~588 MiB of empty
  2 MiB pages and gave back 0 MiB, even on "a buffer was refused". The card marks the run NOT valid for
  fps/flashes because of the 12 s stall. Its fps from the gameplay WAIT to the end was 16.7, worst frame 4,326 ms.)
- **Cost on warm starts: none seen.** Village fps 23.9-25.8 against the control's 23.6, worst village frame
  297-778 ms against 718. Cost on a cold start: +14 s (g1) / +37 s (g2) of black screen at the first 3D scene.

| Start | Valid | Got to / ended | First-scene black (video) | House: largest free / heap pieces / live / empty | Door burst | Lowest pool | Driver refusals | Gate waits | Village fps / worst frame |
|---|---|---|---|---|---|---|---|---|---|
| g1-1 cold run1288 | yes, COLD | out of the door; **crash 542 s**, ~10 s after A | 61.3 s (frozen 53.2, one frame 31.0 s) | 322 / 1,696 / 847 / 468 MiB | **+416 MiB** grown and given back within ~2 s | 2 MiB | 0 | 1 of 2,203, 14 ms | - |
| g1-2 warm run1289 | yes, WARM 1083 | village, 60 s, **script done** | 23.8 s (one frame 4.8 s) | 354 / 1,376 / 843 / 238 | **none** (+0; live +7) | 0 MiB (arrival) | 1 (960 KiB) | 1 of 2,215, 2 ms | 23.9 / 778 ms |
| g1-3 warm run1290 | yes, WARM 1188 | village, 60 s, **script done** | 18.1 s | 624 / 1,248 / 861 / 96 | **none** (+0; live +10) | 2 MiB | 0 | 1 of 2,287, 2 ms | 25.8 / 340 ms |
| g2-1 cold run1291 | yes, COLD (card: not valid for fps/flashes, 12 s stall) | village, 60 s, **script done**; pool 0-46 MiB all 60 s | **84.6 s** (frozen 76.3, one frame 41.6 s) | 284 / 1,568 / 852 / 368 | **+608 then +576 MiB** (two waves, ~8 s apart), given back | **0 MiB for ~6 s** | **64** (1.4-15.6 MiB) | **97 of 2,326, 48.8 s** (33 / 30.1 s at the first scene) | 23.6 / 687 ms; 12 s stall on arrival (frames to 4.3 s) |
| g2-2 warm run1292 | yes, WARM 1170 | village, 60 s, **script done** | 18.0 s | 755 / 1,184 / 847 / 58 | **none** (+0; live +9) | 6 MiB | 0 | no wait line | 24.5 / 297 ms |
| g2-3 warm run1293 | yes, WARM 1195 | village, 60 s, **script done** | 18.9 s | 733 / 1,152 / 804 / 66 | **none** (+0; live +12) | 1 MiB | 0 | no wait line | 24.7 / 352 ms |
| g3-1 cold run1294 | yes, COLD | at the door; **crash 517 s**, ~2 s after A | 48.4 s (frozen 40.3, one frame 18.1 s) | 96 / 2,112 / 888 / 632 | not seen (died first) | 6 MiB | 0 | (no gate) | - |
| g3-2 warm run1295 | yes, WARM 1075 | village, 60 s, **script done** | 18.2 s | 512 / 1,344 / 805 / 218 | **+672 MiB**, given back | 1 MiB | 1 | (no gate) | 23.6 / 795 ms; 2.2 s frame at the door |
| g3-3 warm run1296 | yes, WARM 1178 | village, 60 s, **script done** | 18.1 s | 711 / 1,184 / 809 / 114 | **none** (+0; live +8) | 8 MiB | 0 | (no gate) | 24.9 / 310 ms |

Control for comparison (same method): v6 cold run1271/1274: first-scene black 47.0 / 47.5 s (frozen ~39 s,
one frame 17.8 / 18.0 s), house pieces 2,816 / 2,912 MiB with 1,364 / 1,416 MiB empty, died in the house.
v6 run1273 (the one that got through): door burst +704 MiB, lowest pool 0, 16 driver refusals, village
23.6 fps, worst village frame 718 ms, 2,144 ms frame at the door.

Words: **pool** = the console memory everything draws from; **largest free** = its biggest free block;
**heap pieces** = what the emulator's own store took from the pool; **live** = in use; **empty** = taken but
holding nothing; **door burst** = heap growth in the seconds after the door's A (A = the script's
`wait_met line=117`); **builders** = background threads that compile drawing recipes (pipelines).

## Validity (all 9 valid, READ)

- Build: each batch's `eboot.json` = sha256 7f14d75d16b8fd02... (T134); `install-t134.v6.sh --check-only`
  "T134 is installed" before each group and at verify.
- Env: each run's env.txt = its plan line for line (g1 82, g2 83, g3 81 lines) plus only EDEN_TEST_BOOT and
  EDEN_TEST_SCRIPT; each batch's plan.json = the draft plan. Every planned switch has its `EDEN_ENV` line in
  heap.log. g2/g3 have no `EDEN_ENV EDEN_HEAP_KEEP_ARENAS` line; g1 has it.
- Start lines (eden_log): `Pipeline builders: 2 of 15` (g1, g2) / `8 of 15` (g3); `EDEN_PIPELINE_MEMORY_GATE:
  builds take turns under 256 MiB free, waiting at most 2000 ms, builders' driver compiles too` (g1, g2; at
  25.7 s on a cold boot, 3.7-5.5 s warm); `Stream ring 64 MiB, regions of 4096 KiB` (g2, g3); VMA heap lines
  with 8 MiB blocks (g2, g3: heap 0 "VMA blocks 8 MiB" against 24 in g1). B's spares acted: `spare=` and
  `reused=` above 0 in g2 and g3 (g1: 0/0 all session).
- The queue's SWITCH LINT called `EDEN_PIPELINE_MEMORY_GATE_WORKERS` "DEAD". That is a false alarm: the T134
  source reads it (vk_pipeline_cache.cpp:609) and the start line names "builders' driver compiles too".
- Caches: cold proof COLD for run1288, 1291, 1294 (0 on disk, all three caches absent before the group); WARM
  1083/1188, 1170/1195, 1075/1178 pipelines on disk. Config matched a fresh install for all nine.
- Cycle end: `THIRD PASS DONE` 10:57:49; the owner's caches, env v2.7, config and save are back and checked; no
  pending restore, latched stop or hang flag. (second check: the g3 card.md exists now; its analysis finished after
  this reading. g3 flashes: run1295 25.9/min, run1296 25.1/min, 0 full-scene. Card fps 19.6 / 21.1.)

## Per start

**g1-1, run1288 (cold, A = two builders + gate).**
- First scene: video black 206.0-267.4 s (61.3 s), frozen 212.2-265.4 s. 5 s lines: a 12.0 s and a 16.5 s
  frame, near-zero fps ~225-267 s app. Builds spread out: 125 + 98 + 53 + 53 + 43 new per 10 s (control:
  141 + 136 + 58 + 38).
- After the first scene: 347 arenas (control 794-821), 550 MiB empty pages, 276 MiB idle arenas (control
  1,408-1,502 / 982-1,038).
- House: control at app 520.8 s (control cold 503.5-504.6). Largest free 322 MiB, pieces 1,696, empty 468.
- Door: A at app 532.4. Frame f0108 shows the player walking out of the door; f0109 black; f0110 the app's
  "stopped because of an error". 2-4 s after A the heap grew +416 MiB (the 256 KiB-1 MiB class, 1,952 -> 2,368)
  and gave it back in the same 2 s (`gave back 416 MiB: the pool is short`); GPU thread stale at that sample.
  Door builds: 31 new, 0 from disk, 4 mesh in one 10 s window.
- End: crash 542 s (~10 s after A). `EDEN_HEAP_FAILURE requested=902912 reason=2`, FS thread. Symbolized on
  T134's llvm-pie.elf: `ScratchBuffer::resize_destructive` <- `IStorage::Read` <- `CmifReplyWrapImpl<IStorage>`
  (the reply buffer of a file read; the frame at eboot+0xb86d5 is the terminate handler, as in v6). Pool 2-10 MiB
  in the last 4 s; the heap still held 450 MiB empty (274 MiB idle arenas) it could not use for this request.

**g1-2, run1289 (warm): got through.**
- Black 23.8 s (frozen 15.7; one 4.8 s frame; 8 new pipelines at that scene). End `script_end line=126
  at=503.839`, `script_done`, 60 s from A to the end.
- Door: A at 459.5. Live 818 -> 825, heap growth +0. Builds: 4 new, 26 from disk, 6 mesh. A 754 ms frame 10-15 s
  after A.
- Village arrival: pool 0-1 MiB, one driver refusal (960 KiB), recovered. Village 23.9 fps, worst 778 ms.

**g1-3, run1290 (warm): got through.** Black 18.1 s. Door: live 822 -> 832, growth +0, builds 1 new / 38 disk /
6 mesh. Pool 2 MiB at its lowest (a few seconds after A). 0 refusals. Village 25.8 fps, worst 340 ms.
`script_end line=126 at=503.725`, `script_done`.

**g2-1, run1291 (cold, A + B): got through.**
- First scene: video black 206.2-290.9 s (**84.6 s**), frozen 212.5-288.7 s (76.3 s); one frame 41.6 s
  (report.txt). The gate made builds wait here: `33 of 836 builds waited, 30143 ms in all, 11 at the limit` by
  283.5 s. Largest free dipped to 224 MiB (g1: 354), under the gate's 256 mark. 6 hang-watch lines.
- After the first scene: 312 arenas, spare 94, reused 29; 458 MiB empty, 218 idle.
- House: control at app 548.4 (45 s later than the control cold starts). Largest 284, pieces 1,568, empty 368.
- Door: A at 560.0. Two waves: +608 MiB (pieces 1,600 -> 2,176, live 856 -> 1,246, GPU stale) ~2 s after A,
  given back at once (576 MiB); a second +576 ~10 s after A (gave back 352). Growth in the 256 KiB-1 MiB class
  +1,184 MiB in ~10 s. 57 spare arenas were reused during the waves (286 -> 343). Door builds: 27 new, 0 disk,
  4 mesh.
- Arrival: 64 driver refusals (`no memory for 1408-15652 KiB ... still no memory`), largest free 0 MiB for ~6 s,
  guest reserve 0, GPU thread stale up to 3.9 s. Card: "stalled 12 s in gameplay (from about 577 s app time),
  then went on", worst 4,326 ms. The frames recovered, **the memory did not** (second check): largest free block
  0-46 MiB in all 21 village censuses, 10 of them at 16 MiB or less; 22 images refused (20 render targets,
  577-625 s); report.txt fps last minute 15.5. Heap 1,824 MiB of pieces with 584-592 MiB empty pages from
  ~558 s to the end, "given back so far" stuck at 3,616 MiB.
- Village: frame f0127 shows the player on the porch above the village with the greeting and control back.
  `script_end line=126 at=611.224`, `script_done`. Village 23.6 fps, worst 687 ms; A-to-end 18.4 fps.
- End: largest 17-32 MiB, pieces 1,824, live 859, empty 588. Gate: 97 of 2,326 waited, 48.8 s in all.

**g2-2, run1292 (warm): got through.** Black 18.0 s. Door: growth +0, live +9, builds 3 new / 33 disk / 5 mesh.
Lowest pool 6 MiB. 0 refusals. Village 24.5 fps, worst 297 ms. No gate wait line. `script_end` + `script_done`.

**g2-3, run1293 (warm): got through.** Black 18.9 s. Door: growth +0, live +12, builds 0 new / 33 disk / 7 mesh.
Lowest pool 1 MiB (village arrival). 0 refusals. Village 24.7 fps, worst 352 ms. `script_end` + `script_done`.

**g3-1, run1294 (cold, B alone).**
- First scene: black 48.4 s (frozen 40.3; one frame 18.1 s): like the control (8 builders).
- After the first scene: 537 arenas, spare 185, reused 169, given back 354; still 788 MiB empty, 466 idle.
- House: control at 503.2 (as the control). Largest only 96 MiB, pieces 2,112, empty 632. It left the house
  (control 0 of 3).
- Door: A at 514.8. Frame f0103 shows the player running to the door. Pool largest 6 MiB at A.
- End: crash 517 s, ~2 s after A. Same request, same thread, same stack as g1-1 (`requested=902912 reason=2`,
  FS, IStorage::Read reply buffer). The heap held 656 MiB empty pages (173 spare arenas) at the time.

**g3-2, run1295 (warm): got through, with the burst.** Black 18.2 s. Door: +672 MiB growth (pieces 1,344 ->
2,016, live +75 at the samples), given back; GPU stale; a 2,156 ms frame 10 s after A; pool 1 MiB; 1 refusal.
Builds 5 new / 30 disk / 4 mesh. Village 23.6 fps, worst 795 ms. `script_end` + `script_done`.

**g3-3, run1296 (warm): got through.** Black 18.1 s. Door: growth +0, live +8. Lowest pool 8 MiB. 0 refusals.
Village 24.9 fps, worst 310 ms. `script_end` + `script_done`.

All nine: 0 junk-family lines (unbound subchannel, topology, unmapped reads). Video checks: no white or noise
stretches beyond the normal transitions; the one "patch" event in run1295 (~353 s) sits where v6's runs had it.

## (1) Do two builders + the gate remove or shrink the door burst?

**On warm starts they remove it; on cold starts they do not.** (READ for the sizes, INFERRED for the cause.)
- Warm starts with 2 builders: 0 of 4 had a burst (run1289, 1290, 1292, 1293: growth +0, live +7 to +12).
  With 8 builders: 5 of 6 (v6 run1272 +686, 1273 +704, 1275 +698, 1276 +602; g3 run1295 +672; g3 run1296 none).
  Fisher, 0/4 against 5/6: p ≈ 0.02-0.05. Same door work in both: 3-5 new, 26-38 from disk, 4-7 mesh builds.
- Cold starts with 2 builders: 2 of 2 burst (g1 +416, g2 +608 then +576). At a cold door 27-31 builds are new.
- **The gate did not do it.** In g1 it waited once per run (2-14 ms) and never at a door. A build waits only
  while another build runs and the pool's largest block is under 256 MiB; with 2 builders that rarely happens.
  In g2 it waited 97 times, mostly at the first 3D scene (33 waits / 30 s by 283 s), where it lengthened the
  black screen.
- The burst is visible to a player: every run with a burst had a ~2.1-2.2 s frozen frame within 10 s of the
  door's A (run1273, run1295, run1291); runs without it stayed at 362 ms or less there, except one 754 ms frame
  in run1289.
- INFERRED: fewer driver compiles at once means less compile memory at once. On a cold door there are ~30 new
  compiles in a few seconds, so even 2 at a time make a burst. Fits the door-burst note's best lead (the driver's
  build of the door's mesh pipelines).

## (2) What the hand-backs add on a cold start, and why g2 lived

**The two builders did most of the house work; the hand-backs added less; together they left the least heap.**

| Cold start | Arenas after first scene | Empty / idle after first scene | House: pieces / empty | House largest free | Died |
|---|---|---|---|---|---|
| control v6 (2) | 794-821 | 1,408-1,502 / 982-1,038 | 2,816-2,912 / 1,364-1,416 | 7-80 | in the house |
| g3 B alone | 537 (185 spare, 169 reused) | 788 / 466 | 2,112 / 632 | 96 | door, +2 s |
| g1 A alone | 347 | 550 / 276 | 1,696 / 468 | 322 | door, +10 s |
| g2 A+B | 312 (94 spare, 29 reused) | 458 / 218 | 1,568 / 368 | 284 | lived |

- Why g1 and g3 died at the door (READ in source + logs): the request was 902,912 bytes. Requests of 256 KiB or
  more never go to the arenas: they go to the heap's main space (heap_arenas.inc:2515-2536), which grows from
  the pool. The rescue that asks other arenas is off (`EDEN_UP_HEAP_RESCUE=1`, heap_pages.cpp:157, is in no
  group's env), and it skips spares anyway (heap_arenas.inc:1958-1962). A cheap env-only candidate for the
  next cycle (it covers requests up to 4 MiB; a 0.9 MB buffer fits a 2 MiB arena only if one is near empty). So the 450 MiB (g1) and 656 MiB (g3) of empty heap pages could not serve
  it; only the pool could, and it was at 2-10 MiB (g1) and 6 MiB (g3).
- What B measurably adds next to A (g2 against g1): 128 MiB less heap at the house, 64 MiB less upload ring
  (census `stream=64` against 128), ~100-150 MiB less driver slack at the door (vma_slack 257-312 against
  376-462), and 57 spare arenas reused during the door waves instead of fresh pool. About 300 MiB in all
  (INFERRED sum).
- Why g2 lived where g1 died is **not fully visible**. The logs do not show when g2 asked for the 902,912-byte
  buffer. (second check: "70 against 224 MiB at A" compared different moments. At A itself g1 had 93 MiB. Same
  moments after A, census largest / low, MiB, READ:)

  | After A | g1 cold (died A+9.6) | g2 cold (lived) | g3 cold (died A+2.2) |
  |---|---|---|---|
  | 0 s | 93 / 93 | 70 / 70 | 6 / 6 |
  | +2 s | 176 / 150 (heap +416) | 192 / 106 (heap +576) | 32 / 32, then dead |
  | +4 s | 192 / 2 | 128 / 27 | |
  | +6 s | 129 / 129 | 128 / 128 | |
  | +8 s | 64 / 10, then dead | 128 / 17 | |
  | +10 to +16 s | | 3 / 3 (heap +576), 32 / 3, 49 / 6, 7 / 1 | |

  At g1's death g2 had ~840 MiB free in all against g1's ~475, so it had more total room at that second.
  Its largest block was still only 128 MiB, and 2-8 s later it fell lower than g1 ever did (3, then 1 MiB),
  and it stayed at 0-46 MiB for the rest of the run. **The margins do not explain the survival. Timing luck
  is the main part**, plus maybe that its second door wave kept 224 MiB of new heap pages (the heap gave back
  352 of 576) where g1's gave all 416 back (INFERRED: a 0.9 MB request needs those main-space pages).
- (second check) An env-only switch aimed at exactly this death exists and was in no group: `EDEN_UP_NEW_WAIT_MS`
  (headless/main.cpp:359-436, memory_wait.h). With it, operator new on the file-service thread waits in 20 ms
  steps instead of throwing. In g2-cold the pool came back to 32-128 MiB within 2-4 s each time. It has never
  fired in a field run (v6 G2 had only HEAP_STEAL=3), so it needs its own arm before it counts.
- **Near miss, not a margin.** Pool largest 0 MiB for ~6 s, guest reserve 0, 64 driver refusals, GPU thread
  stale up to 3.9 s, a 12 s near-frozen picture on arrival (frames up to 4.3 s), 4.3 s worst gameplay frame.
  Survived because no request that cannot wait came in those 6 s.

## (3) What it costs

- **Cold first 3D scene (black screen in the video):** control 47.0 / 47.5 s, g3 48.4 s, g1 61.3 s (+14),
  **g2 84.6 s (+37)**. Longest single frame: control 17.8 / 18.0 s, g3 18.1, g1 31.0, g2 41.6 s. Two builders
  spread the ~400 new builds over more time; in g2 the gate added ~30 s of waits on top.
- **Warm first scene:** 18.0-18.9 s in five of six warm starts against the control's 18.0-18.3 s; run1289
  23.8 s (one 4.8 s frame, 8 new pipelines). No cost seen.
- **Time to the village:** warm starts reach the house at app 443.6-448.9 s (control 443.1) and the door A at
  454.7-460.5 (control 454.3): no cost. g2's cold start reached the house at 548.4 s, 45 s after the control
  cold starts (503.5-504.6), and the door A at 560.0.
- **Village (from 25 s after A to the script's end, 5 s windows):** control run1273 23.6 fps, worst 718 ms.
  g1 23.9 / 778 and 25.8 / 340; g2 23.6 / 687 (cold), 24.5 / 297, 24.7 / 352; g3 23.6 / 795, 24.9 / 310.
  Card game fps: g1 20.6 / 21.2, g2 20.9 / 21.1 (control card not compared). No fps loss from 2 builders, the
  64 MiB ring or 8 MiB driver blocks.
- **Picture faults:** none new. 0 junk lines in nine runs. Flashes per minute (card): g1 26.6 / 32.6 (one
  full-scene in run1290), g2 22.8 / 25.9 (none full-scene); g3 25.9 / 25.1 (none full-scene; second check, from
  the card that finished later). Control run1273 24.4. No same-batch control, so no flash verdict.
  (second check: g2-cold's 20 refused render targets did not show as broken frames in f0114-f0127. The black near
  the end (video 613.7-617.3 s) is the same transition the warm runs show, ~1.5 s longer. Not checked frame
  by frame.)
- (second check) g2-cold speed after the door: A to the end 18.4 fps with a 4,325 ms frame (5 s lines); card 16.7;
  report.txt last minute 15.5. The "23.6" above is only A+25 s to the end, after the stall.

## (4) What a newcomer meets with g2's settings

- **One start to the village** (1 of 1 true first start; then 2 of 2 restarts through).
- **The longest black screen is ~85 s** at the first 3D scene (picture frozen ~76 s, one frame of 42 s). A
  newcomer may think it hung there.
- On arrival in the village: ~12 s of near-frozen picture, then normal play at ~24 fps.
- Restarts after that: ~18 s black, no door hitch, village ~24.5 fps.
- With one cold run, "one start is enough" is a hope, not a finding. g1 and g3 show the same door request
  kills a cold start when the pool is empty at the wrong second.

## (5) What must be repeated before g2's lines go into the shipped settings file

1. **Two more g2 groups (fs7-g2-s1-cold, fs7-g2-s2-warm, fs7-g2-s3-warm), each on empty caches.** That gives
   3 true first starts with g2. Needed: 3 of 3 cold starts reach the village (`script_end` + `script_done`),
   the 4 new warm starts with no door burst, and the cold black screen measured each time. One cold start that
   dies at the door means g2 is not ready.
2. **One "returning player" start:** the owner's full caches (a copy) with g2's env. `EDEN_NX2_PIPELINE_WORKERS`,
   `EDEN_STREAM_RING_MIB` and `EDEN_VMA_BLOCK_MIB` are all in the shader-store stamp list
   (vk_pipeline_prep.cpp:91, 133, 164), so every existing player's prepared store gets built again on the first
   start after the update. That start is half cold, and nothing here tested it. (second check: the stamp also holds
   the eboot's size and write time (BuildIdentity, same file), so **every new build already rebuilds the
   store**, with or without these lines. The returning-player start is what every tester does on each update.
   Still untested with g2's env.)
3. Not needed for shipping, useful for the build: g1 cold alone again would say whether A without B gets
   through sometimes. Lower priority than 1 and 2.

The cycle cap is three groups, so 1 and 2 fill the next cycle (two g2 groups + one returning-player group).

## What the test could not see

- When g2's cold start made the 902,912-byte request, so why it lived where g1 died.
- The gate's waits at the door in g2 (its line prints at most every 10 s and nothing printed between 392 and
  628 s; 32 waits fell somewhere in that span).
- g3-1's door: it died 2 s after A, before a census could show a burst.
- Why g2's heap kept ~588 MiB of empty pages for 60 s while the pool sat at 0-46 MiB (second check).

## In plain words (written for the project owner)

1. Nine new-game starts on a fresh install this morning: seven got to the village, two crashed at the house door.
2. For the first time a true first start got all the way to the village (the "fewer builders + hand-backs" set).
3. Fewer builder threads stop the big memory jump at the door on every restart (0 of 4), but not on a first start.
4. The price: on the very first start the black screen after the opening is longer, about 85 seconds instead of
   about 47. Restarts are not slower and play at the same speed.
5. The one first start that got through ran out of memory on arrival and froze ~12 s. Memory stayed almost
   empty for its whole minute in the village, so it got through partly by luck.
6. Before these settings ship: two more first-start groups and one "returning player" start.

## Checked a second time (12 Nov, ~11:30)

Read only. All nine run folders, the runner log, both crash reports and the T134 source were opened again.
No test was started and nothing was posted.

**Confirmed (READ):**
- Endings come from each run's own lines. 7 runs have `script_end line=126` + `script_done`: run1289, 1290,
  1291, 1292, 1293, 1295, 1296. Two crash reports: run1288 at 542 s and run1294 at 517 s. Both are
  std::bad_alloc on FS at eboot+0xb86d5 with the same stack, and `EDEN_HEAP_FAILURE requested=902912
  reason=2`. Largest free block in the reports: 6 and 4 MiB. Heap: 1,920 and 2,304 MiB.
- No start froze before its script ended.
- Caches: COLD proofs (0 / 0 / 0) for 1288, 1291 and 1294. WARM 1083/1188, 1170/1195, 1075/1178. `--status`
  before each group: shader and driver absent. Parks [1], [1,2], [1,2,3]. The owner's 40 files / 1,910 MiB
  are back at the end.
- Every switch reached the app: EDEN_ENV lines, `Pipeline builders: 2 / 8 of 15`, the gate start line,
  `Stream ring 64 MiB` and `VMA blocks 8 MiB` in g2 and g3 only. KEEP_ARENAS appears in g1 only.
  `EDEN_UP_NEW_WAIT_MS` and `EDEN_UP_HEAP_RESCUE` were in no group.
- Gate counts are as written: g1 1 wait per run (14 / 2 / 2 ms); g2-cold 1 → 33 → 65 → 97 waits; no gate
  line in the g2 warm runs.
- Door burst sizes match (+416, +576/+576 heap with the under-1 MiB class at +608/+576, +672). The warm
  2-builder runs show +0 to +32 MiB of heap. Fisher p for 0/4 against 5/6 is 0.024 one-sided and 0.048
  two-sided.
- Village fps and worst frames recomputed from the 5 s lines: they match the table.

**Changed:**
1. g2-cold "then recovered" was wrong for memory. The pool stayed at 0-46 MiB for the whole 60 s in the
   village. There were 22 image refusals (20 render targets) and the heap held ~588 MiB of empty pages
   without giving any back. The card marks the run not valid for fps/flashes (12 s stall).
2. g2 against g1 at the door: "70 against 224 MiB at A" compared different moments. At the same moments
   their largest blocks were about equal, and g2 later went lower. Survival is mostly timing (new table in (2)).
3. g3's "left the house" is ~4 s more of the same walk than the control. It is not a real gain.
4. The g3 card exists now: flashes 25.9 / 25.1 per min, 0 full-scene.
5. Returning player: a new build alone already rebuilds the prepared store (the eboot is in the stamp).
6. Added `EDEN_UP_NEW_WAIT_MS` as the untested env-only candidate for the file-service death.

**Advice from the second check.**
- *Tester default file now?* Yes, but only for the tester build, and only after one returning-player start
  passes. On every measured point g2 is equal to or better than today's default:
  - warm: 2 of 2 clean against v6 G1's 1 of 2, and no door burst;
  - cold: 1 village against 0 of 3 out of the house;
  - no fps or flash loss on warm starts.

  Testers are returning players, and that path (the store rebuilt, the driver cache kept) has not been run
  with g2's env. Tell testers that the first start after an install can sit on a black screen for ~85 s.
- *Smallest repeat for an alpha:* three starts in one cycle:
  - two more g2 true first starts on empty caches, parked between them, with no warm starts (the warm side
    already has 4 of 4 clean with 2 builders);
  - one returning-player start (a copy of the owner's caches with g2's env).

  Bar: both cold starts reach `script_end` + `script_done` with no crash, and the village pool stays above
  16 MiB in most censuses with no image refusals. g2-cold failed that last part. 3 of 3 cold is still thin:
  it only shows the pass rate is likely above ~37%. If either cold start dies at the door or sits at 0 MiB
  again, the next arm is g2 + `EDEN_UP_NEW_WAIT_MS=2000`, not more g2 repeats.
