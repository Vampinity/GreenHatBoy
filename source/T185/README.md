# Source of build T185

GPL-3.0-or-later. This folder holds everything that changed between build T184 ([`source/T184`](../T184/))
and build T185. Start from the T184 tree (see [`source/T184/README.md`](../T184/README.md)) and apply
`t184-to-t185.diff`. After that the tree is `f524b6887bc4768038ebaa1781696967e9861afa`
(`git add -A && git write-tree`). It differs from the tree the build was made from only in comments and patch
headers (e-mail addresses removed, one note's file name replaced by words), so the program is the same.

## What is in here

- `t184-to-t185.diff`: the whole change in one file, made with `git diff --binary --full-index`.
- `front-t184-to-t185.diff`: only the PS5 front end and the build tools (everything outside
  `tools/eglantine-patches`), 2 files: `src/guest_memory_service.inc` and the new graphics driver patch lead-mesh-46.
- `eglantine-patches/`: the 1 new emulator core patch, 1070.

## The changes

All three are aimed at the load from the field into the next area, where the graphics memory pool sits at its
last MiB for seconds. All off unless their line is in env.txt, and none of them changes the shader store.

| Patch | Switch | What it does |
|---|---|---|
| front | `EDEN_UP_GPU_READ_THROUGH_LOADS=1` | The graphics side reads packed game memory straight through (as `EDEN_UP_GPU_READ_THROUGH=2` does all the time) only inside a load window. The window opens when the largest free block falls through `EDEN_UP_GPU_READ_THROUGH_LOADS_MIB` (256), or is under `_HOLD_MIB` (2), or a memory wait passes `_WAIT_MS` (250 ms). It stays open while the pool is under `_HOLD_MIB` or a long wait goes on, and closes after `_CLOSE_S` (30) quiet seconds. Outside a window the core makes no read-through call at all. |
| driver lead-mesh-46 | `RADV_PS5_INTERNAL_RESERVE_MIB=<MiB>` | The graphics driver holds that much of the pool in 2 MiB blocks for its own small buffers (descriptor pools, upload buffers). When one of those is refused, it hands a block back and tries again. `RADV_PS5_INTERNAL_RESERVE_REFILL_MIB` sets when the reserve is filled again. |
| 1070 | `EDEN_UP_VK_OOM_RETRY=<tries>` | A descriptor pool the driver refuses for lack of memory is asked for again a bounded number of times, instead of ending the app. The backstop for when the reserve is empty. |

All three are ours. Built on 14 Nov and checked (same translation id as T184, so a kept shader store carries
over). On the console from 14 Nov 07:36; how it tested is in [BUILDS.md](../../docs/Vampinity/BUILDS.md).
