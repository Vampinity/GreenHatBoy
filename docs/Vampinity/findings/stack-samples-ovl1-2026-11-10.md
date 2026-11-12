# Where the threads spend their time: stack samples of batch ovl-20261110-1 (T107, fast mode, door walk)

> **Found:** Stack samples of the door walk show the biggest time sink outside game code is the drain spin on the front thread; clock reads are under 1% outside wait loops.
>
> **So:** A time-stamp-counter port is not worth it; work on the drain spin and the GPU fence polling first.

Read 11 Nov 2026 00:15 by a reviewer. Samples: 24 files of runs r2 and r3 (pids 1230 and 1232), 5.14 s windows at about 194 samples a second, from 80 s on; 6,000-6,281 samples a thread. Symbols: no T107 ELF is left, so T107 addresses were byte-matched onto the VM's later `llvm-pie.elf` (94% exact, 5% near, 0.9% unmapped). Working files: working folder `sym/` (remap.py, merged.txt, phases.txt, cats.txt). `local-build.sh` still does not keep each build's ELF: the next build overwrites the only copy.

Phases by the 5 s fps lines: H house 60 fps, L village load, F fly-over 15-21 fps, A after the cut 33-36 fps, D late dip 22-26 fps.

## The finding

**The GPU front thread waits about 78% of the time, and 47% of all its samples are spent spinning while it waits for the back thread (GPUBack) to drain its queue. The back thread meanwhile is idle about 36% of the time. The two GPU threads mostly take turns instead of overlapping.**

GPU front, share of samples:

| Waiting on | All | H | L | F | A | D |
|---|---|---|---|---|---|---|
| GPUBack drain (GpuSplit::DrainAt / WaitFor spin plus sched_yield) | 46.9% | 40.8 | 51.5 | 47.6 | 47.0 | 46.6 |
| Nothing queued (HostCommandQueue::PopWait) | 17.8% | 49.5 | 16.7 | 9.9 | 11.2 | 12.1 |
| Host GPU fence (radv_ps5_queue_wait_seq: clock_gettime + nanosleep polling) | 13.3% | 4.5 | 8.5 | 18.6 | 15.3 | 10.3 |

- What triggers the drains (share of all front samples): `Maxwell3D::FrontDmaRead` 16.3% (22.4% in the fly-over), `DmaPusher::Step` / `WaitForListWriters` 15.1%, `ReadSemaphoreWord` 12.2%.
- eden_log agrees: "DMA snapshot: 234077 reads skipped the drain, 28067 drained" at 107 s and "448309 skipped, 75979 drained" at 132 s; the misses are mostly "compute/copy" (20,033 then 50,368).
- The fence wait runs through `Nx2ReadListCopy` <- `ReadGpuWrittenCommandList` -> `MasterSemaphore::Wait` -> `radv_ps5_queue_wait_seq`; the fly-over fps lines show 18-40 ms a frame blocked there.
- The front's real work (about 21%) is command decoding: FrontWrite, macro calls, CallMethod.

GPUBack in the fly-over: about 37% waiting (atomic wait for work in `GpuSplit::BackLoop` 20.6%, half of BackLoop's own 9.8% is its `pause` spin), about 64% working:

| Work | Share |
|---|---|
| Command decode / engines | 16.2% |
| Buffer cache (UsageTracker::Track memset 4.3, uniform compare 1.6, binds, WriteMemory, page sync) | 15.6% |
| GPU memory manager (GpuToCpuAddress, ReadBlock / WalkBlock memcpy) | 9.4% |
| Texture unswizzle / upload (9.8% after the cut) | 6.9% |
| Texture cache other | 3.9% |
| Pipeline config / lookup | 4.0% |
| Descriptors | 2.0% |
| Driver (recording, submit) | 1.5% |

Inclusive on GPUBack: GraphicsPipeline::ConfigureImpl 21%, BindHostStageBuffers 9.8%, JoinImages / InsertImage 9.2%, RefreshContents 8.5%, UploadImageContents 7.8%, NativeQmdScheduler::Signal 5.9%.

Guest cores 4 and 5: JIT code 58-59% in the fly-over (70-73% after the cut), idle or waiting 35% (19-23%), the emulator's own code about 7% (kernel locks and scheduler 2.6, clock 1.4, memory write hooks 0.8-1.3, system calls 0.3-0.4, compile and runtime 0.4-0.9). The guest cores are not the limit in the fly-over.

## Answers

- **Clock reads are not worth a time-stamp-counter port.** Outside wait loops they are under 1% on every thread (front 12.8% and back 5.2% are all inside polling loops; guest cores 1.4%, nearly all lock waiting).
- **Hot spots that are not game code:** the drain spin on the front (the biggest lever by far); `UnswizzleTexture` on GPUBack 6.1% (8.8% after the cut: a CPU texture decode on the back thread instead of the async decoder); the memset in `UsageTracker::Track` 4.3% of GPUBack (4.9% in the fly-over), which `EDEN_UP_FRITCHII_USAGE_TRACKER` (T101+) removes and which fits its one-run +0.9 fps.

## What to look at next

1. Cut front-to-back drains: extend the DMA snapshot to pages written by compute and copy, serve semaphore reads and GPU-written command lists without a full drain; then sample again and check that the front's 47% and the back's idle both fall.
2. `EDEN_UP_FRITCHII_USAGE_TRACKER=1`, three valid runs against a same-batch control; find which images go down the synchronous `UnswizzleTexture` path.
3. The front's fence wait in `ReadGpuWrittenCommandList` / `Nx2ReadListCopy` (19% in the fly-over): an event wait instead of clock_gettime + nanosleep polling in `radv_ps5_queue_wait_seq`.

Not sampled: the Vulkan workers and the radv submit thread. Only GPU was sampled in the house.
