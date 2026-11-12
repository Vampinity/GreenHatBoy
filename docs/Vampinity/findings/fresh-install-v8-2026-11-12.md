# Fresh install, round v8: six new-game starts, two settings groups (T134, 12 Nov 2026, 11:40-12:42)

> **Found:** Six starts (T134): 4 of 4 restarts and 1 of 2 true first starts reached the village. The two safety switches (`EDEN_UP_NEW_WAIT_MS=2000`, `EDEN_UP_HEAP_RESCUE=1`) never acted, so the cold pass was timing luck again.
>
> **So:** With the best settings 2 of 3 first starts reached the village, 0 of 3 with memory to spare. Settings alone do not make a first start safe.

Read-only check, 12 Nov ~12:50-13:30. No console touched, no test started, nothing posted, no file changed
except this note. READ = seen in a log, frame, video check, card or source. INFERRED = my reasoning.
Method as in `fresh-install-v7-2026-11-12.md`: census lines in stderr; script marks (A = the door's
`wait_met line=117`, house = `line=108`, end = `script_end line=126`) placed by their position among the
census lines (the census clock runs ~26 s behind the app clock), app times = EDEN_GUEST_START + script time;
game fps from the `nx2:vi2 5 s` lines in eden_log; first-scene black from video-check.txt; longest frame
from report.txt. "Village" = from A+15 s (arrival) to the script's end. One start is no verdict.

## Answer first

- **4 of 6 got through, 1 cold died, 1 cold got through.** r1 cold (run1301) died at the door, ~2 s after A,
  on the same request as both v7 deaths: `EDEN_HEAP_FAILURE requested=902912 reason=2`, std::bad_alloc on the
  file-service thread, largest free block 3 MiB. r2 cold (run1304) reached the village: `script_end line=126` +
  `script_done`. All four warm starts: `script_end` + `script_done`, no crash file.
- **Neither r2 switch acted, not once, in any of the three r2 starts.** No `EDEN_NEW_WAIT` line (start, gave up
  or refused at once), no `EDEN_UP_NEW_WAIT` 10 s counter line, no `EDEN_HEAP_RESCUE` counter line in 30 memory
  summaries, no `EDEN_HEAP_FAILURE`. Both lines print only when a request has been refused, so the heap never
  refused anything in r2. **The wait and the rescue saved nothing.** r2's cold start lived because no request
  failed, not because a failure was caught. With nothing refused, r2 ran exactly like r1 (source: both switches
  only run after a refusal).
- **r2 cold is another near miss, a bit better than v7 g2's, not a pass with margin.** Village memory checks:
  largest free block median 80 MiB, 15 of 22 above 16 MiB (v7 g2: median 32, 11 of 21). But it fell to 0-2 MiB
  twice. 4 images refused (2 of them screen-size render targets), 2 buffers, 1 staging buffer, 64 driver
  refusals. The picture ran at 6-11 fps for ~20 s from the door into the village, with two 2.2 s frames. The bar
  says no refused images, so it **fails** that part.
- **Same settings in effect, cold record so far: 2 of 3 reached the village** (v7 g2, v8 r2), 1 died (v8 r1).
  **0 of 3 met the full bar.**
- **Warm restarts: 3 of 4 clean, 1 with the door burst.** r1's first warm start (run1302) had a +608 MiB burst at
  the door, a 2.2 s frame and 17 driver refusals in the village. With 2 builders that makes 1 of 8 warm starts
  with a burst (v7 0 of 4).
- **Cost of r2's two lines when they do nothing: none seen.** r2 warm village 24.9 / 24.4 fps, worst frames
  340 / 387 ms, 18.4 / 17.8 s black (r1 warm: 22.7 / 24.6 fps, 19.1 / 18.0 s). No new stall, because no wait
  ever ran.

