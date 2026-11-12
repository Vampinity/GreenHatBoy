# Pipelines still built while playing (11 Nov 2026)

> **Found:** Pipelines still built while playing have two causes: the boot builds only the used list (827-1,592 of about 2,870 on disk), and shader prep refuses some pipelines, always for a texture handle.
>
> **So:** Fix the texture-handle refusal (done later as patch 0577) and decide whether to prepare more of the disk cache at boot.

Question: why does a run on the same route still build pipelines on the GPU thread that are
"on disk, not built at boot"? Analysis of our own logs only. No patch, no test started.
Script: `drafts-2026-11-11/ports/pipeline-build-all/pipeline-leftover.py <batch folders>`.
"(inference)" marks what the logs do not show directly.

## Short answer

Shader prep works for most leftover pipelines. Two things are left:

1. **The boot builds only the "used list", not the whole disk cache.** About 2,870 graphics
   pipelines are on disk. The boot builds 827-1,592 of them. A pipeline the route needs that is
   not on the list gets built on the GPU thread at first sight.
2. **Shader prep refuses some of those, and every refusal is "texture handle".** A refused
   pipeline is translated in full on the GPU thread, about 27 ms. That is the hitch. The others
   are made from the kept translation in under 1 ms each.

The key is stable. The same route on the same list builds the same hashes every run.

## Where the log lines come from (T122 source, `t122-core/src/video_core/renderer_vulkan/`)

- `vk_pipeline_cache.cpp:3036`: "Graphics pipeline built on the GPU thread in N ms: <reason> <key hash>".
  **Logged only when over 2 ms, at most 400 lines a session (line 3034).** The 10 s total line
  ("Runtime pipelines in the last 10 s", line 3040) counts all of them.
- `vk_pipeline_cache.cpp:3120-3122`: the reason. "on disk" = the key hash is in the disk cache
  (`disk_pipelines`) but was not built at boot. "new" = not on disk at all.
- `vk_pipeline_cache.cpp:2175-2181`: the boot builds a record only if its hash is on the used list
  (`!used_pipelines.contains(hash)` → skipped), unless `EDEN_NX2_PRELOAD_ALL_PIPELINES=1`.
- `vk_pipeline_cache.cpp:1041`: the used list keeps 2 sessions (`UsedPipelinesMaxAge = 2`; 8 on MoltenVK).
- `vk_pipeline_cache.cpp:1190-1201`, `2268-2273`: `EDEN_UP_PIPELINE_LIST_KEEP=1` freezes the list and
  logs "N left for their first use, M built at boot".
- `vk_pipeline_cache.cpp:3156`, `3177-3179`: at run time the kept translation is tried first. If it is
  refused, the pipeline is translated on the GPU thread as before.
- `vk_pipeline_cache.cpp:4620`: "Kept translations in the last 10 s: N pipelines made without
  translating, X ms, K refused (reason)".
- `shader_environment.cpp:1436-1454`: the two "texture handle" refusals: a handle shift of 32 or
  more, or the recorded translation did not read the words this descriptor's handle comes from.
- The log prints only the key hash. It never prints the shader hashes or the key parts.
  `EDEN_NX2_PIPELINE_DIFF=1` (`vk_pipeline_cache.cpp:2341-2391`) would print which key part differs
  for known shaders. No run of ours has it on.

## The batches (11 Nov, same script, same env apart from the script name, `EDEN_UP_PIPELINE_LIST_KEEP=1`, `EDEN_UP_SHADER_PREP=1`)

Logs in `eglantine-logs-2026-11-05/`. "Logged" = lines over 2 ms. "All" = sum of the 10 s total lines.

