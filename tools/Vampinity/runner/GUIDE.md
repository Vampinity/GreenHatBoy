# auto-run (the original guide, cleaned for sharing)

Read README.md first: it says what this folder is, what it has not proven yet, and how a cold start works.
This is the guide I wrote for my own copy of the runner, with my address and folders taken out. Wherever it
says "the Mac", any macOS or Linux computer is meant. The console's address comes from `runner-config.json`
(`--host` still overrides it).

The Mac runs a list of agreed EglantinePS5 tests by itself: no closing the app, no Launch, no Continue. It saves everything and tells you the results. You only come back when something needs you.

This copy has not run on a console yet (README.md, "Not proven on a console yet"), so do the first run below before trusting a long batch.

## What you need

- A build with the test settings (`EDEN_TEST_BOOT`, `EDEN_TEST_SCRIPT`, `EDEN_TEST_RECORD`, `test-quit`). On an older build the first test ends in "game did not start" and then a stop, because the app ignores `test-quit`.
- The PS5 on, jailbroken, on the home screen, with websrv and ftpsrv running.
- OBS open with the capture card, WebSocket on, no password. Without OBS the tests still run, with no frames.

## First run

Two small tests, in this order. Write each plan as a small file of your own.

**1. Launcher only, no game.** It asks for a title no game has, so the app opens its launcher with "Configured game was not found" and nothing is emulated. After 30 seconds the tool closes it. The plan, saved as `launcher-only.json`:

```json
[{"name": "launcher-only", "title": "FFFFFFFFFFFFFFFF", "seconds": 30}]
```

```
cd tools/Vampinity/runner
python3 auto-run.py launcher-only.json --host CONSOLE
python3 auto-run.py launcher-only.json --host CONSOLE --go
```

The first line only prints the plan and sends nothing to the console. The second runs it. It ends as "game did not start", with `development game FFFFFFFFFFFFFFFF not found`: for this test that is the right result. What matters is that the app closed by itself and the TV shows the home screen with no CE error.

If it says the app looks open while the TV shows the home screen, that is the leftover from a crash restart (see "If the app is open"): add `--confirmed-closed`.

**2. The game for 60 seconds.** Only after test 1 went well: the same plan with your game's title, `"seconds": 60` and your own `env` lines. Watch the TV: the game should start by itself and close again after 60 seconds.

## The plan file

A JSON list, one entry per test.

| Key | Needed | What it does |
|---|---|---|
| `name` | yes | Name of the test, also used in the folder name |
| `title` | yes | 16 hex digits of the game, for example `0400486024DEC000`. It must be a `.nup`, `.nsp` or `.xci` straight in the game files' `roms` folder: a game that is a folder isn't found. All zeros is refused, because the app's search would take any file it can't read for that title |
| `env` | no | The `env.txt` lines. These replace `env.txt` for the test, so list every switch you want. Two lines are for the runner only and never reach `env.txt`: `EDEN_TEST_COLD=1` (a cold start) and `EDEN_TEST_COLD_SET=1` (README.md, "A cold start") |
| `seconds` | yes | Time limit, counted from `/launch`. A script's clock starts later, so leave room for the boot |
| `script` | no | Pad script file, next to the plan. Lines: `<seconds> <BUTTON> <hold_ms>` or `<seconds> LSTICK <x> <y> <hold_ms>` (`RSTICK` too), `#` for comments. See below |
| `may_hang` | no | `true` for a test that can hang the GPU. At most one per console boot |
| `record` | no | `true` saves the pad events of this run, see below. Not together with `script` |
| `note` | no | Your own note, shown when the plan is printed |

A typo in a key stops the plan before anything happens, so `may_hang` can't silently fall away.

Script details:

- Seconds count from the guest starting, not from "game loaded": the shader cache builds between the two and can take minutes.
- They are wall clock, so a route drifts if the frame rate differs from when it was recorded.
- Sticks are the pad's raw 0-255: 128 is centre, 0 is left and up.
- With the first tester's button mapping CROSS is the game's B, so at the title it does nothing useful (found 6 Nov, first real script run). Use the game's own name `A` to confirm.
- Buttons are `CROSS CIRCLE SQUARE TRIANGLE L1 R1 L2 R2 L3 R3 OPTIONS CREATE TOUCHPAD UP DOWN LEFT RIGHT`, or the game's own `A B X Y L R ZL ZR PLUS MINUS LEFT_STICK RIGHT_STICK`, which follow the game's button mapping. Capitals only.
- The tool checks a script by the app's own rules before it starts, because one unreadable line makes the app drop the whole script. If the app still refuses or skips one, the test runs on with no presses and the summary says so under Notes.
- A script only plays in the game this run booted. Anything started by hand from the launcher gets no presses.

## Video

Every test with frames is also recorded through OBS, into the run's folder as `video.*`. `video-check.py` then scans every frame and writes `video-check.txt`, `video-check.jpg` (a sheet of the worst moments) and `video-check.order.txt` (what each picture on the sheet is). It finds flashes, black, white, noise, tile holes and freezes that timed frames miss. Its scores are pointers: look at the sheet. Videos from older batches are moved to the folder named in `folders.video_trash` at the start of a test (with none set they stay where they are); reports and sheets stay. Under 8 GB free there is no video.

## How a test ends

| Ending | What it means | What the tool does |
|---|---|---|
| Time limit | It ran the whole time. If a GPU wait is being logged right then, the tool holds off a few seconds: it either ends, or reaches 30 s and is a freeze | Closes the app, next test |
| Crash | A crash file appeared | Saves the crash set, closes the launcher it came back in, next test. If the report says the app closes, it uses up one extra start first: the app then opens the launcher once, whatever `env.txt` says |
| Game did not start | Still no game after 120 s, or at the time limit if that comes first | Closes the app, next test |
| **Freeze** | `has waited 30 s` or more in a log | **Stops the batch** |
| **GPU device lost** | `DEVICE_LOST` in a log or crash report | **Stops the batch** |
| **System error** | App gone or 75 s of log silence, and no crash file. Or a crash report said the app starts again and it didn't. This is the CE-108255-1 case | **Stops the batch** |
| **App restarted** | New process, no crash file, so nothing says why | **Stops the batch** |
| **No answer** | `/launch`, `test-quit` or the console itself gets no reply. Or the app took `test-quit` and its `eden_log.txt` still grows when `--quit-wait` is over: it may still be running | **Stops the batch** |

A stop means: notification (settings: notify.command) straight away, `env.txt` put back as it was, logs saved, no more tests. It does not send `test-quit` and does nothing else to the console. The next steps are yours.

If a save was on its way back at that moment (see "One save for every test"), it finishes first and `env.txt` goes back after it. Nothing new is started.

## When the app counts as closed

After `test-quit` the tool waits until the app is really gone. There are two cases.

- **The PS5 took the app's sandbox mounts away.** The process is gone. This is the normal close after a fresh console boot, and it counts at once.
- **The mounts stay.** That happens after a crash restart, and on the console it has then stayed that way for later starts too, until a reboot. The app then counts as closed when all three hold: it took `test-quit` away, `--close-floor` seconds (6) have passed since, and none of its three logs (`eden_log.txt`, `stderr.log`, `heap.log`) has grown for `--close-quiet` seconds (4). The app forces its own exit 3 seconds after taking the file, so 6 is twice that. Never earlier.

Before this the second case always waited the whole `--quit-wait` (20 s). `--close-quiet 0` gives that back.

If `eden_log.txt` still grows when `--quit-wait` is over, the tool looks at the boot trace once more. A new process there means the app crashed on its way out and came back: the tool asks that one to close, once. Otherwise the batch stops ("its logs still grow"), because the game may still be running. Only `eden_log.txt` counts for this stop. `stderr.log` and `heap.log` are rewritten by a new process before its boot trace is new, so those two growing can simply be a restart.

