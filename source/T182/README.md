# Source of build T182

GPL-3.0-or-later. This folder holds everything that changed between test build T181 ([`source/T181`](../T181/))
and build T182. Start from the T181 tree (see [`source/T181/README.md`](../T181/README.md)) and apply
`t181-to-t182.diff`. After that the tree is `6184c2b3126a7213216a9c2a86bd5a7eceaec085`
(`git add -A && git write-tree`). Patch headers have their e-mail addresses removed; the program is the same.

## What is in here

- `t181-to-t182.diff`: the whole change in one file, made with `git diff --binary --full-index`.
- `eglantine-patches/`: the 11 new emulator core patches, 0980 to 0990. There is no front end change.

## The ports

All off unless their line is in env.txt, and none of them changes the shader store. Each is a port by reading
of a change in [zortos293/Lichii](https://github.com/zortos293/Lichii); the patch headers name the commits.

| Patch | Switch | Upstream |
|---|---|---|
| 0980, 0982 | `EDEN_UP_L1515_QUERY_CHEAP=1`: cheaper report lookups, frees and locks | #1515, Zortos |
| 0981 | `EDEN_UP_L1516_FENCE_CHEAP=1`: the fencing thread is woken only when something waits | #1516, Zortos, from Lucas Borges' #1161 |
| 0983, 0985 | `EDEN_UP_L1519_FAST_DRAWS=1`: more draws take the fast path | #1519, Zortos |
| 0984 | `EDEN_UP_L1521_KEEP_GAPS=1`: uniform keep gaps closed | #1521, Zortos with Lucas Borges |
| 0986, 0988 | `EDEN_UP_L1520_WORDS_POOL=1`, `EDEN_UP_L1520_ASYNC_COPY=1`: command list copies reused | #1520, Zortos |
| 0987, 0988 | `EDEN_UP_L1585_STATE_BLOCKS=1`: 3D state writes sent to the back as blocks | #1585, Zortos |
| 0989, 0990 | `EDEN_UP_L1639_PARK_WAIT=1`: frame fence waits park the service thread | PR #1639 by DuskDarf1 (open upstream) |

Built and checked on 13 Nov. T182 itself was not run on the console; these patches are in T183.
