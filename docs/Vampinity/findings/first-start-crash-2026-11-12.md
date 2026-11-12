# First-start crash, T130 cold run, 12 Nov 2026 (checked twice)

> **Found:** On a first start (T130, cold) the game got far behind while the graphics side built the first 3D scene's pipelines; the emulator let it run ahead, re-read command memory the game had already reused, and crashed on a junk draw (shape type 3734).
>
> **So:** The first-start black-screen crash is a stale command-list read, not a memory crash; the fix is to keep the clean submit copy of a list (became EDEN_UP_RESUME_KEEP_COPY in T133, with the TRUST_COPY + RESNAPSHOT=0 pair as the env-only way).

Run: `eglantine-logs-2026-11-05/auto-20261112-005003-batch-first-start.v2/run1233-fs-watch-cold`
(crash 00:54:25, 4 min 6 s after the game started). Warm pair: `run1234-fs-watch-warm`, read
to 504 s of its log at 01:04, still running, no crash. No other run folders existed yet.
One cold run: no verdict on how often this happens.

## Answer in one line

The game got far behind on a first start (graphics side building ~170 recipes for the first 3D
scene), the emulator let the game run ahead after three 4-second waits, then it re-read command
memory the game had already reused for later frames, parsed junk, and one junk "draw" carried a
shape type of 3734 (valid: 0-14), which read far outside a 15-entry table. Confidence: high on
the crash mechanism, medium-high on the run-ahead cause.

## What I checked myself

| Claim | Status | How |
|---|---|---|
| Crash function UpdateDepthBiasEnable | Confirmed | llvm-symbolizer on llvm-pie.elf.zst from the package, code size 0x2c5c750 matches the report |
| Faulting instruction `movl -0x20(%rbp,%rax,4)` = read of the small 3-entry stack table | Confirmed | disassembly 0x15c13f0-0x15c1480 |
| Fault address = stack + huge index (not a freed buffer, not "wild pointer") | Confirmed | 0x407dc3a50 + 0x17900000007 x 4 = 0x5e807dc3a6c exactly |
| Shape-type table has 15 entries | Confirmed | symbol size 0x78 = 15 x 8 bytes (entries are 8 bytes, not 4) |
| Shape type was 3734 | **New, near-certain** | log line 245.205 s "Unimplemented topology=3734"; the table entry at index 3734 in the ELF is exactly 0x17900000007 = rax |
| Stack chain DrawTexture <- Maxwell3D <- GpuSplit::Execute <- BackLoop <- thread start | Confirmed | the Scheduler::Flush/EndRenderPass words are leftovers, as the code read said |
| On screen: logo at ~204 s, then black with overlay "F-- S-- M--" (no new frames) | Confirmed | frames f0042 and f0047 |
| Three 4 s present misses (225.3, 235.3, 244.4 s), two 3 s hang-watch waits (226.0, 238.4 s) | Confirmed | eden_log |
| Game queued ~25 fence steps ahead of the GPU at the third miss (wanted 36515, at 36490) | Confirmed | eden_log 244.44 s |
| "Copy read again after submit" differing: 0 of 53,073 at 151 s, then 57 -> 221 of ~110,980 from 244.88 s | Confirmed | FETCH_COUNT totals |
| Resumed entries never differed (0 of 34,777) | Confirmed | same lines; only the re-read copies changed |
| Junk: unbound subchannel 7 at 244.877 s, puller methods 3, E-19, bad semaphore op, topology 3734 | Confirmed | eden_log tail |
| Warm run: same scene, one 4 s miss (237.1 s), 0 differing re-reads up to 10.59 million, no junk, no crash | Confirmed | run1234 eden_log to 504 s |
| Memory: not the direct cause | Agree | the only failed allocation is a junk-sized image; I did not recheck the timeline read's per-second free-memory figures |

## Corrections to the two first reads

- Timeline read: the bad address is not a wild pointer. It is the stack address plus a garbage
  index, and the index is now known (shape type 3734).
- Timeline read: 0x152dab2 is the thread start-up wrapper, 0x15297f0 is BackLoop.
- Code read: the exact shape type is not unknown; the log names 3734 and it matches the
  register exactly.
- Code read: the differing re-reads begin 0.43 s after the third miss and the crash comes about
  0.55 s after the first differing entry (not 1.4 s).
- Code read's "table of u32": the shape-type table holds 8-byte entries (the small lookup table
  on the stack holds 4-byte entries).
- The FETCH_COUNT "-N" lines are a backwards dump of recent entries printed when junk is found,
  not a stream that "starts" at 244.86 s.

## Where they disagreed

- **Workaround switch.** Code read: `EDEN_NX2_DESYNC_FIX=1`. Timeline read:
  `EDEN_NX2_RESNAPSHOT=0`. Notes (`frame-wait-research-for-gbb-2026-11-09.md`): a RESNAPSHOT=0 run
  deadlocked at the first load, and DESYNC_FIX froze in the one run where it acted (ledger pooled
  6/9 vs 2/4 survivals with the slip forced). So neither is proven safe. The source's own
  comment for `EDEN_GBB_TRUST_COPY=1` (use with `EDEN_NX2_RESNAPSHOT=0`) describes exactly this
  Ocarina failure (game a frame ahead rewrites the same ring, unbound subchannels, crash on
  GPUBack) and says Ocarina's submitted words never change before the parse (0 of 7,675,038).
  Verdict: TRUST_COPY + RESNAPSHOT=0 is the best-aimed existing pair, DESYNC_FIX second;
  RESNAPSHOT=0 alone is ruled out by the old deadlock.
