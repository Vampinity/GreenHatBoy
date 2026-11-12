# Fresh install, round v10: six new-game starts with the IR_FREE lines (T134, 12 Nov 2026, 15:38-16:43)

> **Found:** Six starts with `EDEN_UP_IR_FREE=1` + `EDEN_UP_IR_FREE_RUNTIME=1` (T134): 6 of 6 reached the village, both true first starts included, but neither had memory to spare, and the door wave was as big as before (+448 to +640 MiB).
>
> **So:** Too few to call: on the same settings 2 of 2 first starts with the lines, 1 of 3 without. The next round (v11) on these settings lost both first starts, so these two passes were luck too.

Read-only check, 12 Nov ~16:50-17:30. No console touched, no test started, nothing posted, no file changed
except this note. READ = seen in a log, frame check, card, report or source. INFERRED = my reasoning.
Method as in `fresh-install-v8-2026-11-12.md` / `-v7-`: census lines in stderr, A = the last census before the
door's `wait_met line=117`, house = `line=108`, end = `script_end line=126`, placed by position among the census
lines (census clock ~26 s behind the app clock); app time = EDEN_GUEST_START + script time; game fps and worst
frames from the `nx2:vi2 5 s` lines; first-scene black from video-check.txt; worst frame of the run from
report.txt. Door window = A to A+15 s; village = A+15 s to the script's end, every census line counted
(area and area+3s checks included). One start is no verdict.

r1 = v8 r2 settings (2 builders + gate + no keep-arenas + ring 64 + VMA 8 + NEW_WAIT 2000 + HEAP_RESCUE)
+ `EDEN_UP_IR_FREE=1` + `EDEN_UP_IR_FREE_RUNTIME=1`. r2 = r1 with `EDEN_NX2_PIPELINE_WORKERS=1`.

## Checked a second time (12 Nov ~17:40, read only)

Recounted from the six run folders plus v8 run1304 and v9 run1307 / run1310. **These numbers stand:** all six
endings (`script_end line=126` + `script_done`, crash-index has no file after 13:34:48); IR_FREE lines (8 / 7 per
cold run, all at app 228-280, none later); rescue `214 served, 0 by none` in run1317 only, first printed ~A+21;
no NEW_WAIT or HEAP_FAILURE in v10; door censuses and lows; village checks (r1 23 checks, median 50, min 1, 6 at
16 or less; r2 23, median 124, min 8, 2 at 16 or less; warm as in the table); driver refusals 12 (3 placed on the
retry) and 14 (3); 1 refused image in run1320 (A+51.3); black 82.2 / 82.2 s; worst 38.8 / 50.5 s; gate 97 waits /
55.0 s (r1) and 54 ms (r2). No build failed after its memory was freed (the one "pipeline not ready" error is in
v8 run1304 too).

**Three things the reading got wrong or missed:**

1. **It left out round v9, which had r1's exact settings without the two IR_FREE lines.** run1307 and run1310
   env.txt differ from run1317 only in those two lines (and the script name); v8 run1304 likewise. Both v9 cold
   starts died at the door: `std::bad_alloc` on the FS thread, 583 s and 554 s, largest free block 3 MiB, **with the
   rescue and the wait on** (run1310 shows `EDEN_NEW_WAIT start requested=871571` at A+12.3, then the crash). So
   on identical settings: **without IR_FREE 1 of 3 cold starts reached the village (v8 r2 yes, v9 r1 and r2 no);
   with IR_FREE 2 of 2.** "With the rescue on, 3 of 3" is wrong: with the rescue on it is 3 of 5. The rescue
   alone is v9's set. 1 of 3 against 2 of 2 is still too few starts to tell apart.
2. **The rescue is not proven as the safety net.** In v9 it was on and missed the request that killed run1310
   (an ~0.9 MB operator new on the file thread; the v8 note already says the rescue can serve that size only from
   an arena with that much room in a row). In v10 r2 it served 0 and the start lived anyway, as v8 r2 did. Only
   run1317 used it (214 served; sizes and threads unknown). So "ship the rescue alone" is not supported.
