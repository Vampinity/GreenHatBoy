# Source of test build T181

GPL-3.0-or-later. This folder holds everything that changed between test build T180 ([`source/T180`](../T180/))
and test build T181. Start from the T180 tree: the branch `ocarina-dev-t120` of
[Vampinity/Eglantine-PS5-](https://github.com/Vampinity/Eglantine-PS5-/tree/ocarina-dev-t120) (commit e40829e)
with `source/T134/t120-to-t134.diff` and `source/T180/t134-to-t180.diff` applied.

## Rebuild T181

```sh
git clone -b ocarina-dev-t120 https://github.com/Vampinity/Eglantine-PS5-.git
cd Eglantine-PS5-
git apply --whitespace=nowarn /path/to/source/T134/t120-to-t134.diff
git apply --whitespace=nowarn /path/to/source/T180/t134-to-t180.diff
git apply --whitespace=nowarn /path/to/source/T181/t180-to-t181.diff
make package        # see docs/BUILDING.md (Linux x86-64 toolchain)
```

After the three `git apply` steps the tree is `1f68c594a50882671a23a6c6ba8760bff573428c`
(`git add -A && git write-tree`). As with T180, it differs from the tree the build was made from only in
comments and patch headers (e-mail addresses removed), so the program is the same.

## What is in here

- `t180-to-t181.diff`: the whole change in one file, made with `git diff --binary --full-index`.
- `front-t180-to-t181.diff`: only the PS5 front end (`src/guest_memory_service.inc`).
- `eglantine-patches/`: the 2 new emulator core patches, 0970 and 0971.

The change is one switch, off unless its line is in env.txt: `EDEN_UP_WAIT_RECLAIM=1`. A thread that waits more
than 50 ms for a memory block raises a request, and the GPU thread then frees graphics memory without waiting
for a frame to be drawn: it drains deleted buffers, deletes the least recently used images, gives empty
allocator blocks back to the pool and trims the heap. The waiter keeps waiting while those passes still free
memory. It is aimed at the deaths at the load from the field into the next area, where a thread waited 10 s for
one 2 MiB block while no frame was drawn, so nothing else freed memory.

Tested on 13 Nov in scripted starts (handheld, 1x) at that load: with the switch 3 of 3 got through; play
settings v3.9 without it, in the same round, 2 of 3. Not played by hand yet.
