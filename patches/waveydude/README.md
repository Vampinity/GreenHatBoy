# waveydude core patches

For the Eglantine submodule, applied after Vampinity's T120 series (`tools/eglantine-patches` on `ocarina-dev-t120`), in number order, on my T120 hybrid (Build O on T120). Everything is off unless its switch is set. Source branches on `waveydude/Eglantine-PS5-`: `w11-two-frame-guard` (0927), `w12-stall-probe` (W-12), `w13-driver-cache-exit-only` (0931). Builds are labelled `W-<n>` on the HUD.

| Patch | Switch | What it does |
|---|---|---|
| 0927 | `EDEN_UP_AHEAD_TWO=1`, `EDEN_UP_AHEAD_GUARD_SLOTS=2` | Two frames in flight, each guarded. `AHEAD_TWO` (with `EDEN_NX2_FRAMES_AHEAD=1`): a present waits for the frame two back, not the previous one. `GUARD_SLOTS=2` (with `EDEN_UP_AHEAD_GUARD=1/2/3`): the copy guard gets a slot per frame in flight, copies are tagged by slot, reads take the copy of the frame the back is recording, =3 holds a write only until the back has passed the newest guarded frame. Unset: as before. Built (W-11); ran on the console (12 Nov, see `docs/waveydude/two-frame-guard-2026-11-12.md`). GrowingBlackBeans' runs: `docs/GrowingBlackBeans/two-slot-guard-2026-11-12.md`; merged with 0569 in t134-gbb2. |
| 0931 | `EDEN_UP_DRIVER_CACHE_EXIT_ONLY=1` | The driver pipeline cache (`vulkan_pipelines.bin`, 123 MiB for me) is written at boot and when the session ends, never during play. Its mid-game write ran 24-55 s on a base PS5 and lined up with every stretch of ~1 s frames I had (`docs/waveydude/stalls-driver-cache-2026-11-13.md`). In the shader-store stamp's list and its no-translation list (0926), so setting it does not start an empty store. Built (W-13); **not run yet**. |

Not a core patch: `EDEN_UP_STALL_PROBE=1` (W-12, outer repo `src/stall_probe.h` and `src/guest_memory_service.inc`): times guest-memory slot lock waits and holds and block waits by role (fault, scanner, swapper, keeper), and writes an `EDEN_STALL` line for every 100 ms+ stall with what waited or held in it. Host test `tools/test-stall-probe.cpp`. Built (W-12); not run yet.

Not a core patch either: `EDEN_GUEST_SWAP_PACK_IN_PLACE=2` (W-20, outer repo, `w20-front-pack-pool-first.patch`: `src/pack_place.h`, `PackOut` in `src/guest_memory_service.inc`). A packed guest slot's bytes go to a block of their own first and the slot's 2 MiB block goes back whole; in place only when the pool has no block. `=1` left 430 to 1,340 MiB of the pool free in holes under 2 MiB at every memory wall I hit (`docs/waveydude/pool-holes-in-place-pack-2026-11-13.md`). Host test `tools/test-pack-place.cpp`. Built and installed (W-20); **not run yet**. Settings: `envs/waveydude/w20-game.env.txt`.

Settings for the test: `envs/waveydude/w13-game.env.txt` (the whole per-game env, with the switches above on).

Also used, from others: `EDEN_UP_AHEAD_LOAD_WAIT=1` (in the core already) stops the title-screen freeze with two frames ahead.

## W-32 raw ocarina microphone

Apply 1108 and 1109 in order to the W-32/T183 core after its existing mic stack (1100, 1101 and 1107). The PS5 headless build must already provide `eden_mic_read`.

- 1108 corrects the auto layout used by `EDEN_UP_MIC_FEED=1` for raw mono PCM without timestamps. PCM starts at `+0x1040`, with producer cursor at `+0x1004` and guest consumer cursor at `+0x44`.
- 1109 defers raw microphone PCM delivery until sysmix engages the stream. The feed is opt-in through `EDEN_UP_MIC_FEED=1`, with controller capture enabled by `EDEN_UP_MIC_PROBE=1`.

See the [9.40 findings](../../docs/waveydude/ocarina-mic-2026-11-14.md) for the tested build and recognition limits.

## 1211 shown-frame flash counter

[Patch 1211](1211-up-flash-count.patch) is the original waveydude core patch from the W-series T186 stack. It applies after the existing BlackProbe present-path changes. The patch adds the detector, Vulkan probe, and renderer hookup. Enable it with `EDEN_UP_FLASH_COUNT=1` on both comparison arms. It defaults to off.

W-39 on a base PS5 with firmware 9.40 initialized the probe in Docked and logged its 10-second summaries. Verify each run has a summary with a positive probed-frame count before reading zero event lines as zero detected flashes. The detector measures one-frame flashes at 576 sample points. Longer flashes and persistent missing assets still need visual evidence. Per-event detail is capped at 20 lines per 10-second window, so use the summary counts for totals.

The [host test](test-flash-counter.cpp) exercises the detector independently. After applying the patch to the emulator core, run from that core's root:

```sh
c++ -std=c++20 -Isrc /path/to/GreenHatBoy/patches/waveydude/test-flash-counter.cpp -o /tmp/test-flash-counter
/tmp/test-flash-counter
```

## Castle Town depth feedback and optional screenshots

| Patch | Switch | Target |
|---|---|---|
| [Depth feedback recheck](town-depth-feedback-recheck.patch) | `EDEN_UP_DEPTH_FEEDBACK_RECHECK=1` | Eglantine core. Rechecks the current draw's depth views before reusing a cached barrier decision. Real overlaps still take the original hazard check. |
| [Optional screenshot drop](town-screenshot-drop-on-oom.patch) | `EDEN_UP_SCREENSHOT_DROP_ON_OOM=1` | Eglantine core renderer. Drops the optional screenshot when an allocation inside its setup throws Vulkan device OOM. Other errors still propagate. Releases the failed screenshot callback without submitting a copy or returning a partial frame. |
| [PS5 overlay alternative](town-screenshot-drop-ps5-overlay.patch) | `EDEN_UP_SCREENSHOT_DROP_ON_OOM=1` | Outer PS5 tree that already has the unconditional screenshot-drop transform in `tools/prepare-vulkan-port.py`. Gates that existing recovery. |

Both features default to off. Choose one screenshot patch per build. If the PS5 build generates its renderer with the existing unconditional screenshot-drop transformation, apply the outer-tree alternative there instead of stacking the two variants.

The core patches were checked against the local patched T186 build inputs. Five matched 9.40 pairs measured median Town FPS of 11.26 OFF and 12.67 ON for depth feedback. An extracted host check passed six screenshot cases covering default-off propagation, enabled image and download-buffer OOM recovery, continued propagation of device loss, and successful capture. The local console route did not encounter an eligible screenshot allocation failure. Trinity's indoor run is the hardware test for that path. This packaging does not add a console result.