| Start | Valid / cache | How it ended | First-scene black (video) / longest frame | House: largest / heap pieces / live / empty | Door | Village memory checks (largest free) | Refused | Village fps / worst |
|---|---|---|---|---|---|---|---|---|
| r1-1 cold run1301 | yes, COLD | **crash 545 s** (~2 s after A), bad_alloc FS, 902,912 B; no script_end | 68.6 s (frozen 60.3) / 30.1 s | 312 / 1,568 / 849 / 354 | largest 66 at A, 192 at A+1.5; heap 1,568 -> 2,144 (+576) at the crash; 3 MiB free at the crash | - | 0 before the death | - |
| r1-2 warm run1302 | yes, WARM 1106 | `script_end` + `script_done` | 19.1 s / 2.2 s | 416 / 1,344 / 815 / 250 | **+608 burst** at A+7.6, pool 3 MiB, GPU 2.3 s stale, 2,172 ms frame | 22: median 107, min 6, 2 at 16 or less | 0 images; 17 driver (A+48) | 22.7 / 1,687 ms (3.3 s freeze at the village transition) |
| r1-3 warm run1303 | yes, WARM 1202 | `script_end` + `script_done` | 18.0 s / 1.9 s | 761 / 1,184 / 806 / 88 | no burst (+32) | 22: median 190, min 7, 1 at 16 or less (second check: 23 with the area+3s check, 2 at 7 MiB) | 0 | 24.6 / 305 ms |
| **r2-1 cold run1304** | yes, COLD | **`script_end` + `script_done`** (605 s) | **65.5 s (frozen 55.9) / 25.2 s** | 384 / 1,600 / 851 / 382 | two waves **+544 (~A+2) and +512 (A+9.6)**, each given back in ~2 s; largest 72-140 MiB, dips to 12 and 10; two 2.2 s frames; 6.5-10.6 fps A to A+11 | **22: median 80, min 0, 7 at 16 or less** (second check: 23 with the area+3s check at A+56.6 = 2 MiB, so 8 at 16 or less, 15 above); 0-2 MiB at arrival (A+16 to A+20) and at A+53-59; 9-30 MiB after the end | **4 images (2 render targets 1280x720, 2 textures 384x384), 2 buffers (1 got it on asking again), 1 staging; 64 driver lines (4 placed on the retry)** | 23.7 / 588 ms from A+25 (second check: **898 ms**, 7.3 fps, in the 5 s window of the area change before the end); 9.1-9.7 fps A+11 to A+21 |
| r2-2 warm run1305 | yes, WARM 1201 | `script_end` + `script_done` | 18.4 s / 1.9 s | 829 / 1,184 / 818 / 80 | no burst (+32) | 24: median 260, min 25, 0 at 16 or less | 0 | 24.9 / 340 ms |
| r2-3 warm run1306 | yes, WARM 1213 | `script_end` + `script_done` | 17.8 s / 1.8 s | 669 / 1,184 / 808 / 96 | no burst (+32); GPU 2.4 s stale once at A+2.7; largest 8 MiB (low 5) at A+12-14 | 23: median 184, min 28, 0 at 16 or less (second check: the area+3s check at A+49.4 is 16 MiB, so min 16, 1 at 16 or less) | 0 | 24.4 / 387 ms |

For comparison, v7 g2 cold (run1291, same settings as r1): black 84.6 s, longest frame 41.6 s, village largest
0-46 MiB (median 32), 10 of 21 checks at 16 MiB or less, 22 images refused, 64 driver refusals, 12 s near-freeze.

## Validity (all six valid, READ)

- Build: both batches' `eboot.json` = sha256 7f14d75d16b8fd02... (T134); `install-t134.v6.sh --check-only`
  "T134 is installed" before each group and at verify.
