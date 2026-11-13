# The memory wall on my console: the pool was not full, it was full of holes (13 Nov)

Base PS5 13.60, my T120 hybrid, builds W-13 to W-19. Seven sessions, five of them crashes, all in `runs/waveydude/2026-11-13-*` (logs, heap logs, settings, crash summaries).

**Short version: at every memory wall the pool still had 430 to 1,340 MiB free, with a largest free block of 1 to 8 MiB. The free memory was the tails of guest slots packed in place (`EDEN_GUEST_SWAP_PACK_IN_PLACE=1`), which nothing else can take. W-20 has a fix (`=2`); it is built and installed but has not run yet.**

## What the logs show

`EDEN_POOL_LEDGER` counts everything out of the pool in four size classes. Their sum is what is out; the pool is 12,352 MiB. (The "under 2 MiB" class goes far below zero, because a tail given back is counted there while its block was taken in the 2 MiB class. The sum stays right.)

| Run | Build | Ended | Out of the pool | Free | Largest free block |
|---|---|---|---|---|---|
| `w13-crash-80m` | W-13 | crash, 4,836 s | 11,107 MiB | 1,245 MiB | 1 MiB |
| `w15-crash-51m` | W-15 | crash, 3,048 s | 11,873 MiB | 479 MiB | 1 MiB |
| `w18-crash-38m` | W-18 | crash, 2,303 s | 11,922 MiB | 430 MiB | 1 MiB |
| `w19-run1-24m` | W-19 | closed by hand, 1,412 s | 11,010 MiB | 1,342 MiB | 3 MiB |
| `w19-run2-16m` | W-19 | closed by hand, 973 s | 11,642 MiB | 710 MiB | 36 to 48 MiB |

Each row is the last ledger line of the session against the last largest-free-block reading. `w14-crash-13m` and `w17-crash-19m` ended at 1 MiB too; I have not summed their ledgers.

In `w19-run1-24m` the last `EDEN_SWAP_PACK` line reads `slots=1138 held=1140MiB in_place=5929`: 1,138 slots packed in place, each keeping about 1 MiB at the front of its 2 MiB block and giving back the other 1 MiB. That is about 1,136 MiB of tails, against 1,342 MiB free.

## Why the tails are no use

With `=1`, `PackOut` (`src/guest_memory_service.inc`) keeps a slot's packed bytes in the first pages of the slot's own 2 MiB block and releases the rest. The released part starts in the middle of a 2 MiB step and is under 2 MiB. Guest slots, the heap's pieces (down to one 2 MiB page) and the graphics blocks all ask for whole 2 MiB pages or more, so none of them can take it. The pool reads as empty to every one of them: texture storage refusals, pipeline builds failing for host memory, and in the crashes a guest touch of a packed slot that found no 2 MiB block to unpack into.

It started biting once the game's own memory went up to about 5.9 GB in a later part of the game. Every start since then reached the wall within about 10 minutes.

## The fix I am trying: `EDEN_GUEST_SWAP_PACK_IN_PLACE=2` (W-20)

- A packed slot's bytes go to a block of their own first. The console places it in the lowest room that fits, which is an older tail, and the slot's 2 MiB block goes back whole.
- Only when the pool has no block for the bytes does the slot pack in place, so packing never stops for memory (the reason `=1` was made: run 161).
- `=1` and unset behave as before. Front code only; not in the shader store's stamp list.
- `EDEN_SWAP_PACK` gains `pool_first=<n>`. The first packed slot logs `EDEN_SWAP_PACK_IN_PLACE on when the pool has no block`.
- Patch: `patches/waveydude/w20-front-pack-pool-first.patch` (new `src/pack_place.h`, `PackOut`, host test `tools/test-pack-place.cpp`). Settings: `envs/waveydude/w20-game.env.txt`.

Host test, a model of the pool in 16 KiB pages with lowest-fit placement, started full of guest slots:

| Setting | Free at the end | Of it in whole 2 MiB blocks | Unpacks that found no block |
|---|---|---|---|
| `=1` | about 300 MiB | 0 MiB | nearly all |
| `=2` | about 300 MiB | 230 to 260 MiB | 1 to 11 of about 10,000 |
| unset | 0 MiB (nothing could be packed) | - | - |

That is a model, not a console run.

## First W-20 console run (13 Nov)

First session with `EDEN_GUEST_SWAP_PACK_IN_PLACE=2` on base PS5 13.60:
- **Result:** Played through a later area and successfully reached and obtained the Hookshot without crashing.
- **Memory & Reclaim:** Under memory pressure, `EDEN_SWAP reclaim for graphics` repeatedly surrendered whole blocks to graphics (sweeps of 64 MiB, 65 MiB, 64 MiB, 64 MiB, 64 MiB, 42 MiB, 40 MiB) instead of returning 0 MiB as in W-19.
- Whole 2 MiB blocks remained available in the pool, avoiding the sub-2 MiB tail exhaustion collapse that previously locked the largest free block at 1 MiB.

## Still open / to watch

- Whether whole 2 MiB blocks are enough across even longer sessions for graphics, which asks 4 to 16 MiB at a time: free 2 MiB blocks that lie side by side join, scattered ones do not.
- Vampinity runs with in-place off, so this is probably not the first-start crash. The check is quick on any log: sum the four `EDEN_POOL_LEDGER` classes and compare with the largest free block.

## Two other things from these sessions

- **`short_by` in `EDEN_MEM_CENSUS_TOP` is not a shortfall.** It is the census mark (768 MiB) minus the largest free block. I read it as "766 MiB short" before; that was wrong.
- **Texture marks 1536/2048 instead of 2048/2816 did not help me.** Graphics memory in use stayed at 2.0 to 2.6 GB either way, and the images made and deleted per 600 frames went from about 300 to 500 (W-13, W-15) to 4,000 to 15,000 (W-18, W-19), with about 250 ASTC decodes a second in `w19-run1-24m` (median 14 fps). The comparison is confounded: the pool was already at the wall in those runs.
