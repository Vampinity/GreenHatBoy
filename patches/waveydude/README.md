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

## Ocarina microphone (W-39 stack)

The whole mic stack from my W-39 build, so it can be compared with other mic code. Everything is off unless its switch is set. Verified on a base PS5 with firmware 9.40 only.

**Core patches** (Eglantine submodule), in this order: 1100, 1101, 1107, 1108, 1109, 1110. All six touch `src/core/hle/service/audio/nx2_audio_device_manager.h` (1107 also adds `src/common/nx2_mic_log.h`). Checked: they apply cleanly in that order to Eglantine `0ca2032`.

| Patch | Switch | What it does |
|---|---|---|
| [1100](1100-ocarina-mic-stream-dump.patch) | `EDEN_UP_MIC_DUMP=1` | Logs what the game's two sysmix input streams look like (`InputStream-0<=1ch48kQ15<=AudioVirtualOutput0` and `InputStream-1<=1ch48kQ15<=TrueRawAudioIn`): their ring's non-zero words at open and attach, then both indices about once a second. `EDEN_MIC_DUMP` lines. |
| [1101](1101-ocarina-mic-feed.patch) | `EDEN_UP_MIC_FEED=<data>,<system index>,<game index>` or `=1` | Writes the controller mic's samples (`eden_mic_read`, from the host patch below) into the game's raw mic stream at its rate, and moves the system index past them. With no samples it writes silence. `EDEN_MIC_FEED` lines. |
| [1107](1107-ocarina-mic-log-whole-session.patch) | (with 1100/1101) | The feed and dump lines last the whole session instead of stopping after 200 lines. Host test `tools/test-mic-log.cpp` (in the host patch). |
| [1108](1108-ocarina-mic-ring-layout.patch) | `EDEN_UP_MIC_FEED=1` | Corrects the auto layout for raw mono PCM without timestamps: PCM at `+0x1040`, producer cursor `+0x1004`, guest consumer cursor `+0x44`. |
| [1109](1109-ocarina-mic-feed-when-engaged.patch) | (with 1101) | Holds the PCM back until sysmix engages the stream. |
| [1110](1110-ocarina-mic-feed-reference.patch) | `EDEN_UP_MIC_FEED_REFERENCE=1` | Writes silence into the `AudioVirtualOutput0` input stream, which otherwise stays at 0/0 for the whole session. It was on in the session where Humming worked; whether Humming needs it was not tested on its own. |

**Host patch** (outer repo): [w39-mic-capture.patch](w39-mic-capture.patch). This is the part that opens the PS5 controller's mic. Checked: it applies cleanly to `e40829e`.

- `libSceAudioIn` has no import library in the Payload SDK, and looking its functions up at run time failed on every name and NID (W-14/W-15, `0x80020003`). Instead, the build imports the three functions at link time through a facade, the same way the keyboard's `libSceCommonDialog` is imported: `tools/stubs/libSceAudioIn.c`, built by `tools/build-audio-in-stub.sh` and linked in `headless/CMakeLists.txt`. The native packaging step turns the symbols into imports of the firmware module by NID. Nothing in the stub runs.
- `headless/mic_capture.{h,cpp}`: `EDEN_UP_MIC_PROBE=1` starts a capture thread after the controllers open (`headless/main.cpp`). It tries a few open settings, logs each result, and keeps the last second of 48 kHz mono samples for `eden_mic_read`. `EDEN_UP_MIC_SIGNAL=1` logs the level and pitch of the PCM handed to sysmix.
- Optional and older: `EDEN_UP_MIC_NOTES=1` (`headless/hum_notes.h`, `headless/pad.cpp`) turns the hum's pitch into the ocarina's five buttons. It is not needed with the feed. Host test `tools/test-hum-notes.cpp`.

Host tests (both pass):

```sh
c++ -std=c++20 -O1 -Iheadless tools/test-hum-notes.cpp -o /tmp/test-hum-notes && /tmp/test-hum-notes
c++ -std=c++20 -O1 -I<patched Eglantine>/src tools/test-mic-log.cpp -o /tmp/test-mic-log && /tmp/test-mic-log
```

**Settings** that fed real samples on my 9.40 (per-game env):

```text
EDEN_UP_MIC_PROBE=1
EDEN_UP_MIC_DUMP=1
EDEN_UP_MIC_FEED=1040,1004,44
EDEN_UP_MIC_SIGNAL=1
EDEN_UP_MIC_FEED_REFERENCE=1
```

After an install, check that these lines are still live: one install moved my per-game env aside and the mic went silent again.

**What it fixed and what it didn't:** with these, Instruments heard the mic and played a song. Humming still heard nothing, because the game sends Humming's pitch detector the silent virtual stream. That part is game-side and needs a separate game patch, which is not in this folder. With both, Humming and Instruments worked in one session on 9.40 (Humming pitches 231.5, 181.2 and 201.9 Hz; Instruments 133.7 and 337.8 Hz). Details: [discussion #2](https://github.com/Vampinity/GreenHatBoy/discussions/2#discussioncomment-19763262) and the [9.40 findings](../../docs/waveydude/ocarina-mic-2026-11-14.md).

## 1211 shown-frame flash counter

[Patch 1211](1211-up-flash-count.patch) is the original waveydude core patch from the W-series T186 stack. It applies after the existing BlackProbe present-path changes. The patch adds the detector, Vulkan probe, and renderer hookup. Enable it with `EDEN_UP_FLASH_COUNT=1` on both comparison arms. It defaults to off.

W-39 on a base PS5 with firmware 9.40 initialized the probe in Docked and logged its 10-second summaries. Verify each run has a summary with a positive probed-frame count before reading zero event lines as zero detected flashes. The detector measures one-frame flashes at 576 sample points. Longer flashes and persistent missing assets still need visual evidence. Per-event detail is capped at 20 lines per 10-second window, so use the summary counts for totals.

The [host test](test-flash-counter.cpp) exercises the detector independently. After applying the patch to the emulator core, run from that core's root:

```sh
c++ -std=c++20 -Isrc /path/to/GreenHatBoy/patches/waveydude/test-flash-counter.cpp -o /tmp/test-flash-counter
/tmp/test-flash-counter
```
