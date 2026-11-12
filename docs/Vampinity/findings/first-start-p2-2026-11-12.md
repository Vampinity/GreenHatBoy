# First start with the switch pair (TRUST_COPY + RESNAPSHOT=0): checked (12 Nov 2026)

> **Found:** With the switch pair EDEN_GBB_TRUST_COPY=1 + EDEN_NX2_RESNAPSHOT=0 both first starts got through the black stall, but one crashed in the house (game CPU thread) and the other at the house door (bad_alloc on the file service).
>
> **So:** The pair fixes the black-screen stall; the house-door memory crash is a separate problem that still needs its own fix.

Independent check of a first report on `auto-20261112-020516-batch-first-start-p2.v5` (T130, base PS5 12.40,
new game, opening watched). Both runs had defaults plus `EDEN_GBB_TRUST_COPY=1` + `EDEN_NX2_RESNAPSHOT=0` (the
two env files differ only in the script name). Controls: `run1233`, `run1235`, `run1237` (default cold) and
`run1238` (default warm). READ = seen in logs, source or frames by the second check. INFERRED = reasoning.
Console not touched; no other file changed.

- `run1239-fs-p2-cold` (empty caches): through the black stall, through the long scene, then a crash in the house,
  521 s after app start (SIGSEGV on CPUCore_2, a game CPU thread).
- `run1240-fs-p2-warm`: **finished.** It crashed at 455 s, `std::bad_alloc` on FS (`requested=834033 reason=2`),
  largest free block 6 MiB, heap 1,952 + 125 MiB. READ (result.json, crash file, frames f0091 = "(A) Open" at the
  door, f0092 = black, then the console home screen). Script offset 8.64 s (runs.jsonl), so the three A presses
  were at app 453.5 / 454.5 / 455.5 s: it died 1-2 s after the first A. The batch ended at 02:23:42 and wrote its
  card ("2 runs, 0 valid", no control in the batch).

## Verdict on the report

Mostly right. The black-screen counters, both address classifications, the code path and the game moments hold.
Two points in the memory story are wrong, and some figures are slightly off.

1. **The "+730 MiB driver step" is not a door step, and it also happened in the warm run.** READ (RADV lines,
   stderr clock): run1240 driver 3,080 -> 3,814 MiB between t_s 429 and 439 (control in the house), free
   809 -> 745 MiB. So all three runs (1238, 1239, 1240) take the same ~0.7 GiB driver jump a few seconds after
   control in the house. In 1238/1239 only ~150-220 MiB was free, so it emptied the pool there, before the door.
   In 1240 it fitted. The door load is a **second, separate** jump: free 745 -> 126 MiB at t_s 449, heap pieces
   +768 MiB, live heap 1,754 MiB at the failure.
2. **"The door asks for about 1.5 GiB" double counts.** The heap's new pieces come out of the same pool. Net
   visible pool drop at the door is about 0.6 GiB (745 -> 126), with swap giving some back meanwhile. INFERRED:
   the door needs somewhere between 0.6 and 1 GiB within ~10 s; 1.5 GiB is not shown.

Smaller corrections:
- "2 writes wait for a block from t_s 513 on": READ, it went 0 -> 3 -> 3 -> 0 -> 2 -> 2 (t_s 512-514), and the
  refused-write counter (`failures=` in the EDEN_CRAM lines) was still 0 in the last report. The 42 + 44 slots
  packed out for graphics (128 MiB) come after the last line that shows waiters, so "while two writes were
  still waiting" is INFERRED, not read.
- Supporting evidence the first read missed (READ): the last 5 s fps line is at 514.1 s, the last render lines at
  518.4 s, then only "screenshot already in progress" errors from 519.8 s and the crash at ~521 s. INFERRED: the
  picture stopped about 2-2.5 s before the crash, which fits a game CPU thread sitting out the 2 s
  wait-for-a-block (`WaitForBlock`, 20 ms steps, 2 s unset) and then being refused.
- Render targets went "unbacked" (no memory behind them) from 513.1 s, not 514 s.
- rip is 6.9 MiB into the 6th JIT code area (`code=128ce00000`, held 16-48 MiB), not 7.2 MiB.
- run1235 has 5 dropped-word lines, not 4.
- The 24 "copied during a suspension" entries that all differed (READ: 24/24/24 from 257.7 s on) are the one
  direct sign the pair did something: 24 places where memory had changed after the copy was taken. INFERRED: on
  the old path those would have been read again. The label's exact meaning was not checked in source.

