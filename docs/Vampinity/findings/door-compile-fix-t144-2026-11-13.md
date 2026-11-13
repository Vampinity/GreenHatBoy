# d3 first look: copy-prop free fix (T144, lead-mesh-28), 13 Nov 2026

> **Found:** With `EDEN_NX2_RADV_COPY_PROP_FREE=1` (driver patch lead-mesh-28, T144) the eight heavy mesh compiles at the house door on a first start peak at 78 to 89 MB instead of 347 to 909 MB: the same mesh keys, the same build times, no visible change in the picture. Three short cold starts, so no rate.
>
> **So:** The switch went into the full first-start test next (2 of 2 scripted first starts got into the village, docked, 1x, 13 Nov). Watch one mild side effect: in both fix starts the memory the compiler gave back went to textures, which then went over the device memory budget once.

First read of cycle d3 (three short cold starts on T144) with the two T137 d1 starts for scale.

## What we now know (plain words)

- **The switch was live where it should be.** `EDEN_NX2_RADV_COPY_PROP_FREE on` is in f1 and f2, not in c0.
- **The fix does what it says on the compile.** The same mesh shaders were built in all three starts. In the
  control the eight big ones took 347-909 MB each inside the driver; with the switch on the same keys took
  78-89 MB. Every mesh job in f1 and f2 stayed at or under 91 MB. Build times did not change (about 2 s for
  the biggest ones either way), so the fix saves memory, not time.
- **The driver's heap stays smaller.** The control's heap grew to 2458 MiB during the load, with 958 MiB of
  freed-but-held pages; the fix starts never went above 1658 MiB (f1) / 1384 MiB (f2).
- **The 10 MiB against 59 MiB is not the fix making things worse.** All three starts hit their lowest
  free block in the same place: 2-4 s after the house picture appears, while the character runs and the
  room's textures load. The census samples only every 2 s. The control's own driver line in that same
  wave shows only **20 MiB available** (c0:4086), and f2's big-table line shows a 24 MiB pool (f2:3050). So
  all three dipped to a few tens of MiB. f1's 10 MiB census happened to land on the deepest moment. When
  it did, the GPU side of the census was 2.3 s stale, so the new texture memory showed up as "rest"
  (+763 MiB, c0 had none of that). At that moment the fix starts were holding *less* heap and *more*
  textures than the control (details below).
- **One fix start finished the short script, one did not, the control did not.** f2 found the
  "(A) Open" prompt, opened the door, and reached its own end line (`script_end line=48`, f2:5001).
  c0 and f1 both stopped at a script wait: the line-38 "(A) Open" look timed out (c0:4340, f1:3463),
  so neither went out of the door. Neither crashed: no crash file, no refusal, no heap failure in any
  start. The reason was the walk, not memory: c0 and f1 stopped one step short of the door, then the
  script's fallback push sent the character back into the room.
- **The picture looks the same.** No new flashes, no white or noise frames, and no big flashes. The few
  small flashes come at the same moments after arrival in c0 and f1 (the run and the camera swing).
- **The load got faster in both fix starts** (Load confirm to house picture: c0 88.0 s, f1 75.6 s, f2
  72.7 s). That is two starts against one, so treat it as a lead, not a result.

## Starts and files

| tag | build | switch | run folder (all under `eglantine-logs-2026-11-05/`) | ended |
|---|---|---|---|---|
| c0 | T144 | unset | `auto-20261113-025159-batch-first-start-c0.d3/run1354-fsd3-c0-s1-cold` | stopped at a script wait: `wait_timeout line=38` (c0:4340), `script_stopped` (c0:4341) |
| f1 | T144 | `=1` | `auto-20261113-025756-batch-first-start-f1.d3/run1355-fsd3-f1-s1-cold` | stopped at a script wait: `wait_timeout line=38` (f1:3463), `script_stopped` (f1:3464) |
| f2 | T144 | `=1` | `auto-20261113-030405-batch-first-start-f2.d3/run1356-fsd3-f2-s1-cold` | `script_end line=48 at=193.033` (f2:5001), `script_done` (f2:5002) |
| b1 | T137 | none in binary | `auto-20261113-020054-batch-first-start-b1.d1/run1347-fsd1-b1-s1-cold` | stopped at the 60 s house wait: `wait_timeout line=31` (b1:2368) |
| b2 | T137 | none in binary | `auto-20261113-020629-batch-first-start-b2.d1/run1348-fsd1-b2-s1-cold` | stopped at the 60 s house wait: `wait_timeout line=31` (b2:2375) |

