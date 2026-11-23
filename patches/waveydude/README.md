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

## W-40 refusal fit: pack only what a refused allocation needs

[w40-pack-refusal-fit.patch](w40-pack-refusal-fit.patch). Off unless its switches are set. Outer repo: `src/guest_memory_service.inc`, `headless/performance.cpp`, the port's `headless/vulkan_memory_allocator.cpp`, and two new headers, `headless/refusal_fit.h` and `headless/refusal_trace.h`.

**The problem.** With `EDEN_UP_PACK_ON_REFUSAL=1`, a refused graphics allocation makes the thread that asked pack guest memory itself, one 2 MiB slot at a time, until 64 MiB is free. In a Castle Town walk on my 9.40, all 38 refusals were small: 0.9–2 MiB, mostly 720x405 and 568x568 D32 depth images and 2 MiB staging. Each one still asked for 64 MiB, through `eden_radv_out_of_memory`, and took 100–260 ms. Of 1,359 ms spent packing in that walk, 1,337 ms fell inside the six frames over 250 ms.

**The switches**
- `EDEN_UP_PACK_REFUSAL_FIT=1`: the refusal asks for `max(2 x refused bytes, 8 MiB)`, rounded up to whole 2 MiB slots (`RefusalFit::RoundedAsk`). It keeps the 64 MiB search depth, so it does not give up early, and stops once the smaller target is free. A slot that fails to pack is skipped, and the pass stops after 3 failures in a row (unset: it stops at the first change of the global failure counter). If the RADV allocation still cannot be placed, it is tried once more, and only a second refusal asks for 64 MiB. This uses a link wrap of `eden_radv_private_radv_ps5_memory_alloc`: link with `-Wl,--wrap=eden_radv_private_radv_ps5_memory_alloc`.
- `EDEN_UP_PACK_SPARE_BLOCKS=<n>` (I use 2; only with `EDEN_GUEST_SWAP=3`): n 2 MiB blocks are held only as destinations for a refusal's pack. When the pack finds the pool empty (every failed 8 MiB pass on my 13.60 was "no destination block", all on the packing thread), it packs into a spare, and the source block refills the spare first.
- `EDEN_TOWN_PREPACK_RECOVERY` lines now carry the refused kind, bytes, extent, format, tries, try limit, stop reason, failure mask and spare use. `refusal_trace.h` labels each refusal by its source (`radv` or `allocator`) and kind.

**Results** (my stack, not the alpha: base PS5, handheld 1x, Bilinear, max res off, depth recheck, park wait; combined Castle Town route; store reused; 2 screen pairs, then 5 confirmation pairs; order alternated):

| Console | Build | Walk frames over 250 ms | Packing in the walk | Walk fps, median paired | 64 MiB fallbacks |
|---|---|---|---|---|---|
| 9.40 | fit + 2 spares | 29 → 8 (fewer in 5 of 5 pairs) | 7,027 → 4,059 ms; median per walk 1,317 → 253 ms | +3.00 | 0 → 11 |
| 13.60 | fit, no spares code | 9 → 1 | 2,202 → 929 ms | +2.24 | 0 → 3 |

Graphics refusals go up with the fit (13.60: 11 → 24): each one frees less, so the next comes sooner, but each is short. On the 9.40 they went down (139 → 108), as did driver OOMs (133 → 108), because the spares let packs start. One 9.40 pair went the other way (11.79 vs 18.32 walk fps, 9 fallbacks), but its freezes still fell (9 → 6).

**Porting notes**
- The patch is against my W-series tree: the guest memory service already has my pack-in-place work (`OpenSlab`, `PackOut`, w20). Port by function: `eden_radv_out_of_memory` and the wrap (performance.cpp), `MemoryAllocator::ReleaseRefused` (allocator), and `PackOnRefusal`, `PackOut`, `PackIntoSpare` and the `eden_guest_memory_reclaim` gate (guest memory service).
- The 9.40 file is exactly what was confirmed there. The 13.60 confirmation used the same fit code without the spares functions. With `EDEN_UP_PACK_SPARE_BLOCKS` unset they are skipped, but that exact combination was not run on its own.
- Unset, the only change on the default path is how failures are counted (`CountPackFailure` adds to the same global counter) and an overflow guard on the RADV ask, `min(bytes, 128 MiB) x 4`, which gives the same clamped 64–512 MiB result as before.
- Not a translation input and no stamp switch: my store was reused in every run.
