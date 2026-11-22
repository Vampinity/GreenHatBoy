# Control switch ledger, 19 Nov 2026

Every line of the control, one row each, with what we know about it. Made for GrowingBlackBeans' phase 4 ("explain the control", section 5 of [review-2026-11-15-post-alpha-audit](../GrowingBlackBeans/review-2026-11-15-post-alpha-audit.md)), so that settled lines can be skipped and the rest screened. The same rows as JSON: [control-switch-ledger-2026-11-19.json](control-switch-ledger-2026-11-19.json). The method for screening them in groups is in [grouped-screening-method.md](grouped-screening-method.md).

**The control** is play settings v4.0 ([`envs/Vampinity/play-v40.env.txt`](../../envs/Vampinity/play-v40.env.txt), 169 lines) plus the two test lines `EDEN_TEST_DISCARD_SAVE=1` and `EDEN_UP_FAULT_LOG=1`: 171 lines. It is the control (CB) of this week's batches A and B, on T191 and T196.

## Answer first

Counts over the 171 lines:

| Verdict | Lines | Of which only as a group or a set |
|---|---|---|
| kept: helps | 41 | 19 |
| kept: needed for X | 21 | 0 |
| no effect seen | 10 | 0 |
| harmful | 0 | 0 |
| never tested alone | 74 | 0 |
| unknown | 25 | 0 |
| **all** | **171** | **19** |

What that means for phase 4:

| Phase 4 | Lines | What to do |
|---|---|---|
| screen | 87 | no verdict: switch it off in a group (the method page) |
| reach first | 11 | no verdict, and it may not act on the control at all: a desk reach check before any start |
| weak verdict | 34 | a verdict from one or two starts, an old build or another setup: GBB's call whether to re-open it |
| skip | 39 | a verdict that holds, or a log or test line |

- **Harmful: 0.** No line of the control has harm shown on today's kind of setup. The closest are single old starts (see `EDEN_HEAP_KEEP_ARENAS` and `EDEN_UP_PACK_PRESSURE_MS`), and one start is no verdict, so both are "unknown".
- **Against GBB's 17 Nov list** (the rows of [SWITCHES.md](SWITCHES.md) that say "no verdict yet": 74 of these 171 today): 63 are on both lists. 11 of GBB's get a verdict here: nine log, count and test lines, and two lines that only repeat the default. 35 more join the screen list, because their SWITCHES.md line is a result for another value, another setup (frame ahead on), one start, or a line that never acted. Every one is listed under "Where this differs from the 17 Nov list".
- **27 of the lines to screen are shader store names** (26 until 22 Nov: `EDEN_UP_CANONICAL_KEYS` was missing). Switching one off makes a new shader store (about 2 h to prepare), so those belong in own-store groups, two or three to a store (the method page).
- **19 of the 41 "kept: helps" rows hold only as a group or a set** (the JIT set, the load-window lines, two pairs, the movie set). Per GBB's rule they are "screened as a group", never "each of these was tested".

## How to read the table

- **Verdict.** `kept: helps` = a start with it beat a start without it, on speed, stutter, loads, survival or the picture. `kept: needed for X` = another line or the test logs need it. `no effect seen` = a test with and without it showed no change on what was measured, or the line repeats the default. `harmful` = harm shown. `never tested alone` = on in hundreds of runs, but never on and off apart (other values may have been tried; the evidence says which). `unknown` = a test ran but could not tell: one start, it never acted, or it was only measured beside a line that has since gone.
- **A `weak` verdict, helps or no effect, rests on one or two starts or an old build. It is a lead, not a finding, and every such row is under "weak verdict" for GBB to re-open.**
- **In brackets after the verdict:** how sure. strong = repeated starts or a live A/B with a range; medium = about 3 against 2, or one clear mechanism; weak = one or two starts, an old build or another setup; source = read in the source.
- **Evidence** names the batch or run and the build. Batch and run names point to the owner's run log; the runs that are public are in `runs/`. Builds T42 to T112 ran other play settings (frame ahead on in many), so an old result is a lead, not a fact about v4.0.
- **Date** is the day of the result. For lines with nothing but run counts it is 18 Nov, the day the ledger last read every run.
- **Store** = setting or removing the line changes the shader store's name (it is in the core's TranslationSwitches list, read the way the control uses it: with the source stamp on, which leaves out `EDEN_NX2_TRANSCODE_WAIT` and `EDEN_NX2_PRELOAD_ALL_PIPELINES`; the source stamp line itself changes the name). One line outside that list is marked too: `EDEN_UP_CANONICAL_KEYS` adds " canonical1" to the stamp itself.
- **Source facts** (store names, "repeats the default", reach notes) were read in the T197M tree. The control ran on T186 (the alpha), T191 and T196 too; a source fact should be checked again on the build a batch uses.
- `=0` lines (`EDEN_NX2_OOT_VISUAL_WORKAROUND`, `EDEN_NX2_DOWNLOAD_GUARDS`, `EDEN_NX2_QUERY_KEEP_PENDING`, `EDEN_NX2_RESNAPSHOT`): removing the line returns it to the build's default. For the visual workaround that default is on (source comment); for the other three the default was not checked.
- **The runner adds its own lines** (boot and script lines) to the env.txt of every scripted start: batch B's controls had 173 lines, held128's 172. Only the 171 lines above are the control.

## The lines

