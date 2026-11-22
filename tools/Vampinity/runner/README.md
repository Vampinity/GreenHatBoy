# The start runner, with a cold option

This is the runner behind my scripted starts: it writes `env.txt` for a test, starts the game through
`test-boot-once`, copies the logs while it runs, sees crashes and freezes, closes the app with `test-quit`
about 10 s after `script_done`, and puts `env.txt` back. New here: it can set the caches aside for a cold
start and put them back after, and after every start it logs which caches it moved and what the boot reused.

**Not proven on a console yet.** My own copy of these tools ran about 1,700 scripted starts on one base PS5
between 5 and 17 Nov 2026. This folder is that copy with my address, folders and save path taken out
(17 Nov), plus the cold option (18 Nov) and the caches line (21 Nov). In this form it has not done one start
on a console. What ran is the offline test set below, where a local folder plays the console. Two console steps
of the cold option have never run anywhere: making the empty title folder over FTP, and renaming the recipe
between two folders. Both are checked by a listing and undo everything when the listing does not show them.
Please watch your first cold start and keep its `cold.log`.

## Files

| File | What it does |
|---|---|
| `auto-run-wait.py` | **The one you start.** The runner plus pad scripts with `WAIT`, `MAYBE`, `END` and `STEER` lines, and a test that ends when its script is done |
| `auto-run.py` | The runner itself. Takes a plan (a JSON list of tests), runs each one, writes `summary.md` |
| `cold_caches.py` | The cold option: sets the shader store and the driver cache aside before a start and puts them back after. Also reads the boot log for the caches line |
| `runner_config.py`, `runner-config.example.json` | The one place for your console's address, your folders, your save folder, capture on or off |
| `backup-save.py` | Copies the game's save off the console (reading only) |
| `restore-save.py` | Puts a save backup on the console and checks every file. It removes save slots that are not in the backup, and refuses while the app is open |
| `set-env.py` | Writes or switches off `env.txt` by hand |
| `lint-scripts.py` | Offline check of a route script's timing |
| `video-check.py` | Scans a test's video for flashes, black and freezes (needs ffmpeg; only with capture on) |
| `obs-fit.py` | Makes the capture card fill the OBS canvas. It changes OBS, so run it only on your own set-up |
| `GUIDE.md` | The longer guide: plan keys, how a test ends, what stops a batch, what to do after a stop |
| `CHANGES-FROM-ORIGINAL.md` | What I changed against my own copy, file by file |
| `tests/` | The offline tests |

## What it needs on the console

- A jailbroken PS5 with **websrv** (file view and `/launch`, port 8080) and **ftpsrv** (port 2121) running.
- An EglantinePS5 build **with the test harness**: `EDEN_TEST_BOOT`, `EDEN_TEST_SCRIPT`, `test-boot-once`,
  `test-quit`, and for the routes in `../routes` also `WAIT`, `LOOK`, `GONE`, `MAYBE`, `END` and `STEER`
  (`headless/test_harness.h` and `headless/minimap_steer.h`). Without the harness the first test ends as "game
  did not start" and the batch stops.
- The app closed. The runner will not touch an open app unless you tell it to close it.
- For a route that walks through a doorway: `EDEN_TEST_DISCARD_SAVE=1` in the test's env lines, and a backup of
  your own save at the route's start spot.
- For a cold start: free space. What a cold start builds stays on the console (see below).

## What it needs on the computer

- macOS or Linux. I only ran it on macOS.
- Python 3.10 or newer, standard library only. The tests pass on 3.11 and 3.15. Python 3.9 cannot load the runner.
- Optional: OBS with a capture card (WebSocket on, no password) and `ffmpeg` for frames and video. Without them
  set `"capture": {"enabled": false}` and the tests run with no frames and no video.

## Set it up

```
cd tools/Vampinity/runner
cp runner-config.example.json runner-config.json      # then fill it in
python3 runner_config.py --check                      # says what is still missing
```

`runner-config.json` holds your console's address and the profile folder of your save. It is in this folder's
`.gitignore`. Keep it that way. What each setting is for is written at the top of `runner_config.py`.

## A warm start

A start that is not asked to be cold is a plain start: **the runner moves nothing and restores nothing.** It
starts on the caches that are on the console and afterwards reports what the boot found. If you need a warm
control with the whole cache put back from a copy first, as in
[`docs/GrowingBlackBeans/warm-run-steps.md`](../../../docs/GrowingBlackBeans/warm-run-steps.md), do that restore
yourself before the start. The runner does not do it. Its caches line then shows whether it worked.