## What holds (re-read)

Black screen, run1239 (app/log clock):
- Give-ups ("present fence not reached in 4 s"): 223.5, 233.4, 240.6 s, presents #11529-11531. Windows: 60 fps
  to 214 s, 596 ms worst at 223.5, then single frames of 10.0, 7.1 and 11.2 s, 6.3 fps at 253 s, 19.3 fps at
  258 s. So about 25-30 s with almost no picture.
- FETCH_COUNT at 149 / 257.7 / 509.8 s: submit copy 0/0/966,550 -> 1,960,597 -> 18,399,513 (never compared);
  copy read again after submit 0/0/12 throughout; resumed entries 0 differing; lists read again 0; dropped words
  0; "suspension count changed" 59,820/61,305/61,305 at the end.
- Junk lines in the whole run: unbound subchannel 0, Unimplemented topology 0, Read32 of unmapped GPU address 0.
  One 2 s semaphore wait at 370 s (channel 2); play went on after it.
- Controls, same reading: give-ups at 225.3/235.3/244.4 (1233), 223.1/232.5/241.9 (1235),
  225.0/235.1/239.1/243.2 (1237). 1233: copies read again 221 of 110,984 differing at 245.3 s, 8 unbound
  subchannel, topology 3734, crash. 1235: Read32 of unmapped x16, freeze. 1237: no junk, 0 of 53,968 re-reads
  differing, FETCH_COUNT stops at 151 s, channels 1/2/3/5 wait on semaphores that never move (channel 1 at value
  0), freeze. run1240 (pair, warm cache): 0 give-ups, 0 junk lines.

Crash site, run1239:
- READ: rip 0x128d4e297c lies in the JIT code area at 0x128ce00000 (192 MiB), so it is translated game code.
  Stack (llvm-symbolizer on llvm-pie.elf): Fiber <- MultiCoreRunGuestThread <- PhysicalCore <-
  ArmDynarmic64::RunThread <- A64 Jit GetBlock, plus scheduler leftovers.
- READ: fault 0x830ccfc500 = rdx 0x61b9a00000 + rax 0x21532fc500 exactly (page-table entry + guest address).
  It lies inside `EDEN_GUEST_MEMORY va=8000000000 bytes=15032385536` (ends 0x8380000000), offset 12.2 GiB, 2 MiB
  slot 6246; the CRAM map holds 206 slots in that GiB. trap 12 error 0x4 = a read of a page not present.
- Code (READ, T130 front `src/guest_memory_service.inc`): `ServiceSignal` (1647) -> `HandleGuestWriteFault`
  (1577), which serves reads too. A slot in a no-access state is brought back by its promote step; a swapped-out
  slot (`SlotOut`) needs `SwapIn` (1195), which takes a 2 MiB block from spares, then the pool, then the reserve.
  None -> `WaitForBlock` (1402) every 20 ms for `EDEN_UP_GUEST_WRITE_WAIT_MS` (unset here: 2 s) -> refused (why 2)
  -> the signal goes on to the crash reporter. A watched slot (`SlotProbe`) needs no block (`TouchProbe`), so a
  fatal read means a swapped-out slot with no block, or the 17-repeat rule (why 1). `eden_guest_memory_reclaim`
  (3364) never checks `memory_waiters`; the reserve lends (1458, 1503) do. `eden_guest_write_refused` exists
  (1274) but `crash_report.cpp` never prints it, so the crash file cannot name the case.
- Memory at the end (READ): reserve 0 of 64 MiB, pool 2 MiB free in 50 pieces, 20 images refused, swap
  failures 13 -> 20, reclaim for graphics mostly 0 MiB given back.
- Cause, INFERRED (fairly confident): the game read a page the swap had packed away; no 2 MiB block came within
  2 s; the read was refused. Not a JIT bug and not junk commands.

Game moment, run1239 (READ): hint WAIT at script 498.5 = app 505.3 (offset 6.73), "Saving..." Commits at
505.3-506.6. f0104: the player facing the bright doorway across the room, Move/Change View hint still up.
f0105 black. f0106 the launcher's crash message. The "(A) Open" look gave up at script 513.0 = app 519.8, so A was
never pressed; the crash came during the fallback push, ~16 s after control, before the door. run1238 died at the
same stage (hint +13 s).

