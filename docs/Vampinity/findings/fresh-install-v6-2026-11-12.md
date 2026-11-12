# Fresh install, cycle v6: six new-game starts on empty caches (T134, 12 Nov 2026, 07:32-08:30)

> **Found:** Six new-game starts on empty caches (T134): the switch pair got 6 of 6 past the black screen, but only 1 of 6 reached the village; the other deaths came at requests no current fix guards.
>
> **So:** A newcomer on a fresh install still needs about 3 starts; the next work is memory at the house door (the heap burst), not the black screen.

Read-only check, 12 Nov 08:35-10:00. I touched no console, started no test, posted nothing and changed no
file except this note. READ means I saw it in a log, a frame or source. INFERRED means it is my reasoning.

## Answer first

- **1 of 6 starts got through.** G1 start 3 reached the village, played the arrival scene and stood 30 s outside
  until the script ended (end line `script_end line=126`, `script_done`).
- **The black screen is solved with the switch pair: 6 of 6 got past it** (2 of 2 true first starts), with 0
  junk lines in all six.
- **The G2 fixes did not save anything.** 3 of the 8 acted for sure, a 4th (GUEST_WRITE_WAIT) very likely did.
  2 of the 3 deaths happened at a request no fix guards. The first-start death (G2-1) was most likely a
  game-memory wait that GUEST_WRITE_WAIT guards: it waited its full 10 s (the picture froze ~10 s) and still
  found no memory, so it crashed anyway (INFERRED, see second-check section).
- **A newcomer today needs at least 3 starts.** Start 1 dies in the house, start 2 dies 1 s after opening the
  door, and start 3 is a coin flip. "Just start it again" gets them further each time, but no start is reliably
  through.

| Start | Valid | Past black screen | Got to | Ended | Victim (thread, request) | Pool free at end | Heap at end (pieces / live) |
|---|---|---|---|---|---|---|---|
| G1-1 cold | yes | yes | house, ~10 s after control | crash 513 s | game CPU thread: a write to game memory, refused | 0 MiB | 2,816 / 844 MiB (1,360 MiB empty pages) |
| G1-2 | yes | yes | door, opened | crash 455 s, ~1 s after A | file-service thread: 744,576-byte reply buffer | 3 MiB | 1,824 / 1,495 MiB (was 1,216 / 809 2 s before) |
| G1-3 | yes | yes | **village, arrival, 30 s outside** | **script ended**, closed normally | none | 28 MiB | 1,600 / 812 MiB |
| G2-1 cold | yes | yes | house, door prompt never came | crash 524 s, picture frozen ~10 s before | graphics back thread: a read of game memory that found no block (most likely after a 10 s wait); the driver had been refused memory ~10-15 s earlier | 1 MiB | 2,880 / ~850 MiB (1,406 MiB empty pages) |
| G2-2 | yes | yes | door, opened | crash 457 s, ~1 s after A | file-service thread: 613,465 bytes **inside the file read** (not the reply buffer) | 3 MiB | 1,920 / 1,517-1,607 MiB (was 1,760 / 819 2 s before) |
| G2-3 | yes | yes | out of the door, onto the porch; froze on the first shot of the arrival scene | picture froze ~5 s after A; crash 485 s (abort) | game CPU thread: the guest page tables could not get 2 MiB | 2 MiB (for the last ~25 s) | 1,952 / 1,638 MiB |

Terms, one line each:
- **Pool**: the console memory everything draws from.
- **Heap**: the emulator's own store for its C++ objects. "Pieces" is what it has taken from the pool, "live" is
  what is really in use, and "empty pages" are taken but hold nothing.
- **Pipeline**: a drawing recipe the graphics driver must build. "New" means built from scratch. "From disk"
  means rebuilt from a record a previous start saved, which is cheaper.
- **Black screen**: the ~25-30 s near-frozen picture at the first 3D scene after the opening movies.

## Validity (all 6 valid, READ)

- Build: `eboot.json` in both batch folders says sha256 `7f14d75d16b8fd02…f1a7` = T134. The runner's
  `install-t134.v6.sh --check-only` said "T134 is installed" before each group and at verify.
