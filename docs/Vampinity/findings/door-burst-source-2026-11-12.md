# Door burst: what fills the heap at the house door (T134, fresh-install v6, read only)

> **Found:** At the house door the heap grows about 0.7 GiB in seconds from thousands of 256 KiB to 1 MiB requests, at the same draws (the same mesh pipelines) in every run; no single big block causes it.
>
> **So:** The likely lead is the mesh pipelines drawn and built at the door; next: log driver builds and IR use at the door, test the mesh lead directly, and make the lazy file reader wait instead of dying when its request is refused.

12 Nov 2026, ~09:20-10:30. Read only: no console, no test, no post, no tool or plan edited. Logs of run1272,
run1273, run1275, run1276 (and 1271/1274 for comparison), T134 source (t134/stack/src, t134-wt/headless).
READ = seen in a log or the source. INFERRED = my reasoning. One run per arm is no verdict.
**Checked a second time (~10:40-11:30), corrections marked [checked]; full list at the end.**

## Answer first

- **run1273 had the burst too.** Between two census samples 2 s apart the heap grew by ~736 MiB and gave
  544 MiB back at once (`gave back 544 MiB: the pool is short`). Same size as in the three deaths. (READ)
- **What the burst is made of (READ):** requests of **256 KiB to 1 MiB**, the largest 960 KiB. In run1273's
  window: +3,404 such requests (+1,358 MiB requested), against ~+300-600 (~+150-270 MiB) in a normal 20 s, and
  +704 MiB of heap growth asked by that class. Plus 51 new small-block arenas (+32 MiB) and +2,300 small
  requests that spilled. **No block of 32 MiB or more** in any run (`large=125` never moves).
- **[checked] The same draws at the door in all four runs (READ, new).** The GPU thread's last log lines in
  run1272 and run1275 are: first draw of mesh pipeline `111affc458ee39cb` (task/mesh shader
  `46cc6aaba42f700e`, 3 workgroups), then the build of mesh pipeline `7914b60ef8431847` (77-79 ms), then
  nothing. run1276 got past that point and stopped at the first draw of mesh pipeline `4df769e636e70999`
  (same task/mesh shader). run1273 passed both, and its one long frame of the run (2,139.7 ms) falls in
  the 5 s window that holds the `4df769...` first draw. So the burst and the GPU-thread stop sit at the
  same spot in the door load every time.
