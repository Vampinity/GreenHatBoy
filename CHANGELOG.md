# Changelog

Newest first, with each day's test builds in brackets. Results are from our own tests on a base PS5 (firmware 12.40, docked, full resolution). Credits in full: [CREDITS.md](CREDITS.md).

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
