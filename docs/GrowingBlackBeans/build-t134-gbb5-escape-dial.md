# t134-gbb5: the read-sync escape dial (patch 0932)

GrowingBlackBeans, 13 Nov 2026. Built on t134-gbb4 (01.219.920); gbb5 would be 01.219.921.

| Patch | Switch | What |
|---|---|---|
| **0932** | `EDEN_GBB_READ_SYNC_ESCAPE=<us>` (with `EDEN_UP_AHEAD_READ_SYNC=1`) | How long a read's fence wait runs before it gives up because a channel is suspended on a semaphore acquire. Unset keeps Vampinity's 0567 value of 2 ms, and with it the 500 us yield phase and the 250 us sleep step, so an unset build behaves exactly as gbb4. The yield and sleep steps scale with the setting (escape/4 capped at 500 us; escape/8 clamped to 25-250 us). Floor 10 us. |

## Why

RC1's census (13 Nov, `runRC1`, 167,681 synced reads over eleven 10 s windows):

| | |
|---|---|
| Fence wait time | 133,609 ms (**84.4%**) |
| Flush round trips | 24,614 ms (15.6%) |
| Fence waits | 62,168, **2.15 ms each** |
| Escapes (0567's counter) | **60,480 of 64,897 fence waits, 93.2%** |

60,480 x 2 ms = 120,960 ms, which is 91% of the census's fence-wait time and about **77% of everything
read sync spends waiting**. Read sync once per frame (0930) removed 28% of the syncs — exactly the
coverage the census predicted — and bought 1 fps, because the timer is charged per fence wait and the
other 72% of reads still pay it.

| arm | by eye | fps |
|---|---|---|
| `runRX1` / `runRX2` two ahead, no read sync | flashes, worst at the forest hotspots | 26.65 / 26.65 |
| `runRO1` / `runRO2` + read sync once per frame | **no flashes** | 19.30 / 19.35 |

So the design is right and the constant is what we cannot afford. An escape that ends sooner returns the
same data it returns today — the wait ends without the fence either way — only sooner.

## The risk, stated plainly

A shorter escape means a read gives up on a frame's fence earlier, so it can see data one frame older.
That is a flicker risk, not a deadlock risk: escaping sooner is the safer side of that wait, and the
escape exists to avoid a hang, not to guarantee freshness. The test is whether flicker comes back.

## Test plan once it builds

Profile Player 1, benchmark save. Controls already in hand: RX1/RX2 (26.65) and RO1/RO2 (19.3).

| # | Folder | Arm | What it answers |
|---|---|---|---|
| 1 | `runRE1` | RO env + `EDEN_GBB_READ_SYNC_ESCAPE=250` | the candidate everyday setup: clean and fast? |
| 2 | `runRE2` | the same again | repeat |
| 3 | `runRE3` | RX env + `EDEN_UP_AHEAD_READ_SYNC=1` + escape 250, **no** once per frame | is 0930 needed at all, or is the dial the whole fix? |

Decision rules:
1. **RE1/RE2 clean and within about 2 fps of RX:** adopt read sync + once per frame + the short escape as
   everyday with two frames ahead. Frame-ahead flicker is closed.
2. **Clean but still slow:** the escape is not the whole cost after all; read 0567's counter for what the
   waits became (timeouts rather than escapes would mean the fence genuinely is not ready).
3. **Flicker returns:** walk the escape back up (500, 1000) and find where clean meets affordable.
4. **RE3 as clean and as fast as RE1/RE2:** 0930 is not needed, and the everyday setup is simpler.

## Status

**Built, verified, delivered.** `EglantinePS5-package/t134-gbb5`, contentVersion 01.219.921, commit
`795017a` in the build tree. The patch shipped is **not** the one first written here: that one was
written blind against 0567's diff text, and its anchors did not survive contact with the tree (0929 and
0930 touch the same read path). It was regenerated from the real
`Eglantine/src/video_core/ahead_read_sync.h` and `gpu.cpp`, and `EDEN_GBB_READ_SYNC_ESCAPE` is confirmed
present in the built eboot. Unstripped symbols at `/work2/keep/t134-gbb5-llvm-pie.elf` in the build
container.

### How it was built, and a note for whoever builds next

With `EDEN_SKIP_SOURCE_CHECKS=1`, which is how gbb1 through gbb4 were built too — `build-headless-native.sh`
documents it as the development-build opt-out, and every earlier build log shows the early exit (no check
output at all). I first built without it, which turned on about thirty-five release checks this fork has
never run, and spent a long detour repairing them. Set the flag.

Two things that detour turned up are worth keeping even though they are not ours:

- **A real latent compile break.** In `src/guest_memory_service.inc`, `packed_in_place` and
  `pack_tail_refused` were declared inside a `#if defined(PS5_NATIVE) && defined(EDEN_SWAP_LZ4)` block,
  while the `EDEN_SWAP_PACK` report reads them unguarded. Moved up beside `pack_not_worth` in our tree.
  waveydude is editing that file; worth telling Vampinity.
- **The build container cannot test self-modifying code.** It runs x86-64 under Rosetta, and a write
  through a writable alias does not invalidate Rosetta's translation cache. `alias-test-rosetta.c` in
  this folder is a six-line proof: native x86 prints 42 then 84, this container prints 42 twice. Any
  check that writes code through an alias and executes it will fail here for that reason alone.

### One asymmetry in the RE runs

All three RE envs also carry `EDEN_UP_ASTC_PENDING_STATS=1`, which RX1/RX2 and RO1/RO2 did not. It is
log-only and AS1 measured its cost as nil (26.77 fps against RX's 26.65 twice, above the controls and
well inside the ~1.2 fps noise floor), so it does not move the comparison — but it is a difference
between the arms and should be stated rather than discovered later.