`x:N` = line N of that start's `stderr.log` unless another file is named.

## 1. Switch proof

- f1 `stderr.log:156` and f2 `stderr.log:156`: `EDEN_NX2_RADV_COPY_PROP_FREE on`.
- c0: no line with `COPY_PROP_FREE` (grep count 0). b1/b2 (T137): none either, as expected.

## 2. Mesh build jobs (EDEN_BUILD_BURST event=job, mesh=1, final done=1 line per job)

Peaks are `peak_b` in MB (1e6 B). ms = `end_ms - begin_ms`. "after Load" = job begin minus the steady time
of the Load-confirm wait (line 29). That time is estimated from the nearest earlier `*_ms` stamp, so it is
good to about 2 s.

| key | c0 peak | f1 peak | f2 peak | b1 / b2 peak (T137) | c0 ms | f1 ms | f2 ms | b1 / b2 ms | line c0 / f1 / f2 | after Load, s c0/f1/f2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 91b3e9d693f6ff77 | 909 | 89 | 89 | 909 / 909 | 1992 | 2071 | 2040 | 2157 / 2124 | 3540 / 2750 / 2632 | 79/69/66 |
| 6ece1f1e9567fa66 | 909 | 82 | 82 | 909 / 909 | 2029 | 2011 | 2112 | 2080 / 2184 | 2111 / 1690 / 1690 | 49/47/45 |
| 92429148893ab775 | 909 | 82 | 82 | 909 / 909 | 2069 | 2018 | 2105 | 2103 / 2171 | 2031 / 1729 / 1693 | 47/49/46 |
| b521910e6a0ef6c7 | 531 | 86 | 86 | 531 / 531 | 2107 | 2160 | 2147 | 2258 / 2235 | 2583 / 2049 / 1960 | 60/57/54 |
| 262c57933526efff | 526 | 83 | 83 | 526 / 526 | 2244 | 2247 | 2159 | 2287 / 2331 | 2752 / 2048 / 1993 | 62/56/53 |
| 21c3e692045b3dad | 514 | 84 | 84 | 514 / 514 | 2249 | 2173 | 2139 | 2270 / 2266 | 2753 / 2124 / 2008 | 62/59/55 |
| 297c55c12d9f70d4 | 358 | 78 | 78 | 358 / 358 | 1390 | 1414 | 1442 | 1478 / 1506 | 3323 / 2681 / 2628 | 76/68/66 |
| 40460987216b6dc9 | 347 | 80 | 80 | 347 / 347 | 1788 | 1834 | 1808 | 1903 / 1912 | 2816 / 2125 / 2009 | 66/59/56 |
| 0e4f0733d951ea43 | 270 | 45 | 45 | 270 / 270 | 977 | 948 | 920 | 987 / 966 | 3889 / 3057 / 2759 | 86/74/70 |
| 23e5bf6447247fae | 222 | 51 | 51 | 222 / 222 | 817 | 910 | 899 | 935 / 920 | 2758 / 2127 / 2010 | 65/61/57 |
| f23622cee0718e64 | 212 | 43 | 43 | 212 / 212 | 809 | 902 | 887 | 955 / 923 | 2756 / 2128 / 2011 | 64/61/58 |
| c930807c06740a55 | 191 | 41 | 41 | 191 / 191 | 690 | 673 | 650 | 683 / 708 | 613 / 588 / 588 | 18/18/17 |
| 2428c3f4b9f11c7e | 191 | 41 | 41 | 191 / 191 | 677 | 650 | 590 | 644 / 692 | 617 / 592 / 592 | 18/19/17 |
| 902565eacdd655b1 | 188 | 41 | 41 | 188 / 188 | 730 | 737 | 710 | 744 / 748 | 1270 / 1125 / 1152 | 34/34/33 |
| f8d172d91adfb4f8 | 188 | 41 | 41 | 188 / 188 | 684 | 687 | 649 | 698 / 689 | 1347 / 1227 / 1236 | 36/35/35 |
| ba721e84749eb8db | 188 | 41 | 41 | 188 / 188 | 686 | 673 | 656 | 703 / 678 | 1346 / 1228 / 1159 | 35/36/34 |
| 5aea25bc9ebd6f4a | 302 | - | 51 | - / - | 985 | - | 954 | - | 5085 / - / 3979 | 138/-/97 |
| e17dec1021d63b58 | - | - | 91 | - | - | - | 1976 | - | - / - / 3541 | -/-/84 |
| 60954f71e2f0dbd5 | - | - | 86 | - | - | - | 1856 | - | - / - / 3788 | -/-/91 |
| 5466c5d5d81211ad | - | - | 84 | - | - | - | 1970 | - | - / - / 4051 | -/-/99 |

