# Source of build T183

GPL-3.0-or-later. This folder holds everything that changed between build T182 ([`source/T182`](../T182/))
and build T183. Start from the T182 tree (see [`source/T182/README.md`](../T182/README.md)) and apply
`t182-to-t183.diff`. After that the tree is `b9ee691a9ed8b5460ea19471d12f06ecdd49a388`
(`git add -A && git write-tree`). It differs from the tree the build was made from only in comments and patch
headers (e-mail addresses removed, place names made neutral, one file name replaced by words), so the program
is the same.

## What is in here

- `t182-to-t183.diff`: the whole change in one file, made with `git diff --binary --full-index`.
- `front-t182-to-t183.diff`: only the PS5 front end and the build tools (everything outside
  `tools/eglantine-patches`), 8 files.
- `eglantine-patches/`: the 8 new emulator core patches, 1000, 1001, 1004 to 1006, 1008, 1009 and 1020.

## The changes

All off unless their line is in env.txt, and none of them changes the shader store.

| Patch | Switch | Origin |
|---|---|---|
| 1000, 1001 | `EDEN_UP_AHEAD_GUARD_ALL_READS=1`: the frame-ahead guard's copies serve every GPU-side read of game memory | yuri2301, Eglantine commit c5145ace9 (frame overlap copies) |
| 1004 to 1006 | `EDEN_UP_BACKX=1`, `EDEN_UP_BACKX_DRAW=1`: the back thread skips locks and work that change nothing | zortos293/Lichii #1586 by Zortos, from jpkto, DahBard, skolvolt and lucastaonline |
| 1008, 1009 | `EDEN_UP_L1436_ENGINE_TRACKED=1`: data the GPU's engines write keeps its pages tracked | zortos293/Lichii #1436 by Zortos, from Lucas Borges' #1161 |
| front | `EDEN_UP_NEW_WAIT_BUILDER_SKIP=1`: threads that build pipelines add no memory wait of their own | waveydude, Eglantine-PS5- commit c2eb4e4 (W-05) |
| front | `EDEN_UP_HOST_STACK_KIB=<256/512/1024>`: smaller host thread stacks, each with a guard page | idea from CHI-GETSU's pull request 1 to mihawk-99/PS5_Hookshot |
| 1020 | `EDEN_UP_GFX_SCALE_TIER=<n>`: answers the game's graphics scale tier question with tier n, so the game can draw its own 3D smaller | ours, after nxnative's notes on that service |

Built on 13 Nov and checked (same translation id as T180, so a kept shader store carries over). Not run on the
console yet.
