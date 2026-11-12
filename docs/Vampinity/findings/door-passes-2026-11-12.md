# Door passes tonight: independent check (2026-11-12, 04:20)

> **Found:** New-game runs that passed the house door most likely passed because the village's pipelines were already on disk (0 new compiles at the door against 21-24 in the runs that died); about 65% sure, only 4 passes and 7 deaths.
>
> **So:** Pipeline compiles at the door push the heap over the edge; a fresh install will likely still hit the wall, so test empty caches on purpose.

I checked a first report on why tonight's new-game runs got through the house door when the earlier ones died.
READ means I saw it in a log, a source file or a frame. INFERRED means it is my reasoning. I touched no console
and no file except this note.

## Answer

The most likely cause is that the village's drawing recipes (pipelines) were already on disk tonight. Confidence:
medium, about 65 %.
- In the two clean dead runs (1240, 1242), the door load came with about 21-24 brand-new pipeline compiles.
  In 1240 the program's own memory store (the heap) grew from 1,184 to 1,952 MiB in the same seconds, and the
  run died on a file-service request of 834 KB. READ.
- Tonight's c1, g1 and h1 compiled 0 new pipelines at the door, and their heap stayed at 1,248-1,280 MiB. w0
  compiled 6 new at the door and squeezed through. READ.
- That the compiles caused the heap growth is INFERRED. Nothing logged the heap between t 439 and the crash.
  Patch 0505's own notes say the earlier memory crashes died inside the driver's compiler, and that one large
  compile can hold hundreds of MiB.

The build (T134), PIPELINE_LIST_KEEP, the census and POOL_WALK do not explain it (details below). Only 4 passes
and 7 deaths exist, and the groups differ in several things at once, so this is no verdict.

## Terms

- Pipeline: a drawing recipe the graphics driver must compile before the game can draw with it.
- New compile: a pipeline built from scratch, with no record on disk.
- On-disk build: a pipeline rebuilt from a record already on disk. This is cheaper.
- Heap pieces: the memory the emulator's own store has taken from the system.
- Idle arenas: heap pieces that are taken but hold nothing.
- Pool available: what the console still has free.
- Driver memory: what the graphics driver holds.

## Run count

- Seven runs reached the house and died, not eight: 1234, 1236, 1238, 1239, 1240, 1241, 1242. READ: the wait
  lines, and for 1241 frame f0107, which shows the house.
- 1233 crashed at 246 s, before the house. 1235 and 1237 hung at the wait on line 105. READ.
- The test plan's own list names seven runs. The first read was right about this.

## Tonight's batch (checked on result.json, the wait lines, batch.log and a frame)

| Run | Switches on | Ending | Prompt met (test clock) | Frame | New compiles at the door |
|---|---|---|---|---|---|
| w0 run1255 | none (warm-up) | script_end, 623 s | 448.5 | f0125: porch above the village | 6 |
| c1 run1256 | none (control) | script_end, 605 s | 444.66 | f0122: porch above the village | 0 |
| g1 run1257 | GUEST_WRITE_WAIT 10 s + HEAP_STEAL=3 | script_end, 609 s (result.json now written) | 444.79 | f0112: porch above the village | 0 |
| h1 run1258 | HLE_REPLY_BUFFER + HLE_OOM_RETRY | script end at 579.1; batch.log "Script done after 603 s"; result.json not written yet at 04:15 | 444.09 | f0108: porch above the village | 0 |

Did each switch fire?
- g1: the guest-write wait never fired (EDEN_GUEST_WAITS 0/0/0). HEAP_STEAL logged its mode line and no count.
  READ.
- h1: the reply buffer was active, with about 97,000 allocations saved and 892 KiB held. The OOM retry caught 0.
  READ.
- On these caches the control already passes, so these arms can credit no switch.
- Still to run: d1, vw/v1, k1, a1, a2.

## env.txt, c1 against run1240 (redone, READ)

