# Source of test build T180

GPL-3.0-or-later. This folder holds everything that changed between dev build T134 ([`source/T134`](../T134/))
and test build T180. Start from the T134 tree: the branch `ocarina-dev-t120` of
[Vampinity/Eglantine-PS5-](https://github.com/Vampinity/Eglantine-PS5-/tree/ocarina-dev-t120) (commit e40829e)
with `source/T134/t120-to-t134.diff` applied.

## Rebuild T180

```sh
git clone -b ocarina-dev-t120 https://github.com/Vampinity/Eglantine-PS5-.git
cd Eglantine-PS5-
git apply --whitespace=nowarn /path/to/source/T134/t120-to-t134.diff
git apply --whitespace=nowarn /path/to/source/T180/t134-to-t180.diff
make package        # see docs/BUILDING.md (Linux x86-64 toolchain)
```

After both `git apply` steps the tree is `55a2cc8913724ea6c983b4a3b41622bff6cf3c4b`
(`git add -A && git write-tree`). It differs from the tree the build was made from only in comments and
patch descriptions (private notes and file names taken out, e-mail addresses removed from the patch
headers), so the program is the same. One side effect: `tools/gen-translation-id.py` hashes its own
text, so a rebuild gets a different translation id and builds its shader store again on the first start.

## What is in here

- `t134-to-t180.diff`: the whole change in one file, made with `git diff --binary --full-index`.
- `front-t134-to-t180.diff`: only the PS5 front end and the build tools (everything outside
  `tools/eglantine-patches` and `tools/patch-radv-series`), 32 files.
- `eglantine-patches/`: the 107 new emulator core patches, 0592 to 0960 (numbers that are missing belong
  to side builds and are not in T180). The build applies them to the Eglantine core.
- `patch-radv-series/`: 14 new graphics driver patches, lead-mesh-28 to lead-mesh-35 and lead-mesh-39 to
  lead-mesh-44.

The front diff plus the two patch folders give the same tree as the one big diff. Most new switches are off
unless their line is in env.txt. A few crash fixes are on by default: the ASTC opacity scan in 16 KiB
pieces (0661), the copy engine's scratch in stripes (0920, 0922), a table growth or slot refusal that no
longer ends the session (0890, 0892), the dirty-page split (0835) and the cold-hint bounds check (0641).
Also on without a switch line: a texture-cache list that is now filled only when its log asks for it
(0745), and small changes that do not change behaviour (0602, 0603, part of 0610).
Each patch's description says whether it has a switch. The settings the build was tested with are
[`envs/Vampinity/play-v39.env.txt`](../../envs/Vampinity/play-v39.env.txt).

Ported work is named in each patch's description: among others waveydude (pack in place, the two-slot
guard, the driver cache switch, the ASTC scan change), GrowingBlackBeans (read sync, early guard), Fritchii
(the whole-game shader recipe), heydemoura (the heap memory research in his pull request 104 to EglantinePS5), lethevimlet (one VMA
block size, from his BC-250 work) and the Lichii contributors. Full list: [CREDITS.md](../../CREDITS.md).