- The eight control peaks noted first (909, 909, 909, 531, 526, 514, 358, 347) are right, and they are the
  eight >= 300 MB jobs **before the house**. c0 has a ninth (5aea25bc, 302 MB, c0:5085) about 50 s after the
  script stopped, while the character stood idle. f2 built the same key after the door at 51 MB (f2:3979).
- The T137 baselines give the same peaks to the byte on every shared key (for example 91b3e9d6: 909,346,472 B
  b1:3102, 909,346,424 B b2:3082, 909,346,416 B c0:3540). So c0 is a fair control: the T144 binary
  without the switch compiles exactly like T137.
- Fix peaks fall 4-11x per key. The largest mesh job of any fix start is 90.8 MB (f2:3541, a key only f2
  reached, after the door). `net_b` and `allocated_b` stay about the same as in the control (91b3e9d6
  allocated 2.42 GB c0:3540 vs 2.45 GB f1:2750). So the fix makes the driver hand memory back sooner. It
  does not make it allocate less in total.
- Every mesh job reached `done=1`, in every start (no unfinished job at the end of any log).
- Durations are flat: the fix neither speeds nor slows a compile (91b3e9d6: 1992 / 2071 / 2040 ms).

Totals (all done mesh jobs; parsed from each `stderr.log`):

| | mesh jobs | sum of durations | of it before the house | >= 300 MB | Load confirm (line 29) | house (line 31) | Load to house |
|---|---|---|---|---|---|---|---|
| c0 | 105 | 27.07 s | 26.08 s | 9 (8 before house) | at=53.810 (c0:450) | at=141.791 (c0:4004) | **87.98 s** |
| f1 | 127 | 26.18 s | 26.18 s | 0 | at=53.696 (f1:451) | at=129.345 (f1:3113) | **75.65 s** |
| f2 | 180 | 34.63 s | 25.67 s | 0 | at=53.677 (f2:451) | at=126.412 (f2:2861) | **72.74 s** |
| b1 | 124 | 27.03 s | - | 8 | at=53.852 (b1:450) | not seen in 60 s (b1:2368) | > 60 s |
| b2 | 129 | 27.15 s | - | 8 | at=53.643 (b2:449) | not seen in 60 s (b2:2375) | > 60 s |

(f2's extra jobs and seconds are the door and the next area, which c0 and f1 never reached.)

## 3. The pool

### During the load (Load confirm to house)

- c0: the 909 MB compiles show up as heap growth. Heap 1850 → **2458 MiB** (pieces 2016, free_pages 958) at
  census n=8, `stderr.log:1723-1724`. `largest=` fell from 669 (c0:1611) to 157 (c0:1723) and stayed at
  128-192 for the rest of the load (c0:2017 to c0:3999).
- f1: heap never above 1658 MiB (f1:2105), free_pages 112-190. `largest=` stayed at 690-754 until about 20 s
  before the house (f1:1995 to f1:2608), and went to 467-524 only as the room's textures came in (f1:2849,
  f1:2954).