- Env: each run's env.txt = its plan line for line (r1 83, r2 85 lines) plus only EDEN_TEST_BOOT and
  EDEN_TEST_SCRIPT. r2 = r1 + `EDEN_UP_NEW_WAIT_MS=2000` + `EDEN_UP_HEAP_RESCUE=1` (diff of run1301 against
  run1304). Every planned switch has its `EDEN_ENV` line. No `EDEN_HEAP_KEEP_ARENAS` anywhere. All six also
  carry `EDEN_UP_HEAP_WAIT_MS=2000` (the pipeline builders' wait, a different switch); it printed no wait line.
- Start lines, all six: `Pipeline builders: 2 of 15`, `EDEN_PIPELINE_MEMORY_GATE: builds take turns under 256 MiB
  free ...`, `Stream ring 64 MiB, regions of 4096 KiB`, `VMA heap 0 ... VMA blocks 8 MiB`. r2 only, all three:
  `EDEN_UP_NEW_WAIT_MS=2000: operator new waits that long for memory before it gives up` (heap.log) and
  `EDEN_UP_HEAP_RESCUE a request about to be refused is asked of every arena first` (stderr line 5).
- The queue's SWITCH LINT called `EDEN_UP_NEW_WAIT_MS` "DEAD" (and `EDEN_PIPELINE_MEMORY_GATE_WORKERS` again).
  Both are false alarms: main.cpp:934 reads the first and its start line printed; the second is read in
  vk_pipeline_cache.cpp (v7 note).
- Caches: cold-proof.v2 COLD for run1301 and run1304 (0 pipelines, 0 prepared records from disk; shader, driver
  and jit absent before each group). WARM 1106 / 1202 and 1201 / 1213 pipelines read at boot. Config matched a
  fresh install for all six.
- Round end: `THIRD PASS DONE` 12:43:52; the owner's caches (40 files / 1,917 MiB shader, 104 / 1,034 MiB driver),
  env.txt (both folders, EQUAL to the start copy), eglantineps5.json and save are back and checked; no pending
  restore, latched stop or hang flag. Parked sets 1 and 2 stay on the console as `.from-first-start-N`.
- 0 junk-family lines in six runs. Cards: r1 card done; r2 card done (run1304 "not counted: stalled 10 s in
  gameplay (from about 536 s app time)" = the door, A at app 536.9).

## Per start

**r1-1, run1301 (cold): died at the door.**
- First scene: video black 206.6-275.2 s (68.6 s), frozen 212.8-273.1; longest frame 30.1 s (report.txt). The
  gate waited once (77 ms). (v7 g2's 84.6 s came with 97 gate waits; here the gate hardly acted.)
- House: control (line 108) at app 530.5. Largest free 312 MiB, pieces 1,568, live 849, empty 354, idle 162.
- Door: A at app 542.3. Largest 66 MiB at A, 192 (low 95) at A+1.5, pool 1,176 MiB free in all.
- End: crash report 545 s, "the app stopped itself", std::bad_alloc on FS at eboot+0xb86d5, largest free block
  3 MiB, heap 2,144 MiB of pieces: **+576 MiB since A+1.5** (the door burst was under way). Last lines:
  `EDEN_HEAP_FAILURE requested=902912 reason=2 count=1`, `terminate: std::bad_alloc`. Same request, same thread,
  same address as v7 g1 and g3. No EDEN_NEW_WAIT line: r1 had no wait switch.

**r1-2, run1302 (warm): got through, with the door burst.** Black 19.1 s. Door: under-1 MiB class 1,344 -> 1,952
(+608), pieces 1,344 -> 1,952 at A+7.6, given back (512 MiB) by A+9.7; largest 3 MiB, GPU 2.3 s stale; game frame
2,172 ms (A+4.6 to A+9.6, 7.6 fps). 0 refusals at the door. Village: 17 driver refusals at A+48 (the area change
before the end), lowest 6 MiB, video freeze 3.3 s at that transition (other warm runs 1.7-1.9 s). Village 22.7 fps,
worst 1,687 ms. Card 18.6 fps, 25.7 flashes/min, 0 full-scene.

**r1-3, run1303 (warm): got through.** Black 18.0 s. Door: +32 MiB, no burst. Lowest village check 7 MiB, once.
0 refusals. Village 24.6 fps, worst 305 ms. Card 21.2 fps, 29.4 flashes/min, 0 full-scene.

**r2-1, run1304 (cold): got through.**
- First scene: video black 206.0-271.5 s (**65.5 s**), frozen 212.2-268.1 (55.9 s); longest frame 25.2 s
  (report.txt; game frame 25.7 s). The gate waited once (16 ms).
- House: control at app 525.1 (v7 g2 548.4; control cold starts 503.5-504.6). Largest 384, pieces 1,600, live
  851, empty 382, idle 158.
- Door: A at app 536.9. Two heap waves in the under-1 MiB class: 2,528 -> 3,072 (+544) around A+2, given back
  (`gave back 512 MiB: the pool is short`); 3,072 -> 3,584 (+512) at A+9.6 (pieces 1,632 -> 2,144, empty
  888), given back (448 MiB) by A+11.7. Largest free 72-140 MiB from A to A+8, dips to 12 (A+3.5) and 10 (A+9.6,
  GPU 2.3 s stale). Game fps 6.5 (A to A+4, worst 2,184 ms) and 10.6 (A+4 to A+11, worst 2,216 ms); video 2.0 s
  freeze at the door.
- **The first wave came at the second r1 died in (~A+2), and r2 survived it.** At A+1.5 r2 had 138 MiB largest /
  72 low; r1 had 192 / 95. So the margins were not larger; the request, if made then, found room.
- Arrival (A+15.8 to A+19.9): largest 0-2 MiB, total pool free down to 49 MiB, GPU 2.3 s stale, driver refusals
  and the 2 render targets (1,280x720) refused (report: "render target without memory: 553-554 s"). Game fps
  9.7 / 9.1, worst 1,215 ms. Then 97 MiB for ~12 s, 15-128 after.
- A+52-55 (the area change before the end): 0-8 MiB again, more driver refusals (1.4-15.7 MiB asked) and 2
  more images refused. After the end: 9-30 MiB for its last 16 s.
- End: `script_end line=126 at=588.099` + `script_done`, app 596.9. Village 23.7 fps from A+25, worst 588 ms; card
  17.5 fps, not counted (the 10 s slow stretch at the door). Heap at the end: 1,696 + 125 MiB, 988 in use, 62 spare
  arenas (123 MiB), 3,360 MiB given back.
- **Waits and rescues: 0 and 0.** No `EDEN_NEW_WAIT` start line, so no wait began, on any thread, for any size;
  none ran out; no "refused at once". The 10 s `EDEN_UP_NEW_WAIT` line prints only when a counter moved: it never
  printed. `EDEN_HEAP_RESCUE requests about to be refused: N served by an arena, M by none` prints in each 20 s
  summary when N or M is above 0: 30 summaries, never printed, so 0 served and 0 missed. No `EDEN_HEAP_FAILURE`.
- **The 902,912-byte file-service request:** no log line shows it. A request that is served prints nothing. So
  either it came and was served first time, or it came when nothing else was short. Either way it was never
  refused, so neither switch got to touch it. (INFERRED: it is the reply buffer of a file read at the door, so it
  is almost surely made in every start; v7 could not see it in g2 either.)

**r2-2, run1305 (warm): got through.** Black 18.4 s. Door +32, no burst. Village lowest 25 MiB, 0 of 24 checks at 16 or
less. 0 refusals. Village 24.9 fps, worst 340 ms. Card 21.1 fps, 25.9 flashes/min. 0 waits, 0 rescues.

**r2-3, run1306 (warm): got through.** Black 17.8 s. Door +32, no burst (one 2.4 s stale GPU sample at A+2.7, worst game
frame there 315 ms). Village lowest 28 MiB. 0 refusals. Village 24.4 fps, worst 387 ms. Card 21.1 fps, 23.6
flashes/min. 0 waits, 0 rescues.

## (1) Is r2's cold start a pass with margin?

**No. It is a near miss again, better than v7 g2 on memory, still short of the bar.** (READ.)

| | v7 g2 cold (run1291) | **v8 r2 cold (run1304)** | v8 r2 warm (run1305 / 1306) |
|---|---|---|---|
| Village checks: median largest free | 32 MiB | **80 MiB** | 260 / 184 MiB |
| Checks at 16 MiB or less | 10 of 21 | **7 of 22** | 0 of 24 / 0 of 23 |
| Lowest | 0 MiB, ~6 s | **0-2 MiB twice** (arrival, A+52) | 25 / 28 MiB |
| Images refused | 22 (20 render targets) | **4 (2 render targets) + 2 buffers + 1 staging** | 0 / 0 |
| Driver refusals | 64 | **64** | 0 / 0 |
| Longest freeze after the door | ~12 s near-frozen, frames to 4.3 s | **~20 s at 6-11 fps, two 2.2 s frames, no freeze over 2.2 s** | worst 340 / 387 ms |
| Memory after the end | 17-32 MiB | 9-30 MiB | 101 / 70 MiB |

Bar check: "most checks above 16 MiB" yes (15 of 22); "no refused images" **no**; "no multi-second freeze"
borderline (two 2.2 s frames at the door, none in the village after arrival). A warm start has 3-10x the free room
in the village. The cold start lands on almost no room, twice.

## (2) What the wait and the rescue contributed

**Nothing, because nothing gave them a chance.** (READ in logs and source.)
- Both only run after a refusal: the new handler runs only when operator new failed (main.cpp:353-436); the rescue
  only when the heap got NULL (heap_arenas.inc:2538-2539). r2 had no refusal of a heap request at all.
- So **neither one saved the request that killed r1**. In r2 that request was not refused. In r1 nothing was there
  to catch it.
- The 64 driver refusals and the 7 refused images in r2 cold are not heap requests: they are the pool refusing
  graphics memory (RADV's out-of-memory path and the texture collector). Neither switch covers them.
- What decides life or death at the door (INFERRED from three cold starts with these settings): whether the file
  read's 0.9 MB buffer comes at a second when the door's ~0.5 GB heap wave has the pool at a few MiB. r1 died at
  A+2 during that wave (largest 3 MiB). r2 had its own wave at the same moment and lived. v7 g2 lived with 0 MiB
  later. This is timing, not margin.
- Could the wait have saved r1? Probably, but not shown. In every cold door seen, the pool came back to 32-140 MiB
  within 2-4 s, and the wait holds the file thread up to 2 s, trimming the heap every 500 ms. 2 s may be on the
  short side. The rescue could serve 0.9 MB only from an arena with that much room in a row (arenas are 2 MiB),
  so it is the weaker of the two. **Neither has ever acted in a field run.**

## (3) Cost

- **Black screen, cold:** r1 68.6 s, r2 65.5 s (v7 g2 84.6, control 47.0-47.5). Longest frame r1 30.1, r2 25.2 s.
  The ~19 s less than v7 g2 is the gate: it waited 97 times there, once here. The switches play no part.
- **Black screen, warm:** 17.8-19.1 s in all four (v7 18.0-18.9).
- **Time to the village:** r2 cold reached the door A at app 536.9 (v7 g2 560.0, r1 542.3), warm 458.6-460.4.
  A cold first start is ~77-83 s slower to the door than a restart.
- **fps:** r2 warm village 24.9 / 24.4 fps (r1 warm 22.7 / 24.6, v7 23.6-25.8). Card 21.1 / 21.1. r2 cold
  23.7 from A+25, but 6.5-10.6 fps for the ~20 s from the door into the village.
- **New stalls from waiting:** none. No wait ran, so no wait could stall. The worst stall risk is untested: a
  wait holds its thread up to 2 s (the file thread, so a load stops), and the memory_wait.h header records that an
  earlier version of this wait hung the game for good in one session.
- Flashes (cards): r2 warm 25.9 / 23.6 per minute, r1 warm 25.7 / 29.4, 0 full-scene. No control run, so no flash verdict.

## (4) What a newcomer meets with r2's settings

- **First start: about 2 in 3 reach the village, going by three tries with these settings in effect.** The one
  that dies stops at the house door with the app's error screen, ~9 minutes in.
- A **black screen of ~65-85 s** at the first 3D scene, the picture standing still for ~55-75 s, one frame of
  25-42 s. Looks like a hang; it is not.
- At the door: two 2-second hitches, then ~20 s of choppy play (6-11 fps) into the village. Then normal play at
  ~24 fps. 2 small textures/render targets may come up missing for a moment (not checked frame by frame).
- **Restarts: ~18 s black, village ~24-25 fps.** 1 in 8 restarts so far still had the door hitch (2.2 s).
- The two new lines change nothing they can see today.

## (5) Is one more pair of cold starts (v9) enough to ship these lines?

**Not on its own, and not as "first start fixed".** (INFERRED.)
- What v9 can and cannot show:
  - If a cold start dies at the door again with **no** `EDEN_NEW_WAIT start requested=902912` line before the
    failure, the switches are broken or not reaching that path. That is a clear stop.
  - If both cold starts pass and no wait or rescue line appears, v9 says nothing new about the two lines. It only
    adds cold passes, which r1's settings already give about 2 times in 3.
  - **The only v9 result that supports these lines:** an `EDEN_NEW_WAIT start` on the file thread (902,912 B or
    any size), no `gave up` after it, no crash, and the start reaching `script_end` + `script_done`.
- **Shipping the two lines as a safety net** (not as a fix) is low risk on what is seen. They cost nothing on 3
  starts where they did nothing. They act only when the app would otherwise crash at once. Before they go into the
  default file, **one start where the wait really fires** is needed, to see that it ends (served or gave up) and does
  not hang. A cheap way to get that without waiting for luck: a warm start with `EDEN_TEST_HEAP_NO_GROW=<every>,<s>`
  from shortly before the door (heap_pages.cpp:80, heap_arenas.inc:834: refuses heap growth as if the pool were
  empty). It should make both switches act on demand. That is a proposal, not started.
- **For "first start solved"** the bar still stands and nothing has met it: 3 cold starts in a row reaching the
  village with no refused images, and most village checks above 16 MiB. With a pass rate near 2 in 3, three in a
  row happens about 1 time in 3 by luck alone, so even that is thin.

**What to look at first when reading v9** (in this order, per cold start):
1. Crash file? If yes: `EDEN_HEAP_FAILURE requested=` and the thread, and whether an `EDEN_NEW_WAIT start` /
   `gave up after 2000 ms` / `refused at once` line came just before it (stderr, the crash copy).
2. Any `EDEN_NEW_WAIT` line at all (thread is not printed: match it to the requested size; 902912 = the file read),
   the `EDEN_UP_NEW_WAIT` 10 s counters (`waits begun`, `gave up`, `longest ... ms asleep`), and any
   `EDEN_HEAP_RESCUE requests about to be refused: N served by an arena, M by none` line.
3. The door: the under-1 MiB class waves in `EDEN_HEAP_GROWTH` from A to A+12 and the census largest free at the
   same seconds, to see whether the wave and the file read met.
4. Village: largest free in each check from A+15 to the end (how many at 16 MiB or less), report.txt `Refused:`
   and "render target without memory", driver refusals, and the card's stall line.
5. Only then black screen and fps. The gate's wait count explains most of the black-screen spread (1 wait: ~66 s;
   97 waits: ~85 s).

## What the test could not see

- Whether, and when, r2's cold start made the 902,912-byte request (a served request prints nothing).
- Whether the wait would have caught r1's request in time (2 s limit against a pool that came back in 2-4 s).
- Why r2's door wave left room at A+2 and r1's did not (r1's largest at A+1.5 was the higher of the two).
- The 2 refused render targets in r2 cold were not checked frame by frame for a visible fault.

## In plain words (written for the project owner)

1. Six new-game starts on a fresh install: four restarts all got to the village. Of the two true first starts,
   one crashed at the house door (the same crash as this morning), one got to the village.
2. The two new safety settings never kicked in. Nothing went wrong in a way they could catch, so they neither
   helped nor hurt. The first start that got through did so by luck, like this morning's.
3. That first start was a bit less tight on memory than this morning's (about 80 MB free in the village where
   this morning had about 30), but it still ran out twice and lost a few textures for a moment.
4. Price of a first start: about 65 seconds of black screen after the opening, then ~20 seconds of choppy play
   from the door into the village. Restarts: about 18 seconds black, normal speed.
5. The next round (running now) will only say something about the new settings if one of them actually kicks
   in. A small forced test can make them do that on purpose.

## Checked a second time (12 Nov, ~13:10)

Read only. All six run folders (run1301 from its crash copies: its own `stderr.log` is the restarted app's,
2,928 lines with no door mark), the runner log and the T134 source (main.cpp:355-443, heap_arenas.inc:1921-1968
and 2511-2541, performance.cpp:832-838 and 909-941, guest_memory_service.inc) were opened again. No test was
started, nothing was posted, no file changed but this note.

**Confirmed (READ):**
- Endings from each run's own lines: run1302-1306 have `script_end line=126` + `script_done` (run1304 at=588.099),
  no crash file. run1301: crash report 545 s, std::bad_alloc, FS thread, eboot+0xb86d5, largest free 3 MiB, heap
  2,144 MiB; the crash stderr ends `EDEN_HEAP_FAILURE requested=902912 reason=2 count=1`, "operator new: heap
  exhausted", terminate. No script_end there.
- r2's two switches reached the app in all three r2 starts (`EDEN_ENV` lines and both start lines in heap.log /
  stderr). In all six runs: 0 `EDEN_NEW_WAIT` lines (start, gave up, refused at once), 0 `EDEN_UP_NEW_WAIT` counter
  lines, 0 `EDEN_HEAP_RESCUE ... served` lines, 0 `EDEN_HEAP_FAILURE` outside run1301. Source: the wait runs only
  inside the new handler after operator new failed, and prints a start line on every wait it begins (main.cpp:393);
  the rescue runs only when the heap returned NULL (heap_arenas.inc:2538) and its counter line prints when either
  count is above 0. So the reading "neither acted, not once" holds, and **no wait froze the picture and no request
  waited 2 s and then failed**: there was no wait at all.
- Gate: 1 wait per cold run (77 ms r1, 16 ms r2). Worst frames from report.txt: 30,053 / 2,200 / 1,868 / 25,177 /
  1,861 / 1,793 ms. Video black and frozen spans for both cold starts as written. Refusals in r2 cold as written
  (report.txt: 4 images, 2 buffers, 1 staging); 0 in the other five, except 17 driver lines in run1302.
- Door, census largest / low in MiB at the same moments (A = last census before `wait_met line=117`):

  | After A | v8 r1 cold (died ~A+2.7) | **v8 r2 cold (lived)** | v7 g1 cold (died ~A+9.6) | v7 g3 cold (died A+2.2) |
  |---|---|---|---|---|
  | 0 s | 66 / 66 | 72 / 72 | 93 / 93 | 6 / 6 |
  | +2 s | 192 / 95, then heap +576 and dead | 138 / 72, then heap +544 | 176 / 150 (heap +416) | dead |
  | +4 s | | **12 / 12** | 192 / 2 | |
  | +6 to +8 s | | 140, 43 | 129, 64 / 10 | |
  | +10 s | | **10 / 10**, heap +512 (pieces 2,144), GPU 2.3 s stale | dead | |
  | +12 to +14 s | | 128 / 10, 128 | | |

**Changed / added:**
1. **The luck is double, not single.** r2 cold went through both moments where earlier cold starts died: the
   first wave at A+2-4 (r1 and v7 g3 died there; r2 fell to 12 MiB) and the second at A+10 (v7 g1 died at A+9.6;
   r2 fell to 10 MiB, its heap at 2,144 MiB of pieces, the same size r1 had when it died). At A+2 r1 had *more*
   room than r2 (192 against 138 MiB). Nothing in r2's numbers explains its survival; both switches were idle.
2. Village memory checks, counting every census line from A+15 to the end (the first reading left out the area+3s
   check): r2 cold 23 checks, median 80, **8 at 16 MiB or less** (15 above); r1-3 2 at 16 or less; r2-3 min 16
   MiB, 1 at 16 or less; r2-2 25 checks, still 0. The verdicts do not move: r2 cold still has "most above 16",
   still fails "no refused images".
3. r2 cold worst village frame: **898 ms** (a 7.3 fps 5 s window at the area change just before the end, 3 of
   its 5 s before `script_end`), not 588. The warm runs' worst figures include that same transition.
4. Refused in r2 cold, in detail: 2 render targets 1280x720 (553-554 s) and 2 textures 384x384 (to 596 s); 1 of the
   2 buffers got memory on asking again; 64 driver lines, 4 of them placed on the retry.
5. Missed pressure sign: `EDEN_SWAP ... failures=` rose 0 -> 102 in r2 cold from the arrival on (14 in run1302,
   0 in the other four). These are slots the guest swap could not pack or write out for lack of memory; no
   "could not be mapped again / read back" line anywhere, so no data was lost. One more sign of how tight it was.
6. r2-3 warm dipped to 8 MiB (low 5) at A+12-14 without heap growth.
7. The runner's banner for group R2 still says "a repeat of v7 G2 ... (plan unchanged)"; its env lists show
   `EDEN_UP_NEW_WAIT_MS=2000` and `EDEN_UP_HEAP_RESCUE=1`, and each run's env.txt has them. A stale label only.
   The SWITCH LINT "DEAD EDEN_UP_NEW_WAIT_MS" is a false alarm (main.cpp:934, start line printed).

**Verdict of the second check.** Agrees with the first reading: r2's cold pass is a near miss reached by timing at two danger
moments, not a margin and not the switches. 3 cold starts with these settings: 2 reached the village, 0 met the
bar. The switches have neither helped nor cost anything, because they have never run. v9 says something about
them only if an `EDEN_NEW_WAIT start` line appears; otherwise a forced test (`EDEN_TEST_HEAP_NO_GROW` armed
just before the door on a warm start) is the way to see one wait end without a hang.
