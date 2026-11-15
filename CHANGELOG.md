# Changelog

Newest first, with each day's test builds in brackets. Results are from our own tests on a base PS5 (firmware 12.40, docked, full resolution, unless an entry says handheld). Credits in full: [CREDITS.md](CREDITS.md).

## 15 November 2026 (builds T186 to T190)

- **The first alpha: build T186 with play settings v4.0** ([alpha-t186 in Releases](https://github.com/Vampinity/GreenHatBoy/releases/tag/alpha-t186)). Tested on a base PS5 on firmware 12.40, in handheld at 1x. Before it went up, 2 of 2 scripted first starts from a fresh install (no prepared shaders, no graphics driver cache, the app's default settings plus Handheld; a test save was on the console) of the alpha's app got through the opening and the house door into the village. It replaces the test build T180 (play settings v3.9, frame ahead on).
- **Played by hand for the first time with v4.0:** about 2 hours on T186, handheld, 1x, in two sittings. 3 crashes: twice at the load from the field into the next area (after about 20 and about 55 minutes of play), and once indoors in that area, 327 s after a fresh app start. One stretch of about 34 minutes, with two in-game save reloads, ended with a normal quit. No dark or bright full-screen flashes were seen. Once, in the village after the field with almost no memory free, the picture stood still for a few seconds with white surfaces.
- **What runs out in long play.** In each of the three hand crashes the largest free piece of memory was 0 or 1 MiB. In one session the game's own memory stayed flat (about 5.4 to 6.2 GiB), while memory the emulator holds but cannot reuse grew from about 650 to about 930 MiB between minute 5 and minute 20; at the load from the field the largest free piece was 51 to 110 MiB, and that load needs pieces of 100 to 300 MiB. Our stand-in for a long session (512 MiB taken away) still leaves 457 to 574 MiB, so it is milder than real play. In the village after the field, after about 30 minutes, an in-game reload left the largest free piece at 0 to 4 MiB; a full app restart at the same spot gave 700 to 840 MiB (one try each). So: save, quit and restart the app before a big new area.
- **`EDEN_UP_DRAIN_TO_POOL=1` under the 512 MiB squeeze on T186** (scripted, handheld, 1x): 2 of 2 got through, against 1 of 2 without it, the same count as on 14 November. But the shorter crawl after the load did not repeat: 12 and 33 s under 1 fps with it, 28 s for the start without it that got through. So the shorter crawl we gave for it on 14 November is not shown. Two starts a side.
- **Docked with frame ahead off** (T186, 2 scripted starts): both got through the load from the field, but the screen stayed black for 44 to 55 s and the game ran under 1 fps for 29 to 47 s, with one 13.6 s stop where the picture stood still. The alpha is for handheld for now.
- **T186 on the console.** The counts in this bullet and the next two come from scripted starts at 1x in handheld, with frame ahead off, one batch per test. With its new switches unset its boot lines and speed match T185, and 2 of 2 got through the load from the field. One of the two starts had a 3.4 s memory wait at the load that no T185 start of that kind had, so one more pair is due.
- **Where the frame goes in the area after the field.** New counters in T186 show the part that reads the game's drawing commands waiting on the graphics chip about 18 ms a frame there, nearly all of it one wait for a small list that sets the size of a compute job (macro 0xe74). On the field walk it is about 12.5 ms. Two starts, and the counters may cost 1 to 2.5 ms a frame. If that wait went away completely, the area after the field could go from about 14 fps to about 18 at most. That is where the speed work goes next.
- **Two memory switches under a squeeze** (512 MiB taken away before the load, as a stand-in for a long session): with `EDEN_UP_DRAIN_ON_GROWTH=1` 2 of 2 got through with the speed back after the load, against 2 of 2 through with the speed back in 1 for the same settings without it. One batch, so not proven better yet. `EDEN_UP_BIG_UPLOAD_CHUNK_RELEASE=1` did not act at all and is not tested yet.
- **T188 on the console** (scripted, handheld, 1x, frame ahead off). With all its new switches unset, 5 of 5 starts got through the load from the field: 2 of 2 in its first test and 3 of 3 as the control in its third. With the 12 new lines of T187 and T188 plus `EDEN_UP_L1639_PARK_WAIT=1` all on at once, 1 of 3 got through: one start crashed 31 s into the load, the same kind of memory crash as the three hand crashes on T186, and one ended during the title movie with no crash file. The third test was cut after 6 of 8 starts. That is a count, not a verdict; the next step splits the thread priority lines from the rest. The one start with all lines on that got through walked faster (21.3 fps against 18.1 to 18.4) and had far fewer long frames after the load: one start, a hint. GrowingBlackBeans' thread priorities (`EDEN_GBB_PS5_PRIO=1`) take on firmware 12.40 (one start).
- **Missing plants, far trees and objects: a first lead.** Played by hand, near bushes, rows of far trees and some placed objects only show once Link swings the sword. An existing switch, `EDEN_NX2_NULL_SLOTS=2`, rebuilds two of five drawing programs that were translated with empty slots. With it, the far rows of trees stayed drawn the whole time Link stood in the field, in 2 of 2 starts, and never in the 2 starts without it (T188, one spot). They come out flat and sky blue, a second fault, so the switch stays out of the play settings for now. The scripted sword presses did not make Link swing, so the swing part of that test did not happen. Grass and speed (about 18.6 fps) were the same with and without it.
- **A lead for the crash in the load.** In the crashed T188 start and in one hand crash on T186, the hang watch shows the thread that finishes downloads from the graphics side holding the buffer cache lock while the GPU thread waits for that lock, and a game thread waiting the full 10 s for a page of game memory that had been moved out. One reading: the downloading thread itself waits for memory that only the blocked GPU thread could free. T190 adds log lines that name every thread in that wait, and `EDEN_UP_BC_DOWNLOAD_UNLOCKED=1` (off unless set), which brings the download's pages back in before the lock is taken. It first ran on the console on the evening of 15 November with the switch unset; the fix switch itself has not run yet.
- Built at the desk: T187 (an upload staging cap and texture collector fixes, plus the testers' patches below), T188 (eight upstream pieces, each behind its own switch), T189 (Lichii #1218, a fix for hangs at warps, on by default with `EDEN_UP_L1218_OFF=1` to turn it off, and a guard that stops a second, different game from starting in the same app session when a per-game settings file is involved) and T190 (above). Everything else new is off unless set, and none of them changes the shader store. T187 and T189 have not been on the console yet. Details in [BUILDS.md](docs/Vampinity/BUILDS.md).
- From others: T187 holds waveydude's W-10b low-memory guard for graphics pipeline builds and GrowingBlackBeans' 0901 and 0902 (thread priorities on the PS5). T188 holds ports of zortos293/Lichii #1816 (moonzzeyy), #1795 (zortos293, from jpkto's work), #1810 (the-cashman), #1783 (zortos293) with #1794 (RomainROCH), lethevimlet's oot-bc250 work (deleted buffers freed sooner; recent GPU-written images kept), Djihads80's 16-byte swizzle runs from Eglantine, and heydemoura's PS5 form of Lichii #1789 (cerroverb). T189 holds Lichii #1218 by Nanoc6, with PantACRO4life and zortos293.
- Source of T184 to T186 in `source/T184` to `source/T186`.

## 14 November 2026 (builds T184 to T186)

- Every count in this entry comes from scripted starts at 1x in handheld.
- **Frame ahead is off from now on.** With frame ahead on, the ground near Link loses its sunlight for one frame, again and again, and flags and cloth blink. At the field edge: 187 and 191 ground flashes in 150 s with it on, 0 and 0 with it off. At the gate view in the next area: 117 and 138 cloth blinks a minute with it on, 0 and 0 off (T185, scripted, handheld, 1x, two starts a side). That flicker is too much to keep, so the play settings and every test now run with frame ahead off. It costs about 3 fps in the field fights, 1.5 to 2 fps walking across the field and under 1 fps in the area after the field. With it off, house and village run at about 21 to 22 fps, the field at 18 to 21 and the area after the field at about 14.
- **The load from the field into the next area: a candidate.** T185 lets the graphics side read packed game memory straight through only while a load is going on (a load window), and gives the graphics driver a small reserve for its own buffers. With frame ahead off and the window closing after 10 quiet seconds, 6 of 6 scripted starts got through that load over two rounds, and the graphics thread never had to wait for memory. The same settings without the window got through 0 of 2, 2 of 2 and 3 of 4 in three rounds. The speed after the load is the same. Not through the scripted gate yet: in one of the six starts a game thread still waited 4 s inside the black screen. These settings are play settings v4.0, a candidate (`envs/Vampinity/play-v40.env.txt`, for T185 and newer).
- **A new game with the candidate:** 2 of 2 first starts on a new game got through the opening, the house door and into the village (T185; the second start ran just after midnight, on 15 November). Just a count.
- **With less memory free, the load still struggles.** We take memory away before the load as a stand-in for a long session. With 256 MiB taken the candidate got through; with 384 and 448 it got through but crawled for about a minute; with 576 it crashed (one start each). With 512 MiB: in one batch it got through 2 of 2 but ran under 1 fps for 2 to 4 minutes after the load, in another 1 of 2. With `EDEN_UP_DRAIN_TO_POOL=1` added, 2 of 2 got through in both batches, under 1 fps for 9 to 47 s. That line is not in the play settings yet.
- **Before the load window (T184):** v3.9 with the wait reclaim of T181 got through 12 of 12 starts in one round, but the graphics thread waited for memory in every start, for up to 7.4 s, and the reclaim was not what helped. Reading through all the time stopped those waits but cost 4 to 6 fps in the area after the field. That led to the load window.
- **Tried and parked:** letting the game draw its own 3D smaller (`EDEN_UP_GFX_SCALE_TIER`, T183) saved only 1.6 to 3.2 ms a frame and brought dark floor flashes.
- Built that night, run on 15 November: T186 (counters for where the frame goes, and two memory switches).
- From others: T184 holds ports of zortos293/Lichii #1517 (Zortos with Liomar Oliveira), #1531 (Zortos with Julius Bairaktaris, from stephenjayakar's #717), #1475 (RomainROCH), #863 (nemiward, plant shadows), #823 (janvitos) and #948 (danieljesus), the log line of #995 (Danny Ng) and the render pass idea of issue #1431 (ronaldpena007-ops), a pipeline count after an idea of lethevimlet, and waveydude's W-23 and W-24 probes, all off by default except the #1475 log fix, which is always on. waveydude's pack in place (W-20) ran against v3.9 on T184, two starts each; the run logs are in `runs/Vampinity`.

## 13 November 2026 (builds T138 to T183)

- **Test build T180 for testers**, with play settings v3.9 (`envs/Vampinity/play-v39.env.txt`). Every count of starts below comes from scripted starts at 1x, in handheld unless it says docked. None of it has been played by hand yet.
- **The crash at the house door on a first start: the cause is one graphics driver compile, and a change for it.** A few large drawing programs took up to 909 MB each while the driver compiled them. With the change they take 78 to 89 MB, and the picture is the same. After that, 2 of 2 scripted first starts got through into the village (T144, docked).
- **Played by hand, the builds still crash.** All six starts played by hand that day ended in a crash. The last three crashed at the load from the field into the next area.
- **The whole game's shaders can be built before play, once.** The list made from Fritchii's recipe has 119,524 records. The driver's disk cache slowed this step to about 5 a second after a minute or two. With our cache changes it held 55 to 60 a second for about four minutes, then about 12. On our console the 29,167 that were still missing took 1,505 seconds (about 25 minutes), and the next start skipped the step. The whole set took about 55 minutes of pass time over nine starts, plus about 12 minutes to convert the recipe the first time; from empty in one go it has not been timed. On 14 Nov the scripted starts so far on T181 reused the stored 78,722 pipelines at boot (6 of 6). Restart the app after that step: the one game started in the same session crashed. We have not checked yet whether play uses these shaders. v3.9 does not switch this step on.
- **The load from the field into the next area:** 2 of 12 scripted starts got through on T166 and T173. On T175 to T180 more got through, but those starts mixed several builds and settings, so we no longer add them up. With the settings that pack idle game memory sooner alone, 2 of 2 got through on T177 and 2 of 2 on T179. With all of v3.9: 3 of 3 on T180, 2 of 3 on T181 and 1 of 2 on T184 (14 Nov, not shared), and the starts that got through still froze for 3 to 9 s at that load.
- **Why the others died:** a thread waited 10 seconds for one 2 MiB block of memory and gave up. The parts that free memory only run when a frame is drawn, and no frame is drawn during that wait. A change for this is in T181 (`EDEN_UP_WAIT_RECLAIM=1`: a thread that waits for memory gets graphics memory freed without waiting for a frame). With it, 3 of 3 scripted starts got through that load; with v3.9 alone in the same round, 2 of 3. Not played by hand yet.
- **The next area runs at about 15 fps** (14.6 to 15.6 in the three v3.9 starts). The graphics work there takes about 41 ms a frame, against 17 to 19 in the field. Not solved.
- Built, not run yet: T182 (seven Lichii ports for draws and waits) and T183 (T182 plus four more ports, smaller host stacks after an idea of CHI-GETSU, and a switch that answers the game's graphics scale question, so it can draw its own 3D smaller). All off by default; both keep the shader store. Source in `source/T181` to `source/T183`.
- The scripted routes and the village steering scripts are in `tools/Vampinity/routes`.
- From others: the shader set is built on Fritchii's recipe. waveydude's switch for when the driver cache is written is in the build, and v3.9 uses our every-1024 mode of it. His pack in place (W-20) and two-slot guard are in the build, off by default, and his ASTC scan change is now on by default. GrowingBlackBeans' early guard is in v3.9 and the read sync from GrowingBlackBeans is in the build. Two ideas from heydemoura's heap memory research (his pull request 104 to EglantinePS5) are in the build, off by default. One memory block size for all pools, from lethevimlet's BC-250 work, is in the build, off by default. Many ported fixes come from the Lichii contributors; in T182 and T183 Zortos' #1515, #1516, #1519, #1520, #1521, #1585 and #1436 (several from Lucas Borges' #1161), #1586 (with work by jpkto, DahBard, skolvolt and lucastaonline) and DuskDarf1's PR #1639. Also in T183: yuri2301's frame overlap reads, waveydude's W-05 (no extra memory wait on pipeline builders) and smaller host stacks after CHI-GETSU's idea.

## 12 November 2026 (builds T132 to T134)

- **The black screen after the opening movie on a fresh install is solved with two settings.** On default settings every first start froze or crashed there (3 of 3). With the two settings, 3 of 3 got past it.
- **The title movie plays smoothly with two settings.** Frames thrown away: 652 and 709 without them, 74 and 87 with them.
- **A crash after longer play:** with the fix on, 2 of 2 runs played on through a forced memory shortage. Without it, 2 of 2 crashed. Off by default, not yet seen in real play.
- **The house door on a fresh install, from the second start on: solved in our tests.** With the best settings, which build drawing programs on two threads instead of eight (one in one test group), 16 of 16 second and third starts got through the door into the village. Not on by default yet.
- **Still open: the very first start on a fresh install.** In the morning's first round 1 start out of 6 got through. With the best settings of the day, 4 of 9 first starts reached the village; the others crashed, most of them at the house door, about nine to ten minutes in. None of the 4 had memory to spare.
- **What causes it:** on a first start about 40 new drawing programs are built at once at the door, and memory use jumps by half a gigabyte or more in a few seconds. Two safety settings (wait for memory, take it from the emulator's other memory stores) and a setting that frees memory earlier did not stop it: 2 of 4 first starts with all of them on. A cap on how many are built at once was written, but two reviews showed it would not help: building one at a time was already measured that day and the wave was just as large. Next is a build that measures which part of the emulator takes the memory.
- Built, not tested yet: movie errors no longer end the game (T133).
- From others: one of the first-start settings is GrowingBlackBeans' trust copy; the movie error fix comes from Fritchii; the setting that frees memory earlier is a port of a Lichii fix.

## 11 November 2026 (builds T117 to T131)

- **T120 shared with testers.**
- **Icons and hearts that jump for one frame in the fast settings:** a guard removes them (about 10 to 15 jumps a minute of walking without it, none with it, two test walks each). It costs about 3% speed.
- **Less stutter when you close the pause menu in a wide area:** worst frame 126 to 257 ms, against 316 to 468 ms. A first test, with other settings on at the same time; not yet confirmed on its own. Not a crash fix.
- **A hitch the first time a prepared shader is drawn:** 3 to 7 ms per shader with the new setting, against 60 to 90 ms.
- **Faster in the village** with Fritchii's usage tracker: 1.45 fps more at one test spot, 0.60 at another.
- Built, not tested yet: games that need no key or firmware files start without them, and settings files saved on Windows.
- From others: waveydude's three crash fixes for long sessions (not yet needed in our tests). That start path is a port of heydemoura's work.

## 10 November 2026 (builds T87 to T116)

- **The default settings got about 10% faster:** 16.3, 16.2 and 15.9 fps from the house door into the village, against 14.0 and 15.2.
- **Shader builders wait for memory instead of failing.** 3 of 3 runs got through a forced shortage.
- **The cause of the glitches in the fast settings found.**
- **Preparing all the game's shaders ahead:** converting the set took 67 minutes, now about 4. Not ready for play.
- From others: the 10% comes from EdGlantine-PS5. waveydude's six memory commits are in every build since T113. GrowingBlackBeans brought in notquiteog's fix for bright flashes. The shader set builds on Fritchii's recipe.

## 9 November 2026 (builds T78 to T86)

- **Each session builds on the last one:** the list of built graphics is saved every 20 seconds.
- **Faster default settings:** about 14.2 fps from the house, against 12.4 with test build 2.
- **Shorter freezes the first time you see a place**, once the app has seen it before: the worst went from about 4.2 seconds to 1.0.
- **Long hitches while walking:** one large texture is kept instead of decoded again. Worst frame 448 ms before, 110 to 173 ms now.
- New, optional: running one frame ahead, about 14% faster.
- From others: the 20-second save, part of the faster settings, the frame-ahead fix and finding the cause of the hitches are GrowingBlackBeans' work. The freeze fix builds on an idea from Fritchii and zmckenney.

## 8 November 2026 (builds T53 to T77, test build 2)

- **No dark full-screen flashes in the default settings:** none in 12 walks, where there were 4 to 5 every 35 seconds.
- **The movies are much closer to sync:** the first 10 seconds of the title movie took 23.3 seconds, now 10.0.
- **The out-of-memory crash after New Game:** 4 of 4 runs got through 5 minutes.
- A freeze at the first rupee is fixed.
- Slower: about 11 to 13 fps walking.
- From others: the frame wait is Duck912's, the movie fixes come from Lichii, the memory fix from viejunerd, the rupee fix from GrowingBlackBeans.

## 7 November 2026 (builds T40 to T52, test build 1)

- **Tree leaves, ferns and ground plants are drawn again.**
- **Big white flashes much reduced.** Dark one-frame glitches remained.
- From others: the work moved onto viejunerd's v1.219.020; the flash settings come from Lichii.

## 6 November 2026 (builds up to T39)

- **The white fog over everything is gone.**
- **Dark areas and black water gone.**
- The game's own upscaler runs on the PS5 at full speed.
- A test bench that runs on the PS5 by itself.
- From others: the lead for the fog fix came from Lichii.

## 5 November 2026 (first builds, before the T numbers)

- **The game gets past its stop at 98% loading** with one setting (7 of 7 starts).
- The title screen and New Game work.
- From others: built on viejunerd's EglantinePS5 test build 01.219.007.

## What is next

- The very first start on a fresh install: find out which part of the emulator takes the memory at the house door (a measuring build is next), then fix that. This holds the alpha back.
- The opening should play smoothly on a first start.
- Then: speed in wide open areas.