- **Role of memory.** Code read: not a memory crash. Timeline read: memory near the floor
  lengthened the stall. Both can be true; the crash itself is not an out-of-memory failure.
  Cannot tell from one run how much memory adds to the stall length.
- **Same as the tester's 9.40 black screen?** Only the timeline read judged: a different moment
  (title / first movie, back thread stuck "inside a command", no junk). I agree: same family
  (cold-cache stall plus 4 s give-up), different end.

## Most likely cause (confidence)

1. Empty caches: at the first 3D scene after the opening, the graphics thread builds 173 recipes
   and translates 95 shaders, and a 6144x6144 texture takes 21.7 s to upload. Read from logs.
2. The present wait gives up after a fixed 4 s, three times; the game keeps queuing frames (25
   fence steps ahead). Read from logs; that this let the game reuse the command ring is inferred.
3. When the stalled channel resumes, the refresh re-copies queued lists from memory. Those copies
   now hold later-frame words (221 lists differ). Read from logs.
4. Parsing gets out of step, junk commands follow, a junk draw with shape type 3734 indexes the
   15-entry table with no range check and the read lands in unmapped memory. Read from logs and
   machine code.

Confidence: crash mechanism (steps 3-4) high; that the 4 s give-up plus run-ahead is the trigger
medium-high; why the back thread stalled 3 s twice on an unsubmitted tick low.

## Is this the crash players report?

Probably yes (medium). It hits on a first start only, right after the opening movie while the
screen is black before the first 3D scene, which a player sees as "crashed during/after the
intro". The warm second start of the same route survived. One cold run only.

## Best fix (code)

1. Root, in `video_core/dma_pusher.cpp` (refresh at resume, around line 695, and
   `RefreshSnapshot`): for Ocarina, on pages no GPU work wrote, never replace a submit copy with
   memory that differs; parse the submit copy (make the `EDEN_GBB_TRUST_COPY` behaviour the
   Ocarina default) and log the count.
2. Guard, in `vk_rasterizer.cpp:3878-3879` and `fixed_pipeline_state.cpp:413`: if the shape type
   is above 14, log once and use Triangles. Also reject out-of-range values where they are set
   (`draw_manager.cpp` lines 124-313, including the raw `topology_override` cast at 313). This
   alone turns the crash into junk drawing or a hang, so it is a safety net, not the fix.
3. In `nx2_gsv.h` WaitForFrame: keep waiting past 4 s while the graphics thread is still making
   progress (fence moved, pipeline build or upload in flight), hard cap ~30 s.
4. Later: move the remaining on-thread first-time pipeline builds and the big texture upload off
   the graphics thread to shorten the cold stall.

## Quick workaround in T130/T131 today

Untested on a cold start, so not yet safe to ship blind:
`EDEN_GBB_TRUST_COPY=1` with `EDEN_NX2_RESNAPSHOT=0` (keep `EDEN_NX2_DMA_SNAPSHOT=1`).
Second choice `EDEN_NX2_DESYNC_FIX=1`. Do not use `EDEN_NX2_RESNAPSHOT=0` alone. An alpha can ship
with the pair only after the cold test below shows no crash and no first-load hang.

## Next tests, in order

1. Cold first start, same route, same batch: control (as run1233) vs `EDEN_GBB_TRUST_COPY=1 +
   EDEN_NX2_RESNAPSHOT=0`, about 3 runs each. Read: crash, hang at first load, differing re-reads,
   unbound-subchannel lines, fence misses.
2. If that pair hangs: a third arm with `EDEN_NX2_DESYNC_FIX=1`.
3. Cheap repeat without clearing caches: warm run with the slip forced
   (`EDEN_NX2_DOWNLOAD_GUARDS=2`) and FETCH_COUNT, to see whether the same junk appears.
4. Offline: compare the words of entries 413/424 (1334 and 439 words differing) with later lists
   in the crash log to prove they are a later frame's commands.
5. Build with fixes 1 and 2, then cold A/B against T130; then fix 3.
6. Cold start with no save at all (like a new player), and the tester's 9.40 cold boot on T130.

## In plain words (written for the project owner)

The crash is reproduced: on a first start, right after the opening movie, while the screen is
black before the first 3D scene. With empty caches the emulator needs about 25 s to prepare that
scene, and after waiting 4 s three times it lets the game carry on, so the game writes its next
drawing instructions over ones the emulator had not read yet. The emulator then reads that mix
as nonsense, and one nonsense "shape type" (3734, where only 0-14 exist) makes it crash. A second
start on the same route, with caches filled, froze only briefly and kept going. There is an
existing switch pair aimed at exactly this (`EDEN_GBB_TRUST_COPY=1` with
`EDEN_NX2_RESNAPSHOT=0`), but it has not been tried on a first start yet, so it needs one cold
test batch before an alpha ships with it. One crash is no verdict, so the next batch repeats the
cold start with and without that pair.

Read: run1233 (crash files, eden_log, frames, video-check), run1234 eden_log to 504 s, T130
source (`dma_pusher.cpp`, `nx2_gsv.h`, `draw_manager.cpp`), notes on DESYNC_FIX and RESNAPSHOT.
Console not touched.
