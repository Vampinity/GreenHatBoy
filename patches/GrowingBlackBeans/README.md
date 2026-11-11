# GrowingBlackBeans core patches

For the Eglantine submodule, applied after Vampinity's T120 series (`tools/eglantine-patches` on `ocarina-dev-t120`), in number order. Everything is off unless its switch is set. Source branch: `gbb-t120` (local). Builds are the `gbb-t120-*` releases.

| Patch | Switch | What it does |
|---|---|---|
| 0901 | `EDEN_GBB_THREAD_PRIO_LOG` | Thread priority log, low priority for transcode workers |
| 0902 | | PS5 host thread priorities |
| 0903 | `EDEN_GBB_DUMP_GUEST` | Dump guest code (for disassembly; dumps stay local, never shared) |
| 0904 | `EDEN_GBB_HLE_MEMCPY` | Host memcpy for the guest's memcpy |
| 0907 | with `EDEN_NX2_OVERWRITE_CHECK` | Ahead reads by kind (graphics/compute uniform, upload) |
| 0909 | | Guest thread id per emulated core (sampler marker) |
| 0910 | `EDEN_GBB_THREADS`, `EDEN_GBB_THREAD_PRIO` | Guest thread creation/priority log, priority override |
| 0912 | with `EDEN_NX2_OVERWRITE_CHECK` | Upload ahead reads by binding |
| 0913 | `EDEN_GBB_SVC_PROFILE=<tids>` | Per guest thread: SVC time, outside-SVC ms per frame, waits and wakers |
| 0916 | `EDEN_GBB_DESTROY_UNMAP_ALL` | Port of Lichii #1199 |
| 0917 | `EDEN_GBB_COST` | Host time in GPU-page callbacks, buffer-cache lock, JIT memory callbacks, JIT compile, per thread |
| 0918 | with `EDEN_NX2_OVERWRITE_CHECK` | Ahead audit: stale texture, descriptor, handle and GPU-result reads per frame |
| 0919 | `EDEN_GBB_GUARD_EARLY` | Arms `EDEN_UP_AHEAD_GUARD` before the gpu_behind second wait (fixes stale reads during it) |
| 0920 | with `EDEN_NX2_OVERWRITE_CHECK` | Fence-download landing audit |
| 0921 | `EDEN_GBB_BACK_CALLS` | Split back thread time per ring entry kind, method and call thunk (TSC; low overhead) |

Dropped because T120 has them: 0899 (`EDEN_UP_SSBO_SIZE_CAP`), 0911 (`EDEN_UP_AHEAD_ALWAYS`), 0915 (NaN guard / invariant position), 0905/0906 (0482/0483). Parked: 0914 (our copy guard; superseded by `EDEN_UP_AHEAD_GUARD`).
