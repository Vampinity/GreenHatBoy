# Where the split back thread's time goes

GrowingBlackBeans, 11 Nov 2026. From the stack sampler with frame-pointer chains (`EDEN_SAMPLE_THREADS=GPUBack`) in run K1 (9 Nov, T83 build t83-gbb6, our walking route): 4 windows of 10 s, 8,000 samples, a frame-pointer chain on every sample. Symbols from that build's ELF. **T83, not T120**: T120 changed uploads and register shadows since, so treat the shares as a guide until B2 (`EDEN_GBB_BACK_CALLS`, patch 0921) measures T120.

## The split

- **Waiting** (polling or sleeping for work from the front): 29.3% of samples. That matches the split's own "back idle" figure of about 28-33% in heavy views.
- **Busy:** 70.7%, of which 96.5% is inside `GpuSplit::Execute`.

## Busy time, inclusive (a share can include the lines below it)

| Share of busy | What | Notes |
|---|---|---|
| 54.7% | `RasterizerVulkan::Draw` | everything a draw does |
| 36.6% | `GraphicsPipeline::MakeConfigureSpecFunc` (pipeline Configure) | inside Draw: binding resources for the draw |
| 16.9% | `BufferCache::BindHostStageBuffers` | inside Configure |
| 10.4% | `BindHostGraphicsUniformBuffer` | inside the above |
| 7.7% | `TextureCache::VisitImageView` | texture views per draw |
| 6.3% | `BindHostGraphicsStorageBuffers` | |
| **6.8%** | **`UsageTracker::Track`, from `Buffer::MarkUsage`** | **always on; Fritchii's run-fill version is behind `EDEN_UP_FRITCHII_USAGE_TRACKER=1` (off in our env)** |
| 11.1% | `KeplerCompute::CallMethod` (compute dispatches) | |
| 10.2% | `NativeQmdScheduler::Signal` | inside the compute work |
| 6.0% | `MemoryManager::FlushCaching` | |
| 5.3% | `RasterizerVulkan::InnerInvalidation` | applying guest CPU writes |
| 5.6% | `FenceManager::SignalFenceImpl` | |
| 4.5% | `QueryCacheBase::CounterReport` | 0.9 points of it in malloc |
| 4.4% | `BufferCache::WriteMemory` | |
| 3.7% | `Maxwell3D::CallMethod` | register writes |
| 3.7% | `MemoryTrackerBase::IteratePages` | |
| 2.4% | `Maxwell3D::ProcessDirtyRegisters` | |
| 2.4% / 0.7% | malloc / free | |
| 2.5% / 1.1% / 2.2% | mutex lock / unlock / spin mutex | |

The per-window self list shows `steady_clock::now`, `__emutls_get_address` and mutex unlock high. Those samples are in the **waiting** path (the back's poll-with-backoff loop), not in work, so they cost nothing.

## What this suggests (to confirm with B2 on T120)

1. **Per-draw resource binding is the bulk**: Configure at 37% of busy time, with buffer binds about 17% and texture views about 8% inside it. That fits the "cut the back's cost per draw" lever.
2. **Usage tracker, about 7%:** an env-only test (`EDEN_UP_FRITCHII_USAGE_TRACKER=1`). One collaborator run on a fly-over showed 19.4 fps against 18.2-18.65 in 19 runs without it.
3. **Compute dispatches, about 11%**, with most of it in the native QMD scheduler's Signal.
4. **Register writes:** smaller here (Maxwell3D::CallMethod 3.7% plus dirty processing 2.4%). Our P5 profile (with the profiler on) counted 1.74M 3D register writes a second, 824k of them same-value.

## Ports found in other forks that T120 doesn't have

- **zortos293/Lichii #1095, "engines: write 3D state registers in one call"** (73a1b58e7d): the back writes about 5M 3D registers a second in Ocarina, about half of them state registers; each took three out-of-line calls. It writes them in place instead. Our core has no `CallMethodFast` path, so this needs adapting, not cherry-picking.
- **zortos293/Lichii #1332** (752328bf38, from SerkiGohan): puts GpuSplit's front-side and back-side fields on separate cache lines. Small; could make the ~600 front/back handshakes a frame cheaper. The same commit's MKW frame-pacing change doesn't apply.
- Fritchii #70 (drain draw-written command pages only after a write) and #59 (front-side buffer flushes on the back) are Bananza- and crash-driven; worth a look only if our list-writer waits matter.