- c1 has 84 lines and run1240 has 81. Tonight's file adds EDEN_UP_PIPELINE_LIST_KEEP=1, EDEN_UP_MEM_CENSUS=1
  and EDEN_NX2_POOL_WALK=1. The script name also differs. Everything else is identical.
- w0 differs from c1 only in the script name.
- script.txt and config.json are identical between c1 and run1240.
- 1234, 1236 and 1238 also lack EDEN_GBB_TRUST_COPY=1 and EDEN_NX2_RESNAPSHOT=0.
- The p3 runs (1241, 1242) also differ in these: FRAMES_AHEAD=1, GPU_TRANSCODE_MIB=256, FRITCHII_USAGE_TRACKER=1
  and RADV_PS5_SUBMIT_THREAD=1 were on, and SKIP_STALE_UPLOADS was off. So p3 is not a clean comparison.
- Build: T134 adds patches 0581-0591. Each is off unless its switch is set, and 0581 says "the old code, byte
  for byte". None is set in c1. READ from the patch headers. I did not audit the cost of every line when off.

## Memory side by side (stderr clock t_s, MiB, READ)

Each row reads: pool available / driver / heap pieces (idle arenas).

| Moment | c1 (passed) | run1240 (died) |
|---|---|---|
| Before the first 3D scene (t ~100-200) | 4,962 / 690 | 4,962-4,994 / 689 |
| First 3D scene | t 226: 817 largest free; heap 1,216 (8) | t 217: 873; heap 1,088 (10) |
| Long scene | t 343: 785; heap 1,248 (8) | t 338: 809; heap 1,152 (10) |
| Control in the house (wait 105 at test 433.0 / 433.2) | t 434-444: 753 / 2,923 -> 3,174 -> 2,982; heap 1,280 (8) | t 429-439: 809 -> 745 / 3,080 -> 3,814; heap 1,184 (20) |
| Texture cache just before | 1,485 MiB in 809 images (t 427) | 1,753 MiB in 1,161 images (t 417) |
| Door load (prompt at test 444.6 / 444.4) | t 452: 206 / 3,043; t 454: 180 / 3,844; heap unchanged | t 449: 126 / 3,882 |
| New compiles at the door | 0 (33 on-disk builds) | about 24: 12 by t 452, about 9 more at 453.9-454.3, plus 3 mesh pipelines not in the cache |
| After | t 468: 22 largest free / 3,710; t 474: 3,131; heap still 1,280 | t 455: bad_alloc on the file-service thread for 834,033 bytes; crash file: largest free 6 MiB, heap 1,952 pieces; heap.log live 1,840 MB |

## The "+0.7 GiB driver jump" (verified from the RADV lines)

- In 1240 it came 6-10 s after control (3,080 -> 3,814 at t 439) and stayed at 3,695-3,882 until the crash.
- In c1 control brought only +250 (3,174 at t 436), then 2,982. The +0.8 GiB step came at the door load (3,844 at
  t 454) and fell back to 3,131 by t 474. It came again on arrival in the village (3,707 at t 503 -> 3,073).
- The step is not what emptied the pool. In 1240 the driver rose by 734 MiB while the pool fell only 64 MiB
  (809 -> 745). READ.
- The pool's big fall is the door load itself, about 550-620 MiB in both runs: c1 753 -> 206 at t 448-452,
  1240 745 -> 126 at t 442-449.
- After that fall, 1240 also needed heap and compile memory, and nothing was left.

## PIPELINE_LIST_KEEP and boot builds (code: patch 0479, vk_pipeline_cache.cpp)

What the code does (READ):
- KEEP only makes SaveUsedPipelines return early, so this session does not rewrite vulkan_used.bin.
- It does not change which pipelines this boot builds. That is set by the list already on disk. The log line
  "831 built at boot" is printed only when KEEP is on.
- So the first read's "Yes, KEEP changes how many are built" is wrong. 831 against about 1,093 reflects whose list
  was on disk: the owner's tonight, and the one run1239 wrote for run1240.