### JIT (8)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_JIT_CACHE_MIB=256,192,192` | Size of each guest core's JIT code cache (256, 192, 192 MiB). | unknown (weak) | run210 (T51, 846 s): the caches filled only 64 to 144 MiB, so the cap was never reached in a scripted run | 2026-11-07 | reach first | - |
| `EDEN_JIT_TABLE=1` | JIT: block lookups for indirect jumps go through a table. | kept: helps (weak) | ovl-4 (T107, 2 starts off): 2 to 3 fps slower in the 30 to 35 fps stretch after the fly-over, the same in the fly-over; +2 fps walking as part of the JIT set (t61-l) | 2026-11-10 | weak verdict | - |
| `EDEN_JIT_FCMP_ADC=1` | One of the JIT code generation options (float compare flags). | kept: helps, as a group of 5, never alone (weak) | only as the JIT set of five: +2 fps walking (t61-l, T61); the flashes seen with the set were gone once frame wait was on (t64); never alone | 2026-11-08 | weak verdict | - |
| `EDEN_JIT_CHECKBIT_FLAGS=1` | One of the JIT code generation options (bit-test flags). | kept: helps, as a group of 5, never alone (weak) | only as the JIT set of five: +2 fps walking (t61-l, T61); never alone | 2026-11-08 | weak verdict | - |
| `EDEN_JIT_FREE_MOVES=1` | One of the JIT code generation options (a register placement choice; off is upstream's spill). | kept: helps, as a group of 5, never alone (weak) | only as the JIT set of five: +2 fps walking (t61-l, T61); never alone | 2026-11-08 | weak verdict | - |
| `EDEN_JIT_R13=1` | One of the JIT code generation options (one of a set of six). | kept: helps, as a group of 5, never alone (weak) | only as the JIT set of five: +2 fps walking (t61-l, T61); never alone | 2026-11-08 | weak verdict | - |
| `EDEN_JIT_PAGE_REUSE=1` | JIT: reuses code pages (works only with EDEN_JIT_TABLE). | unknown (weak) | ovl-4 (T107, one start off): the same speed in both stretches | 2026-11-10 | weak verdict | - |
| `EDEN_JIT_DISPATCH_BITS=16` | A smaller JIT lookup table per core (16 bits: about 90 MiB saved). | never tested alone | 16 never compared; =18 rode in a group of safety lines once (t73-r F1, one start) | 2026-11-08 | screen | - |

### buffer cache (6)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_NX2_BC_COLLECT_MIB=256` | The buffer collector starts deleting buffers no draw used once buffers pass 256 MiB. | unknown (weak) | run327 (T61), one start without it at a standing spot in the village: 5.7 flashes a minute against 4.5; not the flicker cause. Speed and memory not compared | 2026-11-08 | weak verdict | yes |
| `EDEN_NX2_UPLOAD_CAP_MIB=256` | Caps one upload request at 256 MiB (run149 crashed on a 3.3 GB request). | never tested alone | on in about 1,850 runs, never on and off apart; a guard | 2026-11-18 | screen | yes |
| `EDEN_NX2_DOWNLOAD_GUARDS=0` | =0 turns off the guards around GPU-to-guest downloads. | never tested alone | only =2 was tried: both starts crashed at about 86 s (run319/320, T61); 0 against unset never compared | 2026-11-08 | screen | yes |
| `EDEN_UP_FRITCHII_USAGE_TRACKER=1` | The usage tracker fills only the pages outside the run it already knows. | kept: helps (strong) | T120 live plan in the village: +1.45 fps (95 % range +1.02 to +1.87, 6 of 6 pairs); a second spot +0.60 (p 0.03) | 2026-11-11 | skip | - |
| `EDEN_STREAM_RING_MIB=64` | Size of the stream upload ring (64 MiB instead of 128). | never tested alone | never on and off apart on this game; one crash in another game at the time (run85, T23), not explained | 2026-11-06 | screen | yes |
| `EDEN_UP_FRITCHII_GRHAND=1` | A guest read whose cache locks stay taken is handed to the GPU side as a flush. | never tested alone | never on and off apart ('untested, caution' since T83) | 2026-11-09 | screen | yes |

### command lists (4)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_NX2_FETCH_COUNT=1` | Counts where each command entry's words came from; also turns off one async copy path. | never tested alone | on in about 1,630 runs, never on and off apart; a shader store name | 2026-11-18 | screen | yes |
| `EDEN_NX2_DMA_SNAPSHOT=1` | Macro reads of memory that was already flushed skip the wait for the GPU side. | kept: helps (medium) | live A/B at a standing spot in the village: off is 1.28 fps slower (95 % range 0.91 to 1.65, p 0.008); t74-d (T74, full frame wait): the same speed as the control, and the reason file says alone it shows no fps while another wait dominates | 2026-11-08 | skip | yes |
| `EDEN_GBB_TRUST_COPY=1` | Command entries the CPU wrote use their saved copy also when resumed (with EDEN_NX2_RESNAPSHOT=0). | unknown (weak) | only measured in a set of five that had frame ahead on (t85-i: +17 %); frame ahead is off in v4.0, so nothing stands for it now | 2026-11-09 | screen | - |
| `EDEN_NX2_RESNAPSHOT=0` | =0: no fresh copy of a command list at resume. | kept: needed for EDEN_GBB_TRUST_COPY | the trust-copy patch needs it; screen the two as one member | 2026-11-18 | screen | yes |

### driver (1)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `RADV_PS5_SUBMIT_THREAD=1` | The graphics driver hands work to the GPU on a thread of its own. | no effect seen (medium) | t85-e (T85, full frame wait): 15.8, 15.5, 15.7 against 15.3 and 15.6; T57b 2 against 2 the same | 2026-11-09 | skip | - |

### driver cache (7)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_UP_DRIVER_CACHE_EVERY=1024` | The driver's pipeline cache is written in play only every 1024 new pipelines. | never tested alone | never on and off apart. Reached in GrowingBlackBeans' warm field starts (T186, handheld, 19 Nov): one write of 1,031 to 1,047 pipelines, 1.4 to 1.5 s, at 161 to 183 s, inside the load at the gate, in all four warm field controls and both L1 starts. Not reached in play in our starts on T197M with the full prepared store (reach read, 19 Nov, 12 controls: 2 pipelines built in play; batch C, 42 of 42 starts: only the boot write, 99 MiB, 0 pipelines counted). Build and store were not told apart; whether it acts likely depends on the cache a start begins with. Screen it as a load question (load_s), 6 or more starts with it off | 2026-11-19 | screen | - |
| `EDEN_UP_CACHE_KEEP_GOOD=1` | A failed pipeline cache write no longer deletes the whole cache file. | never tested alone | on in about 570 runs, never on and off apart; a guard | 2026-11-18 | screen | - |
| `MESA_SHADER_CACHE_MAX_SIZE=8G` | Size cap of the driver's disk shader cache (8 GB). | never tested alone | every run that sets it sets 8G; never on and off apart (GrowingBlackBeans' screen of 17 Nov) | 2026-11-17 | screen | - |
| `RADV_PS5_DISK_CACHE_SKIP_KNOWN=1` | The driver's disk cache drops a write it already holds before compressing it. | never tested alone | on in about 540 runs, never on and off apart | 2026-11-18 | screen | - |
| `RADV_PS5_DISK_CACHE_PUT_NEW=2` | Objects go to the driver's disk cache only when they are new. | never tested alone | on in about 540 runs, never on and off apart | 2026-11-18 | screen | - |
| `RADV_PS5_DISK_CACHE_ZLIB_LEVEL=1` | Compression level of the driver's disk cache (1, the fastest). | never tested alone | on in about 540 runs, never on and off apart | 2026-11-18 | screen | - |
| `RADV_PS5_DISK_CACHE_DRAIN_EXIT=5` | At exit, the driver's disk cache queue is drained for at most 5 s. | never tested alone | on in about 540 runs, never on and off apart; acts at exit only | 2026-11-18 | screen | - |

### driver: compiler (1)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_NX2_RADV_COPY_PROP_FREE=1` | The shader compiler frees a finished branch's working arrays. | kept: helps (medium) | T144 (13 Nov): the eight heavy mesh compiles at the first door took up to 909 MB each without it, 78 to 89 MB with it, same picture; 2 of 2 scripted first starts got into the village | 2026-11-13 | skip | - |

### driver: mesh (3)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_NX2_RADV_MESH_COMPUTE=1` | The graphics driver runs mesh shaders as compute shaders. | never tested alone | on in about 1,810 runs, never on and off apart; off may change what is drawn | 2026-11-18 | screen | yes |
| `EDEN_NX2_RADV_MESH_COMPUTE_LONE=1` | Mesh shaders with no task shader also run as compute (brings the leaves and plants back). | kept: helps (weak) | live-t47 (T47): leaves drawn with it; whole-picture dips rose with it | 2026-11-07 | weak verdict | - |
| `EDEN_NX2_RADV_MESH_COMPUTE_LATE_DEREFS=1` | The driver lowers indirect reads after optimizing, for mesh-as-compute. | never tested alone | on in about 1,790 runs, never on and off apart | 2026-11-18 | screen | - |

### frame pacing (1)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_UP_OOT_FRAME_WAIT=1` | Frame wait: every frame is waited for before the next one. | kept: helps (strong) | t64 (T64): 0 dark flashes in 7 starts against about 11 a minute; t80-f: without it 3 of 3 died at a load; t81-g: without it in play 4 of 4 desynced or hung. Costs speed (13.2 to 13.8 against 18.5 fps on T64) | 2026-11-09 | skip | - |

### game patch (5)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_NX2_OOT_MAX_RESOLUTION=1` | Game patch: the game takes its own 'dynamic resolution off' path, so it always draws at full size. | never tested alone | on in about 1,900 runs, never on and off apart; off changes what is drawn, so speed alone cannot judge it | 2026-11-18 | screen | - |
| `EDEN_NX2_OOT_DYNAMIC_FPS=1` | Game patch: the game's dynamic frame rate, set at load. | unknown (weak) | t61-i run328 (T61), one start without it: the script never saw play begin; why was not checked | 2026-11-08 | screen | - |
| `EDEN_UP_OOT_NATIVE_ZSTD=1` | The game's unpacking calls run on the host's zstd. | no effect seen (medium) | t85 live A/B at a standing spot: -0.11 fps (95 % range -0.22 to +0.01); t81-c one start 14.0 against 14.1. Load times not measured | 2026-11-09 | skip | - |
| `EDEN_UP_OOT_FAST_LOOKUP=1` | Game patch: two byte-by-byte name compares become 8 bytes a step. | unknown (weak) | t81-c (T81): one start, 13.9 against 14.1, no crash | 2026-11-09 | screen | - |
| `EDEN_UP_OOT_POLL_BACKOFF=1` | Game patch: the resource request thread sleeps after a check that changed nothing. | unknown (weak) | t81-c (T81): one start, 14.3 against 14.1, no crash | 2026-11-09 | screen | - |

### loading (2)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_UP_NUP_LAZY_DECODE=1` | Compressed game files are unpacked only as far as reads reach. | kept: helps (weak) | t77-v (T77, title movie): movie starts about 3 s sooner; logo stutter the same | 2026-11-08 | weak verdict | - |
| `EDEN_NUP_CACHE_MIB=32` | Caps the cache of unpacked game files at 32 MiB (512 without it). | never tested alone | on in about 1,810 runs, never on and off apart | 2026-11-18 | screen | - |

