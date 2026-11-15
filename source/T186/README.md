# Source of build T186

GPL-3.0-or-later. This folder holds everything that changed between build T185 ([`source/T185`](../T185/))
and build T186. Start from the T185 tree (see [`source/T185/README.md`](../T185/README.md)) and apply
`t185-to-t186.diff`. After that the tree is `b61e7cd93a7f6970a8ea7a59f57c7a1e25394df6`
(`git add -A && git write-tree`). It differs from the tree the build was made from only in comments and patch
headers (e-mail addresses removed, one note's file name replaced by words), so the program is the same.

## What is in here

- `t185-to-t186.diff`: the whole change in one file, made with `git diff --binary --full-index`.
- `eglantine-patches/`: the 4 new emulator core patches, 1090, 1091, 1100 and 1101. There is no front end change.

## The changes

All off unless their line is in env.txt, and none of them changes the shader store. All four are ours.

| Patch | Switch | What it does |
|---|---|---|
| 1090 | `EDEN_UP_LISTWAIT_STATS=1` | Counters only. Every 10 s: how long the command reader waits for command lists the graphics chip writes itself, by length and by what reads them (grid sizes, mesh counts, other), the reader's and the recording thread's clocks, and the chip waits of each thread. |
| 1091 | `EDEN_UP_LIST_PARK=1` | A test switch: a channel whose chip-written list is not ready parks on it instead of waiting. Not run yet. |
| 1100 | `EDEN_UP_DRAIN_ON_GROWTH=1` or `=<MiB>` | The pressure drain runs as soon as the allocator has grown 256 MiB (or the given size) since the last drain, and deleted buffers are freed once the chip is past them. Needs `EDEN_UP_PRESSURE_DRAIN=1` for the drains. |
| 1101 | `EDEN_UP_BIG_UPLOAD_CHUNK_RELEASE=1` | A chunked image upload of over 64 MiB gives each chunk's staging buffer back once its copy is done. |

Built on 14 Nov and checked (same translation id as T185, so a kept shader store carries over). On the console
from 15 Nov 02:29; its first three tests are in [BUILDS.md](../../docs/Vampinity/BUILDS.md).