3. **IR_FREE does change something, before the door, not at it.** Live heap at the last census before the door:
   cold v10 811 / 801 MiB against 857-858 in v8 r2, v9 r1, v9 r2; at app ~300 s 718 / 713 against 766-772. Warm
   780-791 against 807-829. That is the ~49 MiB the GPU thread's translation pools used to keep (RUNTIME frees it;
   source comment at vk_pipeline_cache.cpp:473-475). Heap pieces held at the door are the same (1,600 with two
   builders), so this is ~50 MiB of extra free room inside the heap, small next to a 450-640 MiB wave (INFERRED:
   it may or may not be what kept r1 alive).

**Could the two passes be luck again? Yes, it cannot be ruled out.** At the same moments the census caught a live
heap jump in both v9 deaths (+708 MiB at A+2.0 in run1307; +809 at A+12.3 in run1310). In both v10 cold starts,
and in the v8 r2 pass, the censuses at the waves show heap pieces growing by 448-640 MiB but live heap up only
26-66 MiB, with the growth given back within ~2 s. A 2 s census cannot tell a smaller wave from a wave it missed.
r2 lived with 0 rescues, exactly as v8 r2 did. Only r1 shows something new (214 rescues), and the same rescue
failed in v9.

**The black-screen cost is not shown.** Without IR_FREE, v9's two cold starts had 86.9 s black (gate 68.8 s of
waits, worst frame 41.6 s) and 71.1 s (gate 0.1 s, worst 30.7 s). The no-IR_FREE range is 65.5-86.9 s, and v10's
82.2 s sits inside it. v9 r1 also reached the door later (script 561.5 s) than v10 r1 (553.4 s). The ~14 s and the
"door 20-34 s later" are run-to-run spread on this evidence. The v11 rule "82 s with ~1 gate wait = IR_FREE's" also
fails: v9 r2 had 71 s with no gate waits, and v10 r2 differs from it in builder count too.

**Smaller points.** run1321 (warm, after `script_done`) logged one guest panic at shutdown (`SetTerminateResult
0x1a80a`, then "Userspace PANIC"). It came about 11 s after the script ended and is in 1 of 18 runs from v8-v10. It
does not change the ending; it should be watched. r2's 3.2 s video freeze is a held black frame during the area
change (warm runs 1.5-1.9 s there).

**Corrected advice:** the reading said to keep the IR_FREE lines out and ship the rescue alone, but that is the v9
set, which lost 2 of 2 cold starts. Keep r1 *with* the IR_FREE lines as the candidate (v11 is already running
exactly that: plan has IR_FREE, RUNTIME, rescue, 2 builders). Call first start solved only if the v11 cold starts
pass the bar too. Then make a decision on dropping IR_FREE only from a same-day back-to-back cold A/B. Nothing ships
from this round alone.

## Answer first (original reading; see the check above for corrections)

- **6 of 6 got through: `script_end line=126` + `script_done` in every run, no crash file.** Both cold starts
  reached the village (r1 run1317 at app 622.3, r2 run1320 at app 630.8).
- **(1) The door wave did not shrink.** r1 cold: +544 MiB at ~A+2, +448 at ~A+10. r2 cold: +640 at ~A+2, +608 at
  ~A+10 (under-1 MiB heap class; heap pieces +544/+448 and +608/+608). Earlier cold starts: +416 to +810. The
  IR_FREE lines did not act at the door: their last line in either cold run is at app 280 s (first 3D scene);
  none in the 280 s before the door or after it. Source: a freeing build prints only when its pools held 32 MiB
  or more, and the GPU thread's pools never held more than 48.7 MiB in any run. So at the door IR_FREE could free
  only a few tens of MiB, far short of a 450-640 MiB wave. The warm starts free the same programs and have no
  wave. What differs is that the cold door builds 39-43 new pipelines in 10 s; the warm one builds 0-3 new
  (INFERRED: the wave comes from building new pipelines, most likely the driver's compile, which IR_FREE does
  not touch).
- **New and important: the heap rescue acted for the first time in a field run.** r1 cold:
  `EDEN_HEAP_RESCUE requests about to be refused: 214 served by an arena, 0 by none`. It is a running total, 0
  in the 20 s summary just after A and 214 in the next one (~A+20), so all 214 came during the door waves and the
  arrival. 214 heap requests would have been refused at the second earlier starts died in. Every one was served.
  No `EDEN_NEW_WAIT` line and no `EDEN_HEAP_FAILURE` anywhere. r2 cold: 0 rescues (its pool had more room at the
  door). The rescue line, not IR_FREE, is what this round shows working.