### memory: GPU lists (1)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_NX2_NO_UPLOAD_STORE=1` | Native channels stop keeping a list of their uploads. | kept: helps (weak) | T49 logs: without it the list only grows, 96 MiB at 13 min | 2026-11-07 | weak verdict | yes |

### memory: drain (3)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_UP_PRESSURE_DRAIN=1` | While the pool is short, the recording thread submits, waits up to 80 ms and destroys deleted buffers. | never tested alone | never on and off apart; batch B (19 Nov) tested EDEN_UP_DRAIN_TO_POOL on top of it, not it | 2026-11-18 | screen | - |
| `EDEN_UP_PRESSURE_DRAIN_PENDING_MIB=256` | The drain starts once 256 MiB of deleted buffers are waiting. | never tested alone | never on and off apart; tunes the line above | 2026-11-18 | screen | - |
| `EDEN_UP_DRAIN_AT_AREA=1` | An area change drains at once and opens a 20 s window of eager drains. | never tested alone | on in about 530 runs, never on and off apart | 2026-11-18 | screen | - |

### memory: driver (3)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_PS5_LAZY_PRESENT=1` | The images for showing a frame are made when first needed, not up front. | never tested alone | on in about 1,850 runs, never on and off apart | 2026-11-18 | screen | yes |
| `EDEN_VMA_BLOCK_MIB=8` | The driver's memory allocator uses 8 MiB blocks (fewer holes). | kept: helps (weak) | t105-b (T105, memory hog test, one start): lasted 23 s of play against 9 and 3 s for the controls | 2026-11-10 | weak verdict | yes |
| `RADV_PS5_INTERNAL_RESERVE_MIB=64` | Holds 64 MiB of the pool for the driver's own small buffers. | unknown (weak) | T185 load rounds: the reserve served once (256 KiB), otherwise never; no sign yet that it saves a start | 2026-11-14 | reach first | - |

### memory: guards (2)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_UP_GPU_BADALLOC_BACKSTOP=1` | An out-of-memory error in one GPU engine call is caught and counted instead of ending the session. | never tested alone | on in about 500 runs, never on and off apart; a guard | 2026-11-18 | screen | - |
| `EDEN_UP_VK_OOM_RETRY=5` | A descriptor pool the driver refuses is asked for again, up to 5 times. | unknown (weak) | T185 load rounds: it never ran (no retry line); a guard | 2026-11-14 | reach first | - |

### memory: guest reserve (3)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_GUEST_RESERVE_FLOOR=32` | The floor of the guest memory reserve that can be lent out. | never tested alone | on in about 1,810 runs, never on and off apart | 2026-11-18 | screen | - |
| `EDEN_JIT_RESERVE_LEND=1` | A JIT code piece the pool refuses is lent from the reserve instead of ending the session. | never tested alone | on in about 1,810 runs, never on and off apart; a guard | 2026-11-18 | screen | - |
| `EDEN_UP_JIT_LEND_UNDER_FLOOR=2` | A JIT code block the pool refuses comes out of the guest reserve, down to 16 blocks. | never tested alone | on since T132, never on and off apart; a guard | 2026-11-12 | screen | - |

