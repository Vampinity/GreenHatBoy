# How close Kokiri is to the memory wall

GrowingBlackBeans, 11 Nov 2026. From the memory census on stderr (`RADV_PS5_MEMORY`, `EDEN_POOL_LEDGER`, `EDEN_VMA_USAGE`) and the texture cache's `Memory margins` lines in 1,055 runs that have them: 968 Vampinity, 87 GrowingBlackBeans. All runs are on base PS5s, mostly Kokiri routes.

## The pool and who uses it

Everything lives in one 12,352 MiB pool (`pool_mib`). Medians over runs that ended normally:

| | Vampinity (843 runs) | GrowingBlackBeans (87) |
|---|---|---|
| Least memory available in the run | 166 MiB (p10 32) | 280 MiB (p10 147) |
| Peak driver (GPU) memory | 4,006 MiB | 3,610 MiB |
| Guest memory held | 5,660 MiB | 5,769 MiB |
| Emulator heap | 1,184 MiB | 1,120 MiB |
| JIT | 448 MiB | 464 MiB |

81 runs touched 0 MiB available at some point (47 of them still finished).

## When it runs out

- **18 real out-of-memory crashes**, almost all on 8-9 Nov builds; one since (10 Nov, `run947`). Newer builds fixed most of them in Kokiri.
- **23 more** are deliberate squeeze tests (`hog<MiB>`, `gpustarve`), which withhold memory to find the margin.
- **Where:** the crashes come at the door into the village, 85-105 s into a walk route. There driver memory climbs about 3-4.5 GB in a minute (from about 0.6 GB) while guest memory sits near 5 GB. The village's GPU resources arriving is the peak.

## The margin, measured by the squeeze tests (Vampinity)

| Memory withheld | Out of memory | Survived |
|---|---|---|
| 512 MiB | 0 | 6 |
| 640 MiB | 0 | 1 |
| 768 MiB | 1 | 2 |
| 896 MiB | 4 | 11 |
| 1,024 MiB | 3 | 2 |
| 1,152 MiB | 6 | 0 |
| 1,280 MiB | 7 | 0 |

So Kokiri has about **0.8-1 GB** of real headroom at its peak with the current memory machinery (swap, eviction), about 7-8% of the pool. A bigger area that needs about 1 GB more GPU memory at its transition will crash, unless the machinery frees more.

## Leads

1. **VMA block slack** (allocated GPU memory blocks not in use; the `block slack` field of `Memory margins`):

   | | Typical | Peak |
   |---|---|---|
   | GrowingBlackBeans | 483 MiB | 765 MiB |
   | Vampinity | 19 MiB | 642 MiB |

   Neither env sets a VMA switch. The everyday envs differ in guest swap (`EDEN_GUEST_SWAP_AHEAD_MIB` 2048 vs 12288, `EDEN_GUEST_SWAP_COLD_S` 90 vs 30), `EDEN_NX2_TC_KEEP_ASYNC` 120 vs 300 and `EDEN_NX2_TRANSCODE_THREADS`, and the routes differ. Cause unknown. Candidates to test: `EDEN_VMA_BLOCK_MIB=8` (on Vampinity's worth-a-look list), and the swap settings. Up to about 450 MiB of headroom at stake for us.
2. **The transition peak:** the old area's render targets stay alive about 2 s after a cut (Vampinity's census). Releasing them earlier lowers the peak directly.
3. **Decoded textures:** the async-decoded image keep limit logs about 1.2 GB dropped over a walk (`Decode image over the kept limit`). Formats kept larger than the guest's (ASTC decoded) multiply GPU memory.
