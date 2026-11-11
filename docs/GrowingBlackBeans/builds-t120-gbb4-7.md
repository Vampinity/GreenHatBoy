# t120-gbb4 to gbb7: what's in them and how to test them

GrowingBlackBeans, 11 Nov 2026. For anyone picking these builds up before I'm back at a PS5. **gbb4-gbb7 have been built but never run on a console.** Everything below about how they behave is what the code is meant to do, not what was seen.

All four builds are T120 (`ocarina-dev-t120`) plus our core patches (`patches/GrowingBlackBeans/`, applied after the T120 series in number order) and two small headless changes (`patches/GrowingBlackBeans/headless-0922-0923.diff`). Every patch is off unless its switch is set: with no new switches, these builds should behave like T120 plus our earlier diagnostics.

| Build | Version | Adds | Release |
|---|---|---|---|
| t120-gbb4 | 01.219.911 | 0921 back-thread breakdown | `gbb-t120-gbb4` |
| t120-gbb5 | 01.219.912 | 0922 vitals + timeline | `gbb-t120-gbb5` |
| t120-gbb6 | 01.219.913 | 0923 flight recorder, effective env line, marker chord | `gbb-t120-gbb6` |
| t120-gbb7 | 01.219.914 | 0924 two-frames-ahead experiment | `gbb-t120-gbb7` |

Each build includes the ones above it. **Use gbb7 unless you want to rule 0924 out**; with `EDEN_GBB_FRAMES_AHEAD2` unset it is gbb6.

## The switches

| Switch | Patch | What you should see | Cost (expected) |
|---|---|---|---|
| `EDEN_GBB_BACK_CALLS=1` | 0921 | Every 5 s: `EDEN_GBB_BACK 5 s (ms per s): busy, waiting, idle hook ...; kinds; anchor 0x...`, then `EDEN_GBB_BACK calls (thunk - anchor ...)` and `EDEN_GBB_BACK methods (engine:method ...)`. Thunk offsets resolve with `nm` on that build's ELF (I keep them; ask). | One TSC read per ring entry on the back |
| `EDEN_GBB_VITALS=1` | 0922 | Every second: `EDEN_GBB_VITALS t_ms= frames= fps= frame_p50_ms= frame_p99_ms= frame_max_ms= present_wait_ms= back_busy_ms_s= front_wait_ms_s= front_waits_s= ring_kwords_s= gpu_busy_ms_s= gpu_subs_s= shaders= shader_ms= fence_pops_s=`. `gpu_busy` needs `EDEN_GPU_TIME=1`; the front waits need `EDEN_NX2_SPLIT_WAITS=1`. | Relaxed atomic adds at existing hooks; under 1% |
| `EDEN_GBB_TIMELINE=<start s>,<seconds>` | 0922 | `EDEN_GBB_TIMELINE: recording ...`, then `... N events ... written to /data/eglantineps5/logs/gbb-timeline-<pid>.bin`. `<start s>` counts from the first present (the intro), so 120 lands mid-walk on a hand-played Kokiri route. Up to 60 s and 1M events. | One clock read and a 24-byte store per event during the window; one hitch when the file is written |
| `EDEN_GBB_FLIGHT=<ms>[,<dumps>]` | 0923 | `EDEN_GBB_FLIGHT: recording ...`, then for each frame of `<ms>` or more: `EDEN_GBB_FLIGHT: frame of X ms at S s; last 2 s (N events) written to .../gbb-flight-<pid>-<k>.bin`. At most `<dumps>` (default 8), at least 5 s apart. Overrides the timeline. | As the timeline, all session; a hitch per dump, after the hitch it records |
| (any of vitals, timeline, flight) | 0923 | Once, at the first present: `EDEN_GBB_ENV count=N KEY=VALUE ...`, every EDEN_, RADV_, MESA_ and ACO_ variable the process has | none |
| touchpad + R3 on the controller | 0923 | `EDEN_GBB_MARK n=K`, and a Mark event in the timeline or flight ring. Neither button should reach the game while held (the touchpad must not tap Minus on release). | none |
| `EDEN_GBB_FRAMES_AHEAD2=1` (with `EDEN_NX2_FRAMES_AHEAD=1`) | 0924 | `EDEN_GBB_FRAMES_AHEAD2=1: presents wait for the frame two back ...`, and every 600 presents a line when one returned with the previous frame still on the GPU side. | **An fps experiment, not a fix.** The copy guard covers one frame in flight, so expect flashes, as with `EDEN_UP_AHEAD_ALWAYS`. A game that reuses command memory one frame later could misread commands; stop if it crashes. |

## How to test them (one or two runs)

Envs: `envs/GrowingBlackBeans/V-vitals-back-timeline.env.txt` (vitals, back breakdown, a 10 s timeline) and `F-flight-recorder.env.txt` (vitals, back breakdown, flight recorder at 100 ms). Both are our everyday env plus those switches; swap in your own env and keep the last lines.

1. **Vitals:** one line a second; `fps` agrees with the `nx2:vi2 5 s` lines; `back_busy_ms_s` is in the range the split line's `1000 - back idle` gives (a few hundred to ~900).
2. **Effective env:** `python3 tools/GrowingBlackBeans/eglog/checkrun.py <run folder>` reports "env.txt matches the env the emulator logged" (or lists the differences).
3. **Marker:** `EDEN_GBB_MARK` lines, and the game doesn't react to touchpad + R3.
4. **Files:** `logs/gbb-timeline-*.bin` or `gbb-flight-*.bin` exist; `python3 tools/GrowingBlackBeans/eglog/timeline.py <file> --perfetto out.json` prints a per-frame summary and writes a trace that opens in ui.perfetto.dev.
5. **Cost:** fps against the same env without the switches (`abcompare.py`); in-run live phases would be better if you have a schedule for them.

If something is wrong, the code is small: `src/video_core/gbb_trace.h` holds nearly all of 0922/0923; the hooks are in `gpu_split.cpp` (`NoteWait`, `BackLoop`, two `extern "C"` functions at the end of the file), `host1x/syncpoint_manager.cpp` (`IncrementGuest`), `fence_manager.h` (`ReleaseThreadFunc`), `vk_pipeline_cache.cpp` (`ReportRuntimePipeline`), `nx2_gsv.h` (after `paced`, and the 0924 branch in the frame-ahead wait), and headless `pad.cpp` and `gpu_time_probe.inc`.

## Also worth a run: shaders built while playing

Not a patch. Boot only builds pipelines on the used list, and a pipeline drops off it after 2 boots unused (`UsedPipelinesMaxAge = 2`, `vk_pipeline_cache.cpp`). A hand-played route uses a slightly different set each run, so most runtime builds in our runs were "on disk, not built at boot" (71%). `EDEN_NX2_PRELOAD_ALL_PIPELINES=1` builds every record at boot. One of your runs (`run482`, title movie) built 1,835 at boot with no memory trouble; gameplay with it is untested. Measure runtime builds after the door, the worst frames, boot time and memory margins.