- f2: heap at most 1384 MiB (f2:2654); `largest=` 424-752 (f2:2524 to f2:2974).
- Report summaries: heap at the end `1632 + 120 MiB ... 1376 given back` (c0 report.txt:19), `1216 + 120 MiB
  ... 224 given back` (f1 report.txt:21), `1248 + 120 MiB ... 576 given back` (f2 report.txt:21). Images
  deleted by the collector during the run: c0 2460 (860 downloaded, report.txt:20), f1 1183 (416, report.txt:22).
  The control threw away about twice as many textures, which fits a tighter pool during its load.

### The lowest point, aligned on the house picture (wait_met line=31)

The census `t_s` clock is not the `EDEN_TEST at=` clock (about 16-18 s apart), so these are aligned by log
order: the first censuses after `wait_met line=31` and before the line-34 look.

| | census line | after house | largest / low (MiB) | gpu | out | guest | heap (pieces / live / free_pages / fragmented) | vma_blocks / used / slack | images (count/MiB) | jit / tables | rest |
|---|---|---|---|---|---|---|---|---|---|---|
| c0 n=30 | c0:4136-4138 | ~2 s | **59 / 59** | fresh | 11760 | 5547 | 1752 (1632 / 743 / 486 / 402) | 3302 / 2895 / 407 | 2272 / 1015 | 448 / 168 | 478 |
| f1 n=13 | f1:3332-3334 | ~4 s | **10 / 3** | stale 2310 ms | **12088** | 5581 | 1336 (1216 / 776 / 108 / 331) | 3261 / 2834 / 427 (stale) | 2178 / 1159 (stale) | 432 / 166 | **1245** |
| f1 n=14 (next, fresh) | f1:3383-3385 | ~6 s | 27 / 8 | fresh | 11686 | 5561 | 1336 (1216 / 770 / 114 / 331) | 3518 / 3210 / 308 | 2529 / 1227 | 432 / 166 | 607 |
| f2 n=6 (fresh) | f2:3007-3009 | ~1 s | 250 / 250 | fresh | 11724 | 5560 | 1304 (1184 / 756 / 108 / 319) | 3662 / 3279 / 383 | 2620 / 1267 | 432 / 166 | 534 |
| f2 n=7 | f2:3136-3138 | ~4 s | **69 / 16** | stale 2309 ms | 11363 | 5550 | 1304 (1184 / 769 / 96 / 318) | 3662 / 3279 / 383 (stale) | 2620 / 1267 (stale) | 432 / 166 | 184 |

Between the census samples:

- c0 `RADV_PS5_MEMORY ... available_mib=192 driver_mib=3188` (c0:4085), then the very next line
  `available_mib=20 driver_mib=3696 retired_mib=63` (c0:4086). That is the control's own trough in this
  same wave: **20 MiB**, between census n=29 (c0:4026) and n=30 (c0:4136).
- f2 `EDEN_BIG_TABLE n=16 ... pool_mib=24` (f2:3050). f1 `EDEN_BIG_TABLE n=23 ... pool_mib=10` (f1:3307),
  then `pool_mib=56` (f1:3368). c0 `EDEN_BIG_TABLE n=45 ... pool_mib=59` (c0:4122).
- The heap did not move at the trough in any start: `heap_2s_mib=+0.0` with class_live 660-670 MiB (c0:4011,
  c0:4122, f1:3184, f1:3307, f2:3050). The heap is not the holder, so the big-table stacks were not
  symbolized and the T144 ELF was not unpacked.

**Why 10 against 59:**

1. **Same moment, different sample.** All three troughs fall 2-4 s after the house picture, in the room's
   first texture wave during the down-left run. The control also fell to 20 MiB (c0:4086). The 2-s census
   caught f1 deeper (its `low=3` is a 250-ms poll, f1:3332). With a sample of three, 59 vs 10 is noise in
   *when* the census fired, not a level the fix changed.
