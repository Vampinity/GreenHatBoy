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
    start's cache state is known. The 30 s bound after the script is gone (GrowingBlackBeans's decision, to put to
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

## Review answer: PR #18 (18 Nov, scorer 8, gate 2)

Vampinity's review of the gate (PR #18), points 1-7. Gate:

23. **Means are read against the noise of a mean** (2 x sd x sqrt(1/n_control + 1/n_candidate)), not one start's
    spread; and p < 0.05 with every candidate start beyond the control's worst start is "real" whatever the means.
    Four baseline starts at 120-150 MiB against a control low of 165 now block, and so do four later-area starts at
    0 MiB. The field's memory lows are already 0-1 MiB, so memory still can't block there; the doc says so.
24. **Capped counters** (">=64"): a capped candidate start counts at its cap (a lower bound, so worse than any
    uncapped control); a control start at the cap marks the number `usable: false` for its key (the field's
    out-of-memory count, FC4).
25. **Starts are sorted before judging:** CRASHED and LOST block; INVALID (quit before the script's END, or a skipped
    window anchor) is left out and reported for a rerun. KV3, LV5 and FC1 are INVALID, not BLOCK.

Scorer:

26. **A skipped line is never a window's anchor.** A `MAYBE` that timed out is logged as `wait_skipped line=N`, and
    was taken as a mark, so a missed field load in the later area would have been scored in the wrong place. Now the
    window has no value (`anchor_skipped_line_N`), the row lists it in `anchors_skipped`, and the start is not
    window-comparable. Windows whose lines are short `MAYBE`s written to time out, used only as a clock, say
    `"clock_marks": true` in windows.json and keep their marks (the Kokiri stands, both versions).

Rescored, all 21 cold starts of 17-18 Nov keep every window value; the floor file's numbers are unchanged except
the field's out-of-memory count, now `usable: false`. Tests: 23 gate, 3 skipped-anchor, 78 in all.

## Review answer: PR #18, waveydude (18 Nov, gate 3)

waveydude's review of the gate at 281d22b: three cases printed PASS and exited 0 (one start; four starts with all
three memory readings missing; two builds pooled as one candidate).

27. **PROVISIONAL is a verdict, with its own exit code (2).** It covers fewer than 4 valid candidate starts, a floor
    of fewer than 4, an unidentified build, and a stable number the floor gates on that was read on fewer than 4
    candidate starts. The report still says what the starts so far lean to. A crash or a lost route blocks, however
    short the arm.
28. **Each side must be one thing.** The starts pooled on one side of a key must share the build (version and
    compile time), the settings (the env hash, harness lines left out), the translation id and the script. The
    control and the candidate may differ. A mixed candidate arm is MIXED (exit 3), with the runs behind each value
    named. `floors` refuses a mixed control arm (exit 3), and each floor key now records its arm.
29. **PASS says what it couldn't clear.** Numbers the floor has no reading of (flashes and hitches on the alpha) or
    can't use (a control at a counter's cap) are listed as NOT CLEARED under the verdict, and in `not_cleared`.
30. **Exit codes:** PASS 0, EXPLAIN 1, PROVISIONAL 2, MIXED / INVALID / NO KEY / NO FLOOR 3, BLOCK 4. With several
    keys, the highest wins. Anything but 0 is not cleared.

The four cold control arms are each one build, one env hash, one translation id and one script; the rebuilt floor
file's numbers are unchanged, and it gains `arm` per key. Leave-one-out over the 16 controls now reads PROVISIONAL
(leaning PASS) on all 16, because one start against three is short on both sides. Tests: 40 gate (17 new, 6 of them
on the CLI's exit code), 3 skipped-anchor, 95 in all.

## Review answer: PR #18, Vampinity's second review (18 Nov, gate 4)

31. **INVALID needs a normal close.** A start that stops before the script's END is INVALID (rerun) only when the
    app closed normally (`end_kind` app_closed), as KV3, LV5 and FC1 did. A log that just stops, with no crash file,
    is HUNG and counts against the candidate like a crash: on the field route everything after the WAIT at line 92
    is MAYBEs, so a freeze in that load met every required leg and was being left out. Test added
    (stopped_early + log_cut blocks).
32. The `__pycache__` files are out of the repo, and `.gitignore` keeps them out.
33. Doc: a field candidate at 0 MiB on all four is worse (likely), so EXPLAIN, not "can't be shown worse".

All 21 cold starts closed normally, so none changes class: KV3, LV5 and FC1 stay INVALID, LV1 stays LOST. 96 tests.

## Review answer: PR #18, waveydude's second review (18 Nov, gate 5)

34. **Missing identity is unverified, for all four fields.** Only a missing build counted before; a start with no
    env hash (an empty or missing env.txt), no script or no translation id was pooled as if it matched, and four
    such rows printed PASS. Now any of the four missing makes the arm PROVISIONAL and names the start
    ("settings (env hash) not recorded on x3"). On the control side the floor records it (`arm_unverified`), and
    every check against that floor is PROVISIONAL until it is rebuilt from complete starts. PROVISIONAL rather than
    INVALID: the start's own numbers may be fine, only its arm can't be shown. Tests: each field missing on one row of
    four, a control missing one, and the CLI's exit code (2).

All 21 cold starts record all four, so the floors are unchanged (`arm_unverified` empty on every key). 99 tests.


## 19 Nov: the warm boot, and two gate notes

- **The warm boot is checked, not only N.** `stk_score.py` reads `pipelines_known`, `left_to_prepare` and
  `own_records` from the boot's shader preparation lines. `stk_gate.py floors` leaves out a warm control whose
  boot isn't prepared (pipelines known not equal to the store's N, or any left to prepare), and records each
  warm floor's boots as `warm_boot` (`own <records> / total <count>`, with the runs). `check` reads a warm
  candidate whose boot isn't prepared, or isn't one of the control's, as PROVISIONAL and names it. A floor file
  without `warm_boot` gets a note saying so. On our runs: runWB2-played (820 own, 80,797 known) is caught;
  WV2-5 pass. The four warm floor files are rebuilt with it; their numbers are unchanged.