| Batch | Build | Boot built / left | Runs | On disk logged | On disk all | Mesh all | GPU-thread ms (all) | Prep refusals | On-disk builds over 10 ms (ms) | Worst cluster |
|---|---|---|---|---|---|---|---|---|---|---|
| 063334 stand-gate-t121 | T121 | 1,592 / 957 | 1058-1060 | 50 / 49 / 51 | 198 / 203 / 201 | 39 / 41 / 38 | 1,643 / 1,724 / 1,714 | 42 / 44 / 44 | 37-39 (1,100-1,164) | 20 builds, 590 ms |
| 105908 stand-gate-t122 | T122 | 996 / 1,865 | 1094-1096 | 19 / 23 / 21 | 125 / 125 / 123 | 39 / 39 / 37 | 616 / 665 / 620 | 12 / 14 / 12 | 8-10 (245-306) | 6 builds, 194 ms |
| 121521 stand-gate-t122 | T122 | 827 / 2,040 | 1107-1109 | 81 / 77 / 80 | 459 / 457 / 453 | 97 / 96 / 93 | 2,569 / 2,566 / 2,548 | 68 / 68 / 68 | 61 (1,846-1,873) | 20 builds, 545-553 ms |
| 131822 stand-gate-t122 | T122 | 1,253 / 1,623 | 1118-1119 | 11 / 12 | 52 / 49 | 66 / 43 | 364 / 317 | 6 / 4 | 2-4 (66-105) | 2 builds, 126 ms |

"new" was 0 in all eleven runs but one (1 in run1060).

### Overlap between runs of one batch (logged on-disk hashes)

- 063334: 44 / 43 / 46 shared pairwise of 49-51; **42 in all three**. Mesh: 16 in all three of 17-19.
- 105908: 14-17 shared of 19-23; 14 in all three. Mesh 13 in all three.
- 121521: 74-76 shared of 77-81; **73 in all three**. Mesh 16 in all three.
- 131822: 7 shared of 11/12.

The differing few are mostly cheap 2-3 ms builds near the 2 ms log cut-off (inference: in or out
of the log by timing, not a different pipeline).

### Without the frozen list (walk-hud 103108, runs 1088-1093; forest-exit-gate 125356, 1113-1117)

