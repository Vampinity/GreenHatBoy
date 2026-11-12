# Thread stacks and command streams: can we get memory back at the door? (12 Nov 2026, ~07:00)

> **Found:** Of the memory ideas from another PS5 port (thread stacks, flexible memory, command streams), only smaller thread stacks would give memory back here, about 60-90 MiB; our streams and flexible memory are already small.
>
> **So:** None of these fixes the house-door wall by itself; EDEN_STREAM_RING_MIB=64 is a free 64 MiB that already exists as a switch.

Source item: upstream-news.md (local note):282 (02:25 run, mihawk-99/PS5_Hookshot PR #1, CHI-GETSU), port-now line upstream-news.md:293. Audit row 10 (forgotten-audit-2026-11-12.md:16, :79). Read only: no source edited, no test started.

## Numbers first

| Lead (theirs) | Ours on T134 | MiB we could get back at the door | How sure | Draft? |
|---|---|---|---|---|
| Host thread stacks 16 MiB each, ~92 threads, 1.37 GiB back | **2 MiB each** by default, about **65-70 threads**, about **125-140 MiB** in all | **~60 MiB** at 1 MiB stacks, **~90 MiB** at 512 KiB | low-medium: one unknown decides it (below) | yes, small, switch off by default, count line first |
| Flexible memory 768 → 544 MiB, +224 MiB | already **320 MiB**; ruled out on 7 Nov | **0** | high | no |
| Command streams 24 MB each, 55-70 KiB used, ~1.1 GiB back | our streams start at **80 KiB** and grow to at most **1 MiB** pieces, given back at each reset; one **16 MiB** ring for the whole driver | **0-10** | high | no |
| (ours, not theirs) the 128 MiB upload stream ring | 128 MiB, held all session | **64** with `EDEN_STREAM_RING_MIB=64`, a switch we already have | medium (safety, not size) | no draft needed: env line only |

Against the door wall (heap grows ~0.8 GiB in seconds, pool at its floor) none of these is a fix by itself. The stack change is a cushion of about 8-12 % of that burst. The other port's 1.4 GiB does not exist in our build, because our stacks are already 8 times smaller.

## 1. Thread stacks

**Size each thread gets**
- Most threads ask for no size, so they get the system default: `std::thread` / `std::jthread` with no attributes. Examples: the 8 pipeline builders (common/thread_worker.h:165, named at video_core/renderer_vulkan/vk_pipeline_cache.cpp:750), and the wrapper's own threads (headless/log_flusher.h:40, headless/stall_watchdog.h:75, headless/crash_report.cpp:809/836/837, headless/jit_list.h:160, headless/audio.cpp:35, headless/devices.h:147, src/guest_memory_service.inc:3304/3306/3329). Mesa's own threads do the same (`thrd_create`, radv_ps5_cs.c:437 submitter, radv_ps5_platform.c:868 kick).
- On this console the default is **2 MiB of direct memory per thread**. Source: the comment at t134-wt/src/direct_memory.c:7 ("the Payload SDK takes 2 MiB of direct memory for each, and keeps freed ones for the next threads"). The wrap treats an exact 2 MiB request as a stack and places it at the top of the pool (direct_memory.c:16, :31, :170-174). This is the same as FreeBSD's default thread stack (2 MiB on 64-bit), and that thread library also keeps freed default-size stacks for reuse. `pthread_create` itself comes from the console's libkernel. Neither the SDK nor the Mesa platform library defines it: ps5-payload-sdk/target/lib/libpthread.a is an empty archive, and libps5platform.a only imports `pthread_create`.
- Threads that already ask for less:
  - GPU worker: 1 MiB (headless/native_gpu_thread.inc:27). The T134 log prints `EDEN_GPU_WORKER_STACK bytes=1048576`: run1256 heap.log:161.
  - dav1d's 4 workers: 1 MiB each (dav1d src/lib.c:161-163 in the build VM; 4 threads per eden_log.txt `libdav1d: 4 threads`; set at video_core/host1x/ffmpeg.cpp:301-311).
  - Update check: 1 MiB (headless/update_notice.cpp:31, :121).
- Guest fibers are separate from host threads. There are 128 of them at 512 KiB in **flexible** memory, 64 MiB in all, none in the heap: run1256 stderr.log:159 `allocations=128 flexible=67108864 fallback=0 stack_bytes=524288`. Code: headless/fiber_stack.h:15-16, :84 (512 KiB default, `EDEN_FIBER_STACK_KIB`). The core's own size is common/fiber.cpp:18-20. This memory is not the pool the door crash runs out of, so shrinking fibers would not help there (see section 3).

**How many threads in a T134 door run** (run1256-c1-door-wall-control, eglantine-logs-2026-11-05/auto-20261112-033108-batch-door-wall-t134/)
- 43 placed by name (heap.log `EDEN_WORKER_PLACED`; the print cap is 64, headless/performance.cpp:313, so this list is complete):
  - 8 VkPipelineBuilder, 4 ImageTranscode
  - 2 nx2:vdec, 2 am:N, 3 bsdsocket, CPUCore_4 and CPUCore_5
  - GPUBack, VulkanWorker, TextureDecoder, VkPipelineSerialization, GPUFencingThread
  - audio threads (AudioManager, AudioRenderSystemManager, DSP_AudioRenderer_Main, DSP_OpusDecoder_Init, DSP_OpusDecoder_Main, audio)
  - FS, vi, ldn, nvservices, TimeWorker, KWorkerTaskManager, am:EventObserver
  - MemCensus, MemoryReport, DeviceMemory:ColdHint, nx2:ColdHint
- 5 pinned: CPUCore_0-3 and GPU (heap.log `EDEN_WORKER_PIN`).
- About 12-15 wrapper threads (the files listed above), 4 dav1d, 1-2 Mesa.
- **Total about 65-70.** About 6 of them already run at 1 MiB, so about **60-64 run at the 2 MiB default: ~125 MiB** (guess range 120-140).
- A rough check from the pool ledger at boot: run1256 stderr.log:111 shows 328 blocks of 2 MiB. Take out guest 172 MiB, reserve 256 MiB and JIT 192 MiB, and about 18 blocks (36 MiB) are left. That fits about 17 stacks plus the driver's zero block, before most game threads start. The ledger cannot show the later count, because the guest's pieces mix in.

**Committed or only reserved?** Committed. Direct memory is physical memory, taken whole when the thread starts. It comes out of the same 12,352 MiB pool that the heap grows from (the heap also asks for the top of the pool, direct_memory.c:5-15). A stack the thread never touches still costs its full 2 MiB.

A cross-check that stacks are not in flexible memory: flexible free drops from 167 to 86 MiB over the boot (stderr.log:111 and the following ledger lines). That is 81 MiB, of which the fibers take 64 MiB. Sixty stacks of 2 MiB in flexible memory would have taken 120 MiB more.

**The one unknown that decides the gain.** Does libkernel take a smaller direct block when a thread asks for a smaller stack, or does it round up to 2 MiB anyway? Nothing in our sources or logs shows it. The 1 MiB threads above are live today, but no log line names their blocks, and class 0 of the ledger mixes in the guest's small pieces. If it rounds up, the gain is 0.

## 2. Command-stream buffers, command pools, staging

- **Driver command streams** (build VM, mihawk-vulkan-review/.deps/work/radv-src/src/amd/vulkan/winsys/ps5/; patched 11 Nov 06:35; the driver was not rebuilt since, local-build.sh:83-86):
  - A stream starts at 20 Ki words = **80 KiB** of heap (radv_ps5_cs.c:34, :52-61, :73).
  - It doubles as needed, up to **1 MiB** pieces (radv_ps5_cs.c:35, :124-125).
  - At each reset every finished piece is freed. Only the current piece stays, at most 1 MiB (radv_ps5_cs.c:175-183, :84-91).
  - Nothing is 24 MB, and nothing is fixed per thread.
  - Eden makes command buffers 4 at a time (video_core/renderer_vulkan/vk_command_pool.cpp:12). Even 16 of them at a full 1 MiB would be 16 MiB, and most never grow past 80-320 KiB.
- **Driver ring**: one 16 MiB ring and one 16 KiB marker page for the single queue, taken once (radv_ps5_winsys.h:28, radv_ps5_winsys.c:44-48; placed at the top by direct_memory.c:153-163). A submission too big for the ring gets a buffer of its own at that moment (radv_ps5_winsys.h:25-27). So shrinking the ring would add allocations at the worst moment. Not worth 8-12 MiB.
- **Eden's own chunk buffers**: 32 KiB each (vk_scheduler.h:399), reused (vk_scheduler.cpp:716, :920-926). Small.
- **Upload stream ring: 128 MiB**, held all session (vk_staging_buffer_pool.cpp:43-46, :168, :187). In the T134 run: `rings=137984/3/137984/131072/3` KiB, with the largest block 131,072 KiB = this ring (run1256 stderr.log, last `RADV_PS5_MEMORY` line). Next to it: a 4 MiB reserved download buffer (:196-199) and a 2 MiB turbo buffer (vk_turbo_mode.cpp:51).
  - `EDEN_STREAM_RING_MIB=<16..128>` already exists (vk_staging_buffer_pool.cpp:97-119). 64 MiB keeps the same region count and gives back 64 MiB.
  - waveydude's preset carries `EDEN_STREAM_RING_MIB=64` (project log:527), and our T125 menu and field runs 1102-1106 used it.
  - The only bad mark: one Mario Kart World death at run85 (a local note of 7 Nov).
  - Not in the live env (env-play-v27/v28 have no line for it) and not in the door-wall batch.
- How much of each buffer is really used: no counter in T134 logs for stream words or ring fill. The driver report gives held sizes only (`upload=9008 KiB in 67 blocks`, `descriptor=8288`, `shader=24320`, `mesh=87040`, same line).

## 3. Flexible memory: confirmed ruled out

- Our param.json sets `flexibleMemorySize` 335,544,320 = **320 MiB** (t134-wt/sce_sys/param.json:40). That is already below the other port's 544 MiB end point.
- headroom-memory-2026-11-07.md:101 and :104: direct and flexible are one launch budget. Shrinking flexible further dropped T46 to 27 MiB free. No gain.
- In T134 flexible free sits at 86-91 MiB all run, with 0 fiber stacks falling back to the heap (stderr.log ledger lines). There is no slack to move.

## 4. Verdict and what to draft

- **Stacks: worth one small switch-gated draft for the next build, but not before the crash work already queued.** About 60 MiB at 1 MiB stacks, about 90 MiB at 512 KiB, and only if the unknown in section 1 goes our way.
  - Draft outline: `--wrap=pthread_create` in the link (same mechanism as the direct-memory wrap). When the caller gave no stack size, set `EDEN_HOST_STACK_KIB` (off unless set; 512-2048, whole 16 KiB pages).
  - The direct wrap must also send blocks of that new size to the top of the pool. Today it knows a stack only by "exactly 2 MiB" (direct_memory.c:172-174). Without that change, small stacks land at the bottom and split the region the graphics memory needs. That is the problem direct_memory.c:4-12 was written to fix.
  - Same build, a count line: at each direct request between 256 KiB and 2 MiB with `from == 0` in the first 120 s, print the size. One boot with the switch at 1024 shows at once whether 1 MiB blocks appear, which answers the unknown.
  - First arm 1024 KiB: the GPU worker and dav1d already run at that size every session. 512 KiB only after that. The other port measured a deepest use of 141 KiB, and the pipeline builders run the same shader compiler they measured.
  - What could break:
    - A thread that goes deeper than its stack hits the guard page: a crash at a known address, likely at the very door where the compiler works hardest.
    - Non-default stacks are not kept for reuse, so threads that come and go would make and free direct blocks.
    - If libkernel rounds up, nothing is gained and nothing is lost.
- **Command streams: skip.** Our driver does not have the 24 MB-per-stream layout; at most about 10 MiB is there to take.
- **Flexible: skip** (above).
- **Cheaper than any draft:** `EDEN_STREAM_RING_MIB=64` is env-only, gives a sure 64 MiB of pool, and has run on T125. One door-wall arm with that line costs no build. Its risk is a stall or crash on very large uploads, not a memory loss.
- Also from the same news item, for the door crash reading: under low memory, RADV can report "SPIR-V parsing FAILED" on a valid shader (upstream-news.md:282 point 3). On our console a parse failure at the door can be an out-of-memory in disguise. Read it that way in door logs.