2. **Not freed heap pages.** The fix starts hold **less** heap at the trough: 1304-1336 MiB against 1752,
   free_pages 96-114 against 486, fragmented 318-331 against 402. The fix gave back what it promised.
3. **More textures in flight at that moment.** Fresh fix samples show more GPU memory: vma_blocks 3518-3662
   against 3302, images 1227-1267 MiB against 1015 (f1:3383, f2:3007 vs c0:4136). At f1 n=13 the GPU side
   was 2.3 s stale, so that wave is booked as `rest` (1245 MiB, normally ~480). The TOP line reads
   `grew_most=rest+763 since n=12` (f1:3334). The next fresh census moves +257 MiB into vma_blocks, and
   `out` falls 402 MiB (f1:3383-3384). So the "rest" spike is mostly the room's texture wave plus
   short-lived driver buffers, not something new the patch holds. The driver logged 13-16 "no single free
   range" splits in the fix starts against 4 in c0 (f1:3232-3244 and later). That is a symptom of the low
   largest-block, and a lead for the next look.
4. Why the fix starts have more textures loaded at the same moment: the control spent its load with a
   128-192 MiB largest block and discarded twice as many textures (report.txt lines above). That is a
   reading, not a proof.

After the trough the fix starts sit higher: f1 `largest=434` from f1:3559 to the end, f2 246-471, c0 192
(c0:4227 onward).

## 4. Refusals and failures

All five starts (grep over each `stderr.log`): `EDEN_NEW_WAIT` 0, `gave up` 0, `refused at once` 0,
`EDEN_HEAP_FAILURE` 0, out-of-memory / `OUT_OF_*_MEMORY` 0, `refused=+N` (N>0) 0, `failures=N` (N>0) 0. No
crash file in any run folder. `crash-index.txt` lists only older crashes (12 Nov and 13 Nov 00:52-01:47),
none from these starts. Driver "no single free range" splits: c0 4, f1 16, f2 13, b1 0, b2 0.

## 5. Picture

- `video-check.txt`: white 0%, noise 0% in all three. The high black share (c0 86%, f1 86%, f2 54%) is the
  black load (c0 57.97-146.46 s, f1 55.08-133.50 s, f2 55.32-130.81 s), the dim room, and black after the
  app quit. f2 is lower because it ran longer, in the brighter next area.
- `flicker.json`: c0 4 flashes, 0 big (video 149.9-156.1 s = house +3 to +10 s). f1 4 flashes, 0 big
  (137.1-143.1 s = house +4 to +10 s). Same count, same moments after arrival: the run and the camera swing.
  f2 has 8 flashes, 0 big, over a different, longer path (door and next area), so it is not comparable 1:1.
- `fog-score.txt`: peak 8 (c0), 9 (f1), 26 (f2 next area); 0 game frames at 50 or more in any.
- Frames (`frames/`, `video-check.jpg`): the room renders fully and identically in c0 and f1 (plants,
  lamps, light shafts): c0 f0031-f0036, f1 f0028-f0033. Nothing differs beyond timing and where the
  character stood. **No rendering change from the patch is visible.**

## 6. Why c0 and f1 stopped at line 38

Script (`script.txt`): line 33 holds the stick down-left for 4 s. Line 34 looks up to 5 s for "(A) Open".
Line 37 is a fallback push "forward" for 1.5 s. Line 38 waits 3 s for "(A) Open".

- c0: line 34 `wait_skipped ... best=55` (c0:4258), line 38 `wait_timeout ... best=0` (c0:4340).
- f1: line 34 `wait_skipped ... best=37` (f1:3391), line 38 `wait_timeout ... best=9` (f1:3463).
- f2: line 34 `wait_met ... score=99` at 6.58 s after the house (f2:3197). That is 0.58 s after the 4-s hold
  ended, so the prompt came only at the very end of the run. The fallback push was dropped, line 38
  passed at once (f2:3198), and the door opened.
