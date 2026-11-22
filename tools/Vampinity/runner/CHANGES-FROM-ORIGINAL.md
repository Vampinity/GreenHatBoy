# Changes from my own copy

These files were copied on 17 Nov 2026 from the tools folder I run my scripted starts with. Only the copies were
edited. Line numbers in the first part are those of the originals. Old values are not repeated here on purpose.

The rule for every change of 17 Nov: a value that belongs to one person or one home became a setting, read
through `runner_config.py` from `runner-config.json`.

## New files (17 Nov)

| File | What |
|---|---|
| `runner_config.py` | The settings reader, plus four small helpers the tools share: `notify`, `keep_awake`, `process_list`, `hwaccel` |
| `runner-config.example.json` | The settings file to copy and fill in |
| `README.md`, `CHANGES-FROM-ORIGINAL.md` | This documentation |

## auto-run.py (the runner), 17 Nov

| Original line | Was | Now |
|---|---|---|
| 90-91 | the app's id and data folder, fixed in the code | `app.id`, `app.data_dir`; the line before imports `runner_config` |
| 102-103 | the ShadowMount log path, and two app folders for `env.txt`, one of them a backup folder that exists only on my console | `app.shadowmount_log`, `app.env_folders` (default: the installed app's folder only) |
| 105 | the output folder, a fixed folder in my home | `folders.out_root` |
| 918 | the capture source's name in OBS | `capture.source` |
| 1041-1042, 1047 | old test videos moved to the macOS Trash | moved to `folders.video_trash`; with none set they stay where they are |
| 1190, 1195-1199 | a macOS notification (osascript) | `runner_config.notify` (`notify.command`: print only, macOS, or your own command) |
| 2538 | `--host` required on every call | `--host` optional when `console.host` is set; still no address in the code, and no address at all is an error (new check after line 2598) |
| 2548-2551 | web, ftp and OBS ports and the OBS host as fixed defaults | defaults from `console.web_port`, `console.ftp_port`, `capture.obs_host`, `capture.obs_port` |
| 2552 | `--no-frames` off by default | on by default when `capture.enabled` is false |
| 2598 (after) | | the address and ports this run was started with are handed on (`runner_config.use_console`), so the save put-back the runner starts talks to the **same console as the test**, also when `--host` differs from the settings |
| 2616-2617 | `caffeinate` (macOS) | `runner_config.keep_awake` (`keep_awake.command`: auto picks caffeinate or systemd-inhibit) |
| wording | my first name in help texts, comments and one variable name (11 lines) | "the owner"; the variable is `told_owner` |

## Small tools, 17 Nov

| File | Original line | Was | Now |
|---|---|---|---|
| `auto-run-wait.py` | | nothing private | no change on 17 Nov |
| `restore-save.py` | 5-8, 18-19 | console address, ports, the save folder with my profile folder, the app id | `console.*` (or the address the runner handed on), `game.save_dir`, `app.id`, `app.data_dir` |
| `backup-save.py` | 2-6, 23 | console address, the save folder with the profile folder, a backup folder in my home | `console.*`, `game.save_dir`, `folders.save_backups` |
| `set-env.py` | 8-12 | console address, the two app folders | `console.*`, `app.env_folders` |
| `obs-fit.py` | 8-9, 12 | OBS address, port and source name | `capture.*` |
| `GUIDE.md` | whole file | the console address (3 places), my folders (2), my first name (1), a save name (1), macOS wording (2) | placeholders and setting names; a short note at the top; the credit line to heydemoura is kept |
| `lint-scripts.py`, `video-check.py` | | | copied without any change |

## The cold option, 18 Nov

New code, not in my own copy. Line numbers are this folder's.

| File | What |
|---|---|
| `cold_caches.py` | **New.** Sets the shader store and the driver cache aside (renames only) and puts them back, the start-up check, the boot-log cold proof. Since the evening of 18 Nov it keeps the shader set's recipe (`*.nx2recipe`) and `shader_set_index.txt` in place by default: it makes the empty live title folder (`allowed_folder`) and renames those two kinds of file between it and the `.cold-aside-` folder (`allowed_pair`, `keep_set`, `return_set`). `EDEN_TEST_COLD_SET=1` moves the set aside too |
| `auto-run.py` | imports `cold_caches`; `EDEN_TEST_COLD` and `EDEN_TEST_COLD_SET` checked in the plan and kept out of `env.txt` (`_SET=1` without a cold start is refused); `--cold`; `Console.rename_cold` and `Console.mkdir_cold` (their own allow-lists, `writable()` unchanged); `Batch.cold_recover` in `prepare`, `cold_aside` before `start`, `cold_back` after `finish_run` and in `run_test`'s `finally`; the cold proof in `close_run`; cold lines in `summary.md` (with the set files kept); `--restore-env --go` also puts back cold-start folders; a `cold_not_back` stop; a host check in `blocked` |
| `tests/test_cold_start.py` | **New** (as `cold_desk_test.py`, 24 cases, a local folder as the console) |

## The caches line and the offline guard, 21 Nov

| File | What |
|---|---|
| `cold_caches.py` | `boot_caches`, `boot_text`, `cache_line`, `cache_short`: what the boot log says about a start's caches (the store's name, new or reused, its pipeline count and build number, pipelines known and left to prepare, records read, Total Pipeline Count, whether a driver pipeline cache loaded) and the one line made from it. The store line is read with the pattern of `tools/stk/stk_score.py`; "reads as" cold, warm or half follows the run contract |
| `auto-run.py` | `Batch.cache_report`, called from `close_run` for every start that was launched: the line goes to `batch.log`, `result.json` (`caches`), `summary.md` ("Caches per start") and, for a cold start, `cold.log`. A start whose boot log does not read as asked gets a note. No verdict changes: `cold.proof` is as it was |
| `tests/offline_guard.py` | **New.** Makes every socket connect, name lookup and child process fail inside the test process, and keeps a list of what was tried |
| `tests/test_cold_start.py` | moved into `tests/`, runs under `unittest`; the guard is put in before the runner loads and every case checks that nothing was tried; the stand-in console's address is a name that cannot resolve; every folder setting points into the scratch folder; the stub start writes boot lines in the app's real wording; 7 new cases (22 to 28): the warm line, the cold line, a log that does not read as asked, a log without a store line, the guard against the real console class, a plan print that makes no console, and a fault in the reader that costs a start nothing |
| `README.md` | rewritten for this folder: a warm start, a cold start, the caches line, what it needs on the console, what is not proven |
| `GUIDE.md` | the two first-run plans are written out (the `first-run/` folder is not here); the videos' folder is the setting; "What it will never do" names the cold renames and the save tool; the part on how my own copy was tested is cut to what applies here; two game names taken out |
| `.gitignore` | **New.** Keeps `runner-config.json` out of git |
| wording | `auto-run.py`, `auto-run-wait.py`, `backup-save.py`, `restore-save.py`, `lint-scripts.py`: comments that named a folder or script of my own set-up, the game or its main character now say it in general words. `restore-save.py`'s first lines now say plainly that it removes save slots. No code line changed in these five places |