## After a stop

The next `--go` refuses until you say you've looked.

1. Look at the TV and at `summary.md`.
2. Press OK on a CE error if there is one. After a GPU hang, reboot and jailbreak again. A hang has frozen the whole console within minutes before.
3. Run again with one of these:

| Add | When |
|---|---|
| `--new-boot` | The console has been rebooted. Also frees the may-hang test for this boot |
| `--clear-stop` | No reboot was needed, you've looked and it's fine |

If the console was gone, `env.txt` could not go back and the summary says so. The app won't boot the test game by itself from a left-over `env.txt`, because it only boots when the tool leaves `test-boot-once` for that one start. But the test's switches stay on for everything you play until you run this:

```
python3 auto-run.py --restore-env --host CONSOLE --go
```

The tool refuses new tests until that's done. The same goes if the Mac was switched off in the middle of a run.

## If the app is open

The tool won't touch an open app. It stops before writing anything and tells you. Then either:

| Add | When |
|---|---|
| `--close-open-app` | Close it with `test-quit` and go on. Only works on an app started with test settings, like one left by a cut-off run. An app you opened yourself ignores `test-quit`: close that one by hand |
| `--confirmed-closed` | You can see it's closed |

The second one is there because of a PS5 quirk: when you close the app by hand after a crash restart, its sandbox stays mounted until the next launch, so it still looks open. The tool knows this after its own crash restarts and doesn't ask.

The same check covers other games: `/launch` kills whatever game is open, so the tool stops if it sees one.

## Risky tests

Mark any test that can hang the GPU with `"may_hang": true`. Printing the plan warns you, and you get a notification when it starts. Two in one plan is refused. A second one on the same console boot is refused until you add `--new-boot`. The tool can't see a reboot itself, so that flag is your word for it.

Put the risky test last: if it hangs, the tests after it don't run.

## Recording a route

Play the route once, with the tool saving it:

```json
[{"name": "route-outside", "title": "0400486024DEC000", "env": ["EDEN_NX2_NO_MESH=1"], "seconds": 300, "record": true}]
```

Start it with `--go`, take the controller, and play. The app closes at the time limit, so give yourself enough. `recorded-input.txt` ends up in the run's folder. Use that file as the `script` of later tests. While a script holds a press the real controller isn't read, so don't count on stepping in during a long stick hold.

## Where everything lands

`<folders.out_root>/auto-<date>-<time>-<plan>/`

- `summary.md`: the one page. `summary.json`: the same for scripts
- `batch.log`: what the tool did and when
- `env-before/`: the `env.txt` files as they were, `config-before.json`: the app's settings
- `run62-<test>/`: one folder per test, numbered on from your earlier runs. It has `env.txt`, `eden_log.txt`, `heap.log`, `stderr.log`, `boot-trace.txt`, any `crash-*` files, `frames/`, `result.json`, and `report.txt` and `fog-score.txt` from run-report.py and fog-score.py

Folders are only ever made new, so no run can overwrite another. Logs are copied while the test runs and only ever added to, so the launcher rewriting its logs after a crash can't wipe them.

Each log copy stops at 256 MiB (`--max-log-mib`), and the summary says if one was cut. `heap.log` reached 500 MB once.

## What it will never do