- **(2) Neither cold start is a pass with margin.** r1 meets the letter of the bar narrowly: 17 of 23 village
  checks above 16 MiB, 0 refused images, no freeze over 2 s after the arrival. But its median room is only 50
  MiB, it was at 1-4 MiB at the arrival and at 2-8 MiB before the end, there were 12 driver refusals, and it needed
  214 rescues. r2 has more room (median 124 MiB, 21 of 23 above 16) but **1 image refused** (fails that part of the
  bar), 14 driver refusals and a 3.2 s picture freeze at the area change before the end.
- **(3) Cost: the cold black screen got longer.** 82.2 s in both (picture still 74.1 / 74.2 s), against 65.5-68.6
  s in v8. Worst frame 38.8 s (r1) and 50.5 s (r2), against 25.2-30.1 s. Cold starts reach the door 20-34 s later
  than v8's. r1's gate waited 97 times (55 s in all, 33 waits and 36 s of it during the first scene); r2's gate
  waited once, but r2 has only one builder. With no start without IR_FREE in this round, the gate and the lines
  cannot be told apart. Warm starts: 18.2-18.8 s black (r1) and 26.0 / 18.5 s (r2; one 6.6 s frame). Village fps
  is unchanged (~23 cold, ~25 warm from A+25).
- **(5) Default: r1 over r2, but the two IR_FREE lines do not go into the default file on this evidence.** They
  showed no effect on the wave and may cost ~14 s of black screen. The lines that earned a place are the
  rescue (+ the wait behind it), which are already in r1. See (5).

| Start | Valid / cache | How it ended | IR_FREE lines (builds, MiB held, thread) | First-scene black (video) / worst frame | House: largest / pieces | Door waves (under-1 MiB class) | Door lowest largest free (census; lowest 'low') | Village checks: median / min / at 16 or less | Refused images / driver lines | Longest freeze after the door | Village fps (A+15 to end; from A+25) / worst |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **r1 cold run1317** | yes, COLD | `script_end` + `script_done` (632 s run) | 8 / 311.8 MiB / GPU thread, all at app 228-280 s | **82.2 s** (still 74.1) / **38.8 s** | 224 / 1,600 | **+544** (~A+2), **+448** (~A+10) | **2 MiB** (A+10.2, GPU 2.3 s stale); low 2 | 50 / 1 / **6 of 23** | **0** / 12 (3 placed on the retry) | game frame 2.8 s at the door (A+12); village 771 ms; video 1.7 s at the area change | 20.9; 23.0 / 771 ms |
| r1 warm run1318 | yes, WARM 1170 | `script_end` + `script_done` | 8 / 311.8 / builder at boot (6-13 s) | 18.2 s / 1.97 s | 596 / 1,184 | none (class stays 0) | 64; low 1 (A+12) | 124 / 18 / 0 of 23 | 0 / 0 | 504 ms | 23.4; 24.8 / 392 ms |
| r1 warm run1319 | yes, WARM 1192 | `script_end` + `script_done` | 8 builder + 1 GPU thread (app 228) / 345.8 | 18.8 s / 1.79 s | 875 / 1,120 | none (+0) | 6 (A+12.3) | 203 / 48 / 0 of 25 | 0 / 0 | 393 ms | 23.4; 24.7 / 393 ms |
| **r2 cold run1320** | yes, COLD | `script_end` + `script_done` (641 s run) | 7 / 277.8 MiB / GPU thread, app 229-279 s | **82.2 s** (still 74.2) / **50.5 s** | 448 / 1,376 | **+640** (~A+2), **+608** (~A+10) | **28 MiB** (A+10.2, GPU stale); low **2** (A+4.1) | 124 / 8 / **2 of 23** | **1** / 14 (3 on the retry) | game frames 2.25 s at the door; 1.7 s in the village; **video 3.2 s** at the area change | 21.1; 23.3 / 1,696 ms |
| r2 warm run1321 | yes, WARM 1151 | `script_end` + `script_done` | 7 builder + 1 GPU thread (app 243) / 311.8 | **26.0 s** (still 18.2) / **6.6 s** (app 242) | 440 / 1,248 | none | 96 | 284 / 32 / 0 of 25 | 0 / 0 | 275 ms | 23.7; 25.4 / 263 ms |
| r2 warm run1322 | yes, WARM 1173 | `script_end` + `script_done` | 8 builder + 1 GPU thread (app 235) / 345.8 | 18.5 s / 1.85 s | 652 / 1,216 | none | 32; low 16 | 241 / 68 / 0 of 24 | 0 / 0 | 317 ms | 22.9; 24.2 / 317 ms |