### memory: guest swap (9)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_GUEST_SWAP=3` | Packs guest memory that has not been touched for a while into compressed slots (mode 3). | never tested alone | on in about 1,840 runs, never on and off apart | 2026-11-18 | screen | - |
| `EDEN_GUEST_SWAP_AHEAD_MIB=12288` | Packs cold slots early while the pool's largest free block is under this size (12288 MiB). | kept: needed for firmware 13.x, as 2048 (medium) | off never run; at 12288 (the control's value) never on and off apart on our firmware. Firmware 13.x, GrowingBlackBeans (16 and 17 Nov, alpha T186, 13.60, handheld, cold first start): 12288 missed the house door in 3 of 3 starts, the frame rate falling to 8 to 17 fps across the door step, against 1 of 10 controls at 2048 (Fisher's exact, one-sided, about 1.4 %; the third 12288 start ran route v7, not v6; runs/GrowingBlackBeans/ runSW1-failure, runSW1-failure2, runSW1 against the runCC series). So a 13.x control runs 2048, not the 12288 listed here, and phase 4 on 13.x skips this line. Older: 2048 on our firmware, 332 s, no crash, same speed (run205, T51, one start) | 2026-11-17 | screen | - |
| `EDEN_GUEST_SWAP_RECLAIM=1` | With guest swap on, memory in packed slots is taken back when the pool is short. | never tested alone | on in about 1,810 runs, never on and off apart | 2026-11-18 | screen | - |
| `EDEN_NX2_CRAM_RESERVE_MIB=256` | Size of a memory reserve held back in blocks (256 MiB; 128 before). | kept: helps (weak) | t66-c (New Game): 256 got through 5 min 4 of 4; the 128 control ran out of GPU memory at 29 s (one control); off never run | 2026-11-08 | weak verdict | - |
| `EDEN_GUEST_SWAP_COLD_S=15` | Guest memory untouched this many seconds (15) counts as cold and can be packed. | never tested alone | 15 never compared; only =90 was tried: ran out of memory 123 s after launch (hand run, T54) | 2026-11-08 | screen | - |
| `EDEN_UP_PACK_PRESSURE_MS=250` | Every 250 ms while the pool is short, cold guest memory is packed. | unknown (weak) | t105-a (T105, one start, with other packing lines): freed 410 MiB but less came back in the end (424 against 547 MiB) and three times as much came back in (thrash); speed the same. The later tuning lines below never compared | 2026-11-10 | screen | - |
| `EDEN_UP_PACK_PRESSURE_MIB=2560` | That packing starts when the largest free block is under 2560 MiB. | no effect seen (source) | the line repeats the default (2560, source comment in the T197M front), so removing it changes nothing | 2026-11-19 | skip | - |
| `EDEN_UP_PACK_PRESSURE_COLD_S=4` | Slots untouched for 4 ticks of 2 s count as cold for that packing. | no effect seen (source) | the line repeats the default (4, source comment in the T197M front), so removing it changes nothing | 2026-11-19 | skip | - |
| `EDEN_UP_PACK_ON_REFUSAL=1` | When memory is refused, cold guest memory is packed at once to make room. | unknown (weak) | t105-a (T105, one start): fired once, after the script; refusals 5 against 15 | 2026-11-10 | screen | - |

### memory: heap (5)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_HEAP_KEEP_ARENAS=1` | The heap keeps memory it has freed instead of handing it back. | unknown (weak) | t51-a run202/203 (T51), one start each: largest free block at the end 878 MiB without it, 623 with it; that reason was later marked disproven, nothing since | 2026-11-07 | screen | - |
| `EDEN_KERNEL_RESOURCE_MIB=8` | Backs only 8 MiB of the game's kernel resource with real memory; the game still sees the full size. | never tested alone | on in about 1,810 runs, never on and off apart | 2026-11-18 | screen | - |
| `EDEN_GMMU_SPARSE=1` | The GPU page table's states sit in a sparse list instead of one big array. | never tested alone | on in about 1,810 runs, never on and off apart | 2026-11-18 | screen | yes |
| `EDEN_MEMORY_REPORT_THREAD=1` | Memory reports and the heap trim run on their own thread, not the graphics thread. | never tested alone | on since T51, never on and off apart | 2026-11-07 | screen | - |
| `EDEN_UP_HEAP_RESCUE=1` | A heap request about to be refused is asked of every heap arena first. | unknown (weak) | never acted in the 6 starts that set it (T88 to T104: no count line) | 2026-11-10 | reach first | - |

### memory: load window (8)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_UP_GPU_READ_THROUGH=2` | The GPU side reads guest memory directly when a block is missing (=2: only inside load windows here). | kept: helps, as a group of 7, never alone (medium) | as the load-window group of seven: T185, frame ahead off, 6 of 6 through the load from the field and the graphics thread never waited; =2 on all the time (T184, 4 starts) cost 4 to 6 fps after the field | 2026-11-14 | skip | - |
| `EDEN_UP_FAULT_RESERVE=1` | A memory fault on the GPU threads may use a reserve. | kept: helps, as a group of 7, never alone (medium) | as the load-window bundle: see EDEN_UP_GPU_READ_THROUGH (T185, 6 of 6); not cleared on its own | 2026-11-14 | skip | - |
| `EDEN_UP_FAULT_LAST_TRY=1` | A last try to save a memory fault before giving up. | kept: helps, as a group of 7, never alone (medium) | as the load-window bundle: see EDEN_UP_GPU_READ_THROUGH (T185, 6 of 6); not cleared on its own | 2026-11-14 | skip | - |
| `EDEN_UP_GPU_READ_THROUGH_LOADS=1` | Opens the read-through window only during loads. | kept: helps, as a group of 7, never alone (medium) | as the load-window bundle: T185, 6 of 6 through, fps 45 to 70 s after the load level with the control | 2026-11-14 | skip | - |
| `EDEN_UP_GPU_READ_THROUGH_LOADS_MIB=256` | Size setting of the load window (256 MiB). | kept: helps, as a group of 7, never alone (medium) | as the load-window bundle: see EDEN_UP_GPU_READ_THROUGH (T185) | 2026-11-14 | skip | - |
| `EDEN_UP_GPU_READ_THROUGH_LOADS_HOLD_MIB=2` | Hold setting of the load window (2 MiB). | kept: helps, as a group of 7, never alone (medium) | as the load-window bundle: see EDEN_UP_GPU_READ_THROUGH (T185) | 2026-11-14 | skip | - |
| `EDEN_UP_GPU_READ_THROUGH_LOADS_WAIT_MS=250` | Wait setting of the load window (250 ms). | kept: helps, as a group of 7, never alone (medium) | as the load-window bundle: see EDEN_UP_GPU_READ_THROUGH (T185) | 2026-11-14 | skip | - |
| `EDEN_UP_GPU_READ_THROUGH_LOADS_CLOSE_S=10` | The load window closes after 10 quiet seconds. | kept: helps (medium) | T185: with 10 the window shut after the black in 6 of 6; with the default 30, 9.0 to 10.9 fps after the load against 14.3 | 2026-11-14 | skip | - |

### memory: loads (9)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_AREA_CHANGE_SCRATCH_RELEASE=1` | At an area change, old scratch memory is freed before the larger new one is made. | never tested alone | on in about 1,850 runs, never on and off apart | 2026-11-18 | screen | - |
| `EDEN_UP_HEAP_HOLD_AT_LOAD=20` | Holds heap memory back through an area load (the unit of the 20 was not checked). | never tested alone | on in about 530 runs, never on and off apart | 2026-11-18 | screen | - |
| `EDEN_UP_RESERVE_TABLES=1` | The texture and buffer caches' slot tables are made at full size at boot. | never tested alone | on in about 530 runs, never on and off apart | 2026-11-18 | screen | - |
| `EDEN_UP_LOAD_HOLD=8000` | The game's load call sleeps for up to 8 s while the front frees memory. | never tested alone | on in about 500 runs, never on and off apart | 2026-11-18 | screen | - |
| `EDEN_UP_LOAD_HOLD_FREE_MIB=2200/512` | That hold ends once 2200 MiB are free with a 512 MiB largest block. | no effect seen (source) | the line repeats the default (2200/512, source comment in the T197M front); raised to 2700/512 it brought no gain and both starts crashed (T185, 14 Nov) | 2026-11-19 | skip | - |
| `EDEN_UP_TABLE_RESERVE=8` | Keeps 8 blocks in reserve for page table growth. | never tested alone | on in about 500 runs, never on and off apart | 2026-11-18 | screen | - |
| `EDEN_UP_HEAP_HOLD_REFILL_MIB=96` | How much the heap hold refills (96 MiB). | never tested alone | on in about 500 runs, never on and off apart; tunes the heap hold | 2026-11-18 | screen | - |
| `EDEN_UP_HEAP_HOLD_SPARE_MIB=64` | How much the heap hold keeps spare through a load (64 MiB). | never tested alone | on in about 500 runs, never on and off apart; tunes the heap hold | 2026-11-18 | screen | - |
| `EDEN_UP_DMA_SCRATCH_MIB=11` | Reserves 11 MiB each of read and write scratch for the copy engine. | never tested alone | on in about 500 runs, never on and off apart | 2026-11-18 | screen | - |

### memory: waits (6)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_UP_HEAP_WAIT_MS=2000` | Pipeline builder threads wait up to 2 s for heap memory instead of failing. | kept: helps (medium) | t100-c2 (T104 to T112, heap starve test): 3 of 3 through with it; without it a crash 6 s after start; speed the same (18.3 against 18.5) | 2026-11-10 | skip | - |
| `EDEN_UP_GUEST_WRITE_WAIT_MS=10000` | How long a game write that needs a memory block waits (10 s). | never tested alone | on since T130, never on and off apart. Batch A (19 Nov, docked): every game-side crash came right after a 10 s memory wait ran out; which line sets those 10 s was not checked | 2026-11-19 | screen | - |
| `EDEN_UP_JIT_COMMIT_WAIT_MS=10000` | How long a CPU core waits for more JIT code cache (10 s). | never tested alone | on since T130, never on and off apart | 2026-11-11 | screen | - |
| `EDEN_UP_NEW_WAIT_MS=2000` | A refused memory request is retried for up to 2 s. | never tested alone | on since T130, never on and off apart | 2026-11-11 | screen | - |
| `EDEN_UP_BLOCK_WAIT_TRIM=1` | While a game write waits for a free block, the heap's empty space goes back to the pool. | never tested alone | on in about 570 runs, never on and off apart (GrowingBlackBeans' screen of 17 Nov) | 2026-11-17 | screen | - |
| `EDEN_UP_WAIT_RECLAIM=1` | A thread that waits for memory while no frame is drawn gets an emergency cleanup pass. | no effect seen (weak) | T184 (14 Nov, 12 starts at the load from the field): 12 of 12 through, but no pass the graphics thread asked for came in time, so it is not what kept them alive | 2026-11-14 | weak verdict | - |

### movies (7)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_UP_VDEC_BUSY=1` | The video decoder refuses input while busy and keeps the refused packet; the main movie fix. | kept: helps (weak) | t73-m1 (T73, title movie): first 10 s took 10.7 s against 23.3 s; t74-n (New Game movie) in sync. One start per step | 2026-11-08 | weak verdict | - |
| `EDEN_UP_FS_NO_THROTTLE=1` | No 40 MB/s read throttle for the game's files. | kept: helps, added stepwise in a set, never alone (weak) | t73-m1 (T73): small on its own, kept in the movie set; one start per step | 2026-11-08 | weak verdict | - |
| `EDEN_UP_AM_THREADS=1` | Two extra host threads for a system service, so video and sync no longer wait behind the screen refresh. | kept: helps, added stepwise in a set, never alone (weak) | t73-m1 (T73): with the two lines above, 4.0 s behind instead of 5.9 s, clean quit in 5 of 5; one start per step | 2026-11-08 | weak verdict | - |
| `EDEN_UP_MOVIE_PACE=1` | Movies drop late frames to stay in time. | kept: helps, added stepwise in a set, never alone (weak) | t73-m1 (T73): movie 1 exactly in sync with the set; one start per step | 2026-11-08 | weak verdict | - |
| `EDEN_UP_MOVIE_CLOCK=1` | Keeps the movie clock from running ahead. | kept: helps, added stepwise in a set, never alone (weak) | t73-m1 (T73): all four movies at 1.00x with the set; one start per step | 2026-11-08 | weak verdict | - |
| `EDEN_NX2_AV1_THREADS=8` | Threads for the movie (AV1) decoder. | never tested alone | on in about 610 runs, never on and off apart; acts only in movies | 2026-11-18 | screen | yes |
| `EDEN_NX2_AV1_FRAME_DELAY=4` | Frame delay of the movie decoder. | never tested alone | on in about 610 runs, never on and off apart; acts only in movies | 2026-11-18 | screen | yes |