- Env: each run's `env.txt` equals its plan line for line (G1 80 lines, G2 88), plus only `EDEN_TEST_BOOT` and
  `EDEN_TEST_SCRIPT`. Each batch's `plan.json` is identical to the draft plan.
- Caches: the cold proof said COLD for run1271 and run1274. Starts 2 and 3 were WARM: 1090 then 1113 pipelines
  on disk in G1, and 1072 then 1123 in G2.
- Config: matches a fresh install (config-check.v2.py, all 6). The runner ended with `THIRD PASS DONE` at
  08:31:36, and the owner's caches, settings and save are back and checked.

## Per start (app-log clock; script marks moved by each run's script_offset_s from runs.jsonl)

**G1-1, run1271 (cold).**
- Black screen: 3 give-ups (225, 234, 243 s), 0 fps from 234 to 249 s, then 20-26 fps. 0 junk lines.
- House: control at app ~503.5 s (wait 108). Frame f0102 shows the player in the house facing the door with the
  Move/Change View hint up. The door prompt was never seen.
- End: crash at 513.2 s, ~10 s after control, before the door. SIGSEGV on CPUCore_5. rip is in the JIT code
  area (0x1210e00000, 256 MiB), so it was translated game code. The fault address 0x81bb200000 lies in game
  memory (va 0x8000000000, +6.9 GiB). Trap error 0x7 means a write to a protected page.
- Memory: pool 0 MiB, guest reserve 0, 9 image refusals from 511 s. INFERRED: the same death as run1239, a game
  write that needed a 2 MiB block and got none.
- Pipelines in the last 60 s: at least 74 new, 0 from disk, 2 mesh (from the 10 s sums; per-pipeline lines stop
  after ~350 on a cold run).

**G1-2, run1272.**
- Black screen: 0 give-ups, one 5 s window at 19 fps.
- Door: control at 441.2 s, "(A) Open" at 452.8 s, first A at ~453.2 s. Frame f0091 shows A Open at the door,
  then black.
- End: `std::bad_alloc` on FS at 454.3 s, `EDEN_HEAP_FAILURE requested=744576 reason=2` (2 = the pool said no).
  Symbolized on T134's llvm-pie.elf: `ScratchBuffer::resize_destructive` ← `CmifReplyWrapImpl<IStorage…>` ←
  `IStorage::Read`. That is the reply buffer for a file read, the case hle-oom was written for.
- Memory: RADV available 757 → 328 → 96 MiB over t 442-449. The heap went from 1,216 pieces / 809 live to
  1,824 / 1,495 in the last ~2 s, with the GPU thread "stale 2313 ms".
- Pipelines in the last 60 s: 15 new, 76 from disk, 9 mesh. 13 of the new ones came in A-5 to A+15 s, almost all
  at 452.3-453.9 s.

**G1-3, run1273: got through.**
- Door: control at 443.1 s, A Open at 454.3 s, A at ~454.7 s.
- Village: frames f0098-f0100 show the greeting scene on arrival in the village. f0104 shows control again on the
  porch above the village.
- End: `script_end line=126 at=503.642`, `script_done`, then the app's normal close. The batch log says "Script
  done after 523 s". No crash file.
- Memory: tight. RADV 6 MiB free at t 464 (driver 3,979 MiB) and 3 MiB at t 502, but it recovered each time.
  Second check: the census shows the pool's largest free block at 3, 0 and 2 MiB at three points around the door,
  and the driver was refused memory 14 times in this run ("still no memory", 0.9-15.3 MiB) without dying.
  Driver refusals alone are survivable. The
  heap stayed at 1,312-1,600 pieces with **live flat at ~805-825 MiB through the door**.
- Pipelines in the last 60 s: 25 new, 0 from disk, 3 mesh. At the door (A-5 to A+15 s): 18 new, 8 from disk,
  5 mesh, mostly 8-12 s after A (the arrival).

**G2-1, run1274 (cold).**
- Black screen: FRAME_WAIT_PROGRESS kept 2 present waits going (they reached the fence after 17.6 s and 6.4 s)
  where G1-1 had 3 give-ups. The stall was about as long: 0 fps at 243-249 s, then 20-26 fps. 0 junk lines.
- House: control at 504.6 s. The door look was skipped at 519.1 s and the A Open wait timed out at 522.1 s.
  Frame f0104 shows the house with the overlay reading "F-- S-- N--" (no frames).
