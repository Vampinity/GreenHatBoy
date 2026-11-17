# Changes to waveydude's scorer (16 Nov 2026, GrowingBlackBeans)

These changes, against waveydude's scorer as he sent it on 16 Nov, make it read any run under the shared run
contract. They are offered back to him; his rules (null not 0, a `_source` for every number, fps_mean
kept, the window recorded) are untouched.

## Fixes

1. **Cold starts.** The store line says `new` on a cold start, not `created`, so every first start lost
   its store, cache state and build. `STAMP_RE` now takes `reused|created|new`.
2. **Build from run.json** stored a Python dict as text; now the tag (or commit) is used.
3. **No machine's paths.** `DEFAULT_ALPHA_ENV` comes from `--alpha-env` or `$STK_ALPHA_ENV`; the indexer
   takes `--roots` or `$STK_RUN_ROOTS`. His tests that used runs on his own machine are not carried over.
4. **Firmware from the log only** (`sdk_version` in the boot trace or log). The network-address map is
   gone: an address must never reach a packed run or the shared repo.

## The run contract

5. **One reader for every folder** (`runfolder.py`): flat, under `logs/`, `.gz` or not. Packed GHB runs and
   our folders score without staging.
6. **Crash files matched to the run** (same build version, crash time within a minute of the log's end).
   Other sessions' crash files are counted in `crash_files_ignored`, never read as this run's.
7. **The store, as waveydude asked:** `shader_store`, `store_state`, `store_pipelines` — plus
   `total_pipeline_count` and `driver_cache_loaded`, and a derived `cache_class` (`cold`/`warm`/`half`).
   Our runAC2 is why: its store said `new (0 pipelines)` while it loaded 921 pipelines and a 12 MiB
   driver cache.
8. **Start and end, derived:** `start_method` (`test_boot`/`launcher`), `end_kind`
   (`app_closed`/`log_cut`/`crash`), `tail_after_script_s`.
9. **Whole-run fps stops at `script_done` + 10 s** (where a runner's test-quit ends a run), so a later
   hand quit no longer moves it. It is still not a gate number.
10. **Route windows as data** (`windows.json`): the new-game village, the field walk and the area after
    the field (Vampinity's definitions, from his control README), and our four Kokiri stands. Columns
    `win_<name>_fps`, `_n`, `_source`.
11. **The out-of-memory cap:** `radv_oom_capped` is true at 64 lines (the log stops counting there).
12. **The driver line's memory minimum** as its own column (`largest_free_block_driver_min_mib`), so two
    runs can always be compared on one source.
13. **Contract checks**, from an optional `declared.json` (intent only: `control`, `intended_cache`):
    `cache_matches_intent`, `start_ok`, `end_ok` (closed normally within 30 s of the script; his runner
    takes 16-22 s), `env_ok`, `window_comparable`, `control_eligible`.

## Validated

- **Tests** (`tests/test_stk.py`): 7 synthetic cases always, 2 against GHB packed runs with
  `STK_TEST_GHB=<clone>`. All 9 pass.
- **Vampinity's published figures**: all 7 field walks and all 7 after-the-field medians reproduce to the
  hundredth; the village for run1559, run1637 and run1638 too. run1588 gives 22.43 against his 22.32: his
  README used a wider window for that T185 batch (app 531-556 s).
- **Cache class** right on all 14 control starts checked (11 his, 3 ours), including runAC2 as `half`.
- **Crash matching:** runWP1's own crash found among five crash files; four ignored.
- **Scale:** all 1,332 packed GHB runs score without an error in 16 s.
- **Not validated:** the Kokiri stand windows (within 1.7% of `stopdrift.py`, which measures differently;
  no owner figure to check against).

## What the archive can and can't give

Over the 1,332 packed runs: firmware 60 (older builds and the packer didn't keep `sdk_version`), store
and cache class 15, route windows 19, memory 1,293, survival 1,332. Missing stays null with a reason.

## Run contract v1: waveydude's four points (16 Nov, scorer 3)

14. **Cold and warm are two controls.** `control_kind` is `cold` or `warm`; `half` is neither and never
    comparable. Two rows face each other only with the same `comparison_key`:
    `route | firmware | build | translation id | store | cold-or-warm` (the build was added in scorer 7,
    see below).
15. **Translation id** (`translation_id`, with `translation_files` and `device_id`) from the store line:
    a new build can start a new store with an identical env, so the key refuses a mismatch.
16. **Route proof.** `route_completed` with `route_reason`: false on any `wait_timeout`, `steer_timeout`,
    `wait_error`, `script_error` or `script_stopped`, on no `script_done`, or when fewer steer lines were
    met than the script has. A route that didn't complete is not scored: its windows are `null` with the
    reason. Columns: `waits_met`, `waits_skipped`, `wait_timeouts`, `steer_met`, `steer_lines`,
    `steer_timeouts`.
17. **`radv_oom_events` is written `>=64`** at the cap, so no reader can compare two floors as equal.

Validated again: 13 tests (11 synthetic, 2 against GHB). On the 11 Vampinity control starts plus our 5,
the key groups exactly as it should: his 7 warm field starts (field-walk spread 0.83 fps), his 2 cold and
2 warm new-game starts kept apart, and our 2 cold starts on 13.60 (AC1, AC3) on their own; AC2, AC4 and
AC5 refused as `half`. Over the 1,332 GHB runs: 827 complete their route, **212 do not** (now unscored),
293 had no script; 26 counts are written `>=64`.

## The close time is recorded, not judged (16 Nov, scorer 4)

18. `end_ok` is now a normal close (`end_kind == app_closed`): the app saved its caches, so the next
    start's cache state is known. The 30 s bound after the script is gone (the user's decision, to put to
    the others): whole-run figures are cut at `script_done` + 10 s, so no number depends on when the app
    closed. `tail_after_script_s` is still recorded. A quit *before* the script ends is still caught, by
    `route_completed`. runCC1–CC3 (closed 65, 69 and 32 s after the script) are now `control_eligible`.

## waveydude's route check, merged (16 Nov, scorer 5)

19. **His `route_check.py` replaces our route proof** (his 10 tests in `tests/test_route_check.py`). Every run gets `route_result`: `completed`,
    `tail_unverified` (every leg and required WAIT passed, but moves after the last check confirm nothing —
    his river runs), `failed`, `manual`, `unknown` (not reached). It counts each STEER leg and each
    required WAIT by line against the route file, so it is stricter than ours was. Our `route_completed`
    is kept as "ran to its end": `completed` or `tail_unverified`. Route file: `script.txt`, else
    `route.txt` (his runner's name), else the env's script name; both hashes are recorded (`script_sha1`,
    which Vampinity's run.json and `windows.json` use, and his `route_sha256_12`).
20. **One change to his check, to offer back: END is not a check.** It ends the script and confirms
    nothing. With END counted, a route ending "WAIT, presses, a stand, END" scored `completed`.
    Without it: **every control start we have — ours and Vampinity's, new-game and field — is
    `tail_unverified`** (3 unconfirmed move lines after the new-game route's last WAIT at the door; 1
    after the field route's). So for now `tail_unverified` stays comparable, flagged; the gate can require
    `completed` once each control route ends on a check in its destination (a LOOK only the village
    matches; a STEER point or LOOK in the area after the field), which is a change to Vampinity's routes.

Validated: 24 tests (his 10 + one for END, our 13 adjusted to his `unknown` for an unmet leg). The 18 control
starts: his result agrees with ours on every one (runWP1, crashed, is `unknown`). Archive (1,332 runs): 810
`completed`, 18 `tail_unverified`, 22 `failed`, 189 `unknown`, 293 `manual`.

## Crash class when survival is unknown (scorer 6)

21. `crash_class` was `"none"` for every run without a crash file, including the 411 archived runs whose
    survival is unknown (no end line, no crash file). It is now `null` with `missing_survival_unknown` there:
    "no crash" is only claimed when the run is known to have ended without one.

## Review answer: the build in the key (16 Nov, scorer 7)

waveydude's required change on PR #11: *"the comparison key needs the build. With the translation id
forced to keep a store, our A186-keep → keep4 all carry `src116270f1…` with different code."*

22. **`build_key` is in the comparison key**, between firmware and the translation id. It is the boot
    trace's `diagnostic build <version> (<compile time>)` — the build that actually ran — or a build
    declared in `run.json`. It is deliberately **not** the store stamp's own build number: that names
    whichever build wrote the store, which with a kept store is not this one. A run with neither has
    `build_key: null` and therefore no key, rather than a key that is right about four fields and silent
    about the fifth.

**It changes how the archive groups, on his point exactly.** Scored over the 1,332 packed runs,
`build_key` is known for all 1,332 and the 15 runs that have a full key keep one, so nothing is lost.
But those 15 went from 2 keys to 4, and the split is not cosmetic: on the field route, warm, 12.40,
one store and one translation id, the old key pooled four `w20` starts (field walk 21.30–21.91) with
seven T186 starts (18.76–19.59). Same five fields, 2.4 fps apart, different compile times. Vampinity's
published figures average the seven, so his numbers were never the problem — the key was.

Validated: 27 tests (25 synthetic, 2 against GHB), including the keep/keep4 case (one store, one
translation id, two compile times → two keys) and a run with no build (no key at all).
