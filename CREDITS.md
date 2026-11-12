# Who did what

The full list behind the short version on the [front page](README.md). It is long on purpose: this project stands on a lot of other people's work, and each of them should be able to find their part here.

## [Vampinity](https://github.com/Vampinity) · started and runs the project

Builds every version, tests it on a real base PS5 (the standard model, not the Pro) and writes the fixes that come out of that. From 5 to 12 November 2026, in numbers (counted on the morning of 12 November):

| | |
|---:|---|
| **88 hours** | of PS5 time in automated test batches |
| **1,210** | test runs, in 340 batches |
| **71 hours** | of recorded picture checked frame by frame, about 15 million frames |
| **133** | test builds |
| **498** | patches in the newest build: own work and ports of other people's work |
| **515** | switches, own and ported, each tracked in a ledger with the runs that used it |

What came out of it:

- **A test bench that runs by itself on a real PS5.** It sets up each run, starts the game, plays a scripted walk, records the picture and checks every frame for flashes and stutter. That is where the numbers above come from.
- **The log pool in [`runs/`](runs/).** The packer that takes private details out of a run before it goes up, and the index of all runs, are his. The folder layout was GrowingBlackBeans' idea.
- **Found what causes the flashes in the fast settings.** The game's own worker threads rewrite graphics memory while the previous frame is still being drawn. A test version that made them wait showed no flashes at all. The guard built on that finding removes the large bright flashes and the jumping icons, at about 3% speed standing in the village; short dark flickers still show in most runs. It sits on top of GrowingBlackBeans' frame race fix.
- **Freezes cut from over 4 seconds to about 1** in places the console has seen before. On the PS5 the freeze turned out to be shader translation, not the graphics driver. (Shaders are the small drawing programs the game uses, and the emulator has to translate each one for the PS5.) So the app now translates them before play. The idea comes from Fritchii and zmckenney; the PS5 version is new. On by default.
- **No dark full-screen flashes in the default settings.** A meter that counts flashes in the recorded picture traced them to timing, and proved Duck912's frame wait on the PS5: 0 flashes in 8 of 8 runs at the pond.
- **About 1.3 fps from choosing which processor cores do what**: 13.9 to 14.3 fps became 15.0 to 15.7 on the walk from Link's house (base PS5, 12.40, docked). GrowingBlackBeans measured +18% to +20% with the same layout on his console.
- **The whole game's shaders converted in about 4 minutes where it took 67**, and in 860 MB where it took 4.3 GB. Opt-in and not for play yet; built on Fritchii's whole-game recipe.
- **Measured what holds open areas back, and where memory runs out** (11 November, first measurements). In heavy views the limit is the emulator's own work for each object, not the PS5's graphics chip. Around an area change the free memory drops to a few MiB (megabytes), and in a wide open area the pause menu makes the emulator throw away and rebuild about a thousand images. Fixes for both are being tested.
- **Found why a fresh install crashed or froze on its very first start** (12 November). With nothing prepared yet, the first scene after the opening movie keeps the graphics side busy for about 25 seconds. The game does not wait that long, runs ahead and overwrites commands that were still waiting to be drawn. With two settings, 3 of 3 first starts got past that point in the test of 12 November, against 0 of 3 without. The two settings are not on by default yet.
- **Made the title movie play smoothly** (12 November). Two settings took the movie frames that were thrown away from over 650 to under 90 over the whole movie, in both test starts. They are not on by default yet either.

## [GrowingBlackBeans](https://github.com/GrowingBlackBeans) · collaborator

The project's second developer. Since 7 November he has tested the builds on his own base PS5, traced several of the worst bugs and written the fix that lets the game run one frame ahead. Since 11 November his runs, patches, tools and notes are in this repo, in his own folders.

| | |
|---:|---|
| **148** | test runs on firmware 13.60, about 4 hours of play: 132 from 7 to 11 November on one fixed route played by hand (from the house into the village and a loop to the water), and 16 in the night of 11 to 12 November |
| **18** | patches on top of T120 ([`patches/GrowingBlackBeans/`](patches/GrowingBlackBeans/)), one of them a port of a Lichii fix, all meant to be off unless their switch is set |
| **15** | dev builds of his own (t83-gbb8, t85-gbb5 to gbb11, t120-gbb1 to gbb7). They are test builds for people who already know the setup |