- **[checked] The GPU thread waits on its own work, not on the console's GPU (READ, run1276).** `Hang watch:
  waited 3 s for GPU tick 280666; the GPU is at tick 280664, the last submitted tick is 280664` and
  `stall dump asked: the GPU has run every submission`. Something on the emulator side never submitted
  the next work.
- **Owner: still not named by any log.** Best fit now (INFERRED, low-medium): the driver's compile of those
  mesh pipelines (with `EDEN_NX2_RADV_MESH_COMPUTE` the driver's compute lowering is inside the pipeline
  build, and that build runs on the builder threads) holding many 256K-1M blocks while the draw waits for
  it. The command-list copies drop to **low** (reasons in (2)).
- **[checked] Why run1273 lived is not "it came later".** run1276's burst came only ~2 s earlier and it
  died. The difference is room at that moment and luck: run1273 bottomed at 3 MiB.

## (1) The burst per run

Census lines (stderr, own thread, every ~2 s). "Pieces" = heap taken from the pool, "live" = in use.
A = the script's arrival check (`wait_met line=114/117`); "area" = the census `why=area` line (all four at
422.3-423.0).

| Run | When (census clock) | Size | Over | Pieces | Empty pages | GPU thread | End |
|---|---|---|---|---|---|---|---|
| run1272 (G1-2) | n=30 427.5 -> n=31 429.6; 0-3 s after A, 5-7 s after area | live 809 -> 1,495 (**+686 MiB**) | <= 2.1 s | 1,216 -> 1,824 (+608) | 100 -> 68 | fresh at n=30; no answer in the 300 ms wait at n=31, which came **after** the abort | FS refused 744,576 B (reply buffer) |
| run1273 (G1-3) | n=123 433.8 -> n=124 435.8; 6-10 s after A, 11-13 s after area | heap grew **~736 MiB** (+704 by 256K-1M requests), then gave back 544; live 809 -> 810 at the samples | < 2 s, freed in the same window | 1,312 -> (2,048, INFERRED) -> 1,504 | 210 -> 394 (idle arenas 116 -> 198) | answered at both samples; the 2,139.7 ms frame matches this window only within the clock error (~1-2 s) | script ended (got through) |
| run1275 (G2-2) | n=122 428.2 -> n=123 430.3 -> n=124 432.4; 0-4 s after A, 5-7 s after area | live 819 -> 1,517 -> 1,607 (**+698, then +90**) | 2.1 s + 2.1 s | 1,760 -> 1,920 (+160) | 574 -> 68 -> 4 (idle arenas 242 -> 68 -> 4) | no frame end from ~428.0 to 432.4 (age 4,368 ms) | FS refused 613,465 B inside NupLazyVfsFile::Read |
| run1276 (G2-3) | n=121 431.7 -> n=122 433.7 -> n=123 435.8; 2-6 s after A, 9-13 s after area | live 817 -> 1,419 -> 1,604 (**+602, then +185**), creeping to 1,638 by n=130 | ~4 s, then held 20 s | 1,408 -> 1,824 -> 1,920 (+512), 1,952 later | 276 -> 118 -> 16 | no frame end from ~431.4 to the end (24,953 ms at n=133) | page tables refused 2 MiB, abort |

[checked] How to read `gpu=stale/2313ms`: the census waits only 300 ms for the GPU thread, and the age counts
from its previous answer (one census earlier). So the first stale sample proves a stop of >= 0.3 s, not
2.3 s. Only a growing age over several samples proves a long stop (run1275, run1276). In run1273 the census
also shows one stale sample later (n=147, 480.6) while the present log's worst frame there is 348 ms.

Request sizes (EDEN_HEAP_CLASSES counts requests of 256 KiB to 32 MiB, cumulative; EDEN_HEAP_GROWTH says
which size made the heap grow):

- run1273, summary at line 2158 -> 2355 (the door window): under1M **+3,404 / +1,358 MiB**, under2M +17 / +18,
  under8M +33 / +95, under32M +5 / +63. HEAP_GROWTH: under1M 1,408 -> 2,112 MiB (**+704**, largest 960 KiB),
  arena 288 -> 320 (+32), arenas made 269 -> 320 (+51), spills 7,977 -> 10,277 (+2,300). given back 960 ->
  1,504 (+544). Next 20 s: under1M +599 / +306 MiB (back to normal). [checked: all recomputed, all match]
- Normal play, 20 s windows (run1272): under1M +458, +505, +496, +513, +300, +651 requests, ~+210 MiB each, at
  22-24 fps (~460 frames). That is **~1.0-1.1 requests of ~0.43 MiB per frame**. G2 (reply buffers kept)
  shows the same steady rate (run1275: ~+450-510 per 20 s), so the steady requests are not reply buffers.
- **[checked] The boot has the same class, much bigger (READ).** In the first ~23 s (game load, 27 pipelines
  from the shader cache, ~250 shader translations logged) under1M went from 30 to 18,736 requests
  (~9.1 GB requested), and the heap grew 1,408 MiB (run1273) / 1,568 MiB (run1276) / 96 MiB (run1275) by that
  class, largest 960 KiB, while the GPU had almost no work (1,100-1,600 host submissions per window against
  ~10,000-12,000 in play). So the main user of this size class is load-time work, not per-frame work.
- The three deaths: no CLASSES or GROWTH line after the burst. Those come from the 20 s summary, which the GPU
  thread decides to write (performance.cpp:1101-1112, RefreshFreeMemory; with EDEN_MEMORY_REPORT_THREAD=1 it is
  written on the report thread but still queued from the GPU thread), so it stops with the GPU thread.
- Per-thread arena reports (EDEN_HEAP_THREAD/SPACES): **none in any run**. They print only on a "refused" heap
  report (performance.cpp:1213), which is also queued from the GPU thread. HEAP_STEAL's brink report never came.
- [ps5-opengl-heap] blocks at the failure: 1,517,703 (1272), 1,527,668 (1275), against 1,456,023 at run1273's
  end. So the burst is thousands of blocks, not millions (~700 MiB / ~0.4 MiB = ~1,750 alive at the peak).
- [checked] The heap-site report did run right after run1273's burst (stderr 2328), but by then the burst was
  freed. It shows ~52 MiB alive from the lazy file reader (25 + 14 + 13 MiB, chains through
  NupLazyVfsFile::Read <- IStorage::Read; symbols from the T134 llvm-pie.elf) and a sampled block from the
  driver's shader create (`radv_shader_create_uncached`, calloc). Nothing of the burst itself.

## (2) Candidates, ranked [checked: re-ranked]

1. **The driver's build of the door's mesh pipelines (new, INFERRED, low-medium).**
   - For: in all four runs the stop and the burst come at the first draws of mesh pipelines with task/mesh
     shader `46cc6aaba42f700e` (READ). With `EDEN_NX2_RADV_MESH_COMPUTE=1` a mesh pipeline is one graphics
     build with the driver's compute lowering inside it (0537 patch notes), queued on the builder threads
     (vk_pipeline_cache.cpp:467-476). The driver's compile memory goes to this heap (calloc from
     radv_shader_create_uncached in the site list). A draw waiting for that build would leave the GPU thread
     waiting on work it never submitted, as run1276's Hang watch shows. When the build ends, its memory goes
     back at once (run1273). Load-time compiles at boot make the same size class, much bigger.
   - Against: not measured. The GPU-thread translation of these pipelines is logged as short (2-79 ms), and
     no log gives the driver build's time or memory.
2. **Shader IR pools (INFERRED, low-medium).** 960 KiB is exactly 8,192 x 120 bytes: one chunk of
   `ObjectPool<IR::Inst>{8192}` (vk_pipeline_cache.h:118; IR::Inst is 120 bytes by its fields in value.h).
   The source says one large program's IR can take "hundreds of MiB" (vk_pipeline_cache.cpp:467-473). Builder
   jobs with their own pools free them when the job ends. Against: the GPU-thread translations at the door
   are all short; a burst of IR would need a builder job or a translation not in the log.
3. **Command-list submit copies (was top; now low for the burst).**
   - nvhost_gpu.cpp:446-511: every SubmitGpfifo copies its entries' words into `entries.submitted_words`, on
     by default. A copy of 64K+ words is >= 256 KiB.
   - Against, three ways: (a) the present waits up to 4 s for its frame's fence (nx2_gsv.h:2621,
     `EDEN_UP_OOT_FRAME_WAIT=1`), so in the first 4 s of a stop the game is held and cannot submit ~1,700
     frame-sized lists in 2 s; run1276's first "not reached in 4 s" came 4 s into its stop. (b) Host
     submissions do not rise at the door (run1273: 8,893 in that window against 9,700-12,100). (c) The boot
     makes the same class with almost no GPU work.
   - Can still explain the slow creep in run1276 (+33 MiB over 20 s, after the present waits gave up).
4. **Texture decode or upload staging (low for the heap).** Async CPU decodes are all logged
   (EDEN_NX2_TC_LOG=1): one per run, **none at the door**. Decode images are Vulkan memory (pool), not heap.
   Synchronous uploads use the kept scratch (census cpu_scratch flat at 65 MiB). The door adds +359/+440/+541
   MiB of GPU images: the other half of the empty pool, not the heap burst. Note: the census's image and
   decode numbers come from the GPU thread, so in the deaths they are frozen at the last answer.
5. **Lazy file reader's whole-file buffers (not the filler: the victim).**
   - nup_container.cpp:446-480: in-memory members are charged to an LRU capped at `EDEN_NUP_CACHE_MIB=64`.
     Files over 32 MiB go to a temp file. The LRU holds the only lasting `shared_ptr`; Read (:563) keeps its
     own only for the call. Decode input chunks are 128 KiB (:359), under the burst's class.
   - Door volume: run1273 cache lines 449.6 -> 456.1 = "511 files, 608 dropped (18 MiB)" -> "265 files, 864
     dropped (27 MiB)", cache full at 63 MiB. It cannot hold 700 MiB; the site report shows ~52 MiB of it.
   - Its 613,465 B request (a file's size, :665) was the one refused when the pool hit 3 MiB.
6. **Emulated service reply buffers (ruled out as the filler).** G2 kept them (`allocations_saved=218,747`,
   `allocated=9`, 892 KiB held) and G2's bursts are as big. Note G2 also differs in 8 other switches.
7. **Guest memory touched for the first time (ruled out for the heap).** That is pool (`guest=`), +74 to +149
   MiB across the burst.

## (3) Why run1273 did not die

- [checked] **Not timing.** Bursts after the area change: 1272 5-7 s, 1275 5-7 s, 1276 9-13 s, 1273 11-13 s.
  1276 came ~2 s before 1273 and still died.
- **Room at that moment.** The pool's largest block was 178-284 MiB before it, with 210 MiB of empty heap
  pages, and the texture cache dropped images 2,412 -> 1,997 MiB between n=122 and n=123. The pool bottomed
  at **3 MiB** (n=124, guest reserve 64 -> 44): a near miss.
- **The deaths had no room.** 1272: pool 96 MiB and the driver at 3,673 MiB. 1275: pool 163 -> 30 MiB and the
  driver 2,985 -> 3,724 MiB around A. 1276: pool 91 MiB. Something else was refused first: FS twice, the page
  tables once. The GPU thread never came back, so the burst was never freed.
- **Not answered:** what the GPU thread waits for at those draws (run1276: a tick never submitted).
- Warm start 2 died in both batches here (1272, 1275); warm start 3 died 1 of 2 (1276 died, 1273 lived).

## (4) Env-only test with T134 switches [checked: rewritten]

Warm start 2, control / arm / control back to back, ~3 valid runs per arm.

- **Measuring, log only, outside the shader-store stamp list (vk_pipeline_prep.cpp, checked by name):**
  `EDEN_UP_DRIVER_BUILD_LOG=1` (driver build count, over-10 ms count, mean and maximum every 10 s) and
  `EDEN_UP_IR_FREE_LOG=1` (IR in use and held for every GPU-thread translation, and any builder job holding
  32 MiB+). Add both to the control env. Limit: both are written from the frame side, so a death may not
  print the stuck window; a survivor (like run1273) will.
- **`EDEN_HEAP_LARGE_KIB=256`: a fix candidate, not a neutral probe.** heap_pages.cpp:110-121 reads it and
  prints `EDEN_HEAP_LARGE requests of 256 KiB or more get memory of their own`; the census `large=` does count
  these blocks (eden_heap_large_held includes them) and keeps printing through a stop; table 8,192 entries
  (~1,750 needed). But: it was already run (t116-k / run992: 17.9/17.7/17.6 fps on the door walk, about
  -0.5 to -0.7 fps, switch-ledger.md and retest-round-2026-11-11.md), blocks under 2 MiB take 16 KiB pages and leave the pool in smaller pieces (heap_arenas.inc:240-243;
  run1276 died on a 2 MiB slot), and it only shows size and timing, which we already know. A survival or a
  death under it could be the switch itself. Run it as its own fix arm.
- **`EDEN_NX2_PB_SNAPSHOT=0`: do not run it at the door.** The env has `EDEN_GBB_TRUST_COPY=1` +
  `EDEN_NX2_RESNAPSHOT=0`, which rely on the submit copy. dma_pusher.cpp:359-380 documents a first-start crash
  (run1233) where reading lists from memory after a long GPU stall parsed later-frame words: junk, then a
  crash. The switch removes that protection on exactly this kind of start, so a junk death would hide the
  answer. If wanted: a house-only run (script ends before the door), reading under1M per 20 s. If the ~1 per
  frame stays, the copies are out with no door risk.
- **Direct test of the mesh lead (has costs):** `EDEN_NX2_MESH_SKIP=111affc458ee39cb,4df769e636e70999` skips
  those two pipelines' draws (vk_rasterizer.cpp:727-760). It is in the stamp list, so the warm store is not
  shared, and a few draws go missing on screen. The pipelines are still built, so: burst gone = the draw's
  wait; burst stays but no stop = the build's memory.

## (5) Code fix outline

1. **Victim cover in the lazy reader** (needed whatever the owner): catch the refusal of
   `make_unique_for_overwrite` (nup_container.cpp:665), trim and wait like HLE_OOM_RETRY, or spill that
   member to the temp file while the pool is short. Turns the FS death into a wait.
2. **>= 256 KiB transient requests back at once** (what LARGE_KIB=256 does), so a finished burst returns to
   the pool without waiting for the next trim. The trim is queued from the GPU thread, so it is late in a stop.
3. **If the mesh lead holds:** limit how many driver builds of mesh pipelines run at once while the pool is
   short, and let the draw skip (or wait with a time limit) instead of blocking the submit side.
4. **Only if the copies are proven:** count copy bytes not yet parsed (nvhost_gpu after
   `submitted_words.resize`, minus at parse), cap them, and reuse a ring instead of a vector per submit.

## (6) Measuring line for the next build (the logs cannot decide)

On the census thread (memory_census.h), which kept printing through every stall: when heap live rises by
>= 256 MiB since the last census, once per 30 s, print one line and the two existing reports.

```
EDEN_MEM_CENSUS_BURST n=%u live=%llu (+%llu) MiB: driver_builds running=%llu (oldest %llu ms, mesh %llu), ir_held=%llu MiB, pb_copies alive=%llu lists %llu MiB, nup_lazy=%llu MiB, gpu_stale_ms=%llu, gpu_waits_tick=%llu submitted=%llu
```

Then call `eden_heap_sites_report()` and `eden_heap_arena_report()` from that thread.
- The site table follows every block of 1 MiB+ and 1 in 128 below (heap_arenas.inc:1506-1529). ~1,750 burst
  blocks give ~14 samples (each counted x128, ~50 MiB): enough to reach the top 24 if they share a chain.
- The arena report names the threads (EDEN_HEAP_THREAD ... grew=) that made the heap grow: a builder
  thread vs the GPU thread vs FS answers the question at once.
- New counters needed: running driver builds with their start time (where the builder job starts/ends), and
  the GPU thread's waited tick vs last submitted (the Hang watch already has both).

## In plain words (written for the project owner) (plain words)

1. The third start that reached the village had the same 0.7 GB memory jump at the door. It was over in 2
   seconds and the memory came back. The memory ran down to 3 MB, so it nearly crashed too.
2. In all four runs the jump comes at the same moment of the door load: when a few special 3D models are
   drawn for the first time. In the crashes the graphics thread stops right there and never moves again.
3. It is not the game's file loading. That cache is capped at 64 MB. The file read was only the one that
   asked last and got refused.
4. Best guess now: preparing those special models' graphics programs takes a lot of memory for a moment.
   The earlier guess (copies of drawing commands) does not fit the numbers. Not proven yet.
5. Next: two log-only switches on the next door runs, then one log line in the next build that names the
   owner the moment it happens.

## Checked a second time (12 Nov, ~10:40-11:30)

What I did: opened the four runs' stderr, eden logs, heap.log and crash reports, the T134 source and the
T134 llvm-pie.elf (symbols for the heap-site and crash stacks). How sure: **size and timing high (READ);
the shared draw point high (READ, same pipeline ids in all four logs); the owner still unknown: driver
mesh builds low-medium, IR pools low-medium, command-list copies low.**

What changed:
1. All burst sizes, class counts and growth numbers recomputed: they match.
2. `stale/2313ms` was read as a 2.3 s stop; it only proves >= 0.3 s (the age counts from the previous census).
   Long stops are proven only in run1275 (>= 4.4 s) and run1276 (~25 s). run1272's stale sample came after
   its abort.
3. run1273's 2,139.7 ms frame: the logs use different clocks; it matches the burst only within ~1-2 s.
4. New: the same mesh pipelines (task/mesh `46cc6aaba42f700e`) are the GPU thread's last logged work in all
   three deaths and sit at the burst in the survivor; run1276's Hang watch shows the GPU thread waiting for a
   tick never submitted, with the console's GPU idle.
5. New: the boot makes the same size class (~18,700 requests, ~9.1 GB, up to 1,568 MiB growth, largest
   960 KiB) with almost no GPU work; 960 KiB = one IR instruction chunk exactly.
6. Command-list copies moved from top to low: the 4 s present wait, flat host submissions at the door, and
   the boot all argue against them.
7. "run1273 lived because its burst came later" removed: run1276's came ~2 s earlier and died.
8. Arm A: already tested (-0.5 to -0.7 fps), fragments the pool, adds no new facts: kept as a fix arm, not a probe.
   Arm B: risky on a first start (documented junk crash with TRUST_COPY + RESNAPSHOT=0): not at the door.
   Added two log-only switches outside the stamp list, and a mesh-skip test with its costs.
9. Measuring line: adds driver builds and the GPU thread's waited tick; sample estimate ~14, not ~25.
