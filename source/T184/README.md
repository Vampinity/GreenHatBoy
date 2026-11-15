# Source of build T184

GPL-3.0-or-later. This folder holds everything that changed between build T183 ([`source/T183`](../T183/))
and build T184. Start from the T183 tree (see [`source/T183/README.md`](../T183/README.md)) and apply
`t183-to-t184.diff`. After that the tree is `d952dd651d07d6da24edb34c4640c275626dbe03`
(`git add -A && git write-tree`). It differs from the tree the build was made from only in comments and patch
headers (e-mail addresses removed, one place name made neutral), so the program is the same.

## What is in here

- `t183-to-t184.diff`: the whole change in one file, made with `git diff --binary --full-index`.
- `front-t183-to-t184.diff`: only the PS5 front end and the build tools (everything outside
  `tools/eglantine-patches`), 2 files: the new graphics driver patch lead-mesh-45 and `tools/prepare-vulkan-port.py`.
- `eglantine-patches/`: the 12 new emulator core patches, 1030, 1032 to 1034, 1036, 1038 to 1041, 1055, 1060
  and 1062.

## The changes

All off unless their line is in env.txt, except 1034, which is always on. The build keeps the shader store.
The plant shadow switch only acts together with the older core switch `EDEN_NX2_MESH_POINTS=1`, and that one
does change the store.

| Patch | Switch | Origin |
|---|---|---|
| 1030, 1041 | `EDEN_UP_JIT_REGALLOC_BITS=1`: the JIT's register allocator keeps track of its slots in bitmasks instead of scanning all 102 | zortos293/Lichii #1517 by Zortos, co-authored by Liomar Oliveira |
| 1040, 1041 | `EDEN_UP_JIT_X64_OPT=1`: four of Lichii's x86-64 code generation options for the JIT | zortos293/Lichii #1531 by Zortos, co-author Julius Bairaktaris, from #717 by stephenjayakar and #641 |
| 1032, 1033 | `EDEN_UP_MESH_BEFORE_PASS=1`: a mesh draw that runs as compute records its compute work before the open render pass, instead of ending the pass and starting it again | idea and upstream patch by ronaldpena007-ops (zortos293/Lichii issue #1431), ported by hand to our own mesh path |
| 1034 | always on: a log line that runs out of memory while it is being written is dropped and counted (`EDEN_UP_LOG_LOST`), instead of ending the app | zortos293/Lichii #1475 by RomainROCH |
| 1036 | `EDEN_UP_PIPELINE_COUNT=1`: a line every 60 s with how many graphics, mesh and compute pipelines are alive, built and destroyed | idea from lethevimlet (oot-bc250 / lichii-bc250); the code is ours |
| 1038, 1039 | `EDEN_UP_AHEAD_GUARD_ORDER_PROBE=1`: waveydude's W-23 marker for the two-slot frame-ahead guard | waveydude (GreenHatBoy discussion 2), ported unchanged |
| 1062 | `EDEN_UP_AHEAD_GUARD_RESUME_PROBE=1`: waveydude's W-24 follow-up probe | waveydude, ported unchanged (his number 0940) |
| 1055 + front | `EDEN_UP_TEX_SHARE=1` with `EDEN_UP_TEX_SHARE_MIB=<MiB>`: while images hold under that size, a short pool no longer makes the texture collector delete them; uneven-mip ASTC textures stay compressed | zortos293/Lichii #823 by janvitos and #948 by danieljesus |
| 1060 | `EDEN_UP_COMPUTE_WAIT_LOG=1`: logs a compute dispatch that waits for its pipeline to be built | the log line of zortos293/Lichii #995 by Danny Ng |
| driver lead-mesh-45 | `EDEN_UP_RADV_MESH_POINTS=1`: mesh programs that draw points or lines also run as compute in the driver (the game draws its plant shadow map that way, so grass and bushes cast no shadow without it) | zortos293/Lichii #863 by nemiward |

Built on 14 Nov and checked (same translation id as T183, so a kept shader store carries over). It was on the
console from 14 Nov 01:24 to 07:36 for the load tests listed in
[BUILDS.md](../../docs/Vampinity/BUILDS.md). Of its own switches only waveydude's two probes have run (two
starts); the others have not run yet.