- Picture: present #16685 waited from ~513.5 s and the wait ended "no progress" after 8.6 s.
- End: SIGSEGV on GPUBack at 524.0 s, reading 0x832d05f600, which is in game memory (+12.7 GiB). Trap error 0x4
  means a read of a page that is not there.
- Memory, before: `radv/ps5: no memory for …: still no memory` 63 times (20 of them 14,660 KiB, the rest
  1,408 / 14,336 / 16,384 KiB), `CreateBuffer VkResult=-2` x6, pool 1 MiB, guest reserve 0, JIT-lend reserve 0
  blocks. These came in the census window t_s 484-488 (stderr clock), i.e. around control, roughly 10-15 s
  before the crash, not in its last second (second check, READ).
- Second check: the crash itself is a read (trap error 0x4, page not there) of game memory by a copy on GPUBack
  (rsi = 0x832d05f600, the source). Every fault on game memory, read or write, goes first to the game-memory
  handler (fastmem_handler.cpp:48-51 → HandleGuestWriteFault → WaitForBlock), which with G2's
  GUEST_WRITE_WAIT_MS=10000 waits up to 10 s for a block. The video shows the picture frozen from 512.0 to
  522.0 s (video clock), then black: a 10 s stall right before the crash. INFERRED: the copy hit a swapped-out
  slot of game memory, waited the full 10 s while the heap sat on 1.4 GiB of empty pages, and was refused.
- Pipelines in the last 60 s: at least 72 new, 0 from disk, 3 mesh.

**G2-2, run1275.**
- Door: control at 441.8 s, A Open at 453.5 s, A at ~453.9 s. Frame f0091 shows A Open, then black.
- End: `std::bad_alloc` on FS at 455.0 s, `requested=613465 reason=2`. Symbolized stack:
  `NupLazyVfsFile::Read` ← `ConcatenatedVfsFile::Read` ← `IStorage::Read` ← `CmifReplyWrapImpl<IStorage…>`.
  The reply buffer is no longer in it (see question 2).
- Memory: pool 163 MiB before the door (G1-2 had 757). The heap had 594 MiB of empty pages. At the failure the
  heap was 1,920 pieces / 1,517 live, with only 68 MiB of empty pages left (574 two seconds earlier) and the GPU
  thread "stale 2310 ms".
- Pipelines in the last 60 s: 18 new, 69 from disk, 7 mesh (14 new in A-5 to A+15 s).

**G2-3, run1276.**
- Door: control at 443.3 s, A Open at 454.4 s, A at ~454.8 s.
- Porch: frame f0092 shows the player walking out of the door. f0093-f0097 are the same frame on the porch above
  the village (overlay F14), with the picture frozen from ~459 s. Second check: that frozen frame is not the player
  walking; it is the camera on the porch at the start of the arrival scene (the scene G1-3 played in
  f0098-f0100). The video shows a 24.7 s freeze (458.0-482.7 s video clock), then black.
- Freeze: `Hang watch: waited 3 s for GPU tick 280666; … last submitted 280664` at 463.6 s. Then present
  #17051 waited 8.2 s and ended "no progress".
- End: `EDEN_SPARSE_TABLES commit failed: out of memory` (a 2 MiB slot of game-memory page tables), then SIGABRT
  on CPUCore_3 at 479.4 s app clock (result.json: 485 s).
- Memory: the census shows the pool at 2 MiB from ~2-4 s after A to the end, with guest reserve 0 and JIT-lend
  reserve 0 blocks. The heap went from 1,408 pieces / 817 live to 1,920 / 1,604 in ~4 s.
- Pipelines in the last 60 s: 4 new, 95 from disk, 10 mesh. At the door: 1 new, 6 from disk, 6 mesh.
- The card's label "JIT / CPU core crash" is wrong. This is an out-of-memory abort.

## Did each G2 fix act? (line names from T134 source, then grepped in each G2 run)