Earlier cold starts with the same settings minus IR_FREE, for comparison: v8 r2 cold (run1304) black 65.5 s,
worst frame 25.2 s, door waves +544 / +512, lowest 12 / 10 MiB, village median 80, 8 of 23 at 16 or less, 4 images
and 64 driver lines refused, 0 rescues; v8 r1 cold (run1301, no wait/rescue) died at A+2 with +576 under way;
v7 g2 cold: black 84.6 s, median 32, 22 images, 64 driver lines.

## Validity (all six valid, READ)

- Build: both batches' `eboot.json` sha16 7f14d75d16b8fd02 (T134); `install-t134.v6.sh --check-only` "T134 is
  installed" before each group and at verify.
- Env: each run's env.txt = its plan line for line (87 lines) plus only EDEN_TEST_BOOT and EDEN_TEST_SCRIPT. r1 and
  r2 differ only in `EDEN_NX2_PIPELINE_WORKERS=2` / `=1`. `EDEN_ENV EDEN_UP_IR_FREE=1` and
  `EDEN_ENV EDEN_UP_IR_FREE_RUNTIME=1` in every heap.log; also NEW_WAIT_MS=2000 and HEAP_RESCUE=1 with their start
  lines. `Pipeline builders: 2 of 15` (r1) / `1 of 15` (r2), the gate line, `Stream ring 64 MiB`, `VMA blocks
  8 MiB` in all six.
- IR_FREE has **no start line and no counter** of its own (source, vk_pipeline_cache.cpp:467-529): proof it ran is
  the `EDEN_ENV` lines plus the per-build line `EDEN_UP_IR_FREE: <kind> <hash> (<thread>): X MiB of IR in use,
  Y MiB held, freed before its driver compile`, printed only for builds whose pools held 32 MiB or more (first 100).
  Counts in the table are those lines (7-9 per run, all "freed"); builds with less than 32 MiB free silently, so
  the true number of freeing builds is not in the logs.
- Caches: cold-proof.v2 COLD for run1317 and run1320 (0 pipelines, 0 prepared records from disk; shader, driver,
  jit absent before each group). WARM 1170 / 1192 and 1151 / 1173 pipelines read at boot. Config matched a fresh
  install for all six.
- Round end: `THIRD PASS DONE` 16:44:36; owner's caches (40 files / 1,924 MiB shader, 104 / 1,026 MiB driver),
  env.txt (both folders EQUAL to the start copy), eglantineps5.json and his save back and checked; no pending
  restore, latched stop or hang. Parked sets 1 and 2 stay on the console as `.from-first-start-N`.
- Same stale labels as v8: the queue banner still says "First-start v8 group R2, a repeat of v7 G2" and the SWITCH
  LINT calls `EDEN_UP_NEW_WAIT_MS` and `EDEN_PIPELINE_MEMORY_GATE_WORKERS` DEAD. Both false alarms (v8 note).

## Per start

**r1 cold, run1317 (two builders).**
- First scene: video black 206.8-289.0 s (82.2 s), picture still 213.0-287.1 (74.1 s). Game frames 11.9 s (app 237)
  and 41.5 s (app 279) in the 5 s lines; report worst 38.8 s. Gate: 1 wait by app 241, **33 waits / 36.4 s by app
  281**, 97 waits / 55.0 s by the end (v8 r2 cold: 1 wait). IR_FREE: 8 GPU-thread lines at app 228-280 (31.8-48.2
  MiB in use, 311.8 MiB held in all), then none.
- House (line 108) at app 550.7, door A at 562.3 (v8 r2 cold 536.9). House largest 224 MiB, pieces 1,600, live 811.
- Door: A largest 98. A+2: pieces 1,600 -> 2,144, under-1 MiB class 2,656 -> 3,200 (**+544**), GPU 2.3 s stale,
  given back (`gave back 512 MiB`). A+4 low 11, A+8 low 6. A+10.2: pieces 2,048, class 3,200 -> 3,648 (**+448**),
  largest **2 MiB**, GPU 2.3 s stale, given back 448. A+12 low 2. Game 11.2 / 9.4 / 6.3 fps in the three 5 s windows
  from A, worst 2,809 ms.
