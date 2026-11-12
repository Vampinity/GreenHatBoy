# First-start test, the second crash (std::bad_alloc on FS at the house door): checked (12 Nov 2026)

> **Found:** The second first-start crash (std::bad_alloc on the file-service thread a second after pressing A at the house door) is a refused allocation in the service reply wrapper, not inside IStorage::Read.
>
> **So:** A fix belongs in the reply path (became EDEN_UP_HLE_REPLY_BUFFER and EDEN_UP_HLE_OOM_RETRY in T134); the door crash is a memory-wall crash and needs memory freed or kept, not a parser fix.

Independent check of a first report on runs 1233-1236 (T130, defaults, base PS5 12.40, new game, opening
watched, no skipping). READ = seen in the logs, source or frames by the second check. INFERRED = reasoning.
Console not touched; no other file changed.

Runs:
- `auto-20261112-005003-batch-first-start.v2/run1233-fs-watch-cold`: crash on GPUBack at 246 s (see
  `first-start-crash-2026-11-12.md`).
- `.../run1234-fs-watch-warm`: crash `std::bad_alloc` on FS at 510 s.
- `auto-20261112-010615-batch-first-start.v2/run1235-fs-watch-cold`: froze at about 219 s, closed by the
  harness at 791 s, no crash file.
- `.../run1236-fs-watch-warm`: finished. Crash `std::bad_alloc` on FS at 498 s, same stack.

## Verdict on the report

Mostly right. Three points that matter are wrong, plus some smaller ones.

1. **The failing allocation is not inside IStorage::Read.** READ: `eboot+0x7636f0` is the first byte of
   `IStorage::Read` (llvm-nm: `00000000007636f0 t Service::FileSystem::IStorage::Read`). It is a
   function pointer left on the stack, not a caller. The real caller is `CmifReplyWrapImpl` (return address
   `0x7639e9`). Before it calls Read, it sizes a temporary output buffer to the game's buffer
   (`cmif_serialization.h:346-348`, `buffer.resize_destructive(ctx.GetWriteBufferSize(...))`). READ:
   `fs_i_storage.cpp` Read has no ScratchBuffer; it reads straight into `out_bytes.data()`. So the read had
   not started yet. The buffer is a fresh local (`OutTemporaryBuffers buffers{}`) on every request, and
   every HLE call with an output buffer does the same thing. The crash is in the request plumbing, not the
   file code.
2. **"About 1.2 GiB sat free in kept arenas" is from the wrong moment.** READ: heap.log
   `live_bytes=1090881791` is the snapshot at the first failure (the 144 MiB decode). At the fatal failure
   it is `live_bytes=1644056915 ... failures=2` (1,568 MiB). The heap held 2,304 MiB plus 173 MiB in large
   blocks, so about 0.9 GiB was free inside it (INFERRED arithmetic). Live use grew by about 530 MiB in
   the roughly 5 s between the two failures, so the door load itself was using up the heap's spare room.
   run1236 was the same: 1,459 MiB live of 2,240 + 125 MiB, about 0.9 GiB free. That room sits in
   scattered pieces: the request had already tried every space of every class
   (`eden_heap_main`, `passed_over` then `CLASS_ANY`) and found no 0.9 MiB piece.