- **Wrote the fix that makes the fast settings possible** (`EDEN_GBB_TRUST_COPY`). Running one frame ahead used to crash, because the emulator read a list of drawing commands from memory again and got the next frame's commands. On his console it took walking from 20.4 to 23.4 fps.
- **Made each session build on the last one** (`EDEN_GBB_PIPELINE_SAVE_20S`, on for everyone). The graphics a session has built are now saved every 20 seconds, so they survive closing the game. On his walk, 8.3 seconds of stalls became 1.8. It is also why a start after a crash is smoother.
- **Found three freezes and hitches**: the freeze at the first rupee (his fix is in every build since), a freeze in the intro with diagnostics on, and a hitch every 20 to 25 seconds from one large texture being decoded again and again.
- **Tests on firmware 13.60, which we cannot test ourselves.** The smaller memory setting in `env-13x.txt` comes from him, and his everyday settings ship as `env-gbb-everyday.txt`.
- **Traced the pond crash and the flashes of one frame ahead**, which pointed the way to the copy guard, and brought in two fixes against bright flashes (still under test).
- **Wrote the log toolkit `eglog`** ([`tools/GrowingBlackBeans/eglog/`](tools/GrowingBlackBeans/eglog/)) and proposed the folder layout of the log pool. The toolkit turns a run's log into a one-page report and tells whether a difference between two settings is bigger than the normal spread between identical runs.
- **Wrote down what a base PS5 can and cannot do with this game** ([`technical-limits.md`](docs/GrowingBlackBeans/technical-limits.md)), checked both sets of runs again from the logs ([second opinion](docs/GrowingBlackBeans/review-2026-11-11-second-opinion.md)), and **collected the memory readings of 1,055 runs** (968 of them Vampinity's). With Vampinity's squeeze tests that put the spare memory in the first village at about 0.8 to 1 GB, lowest at the door into the village ([`memory-wall.md`](docs/GrowingBlackBeans/memory-wall.md)).
- **New measuring switches** (patches 0921 to 0923: a breakdown of the graphics thread's time, a per-second summary and a timeline of each frame, a recorder for the two seconds before a slow frame) and **two frames in flight** (0924): +2.0 fps walking in his night session, with flicker until a guard for two frames exists ([night review](docs/GrowingBlackBeans/review-2026-11-12-night.md)).

## [waveydude](https://github.com/waveydude) · collaborator

He started as a tester and now also writes fixes for the build, most of them for memory and crashes. He tests on two base PS5s and plays much further into the game than our test routes go: on 13.60 one session ran 24 minutes through later areas without a crash.

| | |
|---:|---|
| **2** | base PS5s he tests on, firmware 13.60 and 9.40 |
| **6** | runs shared as full logs on 11 November: four sessions on 13.60 (about 88 minutes in all) and two starts on 9.40, in [`runs/waveydude/`](runs/waveydude/) |
| **12** | messages with fixes, logs and numbers on the old project thread, 10 to 12 November |

What he made that is in the build:

- **Memory fixes that are always on**, since T113 and in the T120 testers' build. The graphics driver asks the app for memory before it gives up, a shader build that runs out of memory fails on its own instead of ending the game, and a guard stops a broken count from asking for about 80 GiB.
- **Memory of their own for big requests** (`EDEN_HEAP_LARGE_KIB`, `EDEN_HEAP_LARGE_MIB`). A large request gets its own memory, which goes straight back when freed, instead of a place inside the heap (the emulator's own memory store). On his console, from the same save, starting at 256 KiB instead of 8 MiB took free memory after loading the first village from about 200 MiB to 1.9 GiB. The table behind it grew from 1,024 to 8,192 entries on his advice. Our short walks showed no gain; long sessions are where it should count.
- **Three crash fixes from his own play** (T130 and later: `EDEN_UP_JIT_SITE_SHARDS`, `EDEN_UP_ASTC_SCAN_CHUNKS`, `EDEN_UP_NEW_WAIT_MS`). The JIT's jump table (the JIT turns Switch code into PS5 code) is split into 128 parts, a texture check works in 16 KiB pieces, and memory waits share one deadline. The first two each removed a large request, 62 MiB and 32 MiB, that had ended one of his runs (one run each so far).
- **More changes, all off by default**: render targets (the images the game draws into) let go under memory pressure, pipeline builds (a shader plus its settings) that take turns when memory is short, two more driver patches, and a lookup that remembers its last answer.
- **His full memory build, tested here as T125**: on our pause-menu route it deleted about 22% less and left more memory free, at the same speed (one run each).

What his logs and tests showed:

- **The black screen on 9.40 is a first start that hangs** on an empty shader store, not a firmware limit.
- **Every new build threw away the stored shader translations**, so the shader step of a first start took him 158 to 305 seconds instead of 36 to 38. A fix is planned for the next build.
- **Frame generation roughly halves the real frame rate** in a heavy view: 11 to 12 fps against 22 to 28.
- **A counter in our memory ledger went below zero** in all his 13.60 runs. Our bug; his logs showed it.

He reports a bad result as fast as a good one: when his own branch crashed two minutes in, he asked us to hold off. He shares save slots so we can test past our own route.

## Standing on other people's work

Code from these projects is ported into the build, most of it behind switches that are off by default. Each port is named in the build notes.

- **[viejunerd](https://github.com/viejunerd)**: the EglantinePS5 NUP build this project is based on, a crash fix, and the ReserveOver memory fix. His repo also hosted the thread where this project grew.
- **[heydemoura](https://github.com/heydemoura)**: EglantinePS5, the PS5 app this all runs in. Ported from his code: starting without keys and firmware files (his PR #94), and two changes to how the graphics work is split and handed over.
- **[Djihads80](https://github.com/Djihads80) and the Eglantine team**: the emulator core, and translating new shaders on separate threads. **The Eden team** before them.
- **BlackBearReloaded**: ProsperoEden and the PS5 app base the app is packaged with. 22 ports from ProsperoEden: memory cleanup, the pipeline cache, image pages, texture decoding and command reading ahead. **drakmor**: ShadowMountPlus.
- **EdGlantine-PS5**: skipping out-of-date texture uploads (the speed gain in the default settings) and a faster shader lookup.
- **[Frizti](https://github.com/Frizti) / [Fritchii](https://github.com/Frizti/Fritchii)**: the shader preparation idea, the whole-game shader recipe, the usage tracker, the water flicker fix, and several speed ideas.
- **[zortos293](https://github.com/zortos293) and the Lichii contributors**: the movie fixes, the shader preparation idea (zmckenney), a faster path for repeated draws, and many more ported ideas. jpkto, for the upload batching.
- **[mihawk-99](https://github.com/mihawk-99)**: PS5_Lichii and the PS5 graphics driver work; ported from it: memory held by idle parts given back, and the JIT's rarely used code moved aside.
- **PlayTendoh**: PS5 graphics driver changes for submitting and waiting.
- **exploitizm**: the PS5 driver path that draws the leaves and plants.
- **notquiteog (Dragoon)** and **NX2navi**: the fix against bright flashes that GrowingBlackBeans brought in.
- **[Duck912](https://github.com/Duck912)**: the frame wait that removed the dark flashes.
- **[lethevimlet](https://github.com/lethevimlet)** (oot-bc250), **justin-wq1337** (the audio crackle fix), **javocsoft**, **kraibse**, **cLohan** and **nxnative**: ideas and fixes named in the build notes.
- **Testers who sent logs**: [Alecsg09](https://github.com/Alecsg09), [remolatron](https://github.com/remolatron), [phtibuios-stack](https://github.com/phtibuios-stack).
- Everyone else whose code is in the build: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Most of the new code is written with Claude, some first drafts with Codex. Every build is tried on a real console before it goes up, and the notes for each build say which changes are not tested yet.