Long scene and warm partner: the fps and recipe counts were not all recounted. Spot checks match (run1240 993
recipes read at boot, 85 windows averaging 39.7 fps over the whole run including menus; no give-ups).

## Verdicts

**Switch pair (what one cold run can carry):** 1 of 1 cold run with the pair got through the first-3D-scene stall
with no junk and played on; 0 of 3 default cold runs did (1 crash with junk, 2 freezes). Fisher p = 0.25: could be
luck. Mechanism fits (no memory re-reads, 24 changed entries kept from the copy, 0 junk lines), but FETCH_COUNT=1
never compares submit copies, so it cannot show the copies were clean. It says nothing on the 1237-type freeze
(no junk, no differing re-reads, semaphores stuck): that failure is not shown fixed. Keep the pair as the leading
candidate, not as a proven default.

**One memory wall?** Yes, with a refinement. All five later deaths (1234, 1236, 1238, 1239, 1240) die with the
pool empty (largest free 2-8 MiB) and the reserve drained; the dying part differs (file service x3, graphics
driver x1, game CPU x1) because whoever asks next loses. But there are **two jumps**, not one: (a) ~0.7 GiB of
driver memory a few seconds after control in the house, which killed 1238 and 1239 before the door when only
~150-220 MiB was free; (b) the door load itself, which killed 1234, 1236 and 1240, the last even with ~750 MiB
free and a full cache. Fixing the first-start leftovers alone will not get through the door.

## In plain words (written for the project owner) (plain words)

With the new pair of switches, the first start got through the black screen after the opening: the picture hung
for about half a minute while the emulator prepared the first 3D scene, then the game played on with no garbled
drawing. All three earlier first starts without the pair died there. This is one run, so it could still be luck.
The long scene then ran at about 20 fps with frequent hitches, like the earlier second starts. A few seconds after
you get control in the house, the graphics side takes about 0.7 GB more memory. On this start that used up the
last free memory, and when the game needed back a piece of its own memory that had been packed away, there was no
room to unpack it, so the game itself crashed on the walk to the door. The next start, with everything cached,
played smoothly (about 24 fps) and survived that moment, but died a second after pressing A at the door, when
loading the village needed more memory again. So memory around the house and the door is the next thing to fix,
not the black screen.

Terms: give-up = the emulator stops waiting for a late frame after 4 s; swap = packing unused game memory away to
make room; reserve = a small emergency stock of memory for the game; cache = stored drawing work from earlier starts.

## Next tests, in order

1. Cold first start: 3 runs with the pair against 3 default, alternating, with `EDEN_NX2_FETCH_COUNT=2` so submit
   copies are compared. Read: give-ups, stall length, differing copies, junk lines, crash or freeze at the first
   3D load, stuck semaphores.
2. Warm door, full cache (like run1240): 3 control against 3 with `EDEN_UP_GUEST_WRITE_WAIT_MS=10000` +
   `EDEN_UP_HEAP_STEAL=3` (+ `EDEN_NX2_POOL_WALK=1` for the EDEN_GUEST_WAITS line). Read: who dies or whether the
   village loads; waits won/lost; steal counts; free memory before and after A.
3. One house-and-door run with `EDEN_UP_MEM_CENSUS=1` to name the ~0.7 GiB driver jump after control and the
   ~0.6-1 GiB door jump.
4. Restart-then-door: house save, fresh app start, Continue, open the door, 3 runs (player workaround).
5. `EDEN_GUEST_SWAP_RECLAIM=0` as its own arm on the cold route: does the game-memory death move or go away?

## Code fixes worth making (not tested)

- `eden_guest_memory_reclaim`: return 0 while `memory_waiters > 0`, as the reserve lends already do.
- `crash_report.cpp`: print `eden_guest_write_refused` (address, why, slot state) and the waits won/lost.
- Keep a guest-only part of the reserve that graphics and page-table slots cannot take below a floor.
- Door: the FS reply-buffer reuse plus a catch around `CompleteSyncRequest` (see
  `first-start-second-crash-2026-11-12.md`), then shrink the two jumps once the census names them.