## Not in this folder

My queue (several plans in a row), my result tool, its flash meter, the tool that cuts a `LOOK` check from a
screenshot, and two data files they read. The cold option also changed two lines of the queue and three of the
result tool; those changes are not here either. The runner still names the result tool in a few comments, and
loads it only for a plan with `live`, which this folder does not support.

## Checked

- 17 Nov: syntax check of every file; with a scratch settings file the wrapper and the runner load and print
  a plan without `--go`.
- 21 Nov: the offline tests, 31 of 31, on Python 3.11 and 3.15 (macOS). Broken on purpose in scratch copies, the
  tests fail as they should: without the stand-in console (the guard stops and lists every try), with the store
  always read as reused, without the caches line, without keeping the shader set, and with a keep rule that
  takes every file.
- 21 Nov: the reader of the boot log against ten packed starts in `runs/` (read as text, nothing run from
  them): from GrowingBlackBeans two cold controls and two half-warm starts of 17 Nov, his store build and two
  warm starts of 18 Nov, and one start of 12 Nov on an older build; from me two first starts of 15 Nov. Nine
  read as their author classed them, and his warm control gave his own numbers (80770 reused, 80770 known,
  0 left, 3 own records, Total Pipeline Count 4). The older build has no store line: its store fields and its class
  come out empty with the reason, as they should.

Not checked: any contact with a console, OBS, a save put-back, and Linux.
