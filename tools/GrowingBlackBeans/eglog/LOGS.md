# EglantinePS5 log lines: what they mean

A field guide for people and agents reading Ocarina of Time runs. Each entry: the line, the switch that turns it on, what it measures, units, what it costs, and how it has misled us before. `eglog.py families RUN` lists which of these a run has.

Where things are: `eden_log.txt` (everything below unless noted), `stderr.log` (GPU time, heap and memory census, JIT memory), `logs/boot-trace.txt` (build, firmware, startup), sampler `.bin` files (need the build's ELF to read).

## Definitions used by every tool

- **Play window:** a 5 s window under 45 fps with at least 40 frames and no frame of 500 ms or more. Over 45 fps is menus or the intro (vblank-paced at 60).
- **Regime**, by the present's fence wait per frame and the back's idle time:
  - **light:** wait under 1 ms and the back idle 20% or more. The game's own CPU sets the pace.
  - **queued:** wait under 1 ms but the back over 80% busy. The GPU side throttles the game through the command queue without a present wait; seen at heavy stands. "No wait" does not always mean CPU-bound.
  - **mid:** wait 1-5 ms.
  - **heavy:** wait 5 ms or more. The GPU side sets the pace.
- **Phase** (hand-played routes): the door is the first window after 35 s with a frame of 300 ms or more. Standing runs from 10 to 60 s after the door, walking from 70 s after it.
- **Era:**
  - **full-wait:** `EDEN_NX2_FRAMES_AHEAD` is not 1, or standing fence wait is over 15 ms (our runs before 9 Nov);
  - **ahead-1:** frame-ahead.

  Never pool the two eras.
- **Back busy:** 1000 minus "back idle" from the split line (one line per 10 s; a window takes the line covering its midpoint), divided by fps. No profiler needed.
- **Never regress frame time on work per frame.** Both are divided by fps, so they correlate by construction. Use per-second rates or the fence-wait model: wait ≈ 0.89 × back busy/frame + 0.60 × host GPU/frame − 31 ms.

## Frame rate and pacing

**`nx2:vi2 5 s: N frames, F fps, mean M ms, 1% low L ms, worst W ms, fence X ms`**
- Switch: always on.
- What: one line per 5 s of presents. `fence` is how long each present waited for the previous frame's GPU work, in ms per frame.
- Cost: none.
- Pitfalls: the first windows after a scene cut include the load. Fps differs by about ±1 between runs of the same setup; use two or more runs per side (`abcompare.py`).

**`nx2:vi2 present #N fence (id, value) now V, waited U us`**
- Every 600 presents. A spot check of a single present's wait.

## The GPU thread (split front/back)

**`GPU split per second: back idle B ms, R ring words, front waited W ms, <site> ms (n/s, longest ms), ...`**
- Switch: `EDEN_NX2_SPLIT_WAITS=1`. Logged every 10 s.
- What it measures:
  - back idle: the back waiting for work from the front;
  - ring words: the volume of GPU-thread work;
  - front waited: the front waiting for the back to catch up ("drains"), broken down by site.
- Sites:
  - `dma snapshot miss`: a macro reads memory that no DMA snapshot covers;
  - `list writers`: a command-list entry waits for earlier dispatches and copies;
  - `acquire check`, `acquire recheck`, `acquire poll`: semaphore acquire reads;
  - `macro dma read`: macro DMA reads, only without the snapshot;
  - `map`: GPU memory maps.
- Cost: small.
- Pitfalls:
  - Drains are short, 10-120 µs, and there are hundreds per frame. Cutting one site moved the wait to the next site (run 33), and cutting several at once starved the back (G2).
  - A heavy frame is about back busy plus 12 ms that isn't overlapped.

**`GPU thread per second: | zone ms (n/s) | ...` and `GPU back thread per second: ...`**
- Switch: `EDEN_NX2_GPU_PROFILE=1`.
- What: exclusive time per zone on the front and on the back.
- Cost: **about 20% fps**. It reads the clock around about 150k zones a second.
- Pitfalls: it inflates the back's per-draw zones. P5 made the back look saturated when it is really about 30% idle. Use it for proportions only, never for absolute ms, and never compare its fps with other runs.

**`EDEN_GBB_BACK 5 s (ms per s): busy, waiting, idle hook; kinds; anchor`**, plus `EDEN_GBB_BACK calls` and `EDEN_GBB_BACK methods`
- Switch: `EDEN_GBB_BACK_CALLS=1` (patch 0921).
- What: the back's time per ring-entry kind, per method (by engine, inclusive) and per call thunk. Thunk addresses are offsets from `GbbBackCalls::Anchor`; resolve them with `nm` on that build's ELF.
- Cost: one TSC read per ring entry; expected under 2%, not yet measured on the console.

**`Graphics pipeline built on the GPU thread in X ms: <on disk, not built at boot | mesh, not in the disk cache | ...>`**
- Switch: always on.
- What: a shader pipeline built while playing, which stalls the frame.
- Pitfalls: about two thirds of all frames of 100 ms or more in play coincide with these. Boot preparation (`PrepareKept` lines) never converges: each run hits mostly new hashes.

**`Shader preparation: N pipelines known, M left to prepare ...`** (`PrepareKept`)
- Switch: `EDEN_UP_SHADER_PREP=1`.
- What: the boot-time pipeline preparation.

## Vitals and timeline (patches 0922/0923)

**`EDEN_GBB_VITALS t_ms= frames= fps= frame_p50_ms= frame_p99_ms= frame_max_ms= present_wait_ms= back_busy_ms_s= front_wait_ms_s= front_waits_s= ring_kwords_s= gpu_busy_ms_s= gpu_subs_s= shaders= shader_ms= fence_pops_s=`**
- Switch: `EDEN_GBB_VITALS=1`. One line per second from the present thread, all on one clock. `gpu_busy` needs `EDEN_GPU_TIME=1`; the front waits need `EDEN_NX2_SPLIT_WAITS=1`.
- Use: per-second rates (never divide by fps to get "per frame" and then regress against fps). `eglog.py` joins them to windows and regimes (`summary()["vitals"]`).
- Cost: relaxed atomic adds at existing hooks; one clock read per back batch and per fence pop. Expected under 1%, to be measured.

**`EDEN_GBB_TIMELINE: N events (D dropped) from S s for L s written to /data/eglantineps5/logs/gbb-timeline-<pid>.bin`**
- Switch: `EDEN_GBB_TIMELINE=<start s>,<seconds>` (seconds up to 60), counted from the first present.
- What: every present (begin, after its waits, end), every front wait on the back (site, start, end), every back batch (start, end, ring words), guest syncpoint increments, fence pops and shader builds, in a 1M-event ring. Copy the `.bin` with the logs; read it with `timeline.py` (per-frame table, Perfetto trace).
- Cost: during the window, one clock read and a 24-byte store per event; the file write at the end makes one hitch. Keep the window inside a stretch you aren't measuring fps on, or accept one slow frame.

## Host GPU

**`EDEN_GPU_TIME wall_ms busy_ms submissions max_ms ...`** (in stderr; eglog aligns at the session end, or one window earlier when GPU busy against fps fits better)
- Switch: `EDEN_GPU_TIME=1`.
- What: host GPU busy time per ~5 s, covering upload and graphics submissions.
- Pitfalls: the lines have **no timestamps**. Tools align them to the eden 5 s windows by the end of the session. Treat a single window as approximate and a regime average as reliable.

## Game threads (guest)

**`EDEN_GBB_SVCPROF t<id> T ms, F frames (ms/frame): in svc S ms (/frame), outside O ms (/frame); top SVCs | waits at ... | wakers`**
- Switch: `EDEN_GBB_SVC_PROFILE=<tid,...>` (patch 0913).
- What: per guest thread, time inside kernel calls versus running game code, per frame; the addresses it waits on; who wakes it.
- Threads: main t86; pool A t152-156; pool B t157-162; zstd streaming t101; name lookup t177 (low priority, about 700 ms/s in the background).
- Pitfalls: "outside SVC" includes JIT and emulator callbacks.

**`EDEN_GBB_COST t<id> ms per frame: write cb, write lock, read cb, mem cb, jit compile`**
- Switch: `EDEN_GBB_COST=1` (patch 0917), with SVC_PROFILE.
- What: host time in GPU-page callbacks and JIT memory callbacks.

**`guest threads t=Ns processes=1` + `Application tid=.. core=.. state=.. pc=..`** (core.cpp)
- Watchdog snapshots of every guest thread: where each was at that moment.

## Frame-ahead, guard and stale data

**`EDEN_UP_AHEAD_GUARD: last 300 presents: armed N (M while one was still armed), pages, ...`** and **`EDEN_UP_AHEAD_GUARD copies: C pages copied before a write (.. a guard, most P of 2048), the pool was full F times; ... of N pages first read with a guard up, U were not in it`**
- Switch: `EDEN_UP_AHEAD_GUARD=2|3`.
- What: the copy guard's work.
- Pitfalls: "not in it" counts guess misses, which are not necessarily stale reads.

**`OverwriteCheck present #N wall MS: ahead writes, ahead reads (by kind); early writes`**, plus `OverwriteCheck 5 s` and `... by binding`
- Switch: `EDEN_NX2_OVERWRITE_CHECK=1` (patches 0907/0912 add kinds and bindings).
- What: buffer reads of bytes written after the frame was presented. "Early writes" are CPU writes over GPU results whose download hasn't landed yet.

**`GbbAheadAudit present #N wall MS [behind]: tex, desc, handle, cpu reads ...`** and **`GbbAheadAudit 5 s`**, plus `landings` lines
- Switch: `OVERWRITE_CHECK` with patches 0918/0920.
- What: stale texture, descriptor and handle reads; frames that ran ahead with the GPU behind; fence downloads that changed guest bytes.
- Cost: the landing compare is expensive (it reads every downloaded byte).
- Pitfalls: "cpu reads in flight" counts all trapped reads of GPU-written memory, including ones answered from earlier downloads; it is not a stale-read count.

**`ReadbackWait 5 s: increments, held, ...`**
- Switch: `EDEN_NX2_READBACK_WAIT=1|2|3`.
- What: guest syncpoint increments held until downloads land.
- Pitfalls: mode 1 doesn't hold semaphore releases, about 15-21k per 5 s during downloads.

## Memory and streaming

- **`Texture cache last 600 frames: created N images, deleted M (...)`** and **`... N uploads from guest memory, M MiB`**: texture churn. Walking: about 2,000+ images and 1.3-1.5 GB uploaded per 600 frames; standing: almost none.
- **`Live switches: phase N 'label' ended after S s: F frames ... = X fps ...`**: in-run A/B phases (`EDEN_UP_LIVE_SWITCHES`). The most precise A/B instrument: A/A noise about ±0.5 fps. Compare with `abcompare.py --live`.

- **`VMA heap 1: usage U MiB of budget B MiB, VMA blocks`**: GPU memory.
- **`Memory margins: base, out of memory, block slack`**: texture cache headroom.
- **`Buffer cache: N buffers M MiB`**.
- **`Native zstd: calls, MiB decompressed on the host in ms`**: needs `EDEN_UP_OOT_NATIVE_ZSTD`.
- **`OoT resource poll backoff: walks in 10 s, avg walk us, slept`**: needs `EDEN_UP_OOT_POLL_BACKOFF`.
- In stderr: **`EDEN_HEAP_SITE`**, **`EDEN_AREA_EVICT frame N: images`**, **`EDEN_JIT_MEMORY`**, **`RADV_PSN_MEMORY`**, all from Vampinity's memory work.

## Build and session

- **`logs/boot-trace.txt`:** `diagnostic build <version> (<build time>), firmware sdk_version 0x..., pid N`. The pid ties sampler files to the session.
- **`EDEN_GBB: position invariant on, colour NaN guard on`**: the AMD fixes are active.
- **Menu settings** (Faster CPU emulation and others) are **not logged**. Write them in the run notes.

## Known blind spots (what no log tells us yet)

1. Per-frame order of events across the game, the front, the back, the host GPU and fences. This is the open question in the heavy views.
2. Where in the game the player is (scene or room).
3. When the player saw a flash; there is no marker button.
4. Menu settings and the effective env with defaults.
5. GPU time with timestamps.
6. Several switches leave no trace in the log (`EDEN_GBB_GUARD_EARLY`, `EDEN_UP_AHEAD_ALWAYS`, `EDEN_GBB_TRUST_COPY`), so `checkrun.py` can't verify them.