- **Rescue: 214 served, 0 missed**, all between the summary at ~A+1 (none yet) and ~A+20. No NEW_WAIT, no failure.
- Arrival (A+16 to A+20): largest 1, 4, 40 MiB (lows 1); 9 driver refusals of 960 KiB to 15.6 MiB ("Eden gave back
  0 MiB, still no memory"), the last placed on the retry. Then 50-56 MiB for ~30 s, 3 MiB at A+37, 2/2/8 MiB at
  A+53-56 (area change before the end). After the end 32-44 MiB.
- Village 20.9 fps (23.0 from A+25), worst 771 ms (a 11.2 fps window at A+57). Video freeze 1.7 s at the area change
  (warm runs 1.5-1.9 s there). Guest swap failures 10. Card 18.4 fps, 41.2 flashes/min, 0 full-scene.

**r2 cold, run1320 (one builder).**
- First scene: video black 206.1-288.3 s (82.2 s), still 212.3-286.5 (74.2 s). Game frames 15.4 s (app 240), 7.5 s
  (248), 31.0 s (279), 6.8 s (282), 3.1 s (288); report worst 50.5 s. Gate: 1 wait, 54 ms in the whole run. IR_FREE:
  7 GPU-thread lines at app 229-279 (277.8 MiB held), then none.
- House at app 559.1, A at 570.8 (8.5 s later than r1, 34 s later than v8 r2 cold). House largest 448, pieces 1,376.
- Door: A largest 126 / low 29. A+2: pieces 1,376 -> 1,984, class 2,496 -> 3,136 (**+640**), GPU 2.3 s stale,
  `gave back 640 MiB`. A+4.1 low **2**. A+10.2: pieces 1,984 again, class 3,136 -> 3,744 (**+608**), largest 28, GPU
  stale, `gave back 576 MiB`. A+14.3 GPU stale again. Game 12.8 / 9.5 / 7.7 fps from A, worst 2,252 ms.
- Rescue 0, NEW_WAIT 0, no failure.
- Arrival: largest 8 at A+16.4, 48 (low 1) at A+18.4, 124 (low 2) at A+20.4. Then 124 MiB steady for ~30 s; 17, 74
  (low 2), 49 (low 12), 8 (low 2) at A+51-57. After the end 74-80 MiB. 14 driver refusals, all in the village (3
  placed on the retry); **1 image refused** (`EDEN_GRAPHICS_MEMORY an image was refused`, stderr 3682). Swap
  failures 11.
- Village 21.1 fps (23.3 from A+25), worst 1,696 ms at A+53; video freeze **3.2 s** at the area change.
  Card 18.3 fps, 41.1 flashes/min, 0 full-scene.

**Warm starts (r1 run1318, run1319; r2 run1321, run1322).** No door wave in any (under-1 MiB class flat). No rescue,
no wait, no refusal of any kind. Village medians 124-284 MiB, 0 checks at 16 or less (lows to 3-6 MiB once each at
the area change before the end). Village 22.9-23.7 fps (24.2-25.4 from A+25), worst 263-393 ms. Black 18.2, 18.8,
**26.0**, 18.5 s. run1321's extra 7.5 s: a 6.6 s game frame at app 242, the same second its pipeline e6f22decb80ad495
was built on the GPU thread (its IR_FREE line at app 242.6); in run1322 that pipeline was built by the builder at
boot (app 20) and again at the first scene without a stall. One run, so no verdict on one builder from it.

## (1) Did the door wave shrink, and is that IR_FREE's doing?

**No, and the logs show IR_FREE was not active at the door.** (READ, plus INFERRED where marked.)

| Cold start | Wave 1 (~A+2) | Wave 2 (~A+10) | Door lowest largest / low | Ended |
|---|---|---|---|---|
| v10 r1 (IR_FREE, 2 builders) | +544 | +448 | 2 / 2 | village |
| v10 r2 (IR_FREE, 1 builder) | **+640** | **+608** | 28 / 2 | village |
| v8 r2 (same, no IR_FREE) | +544 | +512 | 10 / 10 | village |
| v8 r1 (no wait/rescue) | +576, dead at A+2.7 | | 3 at the crash | crash |
| v7 g1 | +416 | dead A+9.6 | 2 | crash |

- Wave sizes are inside the earlier 416-810 MiB range. r1's second wave was 64 MiB smaller than v8 r2's; r2's
  waves were ~100 MiB larger. That is spread, not an effect.
- The IR_FREE lines in the cold runs all fall at app 228-280 (the first 3D scene). There is none from app 280 to
  the end, so no build at the door had 32 MiB or more of translation memory to free. The largest any GPU-thread
  build held in any run was 48.7 MiB. Without the RUNTIME switch the GPU thread keeps only its largest translation
  so far, so the most the RUNTIME switch can hand back at once is ~50 MiB.
- The same eight large programs free their memory in the warm starts too (at boot, on the builders), and the warm
  starts have no wave. What the cold door has and the warm door lacks: `Runtime pipelines in the last 10 s: 43
  built ... new 39` (r1) and `41 built ... new 36` (r2), against `new 0-3, on disk 23-34` warm. (INFERRED: the wave
  is new-pipeline work, most likely the driver's own compile memory, which IR_FREE does not free. The big texture
  decode at the door, 6144x6144, happens in every warm start too, so it is not the cause.)

## (2) Are the two cold starts passes with margin?

**No. r1 passes the letter of the bar by a thin margin. r2 fails it on one refused image. Neither has margin.**

| Bar part | r1 cold run1317 | r2 cold run1320 | v8 r2 cold (no IR_FREE) |
|---|---|---|---|
| Reached the village with `script_end` + `script_done` | yes | yes | yes |
| Most village checks above 16 MiB | **yes, 17 of 23** (median 50) | **yes, 21 of 23** (median 124) | yes, 15 of 23 (median 80) |
| No refused images | **yes, 0** | **no, 1** | no, 4 |
| No multi-second freeze | door 2.2-2.8 s frames; village worst 771 ms; video 1.7 s | door 2.2 s frames; village 1.7 s frame, **video 3.2 s** | door two 2.2 s frames |
| Driver refusals | 12 | 14 | 64 |
| Heap requests rescued | **214** (0 missed) | 0 | 0 |
| Lowest in the village | 1 MiB (arrival), 2 MiB (A+53) | 1 MiB (arrival), 2 MiB (A+53, A+56) | 0-2 MiB twice |

- r1 lived through the same two moments that killed earlier cold starts. It did so with the pool at 2 MiB and 214
  heap requests that only got memory because the rescue took them from other threads' arenas (READ). Without
  the rescue those 214 would have gone to the operator new wait, or failed outright for C allocations such as the
  driver's (INFERRED). That is the safety net working, not room to spare.
- r2's single builder left more room in the village, but not at the arrival (1-8 MiB), and it still lost an image.

## (3) Cost

- **First-scene black, cold: 82.2 s in both** (v8: 65.5 / 68.6; v7 g2: 84.6). Still picture 74 s, worst frame
  38.8 s / 50.5 s (v8: 25-30 s). r1 had 97 gate waits (as v7 g2, which had ~85 s); r2 had 1 but one builder.
  (INFERRED: with no IR_FREE-off start in this round, the ~14 s cannot be pinned on IR_FREE. RUNTIME makes the GPU
  thread allocate its translation pools again for every build, a small cost per build. The gate count and the
  single builder explain at least part of it.)
- **Time to the village, cold:** door at app 562.3 (r1) and 570.8 (r2), against 536.9-542.3 in v8; warm 458.8-468.1.
  A first start now reaches the door ~100 s after a restart would (v8: ~80 s).
- **Door:** 9.5 fps (r1) / 10.5 fps (r2) for 15 s with 2.2-2.8 s frames (v8 r2: 6.5-10.6 fps, 2.2 s frames).
- **Village fps:** cold 23.0 / 23.3 from A+25 (v8 r2 23.7); warm 24.2-25.4 (v8 24.4-24.9). No change.
- **One builder against two:** r2 cost 8.5 s more to the door when cold, one warm start with 26 s black and a
  6.6 s frame, larger door waves, 1 refused image and the 3.2 s freeze. It gained village room (median 124 vs
  50) and needed no rescue.
- **Picture:** 0 full-scene flashes in all six. Cold cards 41.2 / 41.1 flashes a minute, warm 18.5-27.4 (no
  control, and the v8 cold card was not counted, so no flash verdict). The refused image in r2 was not checked
  frame by frame.

## (4) What a newcomer meets with r1's settings

- The game boots to the opening movies as usual. Then **about 80 seconds of black screen** at the first 3D scene.
  The picture stands still for ~75 s, with one frame of ~40 s. It looks like a hang. It is not.
- After that, normal play to the house door. At the door, ~15 s of choppy play (about 10 fps, with 2-3 s hitches),
  then the village at ~23 fps.
- First start, reaching the village: 1 of 1 in this round. [Corrected by the check: with the rescue on it is 3 of
  5 (v8 r2, v9 r1 died, v9 r2 died, v10 r1, v10 r2). On these exact settings without IR_FREE 1 of 3, with IR_FREE 2
  of 2.] In this one the rescue served 214 requests at the door; the same rescue missed in v9.
- Restarts: ~18 s black, no door hitch, village ~25 fps.

## (5) Which default, and what v11 must show

**r1 over r2 as the base.** r2 costs more time and one refused image, and its extra room does not reach the
arrival. **The two IR_FREE lines should not go into the default file on this round.** They did not shrink the
wave, did not act at the door, and come with a black screen ~14 s longer that this round cannot clear them of.
The lines that showed value are `EDEN_UP_HEAP_RESCUE=1` (214 served, 0 missed) and the wait behind it. Those
are the candidates to ship.

v11 (r1's settings, two more empty-cache starts), read in this order per cold start:
1. **Ending:** `script_end line=126` + `script_done`, no crash file. Any crash = stop, whatever else.
2. **Rescue and wait:** the `EDEN_HEAP_RESCUE ... served by an arena, M by none` line. M above 0, any `EDEN_NEW_WAIT`
   `gave up`, or any `EDEN_HEAP_FAILURE` = the net has a hole. Note the served count; 214 is the one data point.
3. **IR_FREE at the door:** any `EDEN_UP_IR_FREE` line after app 300 s. None again = the lines do nothing at the
   door, and that settles (1) for them.
4. **The bar, per start:** most village checks above 16 MiB, **0 refused images**
   (`EDEN_GRAPHICS_MEMORY an image was refused`), no freeze over 2 s after the arrival (5 s lines and video).
   Both v11 cold starts must pass for "first start solved", together with r1 here. That is 3 in a row, and with
   the rescue it is no longer luck alone.
5. **Black screen with the gate count:** read the `GateReport` totals next to the black seconds. Black of 82 s with
   ~1 gate wait = the extra time is IR_FREE's. ~66 s = it was the gate.
6. Before the IR_FREE lines go into the default, IR_FREE needs one back-to-back cold A/B on the same settings
   (without, with, without). Today's comparison with v8 is across rounds and confounded by the gate. Unless that
   A/B shows a shorter or equal black screen and a smaller wave, leave them out and ship the rescue alone.

## What the test could not see

- Which threads and sizes the 214 rescued requests had (the counter has no breakdown), and whether any of them
  was the 902,912-byte file read that killed v7 g1/g3 and v8 r1.
- How many builds freed translation memory under 32 MiB (they print nothing).
- Whether the ~14 s longer cold black screen is IR_FREE, the gate, or run-to-run spread (no IR_FREE-off cold start
  in this round).
- The one refused image in r2 cold and the door hitches were not checked frame by frame for a visible fault.

## In plain words (written for the project owner), corrected by the second check

1. All six starts got to the village, both true first starts too. These settings without the new setting lost both
   first starts in round v9, so: without it 1 of 3, with it 2 of 2. Still too few to call it fixed.
2. The memory spike at the house door was as big as before. The new setting frees about 50 MB earlier on, which
   may or may not be what made the difference.
3. The older safety setting caught 214 requests in one start, but it was also on when v9 crashed, so it is not
   enough alone.
4. The ~80 s black screen on a first start is within the 65-87 s seen without the new setting. No proven cost.
5. Advice: keep the new setting in (v11 is testing exactly that now). Do not ship anything until v11's first
   starts pass too.

## In plain words (original reading, superseded)

1. Six new-game starts on a fresh install, all six got to the village, both true first starts included.
2. The new memory-freeing setting did not do what it was for. The big memory spike at the house door was the same
   size as before, and the setting's own log lines show it was not active there.
3. Something else did help: an older safety setting kicked in for the first time. In one first start it caught
   214 memory requests at the door that would otherwise have been refused, and the game kept going.
4. Price: the black screen after the opening is now about 80 seconds instead of about 65 on a first start. Not
   clear yet whether the new setting causes that.
5. Advice: keep two builder threads. Do not add the new setting to the defaults yet. The safety setting is the
   one to ship, once the two starts running now also reach the village cleanly.
