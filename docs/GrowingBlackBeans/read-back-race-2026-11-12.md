# The flicker with frame-ahead is the read-back race (12 Nov 2026)

> **Found:** With read sync (`EDEN_UP_AHEAD_READ_SYNC=1`) the house-door flash was gone in 6 of 6 runs, one and two frames ahead; without it, it flashed in 6 of 6. With no frame ahead at all it was clean in 3 of 3. Read sync costs about 25% fps, and its check mode shows almost all of its waits are for ranges with nothing new coming.
>
> **So:** The fix to build is a read sync that waits only while a copy-back for the range read is still pending. If it keeps most of the frame-ahead speed, two frames ahead can become everyday.

GrowingBlackBeans. Base PS5 13.60, standard Kokiri benchmark **v2** (a new save that starts facing the door; standing is a heavy view, so don't pool these with the 11-12 Nov morning runs). Ratings are by eye: my in-emulator flash counter counts close objects sweeping past as flashes, so it isn't used here.

## Runs

| Batch | Build | Runs | What changed |
|---|---|---|---|
| Floor test | t120-gbb9 | `2026-11-12-FC4..6`, `FW1..3` | FW: `EDEN_NX2_FRAMES_AHEAD=0` |
| T134 gate | t134-gbb1 | `GB1..3` against FC4-6 | T134 + my series (0916 dropped for T134's 0578) |
| Door session | t134-gbb2 | `DC1..3`, `DS1..3`, `DX1..3`, `DXS1..3`, `DV1` | DS: + read sync; DX: + `EDEN_UP_AHEAD_TWO=1`, `EDEN_UP_AHEAD_GUARD_SLOTS=2`; DXS: both; DV1: DXS + `EDEN_UP_AHEAD_READ_SYNC_VERIFY=1` |
| Title freezes | t134-gbb2 | `DXS1-freeze1`, `DX2-freeze1`, `DXS3-freeze1` | first starts with two frames ahead |

## Results

| Arm (3 runs each) | House door, by eye | Rest of the run | Walking fps | Heavy windows |
|---|---|---|---|---|
| full wait (FW, gbb9) | clean 3/3 | clean (FW2) | 20.6 | all |
| one frame ahead (FC4-6, gbb9) | flash (the player's hotspot) | | 23.5 | 81-95% |
| one frame ahead (DC, gbb2) | flash 3/3 | flashes (DC2) | 24.5 | 77-83% |
| + read sync (DS) | **clean 3/3** | clean (DS2) | 18.4 | 0 |
| two ahead + two slots (DX) | flash 3/3 | flashes (DX2, DX3) | 26.0 | 0 |
| two ahead + two slots + read sync (DXS) | **clean 3/3** | clean (DXS2) | 18.0 | 0 |

- **T134 gate:** t134-gbb1 walking 23.9 against gbb9's 23.5 (noise), heavy windows 24.3 against 24.4, no crash. T134 is now the base. One open point: each GB run had one 290-360 ms frame early on, with nothing logged at that moment.
- **Two frames ahead** removes the heavy windows (the present no longer waits). Walking +1.5 fps on average against the control, but noisy (24.9 / 25.1 / 27.9).
- **Read sync makes every window "light" at about 18.5 fps:** the game's CPU waits in its reads. Two frames ahead gains nothing under it (18.0 against 18.4).

## What read sync waits on (DV1)

- About 76 synced reads per presented frame (Vampinity measured 68 on T128).
- **The word read never changed** (0 times in the run), as in Vampinity's check (3 of 38,016).
- **The bytes around it did, about once a frame** (9-276 per 10 s): records of floats, mostly read at +0x10 in 256-byte records, at 102 different addresses spread over 82 MB. The sync's flush refreshes the whole range, so the game's later reads of that record get this frame's values.
- So the waits that matter are about one in a hundred, and the records are spread out, so a fixed list of addresses won't do. The test has to be per read: is a copy-back for this range still pending (`uncommitted_gpu_modified_ranges`, or committed and not yet landed)? That's `EDEN_GBB_READ_SYNC_PENDING`, next.

## The title freeze with two frames ahead

3 of 6 first starts with two frames ahead froze on 12 Nov (5 in all, gbb8 and gbb2; 0 of 7 with one frame ahead). Same signature every time: right after the title's upscale-fallback blit (about 41-45 s), the back is busy for a second, then the front polls an acquire about 8,000 times a second while the back sits idle and the game's threads wait. The retries started fine. waveydude found `EDEN_UP_AHEAD_LOAD_WAIT=1` fixes it on his console (one start). It's in every two-ahead run of the next session, so the count will tell.

## Retractions

- The flash counter's counts at the door (posted earlier in Discussion #2): not usable. Close objects sweeping past the camera count as flashes, more so at lower fps.
- "Ship a recorded shader cache" (Discussion #4): not allowed, since the cache holds the game's code. The legal options are building on the player's console or shipping a list of shader IDs.

## Update, 12 Nov night

- **Two frames ahead in real play** (`runs/GrowingBlackBeans/2026-11-12-Play2`, new game, two slots, `EDEN_UP_AHEAD_LOAD_WAIT=1`, no read sync): 12 minutes, 29.7 fps on average, half of play at 30 fps or more, heavy windows 1% (27% in the one-frame-ahead play session the day before). No title freeze. The player: smooth and fast. Flicker present, much better in small areas, worst in wide camera shots, the forest and water, which fits the read-back race: the more work the GPU has per frame, the later its copy-back lands.
- **The first narrow read sync (0929, `EDEN_GBB_READ_SYNC_PENDING`) felt as slow as the full one** in a short play. My guess, not measured yet: the ranges read sync waits on are exactly the ones the GPU rewrites every frame, so "written in the last 200 ms" is nearly all of them. Its counters weren't saved; it's measured again on 13 Nov.
- **Next (13 Nov):** a census of read sync's waits (0930: where the time goes, write age, repeats, changes) and a different design, read sync once per frame (one batched flush instead of ~76 round trips). Three runs a side against two frames ahead without read sync.
