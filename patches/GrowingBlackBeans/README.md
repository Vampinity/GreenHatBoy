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
| 0921 | `EDEN_GBB_BACK_CALLS` | Split back thread time per ring entry kind, method and call thunk (TSC; low overhead). Built (t120-gbb4); ran on the console (V1, 12 Nov). |
| 0922 | `EDEN_GBB_VITALS`, `EDEN_GBB_TIMELINE=<start s>,<s>` | Per-second vitals line on one clock; per-event timeline file (presents, front waits, back batches, syncpoint increments, fence pops, shaders) read by `eglog/timeline.py`. Also changes `headless/gpu_time_probe.inc` (feeds host GPU time to vitals). Built (t120-gbb5); ran on the console (every run since 12 Nov). |
| 0923 | `EDEN_GBB_FLIGHT=<ms>[,<dumps>]` | Flight recorder (last 2 s before a slow frame), `EDEN_GBB_ENV` effective env line, touchpad + R3 marker (`headless/pad.cpp`). Built (t120-gbb6); ran on the console (F1, 12 Nov). |
| 0928 | `EDEN_GBB_FLASH=1\|2[,<threshold>,<min cells>]` | Flash counter: each presented frame shrunk on the GPU to a ~120x67 brightness grid (blit chain in the swapchain copy), read back late; one- and two-frame transients counted (all, and motion-proof); `=2` writes the grids to `logs/gbb-flash-<pid>.bin` for `eglog/flashes.py`. Built (t120-gbb9, 01.219.916); ran on the console (12 Nov). |
| 0924 | `EDEN_GBB_FRAMES_AHEAD2=1` | Two frames in flight: presents wait for the frame two back. An fps experiment; the guard covers one frame, so expect flashes. Built (t120-gbb7); **never run**. |
| 0932 | `EDEN_GBB_READ_SYNC_ESCAPE=<us>` | The read-sync give-up timer as a dial (0567's 2 ms when unset). Built (t134-gbb5, 01.219.921); run on the console (RE1/RE2). **Rejected:** +0.68 fps, inside noise, and the flicker came back at 250 us. The 2 ms is load-bearing, not a loose round number. |
| 0933 | `EDEN_GBB_READ_SYNC_REGIONS=<list>`, `_AUDIT=1` | Read sync only inside listed address regions, with an audit mode that syncs everything and counts changed reads falling outside the list. Built (t134-gbb6/gbb7, 01.219.922/923); run (GA1, GR1, GA3). **Rejected as a filter:** a 58% cut in synced reads moved nothing, and the hot set drifts between runs so a fixed list leaks. The audit mode is what proved both. |
| 0934 | `EDEN_GBB_GPFIFO=1` | Log only. What the game submits, counted at the GPFIFO boundary before macro expansion: entries, declared words and parsed headers per channel, every 10 s. Sits on `RecordParsedEntry` beside Vampinity's `EDEN_NX2_FETCH_COUNT`, which counts provenance rather than volume. Built (t134-gbb8, 01.219.924); **not run**. |

The headless (outer repo) side of 0922/0923 is `headless-0922-0923.diff` (pad.cpp, gpu_time_probe.inc).

Dropped because T120 has them: 0899 (`EDEN_UP_SSBO_SIZE_CAP`), 0911 (`EDEN_UP_AHEAD_ALWAYS`), 0915 (NaN guard / invariant position), 0905/0906 (0482/0483). Parked: 0914 (our copy guard; superseded by `EDEN_UP_AHEAD_GUARD`).
