# Who did what

The full list behind the short version on the [front page](README.md). It is long on purpose: this project stands on a lot of other people's work, and each of them should be able to find their part here.

## [Vampinity](https://github.com/Vampinity) · started and runs the project

Builds every version, tests it on a real base PS5 and writes the fixes that come out of that. The first week, 5 to 11 November 2026, in numbers:

| | |
|---:|---|
| **67 hours** | of PS5 time in automated test batches |
| **988** | test runs, in 260 batches |
| **53 hours** | of recorded picture checked frame by frame, about 11 million frames |
| **122** | test builds |
| **463** | patches in the build: own work and ports of other people's work |
| **458** | switches, each tracked in a ledger with its runs and its verdict |

What came out of it:

- **A test bench that runs by itself on a real PS5.** It sets up each run, starts the game, plays a scripted walk, records the picture and checks every frame for flashes and stutter. That is where the numbers above come from.
- **Found what causes the flashes in the fast settings.** The game's own worker threads rewrite graphics memory while the previous frame is still being drawn. A test version that made them wait showed no flashes at all. The guard built on that finding removes the large bright flashes at no speed cost the tests could measure; short dark flickers still show in most runs. It sits on top of GrowingBlackBeans' frame race fix.
- **Freezes cut from over 4 seconds to about 1** in places the console has seen before. On the PS5 the freeze turned out to be shader translation, not the graphics driver, so the app now translates before play. The idea comes from Fritchii and zmckenney; the PS5 version is new. On by default.
- **No dark full-screen flashes in the default settings.** A meter that counts flashes in the recorded picture traced them to timing, and proved Duck912's frame wait on the PS5: 0 flashes in 8 of 8 runs at the pond.
- **About 1.3 fps from choosing which processor cores do what**: 13.9 to 14.3 fps became 15.0 to 15.7 on the walk from Link's house (base PS5, 12.40, docked). GrowingBlackBeans measured +18% to +20% with the same layout on his console.
- **The whole game's shaders converted in about 4 minutes where it took 67**, and in 860 MB where it took 4.3 GB. Opt-in and not for play yet; built on Fritchii's whole-game recipe.
- **Measured what holds open areas back, and where memory runs out** (11 November, first measurements). In heavy views the limit is the emulator's own work for each object, not the PS5's graphics chip. Around an area change the free memory drops to a few MiB, and on a wide field the pause menu makes the emulator throw away and rebuild about a thousand images. Fixes for both are being tested.

## [GrowingBlackBeans](https://github.com/GrowingBlackBeans) · collaborator

The project's second developer. Since 7 November he has tested the builds on his own base PS5, traced several of the worst bugs and written the fix that lets the game run one frame ahead.

- **Wrote the fix that makes the fast settings possible** (`EDEN_GBB_TRUST_COPY`). Running one frame ahead used to crash. He found why: when the emulator picked a list of drawing commands back up, it read the list from memory again and got the next frame's commands. His own check proved the fix safe: 0 of 7,675,038 copies had changed. On his console (firmware 13.60, Link's house and a lap of the village) 26.1 fps became 32.6 standing and 20.4 became 23.4 walking.
- **Made each session build on the last one** (`EDEN_GBB_PIPELINE_SAVE_20S`, on for everyone). He found that closing the game from the PS menu threw away the list of graphics the session had built, so the next session stalled on the same walk again. His change saves that list every 20 seconds: on his 75-second walk, 8.3 seconds of stalls became 1.8. It is also why a start after a crash is smoother.
- **Found two freezes.** The freeze at the first rupee: a warning was being written to storage hundreds of times a second (23,692 lines in 35 seconds); his patch writes it once, and it has been in every build since. And a freeze in the intro with diagnostics on, which he traced to two log lines written while a lock was held; the fix in the build was written from his finding.
- **Found what caused the long hitches while walking.** One very large texture was thrown away and decoded again every 20 to 25 seconds, and each time the walk hitched for 0.9 to 1.6 seconds. The default settings now keep it, which on our console took the worst frame from 448 ms to between 110 and 173 ms.
- **Tests on firmware 13.60, which we cannot test ourselves.** He showed that 13.x needs a smaller memory setting (the 12.x value froze the game for him); that value is what `env-13x.txt` ships. His own everyday settings are in the build as `env-gbb-everyday.txt`, and he measured +18% to +20% from the processor core layout on his console.
- **Traced the pond crash and the flashes of one frame ahead.** He reproduced the crash (4 of 6 loads) and showed where the command stream went wrong. Later he showed that the flashes that remain come from data the game rewrites for the next frame, which pointed the way to the copy guard.
- **Brought in and tested two fixes against bright flashes** (`EDEN_GBB_NAN_GUARD`, `EDEN_GBB_POSITION_INVARIANT`), from notquiteog's Dragoon work. In a three-run test here, bright flashes went from 3 of 3 runs to 0 of 3; three runs is a pointer, not proof. Optional and still under test.

## [waveydude](https://github.com/waveydude)

He wrote the heap and driver memory fixes in the build, and tests well past the first forest on his own base PS5. His logs show where memory runs short.

## Standing on other people's work

- **[viejunerd](https://github.com/viejunerd)**: the EglantinePS5 NUP build this project is based on, and a crash fix.
- **[heydemoura](https://github.com/heydemoura)**: EglantinePS5, the PS5 app this all runs in.
- **[Djihads80](https://github.com/Djihads80) and the Eglantine team**: the emulator core. **The Eden team** before them.
- **BlackBearReloaded**: ProsperoEden and the PS5 app base the app is packaged with. **drakmor**: ShadowMountPlus.
- **EdGlantine-PS5**: skipping out-of-date texture uploads, the speed gain in the default settings.
- **[Frizti](https://github.com/Frizti) / [Fritchii](https://github.com/Frizti/Fritchii)**: the shader preparation idea, the whole-game shader recipe and several speed ideas.
- **[zortos293](https://github.com/zortos293) and the Lichii contributors**: the movie fixes, the shader preparation idea (zmckenney) and many ported ideas.
- **exploitizm**: the PS5 driver path that draws the leaves and plants.
- **notquiteog (Dragoon)**: the fix against bright flashes that GrowingBlackBeans brought in.
- **[Duck912](https://github.com/Duck912)**: the frame wait that removed the dark flashes.
- **[mihawk-99](https://github.com/mihawk-99)**: PS5_Lichii and the PS5 graphics driver work.
- **[lethevimlet](https://github.com/lethevimlet)**, **justin-wq1337**, **javocsoft**, **kraibse** and **nxnative**: ideas and fixes named in the build notes.
- **Testers who sent logs**: [Alecsg09](https://github.com/Alecsg09), [remolatron](https://github.com/remolatron).
- Everyone else whose code is in the build: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Most of the new code is written with Claude, some first drafts with Codex. Every build is tried on a real console before it goes up, and the notes for each build say which changes are not tested yet.