| Switch | Line it prints | G2-1 | G2-2 | G2-3 |
|---|---|---|---|---|
| HLE_REPLY_BUFFER=1 | `EDEN_UP_HLE_REPLY_BUFFER acts…` + 10 s line | **acted**: 226,450 allocations saved, 9 allocated, held 892 KiB, largest request 12.9 MB (1 over the 4 MiB cap) | **acted**: 218,747 saved | **acted**: 227,055 saved |
| HLE_OOM_RETRY=1 | `caught= served= failed=` in the same 10 s line | line with 0 (caught=0) | line with 0: the refusal was not in a set-up | line with 0 |
| DECODE_KEPT_LEVELS=2 | `EDEN_UP_DECODE_KEPT_LEVELS first/…` + 10 s line | **acted** at 222 s on the two 1365x1365x90 texture arrays (peak 321 MiB less held); 0 after | same, 2 decodes at 220.8 s | same, at 222.2 s |
| GUEST_WRITE_WAIT_MS=10000 | start line goes to stdout = **heap.log**; wait lines to the kernel log; `EDEN_GUEST_WAITS` only with POOL_WALK=1 | start line in heap.log (second check); **very likely acted**: ~10 s freeze right before the GPUBack crash (INFERRED) | start line in heap.log; waits not visible | start line in heap.log; waits not visible |
| HEAP_STEAL=3 | mode line at start; counter line every 10 s **only when a count changed** | mode line only, no counter line | mode line only | mode line only |
| JIT_LEND_UNDER_FLOOR=2 | 10 s line `… asked, … lent` | line with 0: 0 asked, 0 lent; reserve fell 128 → 0 blocks | line with 0 | line with 0 (reserve 0 blocks at the end) |
| DRAW_ENUM_GUARD=2 | 10 s line | line with 0: 0 out of range in 5.35 M draws | line with 0 (5.7 M draws) | line with 0 (6.0 M draws) |
| FRAME_WAIT_PROGRESS=30 | `WaitPastDeadline…` + 10 s line | **acted**: 2 waits at the black screen reached the fence; 1 at the end ended by no progress | line with 0 | **acted** once at the end (8.2 s, no progress) |

HEAP_STEAL "no counter line" means no count changed in any finished 10 s window (INFERRED from
`ReportHeapSteal`, performance.cpp:1043-1050). The last ~2 s before each death are never reported.

## (1) Is the first-start black screen solved? Yes, with the pair: 6 of 6

- All six reached control in the house (wait 108 met). READ.
- The two true first starts stalled ~25 s at the first 3D scene and then played on, with 0 junk lines (unbound
  subchannel, topology, Read32 of unmapped: all 0).
- With v5's run1239 that makes 3 of 3 cold starts with the pair, against 0 of 3 default cold runs in v5
  (run1233, run1235, run1237). (second check: run1240 was a warm start, not cold; the earlier "4 of 4 / 0 of 4" was
  wrong.)
- FRAME_WAIT_PROGRESS turned G2-1's give-ups into waits that finished, but the picture stood still just as long.
  It changes the log, not what a player sees.
- The shipped env.txt (rel-0.4-t120) does **not** carry the pair. A newcomer on the shipped file is still in the
  0-of-3 world. This cycle does not test that.

## (2) Why the G2 fixes did not prevent the crashes

**Two of the three deaths were at a request no fix guards; the third (start 1) most likely was guarded and the
guard lost.** Two fixes did their own job well; the memory was gone anyway.

- **Start 1 (graphics back thread).** Correction from the second check: the driver was refused memory ~10-15 s earlier
  (63 refusals, 6 buffer creations failed; G1-1 had 64), but the crash is a read of game memory by GPUBack. That fault
  goes through the game-memory wait that GUEST_WRITE_WAIT_MS=10000 sets, and the picture froze for ~10 s right
  before the crash. INFERRED: the wait ran its full 10 s and found no block, because nothing gave memory back
  (the heap held 1,406-1,416 MiB of empty pages, 980 MiB of them idle arenas, through the whole wait). So the
  longer wait turned a quick crash into a 10 s freeze plus the same crash. JIT_LEND covers code pieces only and
  was never asked.
