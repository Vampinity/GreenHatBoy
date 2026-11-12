# Source of dev build T134

GPL-3.0-or-later. This folder holds everything that changed between dev build T120 and dev build T134.
The T120 source itself is public as the branch `ocarina-dev-t120` of
[Vampinity/Eglantine-PS5-](https://github.com/Vampinity/Eglantine-PS5-/tree/ocarina-dev-t120)
(commit e40829e), which is viejunerd's EglantinePS5 fork plus our builds up to T120.

## Rebuild T134

```sh
git clone -b ocarina-dev-t120 https://github.com/Vampinity/Eglantine-PS5-.git
cd Eglantine-PS5-
git apply --whitespace=nowarn /path/to/source/T134/t120-to-t134.diff
make package        # see docs/BUILDING.md (Linux x86-64 toolchain)
```

After `git apply` the tree is `33f79925bc6a494155a8248ecba657055e1f5a93` (`git add -A && git write-tree`).
It differs from the tree the release was built from only in comments and patch descriptions (names,
private notes and later game areas taken out), so the program is the same.

## What is in here

- `t120-to-t134.diff`: the whole change in one file, made with `git diff --binary --full-index`.
- `front-t120-to-t134.diff`: only the PS5 front end and the build tools (everything outside
  `tools/eglantine-patches` and `tools/patch-radv-series`).
- `eglantine-patches/`: the 40 new emulator core patches, 0550 to 0591 (0556 and 0566 belong to side
  builds and are not in T134). The build applies them to the Eglantine core.
- `patch-radv-series/`: waveydude's two graphics driver patches, lead-mesh-26 and lead-mesh-27.

The front diff plus the two patch folders give the same tree as the one big diff. Every new switch is off
unless its line is in env.txt; the release notes say which are tested.