### picture (6)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_NX2_OOT_VISUAL_WORKAROUND=0` | =0 turns off the fog and exposure shader workaround that is on by default. | never tested alone | set in about 1,860 runs, never on and off apart; off changes the picture | 2026-11-18 | screen | yes |
| `EDEN_NX2_ZPASS_PAUSE=1` | Pauses the occlusion counter at submission; removes the white and gold flashes. | kept: helps (weak) | hand-0927, hand-0848, hand-1054 (T49): flashes gone with it; may cost about 4 fps (routes differed) | 2026-11-07 | weak verdict | yes |
| `EDEN_UP_BLIT_EDGE_CLAMP=1` | Image copies clamp to the edge instead of a white border (the title screen's white frame). | kept: helps (medium) | t79-y (T79, title movie, 2 with against 2 without, edge measure): the white border gone, no fps cost | 2026-11-09 | skip | yes |
| `EDEN_GBB_NAN_GUARD=1` | Shaders: colour outputs never carry NaN. | kept: helps, as a group of 2, never alone (weak) | as a pair with the line below: t112-n (T112, frame ahead on, 3 against 3): the bright glitch in 3 of 3 controls, 0 of 3 with the pair; same speed. Frame ahead is off now | 2026-11-10 | weak verdict | yes |
| `EDEN_GBB_POSITION_INVARIANT=1` | Shaders: positions are computed the same way every time. | kept: helps, as a group of 2, never alone (weak) | as a pair with the line above: see there (t112-n) | 2026-11-10 | weak verdict | yes |
| `EDEN_NX2_MASK_UNWRITTEN=1` | Colour targets the shader never writes are masked off. | no effect seen (weak) | batch k (T42): no gain; replaced later by a finer switch | 2026-11-06 | weak verdict | yes |

### pipelines (18)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_NX2_PIPELINE_FAIL_SOFT=1` | A pipeline build that runs out of memory fails on its own instead of ending the session (after run 61 died that way). | never tested alone | on in about 1,930 runs, never on and off apart; a guard: judge it by its fire line, not speed | 2026-11-18 | screen | yes |
| `EDEN_NX2_PIPELINE_WORKERS=2` | How many threads build pipelines (2). | never tested alone | at 2 never compared; older values only (hand-1013, live-t50: not enough alone for the cold crashes then) | 2026-11-07 | screen | yes |
| `EDEN_GBB_PIPELINE_SAVE_20S=1` | Saves the list of used pipelines every 20 s while it grows, off the graphics thread. | kept: needed for keeping the used-pipeline list fresh (weak) | log read of 8 Nov: without it short test sessions push play pipelines out of the list and they are rebuilt in play; no on and off start | 2026-11-08 | weak verdict | yes |
| `EDEN_UP_SHADER_PREP=1` | Shaders are prepared before play and kept in a store. | kept: helps (medium) | t85-c (T85, cold boots): pipeline builds 3.7 against 12.3 s a minute (-70 %), worst frame about 1.05 against 4.2 s | 2026-11-09 | skip | - |
| `EDEN_UP_PREP_UNREAD_HANDLE=1` | A kept shader that never read a texture handle is not thrown out for it (saves a 26 to 96 ms rebuild). | never tested alone | on since T129, never on and off apart | 2026-11-11 | screen | - |
| `EDEN_PIPELINE_MEMORY_GATE_MIB=1024` | Pipeline builds take turns while the largest free block is under 1024 MiB. | never tested alone | on in about 640 runs, never on and off apart | 2026-11-18 | screen | - |
| `EDEN_PIPELINE_MEMORY_GATE_MS=2000` | How long a build waits for its turn at that gate (2 s). | never tested alone | on in about 590 runs, never on and off apart; tunes the line above | 2026-11-18 | screen | - |
| `EDEN_NX2_GRAPHICS_PIPELINE_OOM_RETRY=1` | A pipeline build that runs out of memory asks for 16 MiB back and tries once more. | unknown (weak) | never acted: no pipeline build failed in the watched T121 start; a guard | 2026-11-11 | reach first | - |
| `EDEN_NX2_PRELOAD_ALL_PIPELINES=1` | Builds every cached graphics pipeline at boot, not only the used list (about 789 more, about 350 MB of driver memory). | no effect seen (weak) | t77-p (T77): the title-logo stutter the same with it; costs the memory above until eviction at about 150 to 190 s | 2026-11-08 | weak verdict | - |
| `EDEN_PIPELINE_MEMORY_GATE_WORKERS=1` | Our own addition to that memory gate (=1); by its notes it acts only with the gate's mark and with EDEN_UP_HEAP_WAIT_MS. | never tested alone | on in about 620 runs, never on and off apart; tunes the gate | 2026-11-18 | screen | - |
| `EDEN_UP_IR_FREE=1` | A boot pipeline build frees its shader IR before the driver compile. | no effect seen (weak) | t98-a run908/909 (T98): frees 271 MiB at 6 to 9 s, but the heap after boot and the free block are the same with or without; speed the same | 2026-11-10 | weak verdict | - |
| `EDEN_UP_IR_FREE_RUNTIME=1` | The same, for builds during play. | unknown (weak) | never acted: no pipeline was built in play in t98-a run909 | 2026-11-10 | reach first | - |
| `EDEN_UP_SHADER_REMOVAL_REFRESH=1` | After shader programs are freed, the stages are looked up again. | never tested alone | on in about 570 runs, never on and off apart | 2026-11-18 | screen | - |
| `EDEN_UP_KEEP_BOOT_PIPELINES=1` | Pipelines the boot built are not evicted before a draw has used them. | never tested alone | on in about 570 runs, never on and off apart | 2026-11-18 | screen | - |
| `EDEN_UP_KEEP_BOOT_PIPELINES_FLOOR_MIB=256` | Keeps them only while the largest free block is at least 256 MiB. | never tested alone | on in about 570 runs, never on and off apart; tunes the line above | 2026-11-18 | screen | - |
| `EDEN_UP_CANONICAL_KEYS=1` | Cached pipeline records get one canonical key (needed by the whole-game shader set). | kept: needed for EDEN_UP_FIRST_START_LIST_WRITE (weak) | EDEN_UP_FIRST_START_LIST_WRITE needs it (its notes); alone it showed no visible effect (t94-a, T94, 2 against 2: 14.1 and 15.1 against 15.1 and 14.7 fps); screen the two as one member | 2026-11-10 | screen | yes |
| `EDEN_UP_FIRST_START_LIST_WRITE=1` | Writes the pipelines a session used, in order, as key hashes (nothing reads the list yet). | never tested alone | on since T138, never on and off apart | 2026-11-12 | screen | - |
| `EDEN_UP_SHADER_PREP_SOURCE_STAMP=1` | Kept shaders survive a reinstall when the translator did not change. | never tested alone | on since T138, never on and off apart; turning it off changes the store's name (a cold first boot) | 2026-11-12 | screen | yes |

### queries (1)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_NX2_QUERY_KEEP_PENDING=0` | =0: query reports are not held back until their fence. | kept: helps (weak) | t71-f f2: 14.8 against 13.9 fps; t72-p p3: about +1 fps late in the walk, no stall at the door; one start each | 2026-11-08 | weak verdict | yes |

### shader set (5)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_UP_SHADER_SET_STREAM=1` | The shader-set extractor no longer cuts big files at 256 MiB. | unknown | by its notes it acts only with EDEN_UP_SHADER_SET, which the control does not set; per the reason file: does nothing alone; source not re-read | 2026-11-10 | reach first | - |
| `EDEN_UP_SHADER_SET_INDEX=1` | The shader-set extractor reads an index instead of every file. | unknown | by its notes it acts only with EDEN_UP_SHADER_SET, which the control does not set; per the reason file: does nothing alone; source not re-read | 2026-11-10 | reach first | - |
| `EDEN_UP_SHADER_SET_PREPASS_WORKERS=8` | Workers for preparing the shader set before the game starts. | unknown | tunes the shader-set prepass, which the control does not turn on; not checked in the source | 2026-11-18 | reach first | - |
| `EDEN_UP_SHADER_SET_COMPUTE=1` | The shader set converts compute records too. | unknown | acts inside the shader set, which the control does not turn on; not checked in the source | 2026-11-18 | reach first | - |
| `EDEN_UP_SHADER_SET_MESH=1` | The shader set converts task and mesh records too. | unknown | acts inside the shader set, which the control does not turn on; not checked in the source | 2026-11-18 | reach first | - |

### shaders: matrix (4)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_NX2_TENSOR=compact` | The game's matrix (HMMA) shader programs run through one shared software helper ('compact'). | never tested alone | on in about 1,880 runs, never on and off apart | 2026-11-18 | screen | yes |
| `EDEN_NX2_TENSOR_ONLY=c00` | Only the listed matrix program (c00) takes the software path. | never tested alone | on in about 1,880 runs, never on and off apart; works with EDEN_NX2_TENSOR | 2026-11-18 | screen | yes |
| `EDEN_NX2_TENSOR_BACKGROUND=1` | While a matrix program's pipeline is not built yet, a stand-in runs instead of waiting. | never tested alone | on in about 1,880 runs, never on and off apart | 2026-11-18 | screen | yes |
| `EDEN_NX2_NET_BARRIER=1` | Keeps a warp's shared-memory reads and writes in order in the matrix programs. | never tested alone | on in about 1,880 runs, never on and off apart | 2026-11-18 | screen | yes |

### shaders: pointers (4)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_NX2_TABLE_POOL_MIB=128` | Size of the pool for pointer tables in shaders (128 MiB instead of the 8 MiB cap). | never tested alone | off never run; only values: 192 against 128 the same speed (run233, T54); 128 kept because the game reads about 130 MiB past a pointer (upstream note) | 2026-11-08 | screen | yes |
| `EDEN_NX2_PAIRED_POINTERS=1` | Shaders bind loaded pointers that compete with a paired constant-buffer pointer. | never tested alone | on in about 1,810 runs, never on and off apart | 2026-11-18 | screen | yes |
| `EDEN_NX2_NATIVE_TABLES=1` | Pointer reads through memory tables use native pointer tracking. | never tested alone | off never run; only =compute was tried (flicker the same, hand-0947, video only); =1 is the setup of the first long hand playthrough | 2026-11-07 | screen | yes |
| `EDEN_UP_WIDE_COMPUTE_SSBOS=1` | Compute shaders get more storage buffer slots. | kept: helps (strong) | t85-d (T85), alone: 15.1, 15.4, 15.7 against 13.7 and 14.2 fps (+1.45, +10 %); with the trio runs 7 of 7 warm starts above every control | 2026-11-09 | skip | yes |

### texture cache (17)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_NX2_TRANSCODE_KEEP_MIB=32` | Keeps at most 32 MiB of decoded copies of compressed images; older ones are destroyed. | never tested alone | acts: 64 dropped by 127 s on T49 (run149, live-t49); never on and off apart | 2026-11-07 | screen | yes |
| `EDEN_NX2_TRANSCODE_WAIT=1` | A decode that finds no memory waits instead of showing black. | never tested alone | added with the line above for run149 (T35); never on and off apart | 2026-11-07 | screen | - |
| `EDEN_NX2_TC_TEMP_BUFFER_FRAMES=600` | Destroys a copy buffer that no copy used for 600 frames. | unknown (weak) | never fires: 0 'destroyed' lines in every T45 to T50 log. Old build: re-check by its line | 2026-11-07 | weak verdict | yes |
| `EDEN_NX2_TEX_TRIM_MIB=64` | Trims the top level of two big texture arrays, about 240 MiB back. | kept: helps (weak) | hand-1008-notrim (T49, video only): the picture was worse without it; =32 no gain (t83-z) | 2026-11-07 | weak verdict | yes |
| `EDEN_NX2_AREA_EVICT=40` | After a burst of new images, deletes images unused for 40 frames. | kept: helps (weak) | t59-p/q (T58, New Game route): at =120 3 of 3 through, without it 3 of 3 ran out of GPU memory at 275 to 281 s; the control's 40 was not compared with 120 | 2026-11-08 | weak verdict | yes |
| `EDEN_NX2_TC_EXPECTED_MIB=2560` | The texture cache's 'expected' memory mark (2560 MiB). | kept: helps, as a group of 2, never alone (weak) | as a pair with the line below: t73-r 0 out-of-margin lines against 3 and 5 in the controls, late fps 14.1 to 14.3 against 12.3 to 13.7; t72-p no stall at the door; one start each | 2026-11-08 | weak verdict | yes |
| `EDEN_NX2_TC_CRITICAL_MIB=3328` | The texture cache's 'critical' memory mark (3328 MiB). | kept: helps, as a group of 2, never alone (weak) | as a pair with the line above: see there (t73-r, t72-p, one start each) | 2026-11-08 | weak verdict | yes |
| `EDEN_NX2_GPU_TRANSCODE_MIB=256` | Budget for decoding the big compressed textures on the GPU (256 MiB). | no effect seen (medium) | t85-f (T85, full frame wait): 15.7, 15.4, 15.3 against 15.6 and 15.6, worst frames the same; ovl-5 (T100) the same | 2026-11-10 | skip | yes |
| `EDEN_UP_AREA_BUDGET=1` | At an area change, the image cleanup deletes about what the burst brought in. | never tested alone | on in about 640 runs, never on and off apart | 2026-11-18 | screen | - |
| `EDEN_NX2_TRANSCODE_THREADS=2` | Number of texture decode worker threads (2). | never tested alone | on in about 600 runs, never on and off apart | 2026-11-18 | screen | yes |
| `EDEN_NX2_TC_KEEP_ASYNC=120` | Keeps CPU-decoded images for 120 frames and retries a decode that found no memory. | kept: helps (weak) | t82-k (T82, docked walk) at =300: big re-decodes 3 and 2 a start down to 1, 1, 1; worst frame 448 and 243 ms down to 110 to 173. The control's 120 was not compared | 2026-11-09 | weak verdict | yes |
| `EDEN_TC_SCRATCH_KEEP_MIB=16` | Keeps at most 16 MiB of image scratch between frames (up to 64 MiB each without it). | never tested alone | on in about 590 runs, never on and off apart | 2026-11-18 | screen | yes |
| `EDEN_UP_STALE_TARGETS=1` | Deletes render targets the game has drawn over once unused for 10 frames. | never tested alone | on in about 590 runs, never on and off apart | 2026-11-18 | screen | - |
| `EDEN_NX2_DEFER_WRITEBACK_OOM=1` | An eviction whose write-back scratch cannot grow keeps the image instead of failing. | never tested alone | on in about 590 runs, never on and off apart; a guard | 2026-11-18 | screen | - |
| `EDEN_UP_SKIP_STALE_UPLOADS=1` | Skips texture uploads that are stale or wholly overwritten. | kept: helps (medium) | x3 (T107, full frame wait): 16.3, 16.2, 15.9 against 14.0 and 15.2 fps; 1 % low 88 to 90 against 181 and 96 ms; t92-a 16.6 against 13.9 | 2026-11-10 | skip | - |
| `EDEN_UP_TC_SHORT_COLLECT=1024` | With the pool short, clean idle images still go even under the collector's 1024 MiB floor. | never tested alone | on in about 570 runs, never on and off apart | 2026-11-18 | screen | - |
| `EDEN_UP_TC_OOM_SPARE_FRAMES=60` | While nothing is refused, the out-of-memory cleanup spares images used in the last 60 frames. | never tested alone | off never compared; held128 (T197M, handheld, 2 starts) set 150 instead: it acted (every count line read 150) and nothing measured moved, but the band was too wide to rule out a moderate effect | 2026-11-19 | screen | - |

### threads (3)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_PS5_PIN=pairs` | Pins guest cores to host cores in pairs. | kept: needed for EDEN_PS5_PLACE | only tested with EDEN_PS5_PLACE, which needs it; screen the two as one member | 2026-11-18 | screen | - |
| `EDEN_PS5_PLACE=CPUCore_4=0/CPUCore_0=1/CPUCore_5=2/CPUCore_1=3/CPUCore_3=4/CPUCore_2=5/GPU=6/GPUBack=8/VulkanWorker=10,11` | Places each emulator thread on a chosen host core (layout A). | unknown (weak) | T52 (runs 211 to 220): 26 once, then 22 and 18 against 22 and 22, no gain; t80-p (v2.1): 15.0 against 14.3 and 14.2, one start | 2026-11-07 | screen | - |
| `EDEN_UP_FRITCHII_WIDEAFF=1` | The game's threads may run on all six guest cores. | unknown (weak) | t83-a (T83): +0.5 fps in one start, inside the noise | 2026-11-09 | screen | - |

### upscale (2)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_NX2_UPSCALE_SAME_SIZE=1` | Upscale stand-in: a read and a store of the same size count as a pair too. | never tested alone | on in about 1,880 runs, never on and off apart | 2026-11-18 | screen | yes |
| `EDEN_NX2_UPSCALE_SQUARE=1` | Upscale stand-in: a packed-float source has each colour squared. | unknown (weak) | never fires: 0 'squares its' lines in every T45 to T50 log; it only touches the stand-in copy. Old build: re-check by its line | 2026-11-07 | weak verdict | yes |

### logs (15)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_NX2_TC_LOG=1` | Logs each texture decode the game hands off, and when it lands. | kept: needed for the test logs | log only, changes no behaviour | 2026-11-07 | skip | yes |
| `EDEN_NX2_HANG_WATCH=1` | At a GPU stall, names the work that has not finished. | kept: needed for the test logs | log only; prints only at a stall | 2026-11-07 | skip | yes |
| `RADV_PS5_MEMORY_REPORT=1` | The graphics driver prints memory reports. | kept: needed for the test logs | log only, changes no behaviour | 2026-11-07 | skip | - |
| `EDEN_NX2_JUNK_TRACE=1` | Logs what fed the first bad command entry (a crash read). | kept: needed for the test logs | log only; 0 lines in T45 to T50; its per-entry bookkeeping cost was never measured | 2026-11-07 | skip | yes |
| `EDEN_NX2_RADV_STALL_DUMP=1` | The driver dumps its state at a 3 s stall. | kept: needed for the test logs | log only; prints only at a stall | 2026-11-07 | skip | - |
| `EDEN_NX2_COND_TRACE=1` | Counts the game's render conditions. | unknown (weak) | log; 0 hits in every T45 to T50 log (the game uses none here); marked 'remove from the release' | 2026-11-07 | weak verdict | yes |
| `EDEN_GBB_FPS_5S=1` | Prints the game's frame rate every 5 s (the 'app counter' in the batch reads). | kept: needed for the test logs | log only: an fps line every 5 s | 2026-11-18 | skip | - |
| `EDEN_UP_MEM_CENSUS=1` | Memory census: who holds the memory, every 2 s while the pool is short. | kept: needed for the test logs | log only; 32 to 34 censuses a start (t102-a); no census-off control was run | 2026-11-10 | skip | - |
| `EDEN_PERF_REPORT=1` | Prints a performance report. | kept: needed for the test logs | log only | 2026-11-18 | skip | - |
| `EDEN_GPU_TIME=1` | Measures how busy the GPU is. | kept: needed for the test logs | log only; 45 to 58 % busy on T49 | 2026-11-07 | skip | yes |
| `EDEN_NX2_SPLIT_WAITS=1` | Reports where the front waits for the back. | kept: needed for the test logs | a report line (the ledger counts it as a switch); never on and off apart | 2026-11-18 | skip | yes |
| `EDEN_UP_AREA_VMA_SNAPSHOT=1` | Writes the allocator's map when over 512 MiB is unaccounted for (count only). | kept: needed for the test logs | count only, at most 3 a session | 2026-11-18 | skip | - |
| `EDEN_UP_PRESSURE_DRAIN_COUNT=1` | A refused allocation's report also names the deleted buffers still holding memory (count only). | kept: needed for the test logs | count only | 2026-11-18 | skip | - |
| `EDEN_UP_BIG_IMAGE_LOG=1` | Count lines for images of 128 MiB or more. | kept: needed for the test logs | log only | 2026-11-18 | skip | - |
| `EDEN_UP_PASSED_ACQUIRE_COUNT=1` | Counts GPU waits whose value already went by (count only). | kept: needed for the test logs | count only | 2026-11-18 | skip | - |

### test lines (2)

| Line | What it does | Verdict | Evidence | Date | Phase 4 | Store |
|---|---|---|---|---|---|---|
| `EDEN_TEST_DISCARD_SAVE=1` | Test line: the game works on a copy of its save, so a test never changes the save. | kept: needed for tests (the save is never written) | test line, not in the play settings; on in every scripted start | 2026-11-18 | skip | - |
| `EDEN_UP_FAULT_LOG=1` | Test line: times each GPU download landing in guest memory and logs the memory waits. | kept: needed for the test logs | test line, not in the play settings; the memory-wait reads of batches A, B and S need it | 2026-11-19 | skip | - |

## Where this differs from the 17 Nov list

**On GBB's list, with a verdict here (11):**

- `EDEN_GBB_FPS_5S`: kept: needed for the test logs; log only: an fps line every 5 s.
- `EDEN_PERF_REPORT`: kept: needed for the test logs; log only.
- `EDEN_NX2_SPLIT_WAITS`: kept: needed for the test logs; a report line (the ledger counts it as a switch); never on and off apart.
- `EDEN_UP_AREA_VMA_SNAPSHOT`: kept: needed for the test logs; count only, at most 3 a session.
- `EDEN_UP_PRESSURE_DRAIN_COUNT`: kept: needed for the test logs; count only.
- `EDEN_UP_BIG_IMAGE_LOG`: kept: needed for the test logs; log only.
- `EDEN_UP_PASSED_ACQUIRE_COUNT`: kept: needed for the test logs; count only.
- `EDEN_TEST_DISCARD_SAVE`: kept: needed for tests (the save is never written); test line, not in the play settings; on in every scripted start.
- `EDEN_UP_FAULT_LOG`: kept: needed for the test logs; test line, not in the play settings; the memory-wait reads of batches A, B and S need it.
- `EDEN_UP_PACK_PRESSURE_MIB`: no effect seen; the line repeats the default (2560, source comment in the T197M front), so removing it changes nothing.
- `EDEN_UP_PACK_PRESSURE_COLD_S`: no effect seen; the line repeats the default (4, source comment in the T197M front), so removing it changes nothing.

**Not on GBB's list, to screen here (35):** their SWITCHES.md line gives a result, but not for this line on and off at its control value on today's kind of setup.

- `EDEN_HEAP_KEEP_ARENAS` (unknown): t51-a run202/203 (T51), one start each: largest free block at the end 878 MiB without it, 623 with it; that reason was later marked disproven, nothing since.
- `EDEN_NX2_OOT_DYNAMIC_FPS` (unknown): t61-i run328 (T61), one start without it: the script never saw play begin; why was not checked.
- `EDEN_NX2_TABLE_POOL_MIB` (never tested alone): off never run; only values: 192 against 128 the same speed (run233, T54); 128 kept because the game reads about 130 MiB past a pointer (upstream note).
- `EDEN_NX2_TRANSCODE_KEEP_MIB` (never tested alone): acts: 64 dropped by 127 s on T49 (run149, live-t49); never on and off apart.
- `EDEN_NX2_TRANSCODE_WAIT` (never tested alone): added with the line above for run149 (T35); never on and off apart.
- `EDEN_GUEST_SWAP_AHEAD_MIB` (kept: needed for): off never run; at 12288 (the control's value) never on and off apart on our firmware. Firmware 13.x, GrowingBlackBeans (16 and 17 Nov, alpha T186, 13.60, handheld, cold first start): 12288 missed the house door in 3 of 3 starts, the frame rate falling to 8 to 17 fps across the door step, against 1 of 10 controls at 2048 (Fisher's exact, one-sided, about 1.4 %; the third 12288 start ran route v7, not v6; runs/GrowingBlackBeans/ runSW1-failure, runSW1-failure2, runSW1 against the runCC series). So a 13.x control runs 2048, not the 12288 listed here, and phase 4 on 13.x skips this line. Older: 2048 on our firmware, 332 s, no crash, same speed (run205, T51, one start).
- `EDEN_NX2_DOWNLOAD_GUARDS` (never tested alone): only =2 was tried: both starts crashed at about 86 s (run319/320, T61); 0 against unset never compared.
- `EDEN_NX2_NATIVE_TABLES` (never tested alone): off never run; only =compute was tried (flicker the same, hand-0947, video only); =1 is the setup of the first long hand playthrough.
- `EDEN_MEMORY_REPORT_THREAD` (never tested alone): on since T51, never on and off apart.
- `EDEN_JIT_CACHE_MIB` (unknown): run210 (T51, 846 s): the caches filled only 64 to 144 MiB, so the cap was never reached in a scripted run.
- `EDEN_NX2_PIPELINE_WORKERS` (never tested alone): at 2 never compared; older values only (hand-1013, live-t50: not enough alone for the cold crashes then).
- `EDEN_PS5_PLACE` (unknown): T52 (runs 211 to 220): 26 once, then 22 and 18 against 22 and 22, no gain; t80-p (v2.1): 15.0 against 14.3 and 14.2, one start.
- `EDEN_GBB_TRUST_COPY` (unknown): only measured in a set of five that had frame ahead on (t85-i: +17 %); frame ahead is off in v4.0, so nothing stands for it now.
- `EDEN_UP_PREP_UNREAD_HANDLE` (never tested alone): on since T129, never on and off apart.
- `EDEN_UP_JIT_LEND_UNDER_FLOOR` (never tested alone): on since T132, never on and off apart; a guard.
- `EDEN_GUEST_SWAP_COLD_S` (never tested alone): 15 never compared; only =90 was tried: ran out of memory 123 s after launch (hand run, T54).
- `EDEN_UP_GUEST_WRITE_WAIT_MS` (never tested alone): on since T130, never on and off apart. Batch A (19 Nov, docked): every game-side crash came right after a 10 s memory wait ran out; which line sets those 10 s was not checked.
- `EDEN_UP_JIT_COMMIT_WAIT_MS` (never tested alone): on since T130, never on and off apart.
- `EDEN_UP_NEW_WAIT_MS` (never tested alone): on since T130, never on and off apart.
- `EDEN_NX2_GRAPHICS_PIPELINE_OOM_RETRY` (unknown): never acted: no pipeline build failed in the watched T121 start; a guard.
- `EDEN_JIT_DISPATCH_BITS` (never tested alone): 16 never compared; =18 rode in a group of safety lines once (t73-r F1, one start).
- `EDEN_STREAM_RING_MIB` (never tested alone): never on and off apart on this game; one crash in another game at the time (run85, T23), not explained.
- `EDEN_UP_FRITCHII_WIDEAFF` (unknown): t83-a (T83): +0.5 fps in one start, inside the noise.
- `EDEN_UP_FRITCHII_GRHAND` (never tested alone): never on and off apart ('untested, caution' since T83).
- `EDEN_UP_OOT_FAST_LOOKUP` (unknown): t81-c (T81): one start, 13.9 against 14.1, no crash.
- `EDEN_UP_OOT_POLL_BACKOFF` (unknown): t81-c (T81): one start, 14.3 against 14.1, no crash.
- `EDEN_UP_HEAP_RESCUE` (unknown): never acted in the 6 starts that set it (T88 to T104: no count line).
- `EDEN_UP_IR_FREE_RUNTIME` (unknown): never acted: no pipeline was built in play in t98-a run909.
- `EDEN_UP_CANONICAL_KEYS` (kept: needed for): EDEN_UP_FIRST_START_LIST_WRITE needs it (its notes); alone it showed no visible effect (t94-a, T94, 2 against 2: 14.1 and 15.1 against 15.1 and 14.7 fps); screen the two as one member.
- `EDEN_UP_SHADER_SET_STREAM` (unknown): by its notes it acts only with EDEN_UP_SHADER_SET, which the control does not set; per the reason file: does nothing alone; source not re-read.
- `EDEN_UP_SHADER_SET_INDEX` (unknown): by its notes it acts only with EDEN_UP_SHADER_SET, which the control does not set; per the reason file: does nothing alone; source not re-read.
- `EDEN_UP_PACK_PRESSURE_MS` (unknown): t105-a (T105, one start, with other packing lines): freed 410 MiB but less came back in the end (424 against 547 MiB) and three times as much came back in (thrash); speed the same. The later tuning lines below never compared.
- `EDEN_UP_PACK_ON_REFUSAL` (unknown): t105-a (T105, one start): fired once, after the script; refusals 5 against 15.
- `RADV_PS5_INTERNAL_RESERVE_MIB` (unknown): T185 load rounds: the reserve served once (256 KiB), otherwise never; no sign yet that it saves a start.
- `EDEN_UP_VK_OOM_RETRY` (unknown): T185 load rounds: it never ran (no retry line); a guard.

## Candidates to take out of the control (10)

"No effect seen" rows (five old-log and one-start rows were moved to "unknown" in the second check: `EDEN_NX2_UPSCALE_SQUARE`, `EDEN_NX2_TC_TEMP_BUFFER_FRAMES`, `EDEN_NX2_COND_TRACE`, `EDEN_NX2_BC_COLLECT_MIB`, `EDEN_JIT_PAGE_REUSE`; they stay in the table under "weak verdict"). None of them should come out on this page alone: a line that showed nothing on one route can still act on another. Taking several out at once is itself one grouped test (control against control minus the set).

- `RADV_PS5_SUBMIT_THREAD=1`: t85-e (T85, full frame wait): 15.8, 15.5, 15.7 against 15.3 and 15.6; T57b 2 against 2 the same.
- `EDEN_NX2_GPU_TRANSCODE_MIB=256`: t85-f (T85, full frame wait): 15.7, 15.4, 15.3 against 15.6 and 15.6, worst frames the same; ovl-5 (T100) the same.
- `EDEN_UP_OOT_NATIVE_ZSTD=1`: t85 live A/B at a standing spot: -0.11 fps (95 % range -0.22 to +0.01); t81-c one start 14.0 against 14.1. Load times not measured.
- `EDEN_NX2_MASK_UNWRITTEN=1`: batch k (T42): no gain; replaced later by a finer switch.
- `EDEN_NX2_PRELOAD_ALL_PIPELINES=1`: t77-p (T77): the title-logo stutter the same with it; costs the memory above until eviction at about 150 to 190 s.
- `EDEN_UP_IR_FREE=1`: t98-a run908/909 (T98): frees 271 MiB at 6 to 9 s, but the heap after boot and the free block are the same with or without; speed the same.
- `EDEN_UP_PACK_PRESSURE_MIB=2560`: the line repeats the default (2560, source comment in the T197M front), so removing it changes nothing.
- `EDEN_UP_PACK_PRESSURE_COLD_S=4`: the line repeats the default (4, source comment in the T197M front), so removing it changes nothing.
- `EDEN_UP_LOAD_HOLD_FREE_MIB=2200/512`: the line repeats the default (2200/512, source comment in the T197M front); raised to 2700/512 it brought no gain and both starts crashed (T185, 14 Nov).
- `EDEN_UP_WAIT_RECLAIM=1`: T184 (14 Nov, 12 starts at the load from the field): 12 of 12 through, but no pass the graphics thread asked for came in time, so it is not what kept them alive.

## Tested this week, outside the control

Not control lines, so not in the table; here so nobody queues them again by mistake. Each is a read with its second check applied.

- `EDEN_NX2_TC_SUPERSEDED=1` + `EDEN_UP_DRAIN_TO_POOL=1` (batch B, T191, 19 Nov): no switch start crashed (0 of 6 docked) while all 3 counted docked controls did, 2 of them in the test's own screenshot; docked memory waits never passed 3.2 s against 6.58 s or more in all 3 of this batch's controls (3 more from batch A). Inside the batch alone the crash comparison is 0 of 3 against 3 of 3, p 0.10. The pair beat `DRAIN_TO_POOL` alone on every docked load measure (3 against 3); direction only, p 0.10 two-sided; handheld the two are about level. One start with `DRAIN_TO_POOL` alone had a 10 s freeze after the load, so `DRAIN_TO_POOL` is not cleared of it; the pair had no such start in 3 docked. Handheld walk maybe 1 to 3 % slower (open). Not a crash rate yet: that needs about 15 docked starts.
- `EDEN_UP_L1639_PARK_WAIT=1` (batch A alone, batch S on top of the pair above, docked, T191): about +3.5 fps in the field (+17 %, 4 against 4 on the counter), but more and longer memory waits and one freeze in the town. Held, not added.
- held128 (T197M, handheld, 2 starts each): eight speed switches and one memory value, none outside the 12 controls on the field (the smallest change it could see was about 3 to 4 %). One crash (RN1), not tied to its switch; one hang picture in 2 of 5 JP starts, not a verdict.

## What can make a row wrong

- **An old result on another setup.** Most results come from T42 to T144, many with frame ahead on. They say what to try, not what v4.0 does.
- **A group or set result read as a single one.** Rows marked "as a group" or "stepwise" were never on and off alone.
- **A line that never acted.** A start without it shows nothing if the code never runs on the route. That is what "reach first" is for.
- **The route.** Most results are from the field route, handheld. Docked, the village and the town are other questions.
- **The source facts** were read on T197M (see How to read).
- **The cache a start begins with.** A reach note can hold on one cache state and not on another: `EDEN_UP_DRIVER_CACHE_EVERY` never writes in play in our T197M starts with the full prepared store, and writes once inside the load in GrowingBlackBeans' warm starts on T186.
- **The firmware.** A 13.x control differs from this one (`EDEN_GUEST_SWAP_AHEAD_MIB=2048`, and no `EDEN_UP_FAULT_LOG`).

Made on 19 Nov 2026 from the owner's switch ledger (18 Nov, T197M, 1,985 runs read), its reason file, the read of this week's batches and their second checks, and the T197M source, with local paths and private details taken out.