- **Start 2 (file service, same address as G1-2).** The same eboot+0xb86d5 does not mean the same allocation.
  0xb86d5 is `main::$_11`, the **terminate handler** (main.cpp:445). The new handler `$_10` throws and
  `__cxa_throw` ends there. **Every** uncaught bad_alloc on any thread exits through that address. The frames
  below it differ:
  - G1-2 (fix off): `ScratchBuffer::resize_destructive` in the reply wrapper, i.e. the reply buffer (744,576 B).
  - G2-2 (fix on): `NupLazyVfsFile::Read` under `IStorage::Read`. The reply buffer was kept and reused (218,747
    allocations saved, largest 12.9 MB already held), so the wrapper asked for nothing. The read itself then
    allocated. With `EDEN_UP_NUP_LAZY_DECODE=1` (shipped), a packed game file of 613,465 bytes is decoded into
    a new buffer of its full size: `member.data = std::make_unique_for_overwrite<u8[]>(uncompressed_size)`,
    nup_container.cpp:665. Files up to half the 64 MiB NUP cache are decoded in memory; larger ones go to a temp
    file. 613,465 is not a buffer size the game picks; it is a file size.
  - Why neither fix covers it: REPLY_BUFFER only replaces the wrapper's output buffers. OOM_RETRY wraps only
    `HleReply::Prepare`, the set-up before the service's code runs. That is a deliberate choice (NOTES section 3:
    "Anything that allocates inside the service's code … is not caught and not retried"). NOTES section 6,
    point 3, named exactly this case ("an allocation inside a file read (decompressing a packed game file) on
    fsp-srv: not covered").
  - `HleReply::Prepare` also appears in the G2-2 stack. It is a leftover return address from the set-up that
    finished earlier ("?" = not checked), not the thrower.
  - HEAP_STEAL=3 should serve a 0.6 MB request from an idle arena (max 2 MiB - 64 KiB). But the heap's live
    memory jumped by ~700 MiB in the 2 s before. Empty pages fell from 574 to 68 MiB and the pool stood at 3 MiB.
    INFERRED: there was little or nothing left to take. Its counter line never printed, so whether it tried is
    not visible.
- **Start 3 (abort).** The guest page tables could not commit a 2 MiB slot after ~25 s with 2 MiB free. No
  switch guards page-table commits. GUEST_WRITE_WAIT covers data slots and JIT_LEND covers code. The guest
  reserve was already 0.

**The two real culprits (READ in the census lines; cause INFERRED):**
- a. **Cold start: the heap sits on ~1.4 GiB of empty pages.** The first 3D scene builds ~400 new pipelines
  (141 + 136 in 20 s, and more at 351-378 s). By t ~220 the heap holds 2.7-2.8 GiB of pieces but only
  0.75-0.85 GiB live: 1.4 GiB of empty pages, 1.0 GiB of them in idle arenas. It keeps them to the end, while
  the pool runs at 0-280 MiB for the next 4-5 minutes.
  - `EDEN_HEAP_KEEP_ARENAS=1` (shipped) "keeps every arena with its record" (heap_arenas.inc:94, 300).
  - Warm starts enter the house with only 1.2-1.4 GiB of pieces. So a first start has ~1.4 GiB less room when
    the +0.7 GiB step after control comes, and dies in the house (3 of 3 now: run1239, G1-1, G2-1).
- b. **Door: the heap's live memory jumps by 600-800 MiB within ~2-4 s after A**, together with the GPU thread
  going "stale" for 2+ s.
  - Seen in all three runs that died at or after the door (G1-2, G2-2, G2-3). Not seen in the one that passed
    (G1-3: live flat at ~810 MiB).
  - What fills it is not named by any line. The census lists graphics categories only, and the 20 s heap-site
    dump never ran after the jump.
  - It is **not** the count of new pipelines at the door: G1-3 built 18 new there and passed, while G2-3 built 1
    and died.

## (3) Why G1's third start passed and G2's did not

- **Not the caches.** Before start 3, G1 had 1113 pipelines on disk (1008 prepared + 27 to prepare) and G2 had
  1123 (1018 + 34). Same store folder (`up_v1_2`), the same "980/962 compared at boot" path.
  - None of the 8 G2 switches is in the shader-store stamp list (vk_pipeline_prep.cpp:38-154, checked by name).
    G2's store was neither separate nor cold.
  - Start 2's door deaths did not lose their door pipelines either. Of start 2's door-time new pipelines, start
    3 rebuilt 0 from scratch and read 7 from disk in both groups. The rest were not met.
- **Not the door compiles.** G1-3 built 18 new at the door; G2-3 built 1 new + 6 from disk + 6 mesh.
- **Not less free memory.** The pool before A: G1-3 416 → 300 MiB; G2-3 640 → 392 → 154 MiB. Empty heap pages:
  G1-3 ~210 MiB, G2-3 ~280 MiB.
- **What differs is the burst.** G2-3 had the same +800 MiB live-heap jump as the two start-2 deaths, ~2-4 s
  after A. It came after the door's file reads were done, so no file read was the victim. The pool sat at 2 MiB,
  the GPU stalled (picture frozen on the porch) and 25 s later the page tables failed. G1-3 had no jump.
- With one group each, 1 of 3 against 0 of 3 is within luck (Fisher p = 1.0). INFERRED: nothing here shows a G2
  switch made start 3 worse. HEAP_STEAL=3 "keeps the arena" and G2-2 did enter the door with 594 MiB of empty
  pages and only 163 MiB in the pool, but G2-3 entered with more pool than G1-3.

## (4) What a newcomer meets today on a fresh install

- **With the shipped env.txt (no pair):** the first start likely hangs or crashes at the black screen (0 of 4 in
  earlier cycles). Not retested here.
- **With the pair** (TRUST_COPY + RESNAPSHOT=0, what G1 ran):
  - Start 1 gets through the black screen and dies in the house a few seconds after control (3 of 3 cold starts).
  - Start 2 dies ~1 s after opening the door (3 of 3: run1240, G1-2, G2-2).
  - Start 3: 1 of 2 reached the village (G1-3), while G2-3 froze on the porch and crashed.
  - So at least 2 crashes before a new game gets through, and about half of third starts make it (2 runs, no
    verdict).
- **Does "start it again" work?** It helps but is not reliable. Each restart gets further (house → door →
  outside) because the caches fill up. The cause of the door death (the live-heap burst) also hit a third start.
- Two things a real player does differently and this test did not try:
  - After start 1, the game has saved in the house. A player would **Continue** there and walk to the door
    without the long opening, so the memory state is different.
  - A brand-new player has no save, so no overwrite dialog.

## What the test could not see

- **The last ~2 s before each death.** HEAP_STEAL's counter line prints every 10 s at most, and only when a
  count changes, so whether it tried at the door is invisible.
- **GUEST_WRITE_WAIT's individual waits.** Its start line is in heap.log (all three G2 runs), but each wait's
  line goes to the kernel log, and `EDEN_GUEST_WAITS` needs `EDEN_NX2_POOL_WALK=1` (not set). G2-1's 10 s
  freeze before the crash fits a full wait, but the wait itself is not logged.
- **What fills the +600-800 MiB door burst.** No heap-site dump after it, and the census has no heap-by-site
  line.
- **Why G1-3 had no burst.** Not answered.
- Per-pipeline lines stop after ~350 on a cold run, so the cold "last 60 s" counts are from the 10 s sums (at
  least 74 and 72; the last 3-4 s are not covered).
- The 30 s stand outside saw G1-3's arrival only up to 30 s. A later memory step is not covered.
- The restart a real player makes (Continue from the house save) and the shipped env without the pair were not
  run.
- One group per setting: no verdict on G1 against G2.

## Verdict

- **Black screen: solved with the pair**, 6 of 6 here and 4 of 4 cold with v5. It is ready to become the
  default; the shipped file still lacks it.
- **House and door: not solved.**
  - The T133/T134 fixes acted where they were built to act: the reply buffer (≈220k allocations saved), the
    kept-levels decode (321 MiB at the first 3D scene) and the frame wait.
  - They did not move the result: G2 0 of 3, G1 1 of 3. Two deaths moved to a request with no fix (the file
    decode inside the read, the guest page tables). The first-start death most likely sat in the 10 s
    game-memory wait and lost, because the heap's 1.4 GiB of empty pages is never handed back.
- **The two biggest leads are both in the heap:**
  - a. After a first start's shader burst, ~1.4 GiB of empty heap pages are never returned (KEEP_ARENAS).
  - b. A +600-800 MiB live-heap burst 2-4 s after the door is opened.
- **Next tests, not run:**
  1. A cold arm with `EDEN_HEAP_KEEP_ARENAS` unset (or a trim of idle arenas when the pool is short) to see
     whether start 1 survives the house.
  2. A heap-site dump at the failure, and on the door burst, to name what grows.
  3. Cover the lazy-decode allocation in `NupLazyVfsFile`: spill to the temp file, or wait and retry when the pool
     is short.
  4. A Continue-from-house restart test, the route a newcomer really takes.

## In plain words (written for the project owner) (6 lines)

1. Six fresh-install starts this morning: one got to the village, five crashed.
2. The black screen after the opening is fixed with the two-switch pair: 6 of 6 got past it.
3. The new fixes worked as built but saved no start. Each crash just moved to another part that ran out of memory,
   and on the first start the longer wait only added a 10-second freeze before the same crash.
4. First starts die in the house because the emulator keeps ~1.4 GB of empty memory after building its drawing
   recipes the first time.
5. Opening the door makes the emulator's memory jump by ~0.7 GB in 2-4 seconds. That killed both second starts
   and one third start.
6. A newcomer needs at least 3 tries right now, and the third works about half the time.

## Checked a second time (12 Nov, ~09:00, read only)

Recounted from the six run folders, the runner log, the cache proofs and the T134 source and symbols. Nothing on
the console was touched, no test started, nothing posted.

Confirmed (READ):
- Endings: 5 crashes, 1 script end (G1-3 has `script_end line=126` and `script_done`, no crash file). No run is a
  freeze reported as a crash or the reverse; G2-1 (~10 s) and G2-3 (~25 s) froze first and then crashed.
- Caches: COLD proofs for run1271/run1274 (0 on disk, jit absent); WARM 1090/1113 (G1) and 1072/1123 (G2); park
  and restore steps happened between groups only. The queue ran with `--no-net-resume`; no latched stop, no
  pending restore, no hang flag.
- Env: every G2 switch, the pair and KEEP_ARENAS appear as `EDEN_ENV` lines in each run's heap.log, spelled as in
  the source. Nothing was dropped or misspelt. POOL_WALK is unset in all six.
- Stamp list: of all names in vk_pipeline_prep.cpp's list, only EDEN_NX2_RESNAPSHOT matches, and both groups set
  it the same. G2's store was not separate.
- Stacks: re-symbolized on the T134 symbol file (code size 0x2cd53a0). G1-2 = ScratchBuffer::resize_destructive
  in the reply wrapper; G2-2 = NupLazyVfsFile::Read+0x87c under IStorage::Read. Prepare's frame in G2-2 is a
  leftover: Prepare returns before the service call (cmif_serialization.h:518-531).
- Door burst: live heap 817 -> 1,419 -> 1,604 MiB within ~4 s in G2-3, 809 -> 1,495 in G1-2, 819 -> 1,517 -> 1,607
  in G2-2; G1-3 stayed at 805-816. GPU "stale" starts with each burst.
- HEAP_STEAL printed only its mode line in all three G2 runs. Fisher p = 1.0 for 1/3 against 0/3.

Changed:
1. G2-1's victim: not "the driver was refused". The driver refusals (63, not 3; CreateBuffer -2 x6 is right; G1-1 had 64 too)
   came ~10-15 s earlier. The crash is a GPUBack read of game memory; such faults go through the game-memory
   wait that GUEST_WRITE_WAIT_MS=10000 sets, and the picture froze ~10 s right before the crash. INFERRED: the
   wait ran its full 10 s and lost. So "none of the deaths was a request the fixes guard" is now "two of three".
2. GUEST_WRITE_WAIT "no line" was wrong: its start line is in heap.log (the app's stdout) in all three G2 runs.
   Only the per-wait lines are invisible (kernel log).
3. "4 of 4 cold starts with the pair, against 0 of 4" was wrong: run1240 was warm. It is 3 of 3 (run1239, G1-1,
   G2-1) against 0 of 3 default cold runs (run1233, run1235, run1237).
4. G2-3 froze on the first shot of the arrival scene on the porch, not while walking out.
5. G1-3 also had its pool at 0-3 MiB near the door and 14 driver refusals, and still got through.

Not changed: the table's times, threads, heap and compile counts match what I spot-checked; the per-run compile
counts in the last 60 s were not recounted line by line.
