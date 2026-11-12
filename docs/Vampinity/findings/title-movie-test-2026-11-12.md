# Title movie test: more decoder threads (12 Nov 2026, 07:04-07:25, T134)

> **Found:** EDEN_NX2_AV1_THREADS=8 with EDEN_NX2_AV1_FRAME_DELAY=4 cut the dropped title-movie frames from 44-45% to under 2% in the heavy stretch; 8 threads alone fixed most of it.
>
> **So:** Put both lines in the play settings; the flash meter counts more small patches with them on, which still needs a look at the clips.

Batch `auto-20261112-070408-batch-title-movie` (eglantine-logs-2026-11-05), six title starts, no button
presses. Build T134 (eboot hash 7f14d75d16b8fd02, read at 07:04). READ = measured from a log or a video.
INFERRED = my reasoning. Background: `title-logo-stutter-2026-11-12.md`.

## Verdict

**Frame delay 4 with 8 threads (arm D) fixes the title movie stutter. 8 threads alone (arm B) fixes most of it.**

- READ: over the whole 99 s title movie, frames thrown away ("late dropped": decoded too late, so skipped):
  control 709 and 652, B 172 and 132, D 87 and 74.
- READ: in the heavy stretch after the cut to the dark grass shot (about movie second 10.5 to 29), the
  controls threw away **44-45%** of the frames and showed about 33 pictures a second. Over the same
  stretch (movie ~10.5-31 s, the nearest log marks) B threw away **3.8%** (47 of 1247 in both starts),
  D **1.6-1.8%** (20 and 22). (second check: the earlier "B 4-6%, D 2.0-2.4%" was only the first 10 s of it.)
- READ: the first peek (frame 2400: 593, 549, 107, 75, 71, 50) has the right numbers, but
  "frame 2400" counts shown frames, so it sits at a different movie time per arm (controls at movie
  49-50 s, B and D at 41-42 s). At the same movie time (~41 s) the controls had ~520-575. Same conclusion.
- **Open (second check): the standard flash meter says B and D have MORE flashes**: 35.7 and 41.0 a minute
  vs 27.1 for the controls (card.md: 1.32x, p=0.04; 1.51x, Holm p=0.002). All small patches, no
  full-screen flash. READ from flicker.json: the whole extra sits in movie seconds 10-30, right after
  the cut (controls 24 and 33 events there, B 43 and 51, D 52 and 50). Movie 30-99 s is the same in
  every arm (31-42). In B and D the events start at the cut (9.5-9.9 s), in the controls only at 17 s.
  INFERRED: the meter counts the movie's own dark changes once that stretch plays smoothly; while the
  controls stutter it can't (it needs steady frames before a dip). Not proven. **Watch a side-by-side
  clip of movie 9-30 s (a2 against d2) before calling this fixed.**
- The cost is small: about 37 MiB more heap in use while the movie plays (D), no change in game frame rate,
  start-up time or picture/sound sync. The logo hitch (the single ~0.1 s frame when the logo appears) did not change.
- The cold/warm shader-store confound does not bias the result. a1 was cold too, so every arm had one cold
  start and one warm start, and the drop counts don't depend on it (see below).

## 1. Per start

"Cold store" = no stored shaders for that start's settings, so they were prepared at boot (2202 pipelines in
about 16 s). Prep was done at 27.5-27.8 s, long before the movie (58.8-63.7 s), so it can't touch the movie.

| Start | Arm | Valid | Store | Dropped (whole movie) | Worst stretch (movie time) | Heavy part 10.5-29 s | Game fps on title | Logo hitch | Heap held / in use | Pool largest free |
|---|---|---|---|---|---|---|---|---|---|---|
| a1 run1265 | control, 4 threads | yes | cold | **709** | 10.9-29.2 s: 494 dropped, 45% | 33 pictures/s | 60.0 | 95.9 ms | 1024 / 711 MiB | 6585 MiB |
| a2 run1268 | control, 4 threads | yes | warm | **652** | 10.4-28.2 s: 465 dropped, 44% | 34 pictures/s | 60.0 | 92.6 ms | 992 / 709 MiB | 6550 MiB |
| b1 run1266 | 8 threads | yes | cold | **172** | 0-10.9 s: 56, 8.5% (start of movie) | 10.9-21.5 s: 37, 5.8% | 60.1 | 93.2 ms | 1056 / 731 MiB | 6495 MiB |
| b2 run1269 | 8 threads | yes | warm | **132** | 10.4-20.9 s: 27, 4.3% | 4.3% then 3.2% | 60.0 | 92.3 ms | 1024 / 727 MiB | 6521 MiB |
| d1 run1267 | 8 threads + delay 4 | yes | cold | **87** | 0-10.8 s: 47, 7.3% (start of movie) | 10.8-21.0 s: 15, 2.4% | 59.9 | 92.5 ms | 1056 / 748 MiB | 6510 MiB |
| d2 run1270 | 8 threads + delay 4 | yes | warm | **74** | 0-10.4 s: 27, 4.3% (start of movie) | 10.4-20.6 s: 12, 2.0% | 59.9 | 97.8 ms | 1024 / 746 MiB | 6524 MiB |

