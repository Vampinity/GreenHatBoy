# The shared warm store, and the first two warm floors (18 Nov 2026)

GrowingBlackBeans, on the alpha T186 (01.219.028) as released, base PS5, firmware 13.60, handheld 1x. Runs are in
`runs/GrowingBlackBeans/2026-11-18-runW*`; floor files in `tools/stk/floors-warm-*-2026-11-18.json`.

## The store (runWS2)
Shader set prepass on the alpha, from the recipe `oot-v131072-cache-v54.nx2recipe` (sha256 b5cd068b..., the same as
Vampinity's). `recipes read 1, selected 1`; 80,770 keys, 80,743 kept, 27 failed, in 7,599 s; store `prep_5093ab9e`,
755 MiB; translation id src7f9773909a21e3689fd7c18d27a3c10c. No crash, no out-of-memory line. (runWS1 built nothing:
setting the caches aside had taken the recipe with them.) The cache was copied off the console after the build,
with a SHA-256 list split into FIXED (the store, its index, the shader set) and GROWS (the driver cache, the app's own
pipeline files): waveydude's suggestion.

A warm start logs `store prep_5093ab9e reused (80770 pipelines)`. **N = 80,770** (the records, not the 80,743 kept).

## What a warm start has to restore
Two findings decided how warm starts are run:
1. **The app's own files grow with play.** After runWB1, runWB2 read 820 own records at boot (WB1: 36) and built 6
   shaders during play (WB1: 199). N didn't show it: N counts only the store. Kept as `runWB2-played`, not a control.
2. **The store itself can grow.** After a restore of the GROWS files only, the store read 80,798. It had grown by 28
   during or after runWB2-played's play, with no log line saying so. Kept as `runWB2-n80798`, not a control.

So every warm control from runWB2 on starts from a restore of the whole cache from the post-build copy (both cache
folders deleted, the copy uploaded). The boot then reads: 80,770 reused, 80,770 known, 0 left to prepare, 3 own
records, Total Pipeline Count 4. runWB1, the first start after the build, read 36 own records (all already in the
store; the copy caught 3) and is kept as control 1: the known set is the same.

## The floors: warm against cold, 4 starts a side
p is the two-sided permutation test on the means; 0.029 is the smallest a 4-and-4 test can give.

Baseline (new-game v9; warm runWB1-4, cold runBW1, 2, 4, 5):

| number | cold | warm | p |
|---|---|---|---|
| worst frame, ms | 10,989-22,499 | 2,888-3,056 | 0.029 |
| smallest largest free block, MiB | 165-362 | 496-720 | 0.029 |
| fps median | 26.5-26.95 | 27.85-28.1 | 0.029 |
| village fps | 15.87-22.43 | 19.1-22.6 | 0.34 |
| shader builds during play (not gated) | 358-361 | 192-199 | - |

Kokiri (four stops v2; warm runWK1-4, cold runKV1, 2, 4, 5):

| number | cold | warm | p |
|---|---|---|---|
| worst frame, ms | 33,104-35,294 | 2,814-2,975 | 0.029 |
| smallest largest free block, MiB | 219-479 | 532-704 | 0.029 |
| fps median | 17.7-18.0 | 18.9-19.3 | 0.029 |
| stops A-D fps | no change (p 0.17-1.0) | | |
| shader builds during play (not gated) | 360 | 187-188 | - |

radv OOM events 0 on every start. Hitches and flashes are not measured on the alpha.

## What it says
- On both routes the store turns the first-load stall into about 3 s on every start (from 11-22 s and about 34 s),
  and roughly doubles the free memory at the tightest point.
- The stops and the village window don't move: the store helps loading, not steady frame rate.
- **Open question:** about 190 shaders are still built during play with all 80,770 known. The store doesn't cover
  everything these routes use; the first-start lists the app writes at shutdown name which.

Next: the field (WF1-4) and later-area (WV1-4) warm floors, the same way.