1. Put the route script next to a plan file, for example `one-start.json`:

   ```json
   [{"name": "field-control-1",
     "title": "0400486024DEC000",
     "seconds": 1200,
     "env": ["EDEN_TEST_DISCARD_SAVE=1"],
     "script": "field-to-past-field.txt"}]
   ```

   `env` replaces `env.txt` for the test, so list every line of your control settings there. The runner adds
   `EDEN_TEST_BOOT` and `EDEN_TEST_SCRIPT` itself.

2. Look at the plan. This sends nothing to the console:

   ```
   python3 auto-run-wait.py one-start.json
   ```

3. Back up your save once, then run the start with that backup put back first:

   ```
   python3 backup-save.py field-start
   python3 auto-run-wait.py one-start.json --save ~/ghb-runs/save-backups/field-start --go
   ```

4. The result is in `<folders.out_root>/auto-<date>-<time>-one-start/`: `summary.md`, and one folder per start
   with `eden_log.txt`, `stderr.log`, `env.txt`, `boot-trace.txt`, `heap.log`, `script.txt`, `result.json` and
   any crash files. That folder is the run contract's run folder, without `declared.json`: the runner does not
   write that file. **The runner masks nothing.** `batch.log`, `summary.md` and the runner's state file hold
   your console's address, so they stay on your computer. Pack a run folder with `tools/pack-run.py` before you
   share it, and look through the result yourself.

## A cold start

A cold start is a start with no shader store and no driver cache, like a new player's first start. Ask for
one with this line in a test's `env`:

```
EDEN_TEST_COLD=1
```

or make every test in the plan cold with `--cold` on the command line. The line is for the runner only. It
never goes into the console's `env.txt`.

```
python3 auto-run-wait.py one-cold-start.json --save ~/ghb-runs/save-backups/field-start --go
```

What happens, step by step. Each step is written to `cold.log` in the run folder:

1. Right before the start the runner checks that the app is closed: no sandbox mounts, `eden_log.txt` the same
   size for 20 s, no `test-quit` lying around. If not, it refuses and moves nothing.