Notes on the columns (all READ):
- **Valid:** all six reached the title screen (title check met at 45.4-49.3 s, score 93-96) and played
  the title movie to its end-of-stream line (pts 99.1 s). The batch-level eboot hash is T134's. Each env
  file is the play file plus the test's standard additions (`EDEN_UP_PIPELINE_LIST_KEEP=1`,
  `EDEN_GPU_TIME=1`, `EDEN_UP_AHEAD_GUARD=3`, `EDEN_TEST_*`) plus only the planned switches. The log
  confirms each one: "AV1 decoder libdav1d: 4 threads, frame delay auto" (a), "8 threads, frame delay
  auto" (b), "8 threads, frame delay 4" (d).
- **Every frame was decoded.** Shown + dropped = 5947 in every start, which is exactly 99.1 s at 60 a second.
- **Later in the movie** (after 29 s), the controls still dropped 17-41 frames per 10 s (3-6%). B dropped
  3-26 per 10 s, D 0-10. (second check: corrected from 16-38 / 3-25 / 0-9.) The opening movie's level from the earlier note is 1-6 per 10 s. D is at that
  level for most of the movie.
- **The first 10 s of the movie** drop 47-57 frames in the cold starts and 25-27 in the warm ones, in
  every arm. The settings don't change this. It is the title screen still loading when the movie starts.
  It is the only place where cold vs warm shows, and it is the same for all arms.
  Second check, READ: the cold starts also have one very slow frame as the movie starts (worst frame
  483, 507 and 395 ms in a1, b1, d1; 95-98 ms in the warm starts). Not caused by the settings, but the
  next play boot is cold, so expect that once. Cold minus warm inside one arm: 57 (control), 40 (B),
  13 (D) frames, against 480-620 between arms, so the cold store can't explain the result. D's cold
  start (87) beats B's warm start (132) and both controls; every B and D start beats every control.
  (card.md's notes call all six starts "cold boot"; the log says a2, b2 and d2 had 0 left to prepare.)
- **Game fps on title:** "presents" are the pictures the game hands to the screen. From 15 s into the
  movie until it ends, every start presented 4794-5100 frames, which is 59.9-60.1 a second.
- **Logo hitch:** the worst frame in the 5-second window with the logo, 92-98 ms in all six starts. Earlier
  runs had 97-101 ms. **No change.**
- **Memory:** read from the memory report every 20 s in stderr.log. The table shows the title-screen value,
  the same over 5 reports. Heap = the emulator's own memory. "Pool largest free" = the biggest free block
  of console memory. The flexible free pool was 86 MiB in all six starts, and the GPU block memory (VMA)
  was 424 MiB in all. This batch has no `EDEN_UP_MEM_CENSUS`, so the census "pool free" line is missing.
- **Thread count:** no log line counts threads. INFERRED from the code (`ffmpeg.cpp` 300-314): dav1d
  starts as many worker threads as asked, so 8 instead of 4 while a movie decoder is open (+4). All of
  them run on the shared CPU group `1e80` (5 CPUs, inherited from `nx2:vdec`). Frame delay adds frames
  in flight, not threads.

## 2. On the picture (video frame-difference)

The six recordings were copied to the scratch folder. I ran the same method as the earlier note (video
scaled to 192x108, right-edge strip, a frame counts as "unchanged" when its mean change is under 0.04)
on two strips: the earlier sky strip, and a grass strip at the bottom right that the logo and menu never cover.

- **The per-second "repeated frames" count does not work on this batch's recordings.** READ: in the smooth
  bright shot before the cut, it already counts 18-46 of 60 frames as unchanged in every start, arms
  included. I re-ran the same code on run1256 (earlier note) as a check. It gave 0-10 of 60 there, which
  matches the note. The picture is the same, but this batch's video changes about 8 times less from frame
  to frame (median change 0.03-0.06 vs 0.40). That's below what the recording's compression keeps: OBS
  stores 3 of every 4 frames as in-between frames ("B-frames"). The cause is not certain. The env differs
  from run1256's in 9 switches, among them `EDEN_NX2_FRAMES_AHEAD=1`. So a "repeated frames per second"
  number from these videos would be noise, and I don't give one.
- **What the video can see:** freezes longer than the 5-6 frame pattern the compression makes. READ, from
  the cut to 8 s after it:
  - control a1: freezes of 13, 18, 9, 9 and 12 frames (grass strip); 17, 18, 9 and 12 (sky strip)
  - control a2: 10, 19, 8, 15, 10 and 12 frames (grass); 10, 13, 19 and 20 (sky)
  - b1: one freeze of 12 frames (grass), 10 (sky), both at 5 s after the cut
  - b2, d1, d2: none longer than 7 frames
  So the visible 0.15-0.33 s freezes after the cut happen only in the controls. That matches the logs.
- Freezes of 49-61 frames at about 79-86 s after the cut appear in all six starts. That is the movie's own
  end, where it holds a still. Not a drop.

## 3. Costs

- **Memory (READ):** heap in use at the title screen: control 709-711 MiB, B 727-731 (**+18-20 MiB**),
  D 746-748 (**+37 MiB**). Heap held: control 992-1024, B and D 1024-1056 (+32 MiB in the worst case).
  The largest free pool block was 30-90 MiB smaller in B/D (6495-6524 vs 6550-6585), but it differs by
  ±35 MiB between the two controls too, so that part is noise. INFERRED: the heap is never given back
  ("0 MiB given back"; `EDEN_HEAP_KEEP_ARENAS=1`). So the extra ~32 MiB stays held for the session as
  reusable space after the movie closes, and it is not returned to the pool. On this console that counts.
  Second check, READ: the +32 MiB held shows in both pairs (a1 1024 vs b1/d1 1056; a2 992 vs b2/d2 1024).
  The extra "in use" goes away when the movie decoder closes: the last report after the movies reads
  641 MiB in use in both a2 and d2.
- **CPU for the rest of the emulator (READ):** the game held 60 fps through the movie in every start.
  D shows a few more single slow frames: the worst frame per 5 s during the movie reached 45-50 ms in
  both D starts (d1 45 and 48 ms, d2 49 and 42 ms; d2's 50 ms came after the title movie). Controls
  reached at most 38-40 ms during the movie, B 40-43.
  That's one frame in 300 now and then, not something you'd feel. INFERRED: 8 decoder threads share 5 CPUs
  with other helpers, VulkanWorker (CPUs 10-11) among them.
- **Picture/sound sync (READ):** in every 10 s stretch of every start, wall-clock time and movie time
  match within 0.03 s. Over the whole movie, 99.07-99.12 s of wall clock for 99.10 s of movie. No line
  about drift, pts or "behind" appears in any log. Late frames are skipped, not slowed, so sync holds by
  design. (second check: this is the picture's clock against the wall clock; no log measures the sound, so
  sound sync itself is INFERRED.)
- **Start-up time (READ):** the game started 6-7 s after launch in all six. The title check was met at
  48.7-49.3 s (cold) and 45.4-45.5 s (warm), the same in every arm. The movie's first frame came 60-64 ms
  after the decoder opened in every arm, so frame delay 4 adds no visible start delay.
- **The second movie** (a 30 s movie after the title movie): 1-18 drops in all arms. Nothing to fix there.

**What this test could NOT see:**
- **The opening movie after New Game:** no button was pressed, so it never played. It already dropped only
  34-35 frames in 154 s before. Untested with these settings.
- **Play outside movies:** the extra threads exist only while a movie decoder is open. INFERRED: they end
  when the decoder closes after each movie. The one lasting cost is the ~32 MiB of held heap. No play or
  walk route ran, so its effect in memory-heavy places is untested.
- **A fresh install:** all six starts were on an installed game with files already on the console.
- **Later movies, the Continue path** (a button press cuts the title movie short), **long sessions.**
- **Per-frame decoder timing:** draft N1 (`EDEN_UP_MOVIE_STATS`) isn't in T134. So why 4 threads fall
  short is still inference: dav1d is short of CPU on the detailed grass shot. The settings test is
  consistent with that.

## 4. Recommendations

### Play settings file: yes, add both now

Add `EDEN_NX2_AV1_THREADS=8` and `EDEN_NX2_AV1_FRAME_DELAY=4`. (second check: right after the side-by-side
clip of movie 9-30 s shows no picture fault; it needs only the recordings already on the build computer.)
- Why: this removes the stutter you'd see on every boot to the title screen.
- Shader store cost (READ, `vk_pipeline_prep.cpp`): the store's "stamp" is a fingerprint of every listed
  switch that is set. Both AV1 switches are on that list, so adding them gives the play file a new stamp.
  - The store built during d1/d2 **cannot be reused**: every test env also sets `EDEN_GPU_TIME=1`, which
    is on the list too, and the play file doesn't set it. So that store's stamp differs from the play file's.
  - The console keeps **3 stores in all**, the one in use included (`StoresKept = 3`; `RememberStore`
    puts the newest first in `prep_stores.txt` and deletes everything past the third).
  - Second check, READ from that code and the logs: a1, b1 and d1 each made a new store (three cold boots
    with three new stamps). That pushed the play store out for certain at d1, not "most likely".
  - So the next play boot prepares shaders from scratch either way, about 16 s once at boot
    (2202 pipelines). Adding the two switches costs nothing on top of that.
- Not for D alone: B (threads only) leaves 2-3 times as many drops as D. D was better in both pairs.

### Next build: make them the default, and take them out of the stamp list

- Default: in `src/video_core/host1x/ffmpeg.cpp` (lines 301-310), change the AV1 default from 4 threads to
  8 and from frame delay 0 ("auto", which is 2 for 4 threads) to 4. Keep both switches as overrides.
  - The stamp only fingerprints switches that are **set**, so a new code default changes no stamp and
    makes no store rebuild.
  - Then remove the two lines from the play file in the same step. Its stamp goes back to what it was
    before, so expect one more 16 s boot if that store is gone by then.
- Stamp list: READ, the two switches are read in only one place, `DecoderContext::DecoderContext` in
  `src/video_core/host1x/ffmpeg.cpp` (AV1 codec only). No shader translation or Vulkan pipeline code
  reads them. They are on `TranslationSwitches` (`vk_pipeline_prep.cpp` line 53) only because the list
  is generated from every `"EDEN_..."` name in `src/video_core` and `src/shader_recompiler`.
  - Removing them is safe for the shaders. But the list check (`run_checks_prep.sh` rule, copy in
    `t129/switchlist-check.py`) fails when a name in that tree is
    missing. Second check: the check has no "left out on purpose" list. It skips only names starting with
    `EDEN_UP_SHADER_PREP` and files named `vk_pipeline_prep*`; `EDEN_UP_PREP_UNREAD_HANDLE` passes only
    because it is named in that file alone. So change the rule in `shader-prep/tools/run_checks_prep.sh`
    itself (not just the copy): skip `src/video_core/host1x/`, or add a small named exclusion set.
  - Do it in the same build that changes the default. Then a test arm on these switches no longer forces
    a cold store of its own, which removes this batch's confound for good.
- Before calling it final: the side-by-side clip of movie 9-30 s (flash meter, above), one run of New
  Game with D, to read the opening movie's drop count and the memory in the first area after it, and a
  play check on the village route to confirm the held +32 MiB doesn't hurt. Not before all three.

## In plain words (written for the project owner) (short)

1. Fixed. With the two settings, the title movie throws away 74-87 frames instead of 650-710. On the bad
   stretch after the cut that's 2% instead of 45%. The 0.2-0.3 s freezes after the cut are gone on the video.
2. Cost: about 37 MiB more memory and an occasional 50 ms frame during the movie. Game speed, sound sync
   and start-up time are the same. The short hitch when the logo appears is unchanged (separate problem).
3. Put both lines in your play file now. The first boot after that prepares shaders for ~16 s, once (and
   probably would have anyway). Next build: make them the default so nobody needs the lines.
4. Not tested yet: the New Game opening movie and normal play with these settings.
5. One open point: the flash meter counts more small dark flickers right after the cut with the new
   settings. Most likely it is just seeing the movie play smoothly now, but a side-by-side clip comes
   first (build computer only, a few minutes, no console).

## Checked a second time (12 Nov, after 07:30)

Recounted from each start's eden_log.txt, env.txt, stderr.log, flicker.json, card.md and the T134
source. Held up: all six totals (709, 652, 172, 132, 87, 74, title movie, shown + dropped = 5947), all
six valid, env files differ only in the planned switches (plus the script name), cold/warm split,
memory figures, start-up times, stamp = only switches that are set. Changed: heavy-stretch percentages
for B/D on the same window (3.8% and 1.6-1.8%), frame-2400 positions, later-movie ranges, D's worst
frame, store rotation (play store certainly gone), the switch-list check wording, sound sync marked
inferred. Added: the flash meter's higher count for B/D (open, clip check owed), the cold-boot movie
start hitch, the in-use memory going back after the movie. Build default: not until clip, New Game
run and village play check.