3. **The 144 MiB decode failure is not part of the chain.** run1236 has no such failure. READ: its only
   `EDEN_HEAP_FAILURE` is the FS one (`requested=480902 reason=2 count=1`), and the 6144x6144 texture was
   queued again at 483 s with no error. Holding that decode back (the first report's fix 3) is not shown to matter.

Smaller corrections:
- run1234 timing. READ, frames: f0100 shows the house with "Saving...", f0102 shows the door with
  "(A) Open", f0103-f0104 are black, f0105 is the launcher's crash message. The test clock (490.2 s) runs
  about 17 s behind the log clock (INFERRED from the save Commit lines at 495-496 s). So the 144 MiB failure
  (log 504.7 s) came while the player walked to the door, before A was pressed. The fatal FS failure came
  1-3 s after the A presses, on the black load.
- "Five off-by-default crash fixes" is incomplete. T130 has eight fix switches (`t130-allfixes-menu`
  note): HEAP_STEAL, NEW_WAIT_MS, JIT_SITE_SHARDS, ASTC_SCAN_CHUNKS, PE_TRANSCODE_BOUND,
  PS5_TRANSCODE_PENDING_MIB, PREP_UNREAD_HANDLE and AREA_BUDGET. AREA_BUDGET (fewer texture deletions after
  a burst) is the one aimed at the texture churn behind the "memory hitches". It is not aimed at the FS
  crash, and its effect on memory at the door is untested. In the field all-fixes runs, HEAP_STEAL and
  NEW_WAIT **never fired**, so neither has any evidence on a real refusal yet.
- Stutter at 425 s: that window had 37 new pipelines and 1,031 ms of builds (READ), so the 2.3 s hitch
  there is not clearly a pure memory hitch. The other memory-hitch attributions stay INFERRED.
- run1235 "stall about 19 s, similar to run1233": the stall started at about 219 s (first 4 s give-up at
  223.1 s, READ) and **never ended**. Give-ups came for presents #11498, #11499 and #11500 at 223.1,
  232.5 and 241.9 s, and no present followed. The present count reached 11500 but present #11500 never
  completed. It is a freeze, not a stall of measurable length.

## What holds (re-read)

- Symbolised stack (llvm-pie.elf, code size 0x2c5c750 matches): `main::$_11` (terminate handler) <-
  `std::__terminate` <- `failed_throw`/`__cxa_throw` (no catch anywhere) <- `main::$_10` (the
  `set_new_handler` lambda, main.cpp:355-443, which prints EDEN_HEAP_FAILURE and throws) <- `__wrap_malloc`
  <- `ScratchBuffer<u8>::resize_destructive` <- `CmifReplyWrapImpl<..., IStorage, ...>` <-
  ServiceFrameworkBase::InvokeRequest/HandleSyncRequest <- SessionRequestManager <- ServerManager loop <-
  `Service::FileSystem::LoopProcess` (fsp-srv, the single file-service thread). run1236's stack is
  identical (diffed).
- Sizes: run1234 `requested=902912 reason=2 count=2`; run1236 `requested=480902 reason=2 count=1`. In
  the code, reason 2 is `EDEN_HEAP_WHY_NO_MEMORY` (heap_arenas.inc:791). Largest free block 2 MiB
  (1234) and 3 MiB (1236).
- run1234 last 30 s, READ: `Direct allocation failed` for 52 and 146 MiB, then `EDEN_HEAP_FAILURE
  requested=150994944` (the 6144x6144 texture; "No memory to decode ... tried again in 300 frames" at
  504.7 s). Swap reclaim for graphics then returned 29, 0, 9, 0, 39 and 0 MiB of 64 asked, and the
  texture cache logged "Out of device memory: keeping 3072 MiB more free" at 508.9 s. No EDEN_NEW_WAIT
  or steal lines appear: both switches were off (env.txt). EDEN_UP_HEAP_WAIT_MS=2000 covers only
  pipeline builders (heap_pages.cpp:52).
- Pool timeline, RADV available MiB, READ: 11,234 at boot, 5,134 from 90 to 225 s, 32 then 128 at
  235-236 s (driver 3,703 then 3,384 MiB), 219 MiB 246-347 s, 97 then 90 MiB 356-496 s, and 8 MiB at
  499 s (driver 3,722 MiB). run1236: 220 MiB to 483 s, then 29 MiB at 487 s (driver 3,512 MiB).
- run1236: a JIT "no memory for its next part" wait, "memory found after 180 ms", while the reserve
  went from 32 to 24 blocks, right before the failure. READ.
- Caches: run1234 boot reads 320 records (292 known); run1236 292; run1235 0. READ. Both warm runs were
  therefore cold for everything after the first scene. 0 on-disk hits after 250 s in run1234 (READ).
- run1235 junk, READ: `Read32 of unmapped GPU address 0x200120ad2113da9c` x17 from 238.3 s. At 240.3 s,
  channel 2 waits on that address. Channels 1, 3 and 5 wait on real semaphores (0x2113ed1000/48) that
  never advance (INFERRED: they wait on work stuck behind channel 2). At 238.2 s the copy re-read
  comparison showed 1 and then 2 differing of about 113,810. The harness ended the app at 791 s.

## Which existing switches act on this exact path (code read)

- **EDEN_UP_NEW_WAIT_MS** (main.cpp:368-406): yes. `operator new` calls the handler after each refusal.
  With the switch set, a request under 1 GiB (`LargestWaitedRequest`) sleeps 20 ms per step and trims
  the heap, up to the limit, and only then throws. The cost: fsp-srv is one thread, so while it waits
  every file read in the game waits too (up to 2 s). Also, the 144 MiB decode failure goes through
  operator new as well, so its thread would also wait up to 2 s before the decode code's catch (INFERRED
  side cost). Whether memory comes back in 2 s is unknown: at the brink, swap gave back 0-39 MiB.