- **Vampinity's two notes on PR #18:** MIXED now lists the fields not recorded as well as the ones that differ;
  a floor file built before the arm check (no `arm_unverified`) makes the verdict PROVISIONAL, as does one without
  `warm_boot`.
- **After Vampinity's review of PR #23:** a warm control with two boots is refused unless allowed on purpose
  (`floors --allow-mixed-boot KEY`; our baseline, for WB1's 36 own records, is the one such floor and carries
  `warm_boot_mixed_on_purpose`). That also catches a grown own cache with exactly N known (his 14-15 Nov warm runs:
  6,646-7,816 own records). `floors` prints each key's boots. A candidate arm whose starts boot differently is
  MIXED. A control start with no boot lines goes into `arm_unverified`. The boot checks read only valid starts. The
  scorer has tests for the two boot lines. 16 new tests in all.

## 19 Nov: the after-the-load window stops at script_done + 10 s

`after_load_low` ("from 70 s past the load's lowest line to the end") ran to the log's end, so a start quit later
got more tail (Vampinity, PR #20). It now stops at script_done + 10 s, like every whole-run number. The other window
kinds end at their own marks or stamps and are unchanged (new-game's village windows run a few seconds past
script_done by design). Floors rebuilt: only `win_after_field_fps` moves (cold 13.80-14.00, warm 14.0-14.15).

## 19 Nov: memory at the wall, and the load's length

On the field route the largest free block's minimum sits at 0-2 MiB on every start, so it can't show a change for
the worse (Fable's check of the Phase 4 plan). Four numbers that can, from lines the alpha already logs:
- `refused_pool_events` (stable): `EDEN_REFUSED_POOL` lines; not capped like the OOM lines.
- `seconds_under_16_mib` (stable): census lines with the largest free block under 16 MiB, 2 s each.
- `stranded_at_low_mib` (stable): at the lowest census, the heap's free pages + fragmented + the GPU blocks' slack
  (the pool line `memmap.py` reads).
- `load_s` (smooth): MEASURING.md's "black screen at each load", on routes with a load window: from the load's mark,
  past the black, to the first 5 s line from which play holds at half the after-load fps for 15 s. 5 s resolution.
On the field: warm 7, 0, 5, 11 refusals; 22-56 s under 16 MiB; load 12-23 s (cold 146-165 s). All floor files are
rebuilt; every number they already had is unchanged.

## 19 Nov: after Vampinity's review of PR #24

- **The memory numbers stop where test-quit ends a run** (his point 2). Refusals, seconds under 16 MiB and
  stranded at the low read the log up to the `script_done` line, then the census lines of the next 10 s on the
  census's own clock (it runs about 13 s behind the script's, so the cut is by log order, not `t_s`). A start with
  no census after `script_done` stops at its line; one with no `script_done` reads to the log's end, as fps does.
  New column `memory_window` says which. `largest_free_block_min_mib` is unchanged (it still reads the whole log).
- **A refusal line with 16 MiB or more in its largest block isn't counted** (point 1): `EDEN_NX2_POOL_WALK=1` prints
  the pool line every 20 s with nothing refused. With the filter the count stays usable with that switch on.
- **A control at 0 on every start can't block** (point 3): no noise to read against, so one stray line per start
  read "real". A worse reading there is "watch", with the reason in the note, until there's a minimum size.
- **`stranded_at_low_mib` is gated only where the control goes under 16 MiB**, and reads the median over the census
  lines tied at the lowest block (point 4). Elsewhere the floor marks it unusable, with the reason.
- **`load_s` has fixtures** (point 5): the black, the stall and a false start; play that never holds; two good lines
  before the cut (the 3-line minimum); no black.
- **From the #23 follow-up:** a candidate arm that boots two ways is still BLOCK when a start crashed or a stable
  number is really worse (MIXED used to hide it); the invalid-start test now fails without its fix.
- The packed-run test of his seven field starts carries the after-the-field values as cut by PR #20 (run1591 13.35,
  run1604 13.95, run1613 13.35); it failed on `main` since that merge.

Floors rebuilt from the same 32 starts. Refusals and seconds under 16 MiB don't move on any key (none of our control
starts had either after the route ended). Stranded moves on the ties (field cold 1014, 1155, 974, 1106 → 963.5,
1128, 974, 1005.5) and is gated only on the field, cold and warm, and the cold later area. 131 tests.