- Frames: in c0 (f0032) and f1 (f0029) the character ends the run against the basket next to the camera,
  one step short of the door, with no prompt on screen. After the fallback push the camera has swung behind
  him, so "forward" walks him **into** the room: in c0 f0033-f0036 and f1 f0030-f0033 he stands with his
  back to the camera at the pots in the far corner, idle. The picture is fully loaded, so this is not a
  loading problem. He is short of the door and then pushed the wrong way.

**What would make the short script reach the door on a cold start:** make the run closed-loop. Keep nudging
down-left in short steps until the "(A) Open" look matches, instead of a fixed 4-s hold followed by a
"forward" push in a camera that has swung away from the door. A cold start's slower frames shift how far
4 s carries him.

## What three short starts can and cannot show

**Can show:**
- The switch is live in f1 and f2 and off in c0.
- The mesh compile peak falls on the same keys, same build, same path: 909 → 82-89 MB, and every mesh
  job stays at or under 91 MB.
- The heap stays about 400 MiB smaller with the fix.
- The picture is unchanged on the stretch both arms covered.
- One fix start (f2) went out of the door and reached its own end line without a crash.

**Cannot show:**
- A rate: one control and two fix starts. One pass is no verdict.
- That the fix gets out of the door where the control dies. The control never tried the door, so there is
  no c0 door to compare with f2's.
- The full newcomer path with the opening's pool drain (that is v16).
- That the stored pipelines are byte-identical.
- Whether the driver cache still loads on the first warm start after a fix start (item 7 of the test plan).
- Whether the 12-15 s faster load is real.
- The lowest pool point to better than the 2-s census plus the 250-ms `low=` poll. Use the driver and
  big-table lines between samples.

## Second check (13 Nov 2026)

Re-derived from the raw `stderr.log`, `eden_log.txt`, `report.txt`, `video-check.txt`, `flicker.json` and
`fog-score.txt` of c0, f1, f2, b1, b2. Jobs were counted per `id`, last line
of that id (a job prints one line per 2-s window; the `done=0` lines carry running peaks). "Room arrival" =
`wait_met line=31`; "exit look" = line 38. `x:N` = stderr.log line unless a file is named.

### Confirmed

- Switch: `EDEN_NX2_RADV_COPY_PROP_FREE on` at f1:156 and f2:156 only; `NX2_RADV_COPY_PROP_FREE=1` in the
  f1/f2 report settings, absent in c0.
- Mesh jobs: c0 105, f1 127, f2 180, b1 124, b2 129 ids; every one ends `done=1 success=1`; no unfinished
  job of any kind in any start (window sums: `failed=0`, `overflow=0`, `disk=0` everywhere).
- Peaks: the 17 keys that reach >= 100 MB without the switch (c0, b1, b2) all appear in f2; f1 has 16 of 17
  (missing only 5aea25bc, built in c0 after its script stopped). Largest mesh job: f1 88.9 MB (f1:2750),
  f2 90.8 MB (f2:3541); c0/b1/b2 909.3 MB, same bytes per key across T137 and the T144 control.
  No shared key has a higher peak with the switch (147 shared keys; the "equal" ones are 0.1-3 MB jobs).
- Duration per job is flat: on keys shared with c0, f1 needs 0.997x and f2 0.977x of c0's time; c0 itself
  needs 0.971x of b1's. `allocated_b` per shared key is +1.5% with the switch, `net_b` the same.
- Heap: max census heap 1658 MiB (f1:2105) / 1384 (f2:2654) against 2458 in c0 (census n=8, pool line
  c0:1725, not 1724) and 2458 / 3034 in b1 / b2. The ~400-800 MiB heap saving holds against T137 too.
- No crash, no `EDEN_HEAP_FAILURE`, no refusal. `<Error>`/`<Critical>` lines in `eden_log.txt`: 612 in each
  of the five starts, same kinds. No line kind exists only with the switch except the switch line itself
  and normal key/size variants.
- Picture: white 0 %, noise 0 %, big flashes 0; c0 flashes at picture +3.4 to +9.6 s, f1 +3.6 to +9.6 s.
  The sampled frames (c0 f0032, f1 f0029) show the same fully drawn room.

