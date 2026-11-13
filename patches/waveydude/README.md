# waveydude core patches

For the Eglantine submodule, applied after Vampinity's T120 series (`tools/eglantine-patches` on `ocarina-dev-t120`), in number order, on my T120 hybrid (Build O on T120). Everything is off unless its switch is set. Source branches on `waveydude/Eglantine-PS5-`: `w11-two-frame-guard` (0927), `w12-stall-probe` (W-12), `w13-driver-cache-exit-only` (0931). Builds are labelled `W-<n>` on the HUD.

| Patch | Switch | What it does |
|---|---|---|
| 0927 | `EDEN_UP_AHEAD_TWO=1`, `EDEN_UP_AHEAD_GUARD_SLOTS=2` | Two frames in flight, each guarded. `AHEAD_TWO` (with `EDEN_NX2_FRAMES_AHEAD=1`): a present waits for the frame two back, not the previous one. `GUARD_SLOTS=2` (with `EDEN_UP_AHEAD_GUARD=1/2/3`): the copy guard gets a slot per frame in flight, copies are tagged by slot, reads take the copy of the frame the back is recording, =3 holds a write only until the back has passed the newest guarded frame. Unset: as before. Built (W-11); ran on the console (12 Nov, see `docs/waveydude/two-frame-guard-2026-11-12.md`). GrowingBlackBeans' runs: `docs/GrowingBlackBeans/two-slot-guard-2026-11-12.md`; merged with 0569 in t134-gbb2. |
| 0931 | `EDEN_UP_DRIVER_CACHE_EXIT_ONLY=1` | The driver pipeline cache (`vulkan_pipelines.bin`, 123 MiB for me) is written at boot and when the session ends, never during play. Its mid-game write ran 24-55 s on a base PS5 and lined up with every stretch of ~1 s frames I had (`docs/waveydude/stalls-driver-cache-2026-11-13.md`). In the shader-store stamp's list and its no-translation list (0926), so setting it does not start an empty store. Built (W-13); **not run yet**. |

Not a core patch: `EDEN_UP_STALL_PROBE=1` (W-12, outer repo `src/stall_probe.h` and `src/guest_memory_service.inc`): times guest-memory slot lock waits and holds and block waits by role (fault, scanner, swapper, keeper), and writes an `EDEN_STALL` line for every 100 ms+ stall with what waited or held in it. Host test `tools/test-stall-probe.cpp`. Built (W-12); not run yet.

Settings for the test: `envs/waveydude/w13-game.env.txt` (the whole per-game env, with the switches above on).

Also used, from others: `EDEN_UP_AHEAD_LOAD_WAIT=1` (in the core already) stops the title-screen freeze with two frames ahead.

- **0936** — W-19 experiment, `EDEN_NX2_GRAPHICS_PIPELINE_OOM_WAIT_RECOVERY=1`. Gives the existing graphics worker retry up to 128 ms to observe memory recovery. Off by default.