What boot builds cost the driver (READ):
- The driver's shader store was 16,128 KiB in 6 blocks in both 1240 (1,093 built at boot) and c1/w0 (831 built).
- Driver memory at t 100-200 was 689 against 690.
- Evicting the unused boot pipelines (960 in 1240 at 186 s; 804 in c1 at 193 s) returned about 17 MiB in each
  (689 -> 672, 690 -> 673).
- So a built pipeline costs the driver about 20 KiB. 262 more pipelines is about 5 MiB, which cannot explain a
  difference of hundreds of MiB.
- The heap at the first scene was actually higher tonight (1,216 against 1,088), and tonight still passed.

## Corrections to the first read

1. A claimed point against the cache cause is wrong. The first read said 1240 and 1242 "had nearly full caches
   (15-17 new) and still died". Their 10 s summary lines missed the last window, because the runs died first.
   - Per-pipeline lines show about 24 new compiles in 1240 and 21 in 1242 (t 448-454.7), all during the door load.
   - This supports the cache cause rather than counting against it.
2. KEEP does not change this boot's builds (see above). Its only link is that tonight's list is the owner's.
3. 1242 died differently. Its heap was already 1,856 MiB of pieces with 260 MiB idle, and the pool was at 220
   before control. Its heap barely grew (to 1,920 at the crash). It also had the p3 extra switches.
4. Timing of the driver step: in c1 it came at the door load, not a few seconds after control. Several of the first read's time labels are 2-4 s off: peak 3,844 at t 454, not t 452; 22 MiB free at about t 468.
5. Tonight is now 4 of 4 passes (h1 also passed), against 0 of 7. A Fisher test gives p about 0.003. But the
   groups differ in cache state, build, settings, time and the crash before them all at once, so the test does
   not name a cause.
6. "A newcomer needs about three starts" is not supported.
   - The door compiles happen in the last 1-2 s before a crash, and records are saved every 20 s.
   - So a door death probably loses them, and the next warm start meets the same ~21 compiles again (INFERRED).
   - A newcomer could loop on the door. Untested.
7. Other differences the test plan did not list (READ):
   - 1240 and 1242 started right after a crashed run. Tonight's runs started after clean exits.
   - 1240 held 270 MiB more texture cache before the door (1,753 against 1,485).
   - Both dead runs failed on the same file-service request, of about 833-834 KB.

## Deciding test

A. Cheap, and leaves the owner's caches untouched:
- Run T130 with run1240's exact env.txt plus EDEN_UP_PIPELINE_LIST_KEEP=1 on the owner's caches. KEEP only stops
  the list being rewritten.
- Do two starts.
- If both pass with 0 new compiles at the door: the build, the census and POOL_WALK are cleared, and the cache
  cause stands.
- If they die: the cache cause falls.

B. Confirms the cause:
- Use T134 with c1's env.txt. Set the owner's caches aside with cold-start.v3.py, which renames them and deletes
  nothing. Check it first with --status, since its header calls it an offline-checked draft.
- Run a cold start and then two warm starts. Then put the caches back and confirm with --status.
- Read the new compiles per second at the door, the heap pieces from the prompt to A+10 s, and whether it crashed.
- If a warm start dies at the door during about 20 new compiles while c1-type runs do not: the cause is
  confirmed.
- If it passes with about 20 new compiles and a flat heap: the cause falls.

## In plain words (written for the project owner) (6 lines)

1. Tonight 4 of 4 new games reached the village. Earlier, 7 of 7 died at the house.
2. The likely reason is your own caches. Tonight the village's drawing recipes were already on disk, so nothing had
   to be compiled during the door load.
3. In the dead runs about 20 recipes were compiled right at the door, and memory ran out in that second.
4. The new build and the new settings changed under 30 MB before the door, so they are not what saved these runs.
5. It is still tight: 0-22 MB free after A even tonight. A fresh install will likely hit the wall.
6. Next: one safe test of the old build on your caches, then one empty-cache test on the new build.