### Corrections

1. **"The same mesh shaders were built in all three starts" (line 9) is not exact, and it is c0 that
   differs.** Counting real compiles before room arrival (>= 5 ms or > 5 MB): f1, f2, b1 and b2 built the
   **identical 59 keys**; c0 built 53 of them plus one other. c0 skipped six small ones (231df70f, 2edb03e0,
   367017e6, 703753aa, b0211856, feec40e1, 2.8-3.0 MB each, f1:701-711) and got d70ef4a9 as a 0-ms job after
   room arrival (c0:4148; 41.7 MB in b1/b2, 30.9 MB in f1/f2); only c0 compiled 3c94c789 (41.7 MB, c0:798),
   a 0-ms job in the other four. The other key differences are 0-ms jobs (45 / 65 / 59 / 65 / 70 of them).
   So the fix starts did not build fewer pipelines; all big keys are present.
2. **The 12-15 s faster load is not a fix effect.** The video gives one clock for all five starts (end of the
   long black load span, `video-check.txt`): c0 57.97-146.46 s = **88.5 s**, f1 78.4 s, f2 75.5 s, and the
   unpatched T137 starts b1 55.92-136.57 = **80.7 s**, b2 79.3 s. T137 without the patch loaded about as fast
   as the fix starts; c0 is the slow one. A likely reason, visible only in c0: its builds queued at the
   pipeline memory gate, `65 of 1382 builds waited, 34189 ms in all, 10 at the limit` (c0 eden_log.txt:3628),
   against `1 ... 96 ms` (f1 eden_log:3627), `1 ... 134 ms` (f2 eden_log:3631), `1 ... 1734 ms` / `391 ms`
   (b1 eden_log:3081, b2 eden_log:3106). c0's pool sat at largest 128-192 MiB through the load, lower than
   b1 (160-288) and b2 (89-544 MiB). So c0 is a fair control for compile size, but a slow-luck control for
   load time. Drop "faster load" from the leads.
3. **Out-of-memory lines exist, in the fix starts only** (section 4 grepped `stderr.log` only). `eden_log.txt`:
   - f1: `Image 1024x1024 ... is over the memory budget; allocating it anyway` (3621), `Out of device memory:
     keeping 512 MiB more free` (3622), another over-budget image (3628), `keeping 1024 MiB more free` (3629).
     The gate line in between says `10 MiB free` (3627): this is the same moment as the census `largest=10`
     (f1:3332). report.txt:14-15 lists both events.
   - f2: over budget + `keeping 512 MiB more free` at the same room wave (3623-3624, gate `69 MiB free`
     3631, census `largest=69` f2:3136), again at 3742-3743 (1024 MiB, after the exit look), and in the
     next area 4197-4200 (1408) and 4290-4292 (1920). report.txt:14-15: 7 over budget, 4 short.
   - c0, b1, b2: **0** over-budget lines; the texture cache's `Memory margins ... out of memory` stays 0 MiB
     for the whole run (157 / 135 / 136 lines). In f1 it stays 768-1024 MiB from 141 s to the end (49 lines),
     in f2 512-1920 MiB.
   Nothing failed (every image was still allocated), but this is a real difference the note missed.
4. **The "10 vs 59 MiB is census sampling" reading mixes metrics.** The control's 20 MiB comes from the
   driver line (`available_mib`, c0:4086); the 10 MiB is the census / big-table pool. On the same metric:
   census `low` c0 59 (c0:4136) / f1 **3** (f1:3332) / f2 **16** (f2:3136); big-table `pool_mib` c0 59
   (c0:4122) / f1 10 (f1:3307) / f2 24 (f2:3050); driver `available_mib` c0 **20** (c0:4086) / f1 140
   (f1:3421) / f2 666 then 135 (f2:3216, f2:3505, the second after the exit look). The driver lines come
   only every ~10 s. So all three dipped hard in the same room wave and the depth order flips with the metric;
   "the same dip" holds, "not deeper with the fix" cannot be shown. What does separate the arms is item 3.
   The note's explanation for *why* still fits: the heap gave back ~400 MiB, the texture side took it
   (vma_blocks 3518-3662 vs 3302, images 1227-1267 vs 1015 MiB) and ran past the device budget. Read:
   the fix moves memory from the compiler to textures; it does not by itself raise the pool floor in a
   texture wave.