No `--go`, no contact with the console at all. It has no default address. It can only write `env.txt` in the app folders of the settings, `test-quit`, `test-boot-once`, and its own `auto-run-*.txt` scripts in `/data/eglantineps5` (plus the app's settings file and the live switch file for a plan that uses `config` or `live`). Anything else is refused in the code. Since 18 Nov a cold start, and the start-up check of every `--go`, may also rename the two cache folders and make one empty folder. With `--warm-copy` it also renames your two cache folders aside for the batch, and before every start deletes and uploads what is inside the two live ones (README.md, "A warm control"). README.md, "What it writes on the console", has the full list. With `--save` the save tool writes the game's save folder. It can only start EglantinePS5. It never installs a build, never renames or moves app folders, never touches PSN or firmware.

It leaves the `auto-run-*.txt` scripts on the console. They're small, and the next run with that name replaces them.

## Timing options

The defaults fit the logs so far. All in seconds, see `--help`:

`--poll 5` · `--frame-every 5` · `--silence 75` (the game logs every 15) · `--no-answer 60` · `--boot-wait 60` · `--game-wait 120` · `--restart-wait 60` · `--quit-wait 20` (after the app answers `test-quit` it gets this long again to go) · `--close-floor 6` · `--close-quiet 4` · `--stall-grace 12` · `--settle 4`

Three of these decide the time between two tests:

| Option | What it does | Old behaviour |
|---|---|---|
| `--close-quiet 4` | An app that took `test-quit` but keeps its sandbox mounts is closed once no log of it has grown for this long. See "When the app counts as closed" | `--close-quiet 0`: only after the whole `--quit-wait` |
| `--close-floor 6` | And never sooner than this after it took `test-quit`. Only used with `--close-quiet` above 0. Keep `--quit-wait` at least as long as the two together, or the "logs still grow" stop is off | not used |
| `--save-late` | A switch, no number. Puts the save back right before each start, after the whole `--settle` pause. See "One save for every test" | this is the old order |

`--settle 4` is the pause before the next test. It now counts from the moment the app was seen closed, so it is usually over by the time the reports are written. With `--save-late` it is the full pause before each start again.

`--close-quiet 0 --save-late` together give the timing from before these options existed.

The tool keeps the Mac awake while it runs (settings: keep_awake). Don't close the lid.

## How it was tested

My own copy was tested against a mock console on my Mac: websrv, ftpsrv, the app, and OBS, with freezes, device-lost, CE errors, a dead console and a dozen other cases simulated from real log lines. The script check was compared with the app's real parser, and one test compiled the app's own `test_harness.h` to run the tool against it. That mock and those tests are not in this folder: they are not cleaned of my own paths.

What is here is `tests/`: the offline tests of the cold option, the caches line and the whole-cache restore (README.md, "Tests"). They do not cover the rest of the runner.

Credit: the fresh-boot check and reading crash reports follow the idea of heydemoura's `mkw-bench-console.py` (GPL-3.0-or-later), rewritten here.

## One save for every test

A scripted walk goes through doorways, and the game then autosaves in the new place, so the next test starts somewhere else. `--save <folder>` puts a save backup back before every test. The standard one is a backup of your own save at the start spot, in `folders.save_backups`. `backup-save.py <name>` makes a new backup. Compare flash counts only between runs from the same save.

When the save goes back:

- **Before the first test:** right before its start, as always.
- **For every later test:** right after the test before it was seen closed, while the Mac checks the video and writes the reports. The console has nothing else to do then. The estimate from the t85 to t89 logs is 15 to 20 seconds saved per test; it has not been measured on the console yet. The next start waits until the save is back. Until then the tool writes nothing to the console and starts nothing there. It only reads `crash-index.txt`.
- **Not early** after the last test, after a live test, after a crash that closed the app, or when the app still looks open. Then the save goes back right before the next start, the old way.
- **If the app is open before a start** (someone opened it in between), the tool closes it first and puts the save back once more.

restore-save.py still makes its own check each time: with mounts left on the sandbox it watches `eden_log.txt` for 6 seconds and writes nothing if it grows. A save that can't go back stops the batch before the next start.

A Ctrl-C never cuts a save off halfway. The tool waits until the save is back, says so, and then puts `env.txt` back.

`--save-late` gives the old order: the save goes back right before each start, after the full `--settle` pause.