Each run saves the list, so the next boot builds what the run built. Result: the first run builds
many (114 on disk logged in run1088, 42 in run1113), the next runs few (2-10), and **the hashes
never repeat: 0-1 shared between any two runs**. That is the pattern the collaborator saw ("only 3
overlapped"). It does not mean the key changes: a hash built in run N goes on the list, so run N+1
builds it at boot and cannot show it again. Every one of those builds was "on disk", so its exact
key had been seen before.

## Why the same pipelines are left over

- **Frozen list (our test runs).** With `LIST_KEEP=1` the list is the one the last non-keep session
  left (a walk or play session elsewhere). The stand-gate route needs about 450-550 more on-disk
  pipelines than the list of batch 121521 had, and about 160 more than batch 105908's. The number
  depends on what ran before the batch, not on the build. Within a batch it is the same every run.
- **Two-session list (play and the collaborator's runs).** A pipeline the last two sessions did not
  use is not built. Route variation (camera, NPCs, effects) touches a few rarely used keys each run
  (inference). The kept set then grows (1030 → 1245 → 1269 in his runs) but never covers the 2,870
  on disk.
- **Unstable key part: not seen here.** Same list, same route → same hashes (42 of ~50, 73 of ~80
  in all three runs), and almost no "new". No per-boot value or address is in the key. Different
  keys for the same shaders do exist (canonical keys: 893 against 1,116 for the same content), so
  some keys are variants of one shader set (inference: these widen the pool of rarely used keys).
  `EDEN_UP_CANONICAL_KEYS` is off in all these runs.

## What the time goes on

- Prep handles most: run1108 made 485 pipelines from kept translations in 359 ms (0.7 ms each).
- The 68 refused ones cost ~1,870 ms (61 on-disk builds over 10 ms, median ~27 ms). The count of
  slow on-disk builds tracks the refusal count in every batch: 37-39 vs 42-44, 8-10 vs 12-14,
  61 vs 68, 2-4 vs 4-6, 91 vs 108 in run1088. **All 203 refusals in today's logs say "texture handle".**
- Mesh pipelines are never kept by prep (`vk_pipeline_cache.cpp:4684-4690`: task/mesh run as compute "are never kept") and are
  not built at boot without `EDEN_UP_MESH_CACHE=1`: 14-22 logged a run, 165-380 ms. The same ones
  every run (13-16 in all three).

### When (run1108, app seconds; script clock = app − 14.3)

- 84-88 s: 35 builds as the house first draws after the load.
- **93.0-93.6 s: 20 builds, 545 ms**, 1.4 s after the stick push: the start of movement. Same cluster
  at 95.2 (run1059) and 94.5 (run1060). This is the collaborator's 605 ms hitch.
- 95-104 s: ~35 builds through the door and into the fly-over (area change).
- 119-123 s: 8 builds, the fly-over's later view.

So: area changes and the first camera move, not steady play.

## What would stop them, and the cost

| Option | Stops | Cost |
|---|---|---|
| Build every on-disk pipeline at boot (`EDEN_NX2_PRELOAD_ALL_PIPELINES=1`, exists) | All "on disk" builds, but the refused ones only move to boot (boot translates them on workers) | ~2,870 graphics + ~256 compute = ~3,130 against 1,083-1,824 now. From six boots (cache load → game start: 1,083 → 8.6 s, 1,252 → 9.2 s, 1,824 → 10.4 s) about 2.5 ms a pipeline on 8 workers, so **~+3-5 s boot** (inference). Memory: not measured. Each built pipeline stays resident; the forest exit already runs at 0-16 MiB free (project log 11 Nov 05:47, 06:13). review-2026-11-07 item 20 said keep it off for memory. Needs one memory-census run before any use. |
| Keep the list longer (`UsedPipelinesMaxAge` 2 → e.g. 8) | Most stragglers in normal play, after a few sessions | Boot grows toward the union of those sessions (same ms a pipeline as above), less than build-all. Does nothing for test runs with `LIST_KEEP=1`, and nothing for refusals. |
| Make the "texture handle" check accept these cases | The ~27 ms builds, which are most of the hitch time (1.1-1.9 s of 1.6-2.6 s a run in the bad batches) | Code work in `shader_environment.cpp:1436-1454`. Risk: a wrong kept translation = wrong texture (glitch). Needs `EDEN_UP_SHADER_PREP_VERIFY` runs. Cheapest per ms saved (inference). |
| Canonical keys (`EDEN_UP_CANONICAL_KEYS=1`) | Fewer variant keys (attribute types read, blend of non-blending attachments, attachments past the last target, depth bounds; `vk_pipeline_cache.cpp:2013-2017`), so fewer rarely used keys | Does not touch the list size rule or the texture-handle refusals. Changes every hash (a new list and store on first boot). |
| Mesh cache at boot (`EDEN_UP_MESH_CACHE=1`, exists) | The 14-22 mesh builds a run (165-380 ms) | Builds all mesh records at boot; memory not measured. |
| Build on a worker, draw waits or is skipped | Moves the 27 ms off the GPU thread | Tested before as async translation (0508, `EDEN_UP_ASYNC_TRANSLATION`); earlier notes say it broke the game. A waiting draw still stalls the frame; a skipped draw is a missing object. |

## For the collaborator's question ("did shader prep not work?")

It works: of ~550 leftover pipelines in run1108, ~485 came from kept translations in under 1 ms.
What he measured are the ones prep refuses (texture handle) plus mesh pipelines, which prep never
keeps. They are the same every run on a fixed list. His "3 overlap" comes from the list saving
each run, not from a moving key.

## Notes on our own tools

- `postprocess.py` counts only the logged lines (`PIPE_BUILT`, line 176), so the card shows builds
  over 2 ms. Fine for hitches, but "on disk" in the card is 1/5 to 1/6 of the real count.
- The test numbers for first-visit stutter depend on which list the batch inherited (827-1,592 built
  at boot today). Compare stutter only within one batch.
- Next useful run (not started): one stand-gate run with `EDEN_NX2_PIPELINE_DIFF=1` to name the key
  parts of variant keys, and a log line naming the refused key hashes and which of the two
  texture-handle checks failed.