5. **Texture discards: f2 is left out.** c0 2460, f1 1183, but f2 **6283** (report.txt:22, longer path into the
   next area); T137 b1 530, b2 547 (idle in the room after their script stopped). Whole-run totals over
   different paths and lengths; the "control threw away twice as many" reading rests on f1 alone.
6. **More mid-size heap requests with the switch** (not in the note). `EDEN_HEAP_CLASSES under1M` before room
   arrival: c0 27,429 req / 12,230 MiB (c0:3694), f1 40,589 / 16,780 (f1:2828), f2 42,234 / 17,474
   (f2:2711); run end c0 33,205, f1 46,025, b1 30,659, b2 30,595. About +45 % requests, +4.5 GiB requested.
   That is the per-branch free and re-allocate the patch does. It costs no growth: `EDEN_HEAP_GROWTH`
   spills c0 72,195 vs f1 3,786 / f2 4,184 (c0:3692, f1:2826, f2:2709), under1M growth 1728 MiB vs 0, and
   fragmented / free_pages are lower (318-341 / 96-190 vs 399-412 / 462-958). No time cost shows in job
   durations. Worth one look under a profiler, not a blocker.
7. **"Every mesh job in f1 ... all before the house"**: f1 has 124 before and 3 after room arrival (0-ms
   jobs, f1:3255-3263); the 26.18 s is all before. c0 has 98 before, 7 after.
8. Small: fog-score.txt scored only **4** game frames in c0 and f1 (17 in f2), so "0 at 50 or more" is a thin
   check. c0's `stderr.log` ends at line 5413 inside the shutdown, before the `kernel.Shutdown()` line f1:4067
   and f2:5499 carry; result.json says `script_stopped`, so this is log capture, not a crash.
9. Driver cache: all five load `Total Pipeline Count: 0` (eden_log) and `Shader cache ready: 0 pipelines`
   (stderr), and each writes `Vulkan driver pipelines cached at: .../vulkan_pipelines.bin` (c0 eden_log
   4079/4210, f1 3729/4147, f2 4049/4324) with no size, count or hash. These logs cannot say whether cache
   content or identity changed. Item 7 of the test plan (first warm start after a fix start) stays the only test.

### Final statement

- **Holds:** with the switch on, the same mesh keys peak at 41-91 MB instead of 188-909 MB, the full set of
  real compiles matches the T137 starts key for key, every job finished, job times are unchanged, and the
  driver heap stays 400-1600 MiB below the unpatched starts. No crash, refusal, heap failure or new error line,
  and no visible rendering change on the stretch c0 and f1 share. c0 and f1 stopped at a script wait
  (line 38, the walk); f2 has its own end line (f2:5001). Three short starts: no rate.
- **Is there any sign the fix makes something worse? Yes, one, mild and not fatal:** in both fix starts, and
  in none of the three unpatched starts, the room's texture wave pushed image allocations over the device
  memory budget (`allocating it anyway`), the pool fell to 3-16 MiB on the census, and the texture cache then
  kept 512-1024 MiB extra free for the rest of the run (f1 eden_log:3621-3629, f2 eden_log:3623-3743). The
  memory the compiler gave back went to textures. Also new, cost-free so far: ~45 % more mid-size heap
  requests. Nothing else got worse: not compile time, not heap fragmentation, not the picture.
- **Withdrawn:** the faster load (c0 was slow; T137 loaded in 79-81 s like the fix starts) and "the same
  pipelines in all three" (c0 is the one that differs).
- **For v16:** watch `over the memory budget` / `Out of device memory` in `eden_log.txt` next to `largest=` at
  each texture wave; if the fix starts hit them at the exit waves too, the compile fix alone will not lift
  the pool floor there.
