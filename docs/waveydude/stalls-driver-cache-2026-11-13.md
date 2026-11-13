# The ~1 s stall stretches: the driver pipeline cache write (13 Nov 2026)

> **Found:** every stretch of ~1 s frames in my W-10 and W-11 runs in a later area happened while the periodic driver pipeline cache write was in flight, and ended within a few seconds of that write's log line. The file is 123 MiB; on a base PS5 near its memory limit the write took 24-55 s.
>
> **So:** 0931 (`EDEN_UP_DRIVER_CACHE_EXIT_ONLY=1`) writes it at boot and at exit only. Built as W-13, **not run yet**.

waveydude. Base PS5 13.60, my T120 hybrid, W-10 and W-11 (see `two-frame-guard-2026-11-12.md`).

## What the stalls look like

- Frames of 954-990 ms, sometimes two in a row, about one every 2 s, for 30-50 s at a time. In W-11: about 211-264 s and 419-462 s.
- The guest cores are **more** idle than in smooth play: 2-4.7 s of every 5 s against 1.4-2.3 s (`EDEN_PERF_IDLE`). The game is waiting, not working.
- Single GPU-front operations that read guest memory take 400-920 ms (`dma snapshot miss`, `list writers`, `macro dma read` longest), against a few ms in smooth play.
- The game decodes no assets in them (native zstd counters flat).
- The 15 s guest-thread dump, timed by a host thread sleeping 100 ms at a time, came up to 6 s late across them: the whole process was held up.

## What lines up

`pipeline_cache_save` in `EDEN_PERF_COST` (the 5 s report) is one call each time, logged in the window it ends in:

| Run | Slow stretch | Write began (from its length) | Write ended (log line) |
|---|---|---|---|
| W-11 | ~211-264 s | ~206 s (55.4 s) | 261.3 s |
| W-11 | ~419-462 s | ~415 s (42.1 s) | 456.8 s |
| W-10 | ~423-460 s | ~433 s (23.9 s) | ~457 s |

`QueueVulkanPipelineCacheFlush` writes the whole driver cache every 128 new pipelines, at most every 30 s (or a second per MiB): `vkGetPipelineCacheData` into one buffer, a file beside the cache, a rename. A new area builds pipelines, so it comes in new areas. Vampinity's hint (look for first-time shader work in each stall's window) is what pointed here.

## Ruled out

| Suspect | Why not |
|---|---|
| Memory waits (`EDEN_UP_NEW_WAIT_MS`) | None logged |
| The game unpacking assets | Native zstd counters flat in the stalls |
| Cold memory hints | `HintCold` is empty on the PS5 build |
| Ocarina poll backoff | About one a second, never over 4 ms |
| Shader builds themselves | About 1 s of every 10 s in the stretches |

Not ruled out: how exactly the write holds everything up (the 123 MiB copy squeezing the pool, the driver's cache lock, or both). W-12's `EDEN_UP_STALL_PROBE` (not a core patch, see `patches/waveydude/README.md`) records slot lock and block waits per stall and would show the first.

## The fix and what it costs

0931: with `EDEN_UP_DRIVER_CACHE_EXIT_ONLY=1` the mid-game writes stop; boot and exit writes stay. A crash loses the driver builds made since boot, so those pipelines take their driver compile again next session. Translations (`vulkan.bin`) are a different file and are kept.

## Next

One run of W-13 (`envs/waveydude/w13-game.env.txt`, probe on) in the same later area: no stall stretches, and no `EDEN_STALL` lines, would confirm it.