- **EDEN_UP_HEAP_STEAL=2/3** (heap_arenas.inc:1101-1105, 1970-2002): yes. A request of 256 KiB or more
  goes to `eden_heap_main`, and when growth is refused and all spaces were tried, mode 2+ serves it
  from arenas no thread is on (the steal limit is 2 MiB - 64 KiB, so 0.9 MiB fits). Whether a fitting
  free piece existed here is unknown: no mode-1 counts were taken. Earlier sessions had 100+ empty idle
  arenas (INFERRED likely). Mode 3 also asks idle arenas first for 1 s after a pool refusal.
- Neither switch gives the **graphics driver** memory. It draws from the pool, and it was already being
  refused at the door ("still no memory"). If FS survives, the village load could fail on the graphics
  side next. Nothing in these runs shows what happens then (INFERRED risk).
- ASTC_SCAN_CHUNKS, PE_TRANSCODE_BOUND, TRANSCODE_PENDING_MIB, JIT_SITE_SHARDS, PREP_UNREAD_HANDLE: not on
  this path. AREA_BUDGET: not on this path; it may lower churn but keeps more textures, so its net effect
  at the door is unknown.
- `EDEN_GUEST_SWAP_AHEAD_MIB=auto` is already 12288 here, so no change. Neither the default env nor the
  fast file contains any of the eight fix switches.

## What one run cannot carry

- 2 of 2 warm runs crashed at the same door with the same stack. That makes it a pattern, not chance, but
  the exact request size differs (902,912 / 480,902), so the "victim" is whoever asks next. Another run
  could die on a different thread or survive.
- 2 of 2 cold runs failed at the first 3D load, one by crash and one by freeze. Which outcome comes is
  not predictable from two runs.
- Whether HEAP_STEAL or NEW_WAIT saves the door: zero runs. Whether a fresh app start then Continue gets
  through the door: not tested in this batch.

## In plain words (written for the project owner) (plain words)

Both first starts with empty caches died at the black screen right after the opening movie: one crashed,
the other froze for good, from the same fault (the emulator gives up waiting and then reads drawing
instructions the game has already overwritten). Both second starts got through the opening and the long
scene, which stutters because only the first scene was cached and memory sits almost full. Both then
crashed a second or two after you press A at the house door. The part that answers the game's file reads
asked for under 1 MB and got nothing. The emulator had about 0.9 GB free inside its own memory, but only
in small scattered pieces, and the next scene's loading was eating that room too. Start 3 is untested:
the long scene should stutter less because start 2 cached it, and the door will likely crash again. My
guess is that quitting after the "Saving..." in the house and continuing from that save gets past the
door, because a fresh load uses less memory, but tonight nobody tested that. Two switches already in
T130 aim at exactly this crash: one lends memory from idle stock, the other makes the request wait instead
of giving up. Neither has ever fired in a test, so next is a batch of warm runs with and without them.

Terms: cache = stored drawing work from earlier starts; pipeline = a ready-made drawing recipe; heap =
the emulator's own memory for small requests; swap = packing unused game memory away to make room.

## Best fix (code)

Stop the HLE request plumbing from needing new memory for every output buffer. For map-alias buffers
like IStorage::Read, read straight into the game's own memory. Otherwise keep one reusable buffer per
service thread that never shrinks. Then catch `std::bad_alloc` around `ServerManager::CompleteSyncRequest`,
trim the heap and retry once, and only then fail. The deeper cause is the pool sitting at the floor from
the first 3D scene on (graphics driver about 3-3.7 GiB, texture churn). That needs its own memory work and
is not fixed by this.

## Workaround today

- Settings (untested, never fired yet): `EDEN_UP_HEAP_STEAL=3` and `EDEN_UP_NEW_WAIT_MS=2000`, in the
  default env and the fast file.
- Player route (INFERRED, untested here): after control in the house, let "Saving..." finish, quit, start
  the app again, Continue, then open the door.

## Next tests, in order

1. Warm first-start route on a cache from a run that reached the house: 3 control runs against 3 runs with
   HEAP_STEAL=3 + NEW_WAIT_MS=2000, alternating. Read: door crash yes/no, EDEN_NEW_WAIT and steal 10 s
   lines, RADV "still no memory" after the door, largest free block. Add HEAP_STEAL mode-1 style counts if
   possible.
2. Restart-then-door: house save, fresh app start, Continue, open the door, 3 runs on defaults. This
   tests the player workaround.
3. Cold first start: 3 control runs against 3 with GBB_TRUST_COPY=1 + NX2_RESNAPSHOT=0. Read: crash or
   freeze at the first 3D load, differing re-reads, unmapped semaphore lines.
4. Start 3 on defaults (warm, then warm again) to measure the long-scene stutter on a full cache and see
   whether the door crash repeats.
5. Fast file + heap pair (+ AREA_BUDGET as its own arm later) from cold: what a newcomer would get from
   the best file.
6. A true no-save start, cold, on whatever passes 1 and 3.