2. On the console it renames two folders, and only these two, to `<name>.cold-aside-<date>-<time>` in the same
   place: `<data_dir>/user/cache/shader/<title>` (the game's shader store, with the driver pipeline cache
   inside it) and `<data_dir>/cache/radv` (the driver's disk cache). No copy, no delete. If neither is there it
   says so and moves nothing.
3. **The shader set stays in place.** Its two input files sit at the top of the title folder: the recipe (any
   `*.nx2recipe`) and `shader_set_index.txt`. A store build needs them and the app never writes them, so they
   are not cache. The runner makes a new, empty `<title>` folder and renames those files into it from the
   `.cold-aside-` folder. The rule goes by file name, and only at the top of the title folder. What the set
   builds (`prep_shader_set.*`, `shader_set_prepass.skip`) is cache and stays aside. To move the set aside as
   well, add `EDEN_TEST_COLD_SET=1` next to `EDEN_TEST_COLD=1`.
4. Before the first rename it writes `cold-note.json` in the run folder: what goes where, file counts and
   sizes, which set files stay. The same note goes into the runner's state file.
5. After the test, also after a crash, a stop, a tool error or Ctrl-C, once the app is closed: the set's files
   go back into the `.cold-aside-` folder first, then what the start built is renamed to
   `<name>.cold-built-<date>-<time>`, the old folder goes back to its own name, and a listing of every file
   under it must show the same paths and sizes as before.
6. If the app is still open (a freeze) or the console does not answer, nothing is moved back yet. The batch
   stops, `summary.md` says **NOT BACK**, and the next `--go` (any plan) or `--restore-env --go` puts them back
   first. That start-up check also finds a `.cold-aside-` folder by its name when the note is gone.

Good to know:

- **The `.cold-built-` folders stay on the console.** Nothing is ever deleted, so each cold start leaves what it
  built next to your caches. A played-in store plus driver cache was about 4 GB on my console. Look at them or
  remove them yourself.
- It moves the game's own store folder and `cache/radv`, not all of `user/cache` and `cache`. The JIT block list
  (`user/cache/jit`) and other games' stores are left alone.
- A `radv-shader-cache` file in the app folder refuses a cold start: with the driver cache gone the app would
  move that file in and use it, so the start would not be cold.
- The put-back check compares paths and sizes, not the bytes. A rename does not change content, but if you want
  proof byte for byte, take your own hash list before and after.
- With `EDEN_UP_SHADER_SET=1` on, a cold start converts the recipe again. That took about 12 minutes on my console.

## The caches line

After every start, warm or cold, one line says which caches the runner set aside and what the boot log says the
start reused. It is in `batch.log`, in `result.json` under `caches` (with each number as its own field), in
`summary.md`, and for a cold start at the end of `cold.log`.

A warm start:

```
Caches: none set aside by the runner (not a cold start; it starts on what is on the console). Boot log: store
prep_5093ab9e reused (78735 pipelines), build 84805134; 78735 pipelines known, 0 left to prepare; 7816 records
read (7816 own); Total Pipeline Count 4204; driver pipeline cache loaded. Reads as warm
```

A cold start:

```
Caches: set aside for this start: shader store /data/eglantineps5/user/cache/shader/0400486024dec000 (41 files,
2.9 GiB), driver cache /data/eglantineps5/cache/radv (3120 files, 1.3 GiB); shader set kept in place:
<name>.nx2recipe, shader_set_index.txt; put back: yes, checked by a listing. Boot log: store prep_5093ab9e new
(0 pipelines), build 84805134; 0 pipelines known, 0 left to prepare; 0 records read (0 own); Total Pipeline
Count 0; no driver pipeline cache loaded. Reads as cold
```

The two examples only show the form; neither is from a start with this runner. The reader was checked against
ten packed starts in `runs/` (cold, half and warm ones of GrowingBlackBeans and two first starts of mine): nine
read as their author classed them, and one from an older build has no store line, so it gives no store and no
class, with the reason. The store line is read with the same pattern
as the shared scorer (`tools/stk/stk_score.py`), and "reads as" follows the run contract: warm is a reused
store; cold is a new store, Total Pipeline Count 0 and no driver pipeline cache loaded; half is a new store
with something left from an earlier start, which is never a control. A start whose boot log does not read as
it was asked gets a note in `summary.md`. When the log has no store line, the store's fields and `reads_as`
are `null` and `why_missing` says why. The other counts are still read when the log has them.

A cold start also keeps its older check in `result.json` under `cold.proof`: three boot counts that must all be
0. On the nine packed starts with a store line the two checks agree, also on GrowingBlackBeans' store build of
18 Nov, which booted with the shader set on and the recipe in place.

## What it writes on the console

Only these:

- `env.txt` in the folders listed under `app.env_folders`, put back after the batch.
- `test-quit`, `test-boot-once` and its own `auto-run-*.txt` script copies in the app's data folder.
- `eglantineps5.json` and the live switch file, only for a plan that uses `config` or `live`.
- With `--save`: the game's save folder named in `game.save_dir`. The backup is written over it and **save
  slots that are not in the backup are deleted.** Back up your own save first.
- For a cold start, and in the start-up check of every `--go`: the renames above, and the one empty `<title>`
  folder. Never a delete under a cache folder.

It never installs a build.

## Tests

```
python3 -m unittest discover -s tools/Vampinity/runner/tests -v
```

31 cases, a few seconds, no console and no network. A local folder plays the console. The runner's real
`main`, plan check, start-up check, cold set-aside and put-back, and summary all run. Only starting and closing
the game are stubbed. `tests/offline_guard.py` makes every socket connect, name lookup and child process fail,
and each case checks that none was even tried. One case points the real console class at the guard to show
that it holds.

What the tests cannot show: anything a real console does. The FTP rename and folder make, the timing of the
listings on a big store, a real freeze, and the boot log of a real cold start with this runner.

## Not in this folder

| Piece | Why not |
|---|---|
| The queue (several plans in a row) and my result tool with its flash meter | They lean on my own folder layout and are not cleaned for sharing |
| `declared.json` per run | The runner does not write it. The settings file already has the console label |
| Early stop rules, pre-flight checks of a plan's switches, live switch tests | Not cleaned of my own paths. The runner works without them: every start runs |
| A mock console for the rest of the runner | Mine is not cleaned. `GUIDE.md` says how the original was tested |

## Credit and licence

waveydude asked for the caches line (which caches moved, that they went back, what a warm start reused).
GrowingBlackBeans pointed out that the recipe sits in the folder the cold option moves, which is why the shader
set now stays in place. The store line pattern and the cold, warm and half classes are those of `tools/stk`
(waveydude's scorer with GrowingBlackBeans' run contract changes). The fresh boot check and the reading of
crash reports follow the idea of heydemoura's `mkw-bench-console.py` (GPL-3.0-or-later), written anew here.

Licence: GPL-3.0-or-later, like the rest of this repository.
