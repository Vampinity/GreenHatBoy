# Changelog

Newest first, with each day's test builds in brackets. Results are from our own tests on a base PS5 (firmware 12.40, docked, full resolution). Credits in full: [CREDITS.md](CREDITS.md).

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
- Built, not tested yet: starting without keys and firmware files, and settings files saved on Windows.
- From others: waveydude's three crash fixes for long sessions (not yet needed in our tests). The start without keys is a port of heydemoura's work.

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
