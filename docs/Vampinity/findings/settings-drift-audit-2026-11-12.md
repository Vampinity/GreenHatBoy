# Settings drift audit, 12 Nov 2026 (about 03:15-03:45, corrected after a second check)

> **Found:** Many queued tests did not use the owner's current play settings: 8 starts in the night's list and 48 parked ones missed the usage tracker by accident, because every plan carries its own frozen copy of the settings.
>
> **So:** Every queued test is now compared with the play file (env-drift.py) and each difference must be on purpose; two proven fixes were proposed for the play file.

Question from Vampinity: "how many switches do you 'forget' to switch on exactly? how does this happen? this must mean we are
often not testing what we want to test."

Read only. Nothing on the console, in `night-steps.txt`, in any plan, queue, env file or tool was changed. New files:
this note, `env-drift.py`, `drift-declared.json`,
`env-play-v28-proposed.txt` (not installed anywhere). An earlier draft named the proposal
`env-play-v27-proposed.txt`; it clashed with the real v2.7 and was removed.

Words, one line each:
- **play file**: `env-play-v27-fast-docked.txt` since 12 Nov 03:14 (Vampinity's yes, "we obviously need this
  fix"): v2.6-fast + the copy guard, 82 lines. `put-owner-back.sh` installs it (backup `.bak-v26`). It goes on the console
  when the chain hands it back; until then the console holds a test env.
- **plan**: a `batch-*.json`; every start in it carries its own full copy of an env list.
- **queue**: a `queue-*.json`, a list of plans; `night-steps.txt` lists the queues still to run.
- **drift**: a queued start that lacks a play-file line or has another value for it.
- **deliberate**: the test needs that difference (for example it tests that very switch, or default settings).
- **accidental**: copied from an older env and never updated.
- **frame-ahead**: `EDEN_NX2_FRAMES_AHEAD=1`, the fast setting; the guard only acts when it is on.

## Cliff's notes

1. **The guard is now in your play file** (v2.7, your OK at 03:14). Two more proven fixes are not: the shader hitch fix
   and the pause-menu fix. Proposal: v2.8 = v2.7 + those two (`env-play-v28-proposed.txt`). Not one proven fix is a build
   default: every new switch since T82 ships off.
2. **Queued tests now** (03:35, after the chain was cut to the alpha blockers at 03:31): 82 starts in 8 queues, all on
   T134; 10 run now (house door), 72 are ahead. Of those 72: 55 hold every line of v2.7, 9 differ only on purpose,
   **8 differ by accident**, all missing the usage tracker (`t131-lean-ssbo` 4, `decode-bound-door` 4). The 17 parked
   steps (`night-steps.later.txt`, 189 starts) hold 48 more accidental starts, 2 of them (`t111-s`) also without the fast
   lines and the heap wait.
3. **The guard was the big one**: until 03:03 it was off in 154 of 285 queued starts (a count of queued starts, not of
   frame-ahead starts). Since 03:03 it was on in all 263 frame-ahead starts of the full chain; the other 23 run without
   frame-ahead, where it does nothing. In the cut chain: 70 of 72 starts ahead run frame-ahead, all 70 with the guard.
4. **Past verdicts**: none is overturned. The doubt is in picture judgements made without the guard (the "bars, wedges
   and hearts" in the T130 menu stills are the icon glitch the guard removes), in absolute fps numbers, and one batch
   lost a control to it (t130-allfixes-exit, below).
5. **Why**: each plan freezes a copy of an env; nothing compared it with the play file; a proven fix stays a line in one
   note until someone copies it; the open question "does the fast file ship with the guard" was not put to you again
   until 03:11.
6. **Cure**: `env-drift.py` (second check, read only, compares with whatever `put-owner-back.sh` installs),
   `drift-declared.json` (the on-purpose differences with reasons), the v2.8 proposal, and build defaults for the next
   build.

## 1. Proven fixes against the play file

"Queued on" = starts ahead in the cut chain (of 72, 03:35) that have the line.

### Not in the play file v2.7

| Switch | What it fixes | Evidence | Cost | Build default | Queued on |
|---|---|---|---|---|---|
| `EDEN_UP_PREP_UNREAD_HANDLE=1` | a hitch the first time a kept shader is drawn (the emulator threw the kept copy away and rebuilt it mid-game) | door walk, 2 controls against 2 fix runs + 1 check run, same batch, alternating: 6-7 refused builds a run -> 0, door worst frame 190-226 -> 154-155 ms (`t129-prep-door-2026-11-11.md`); village exit: the same pipelines 64-88 -> 3-7 ms, 1 valid control (`t130-allfixes-exit-2026-11-12.md`). Proven at the single-pipeline level. Open: the fault-injection check (`VERIFY=2`, `queue-t129b`) has not run, so "a reused shader always draws right" is not shown yet | none seen (standing fps 22.1-22.4 in all door runs) | no (T129, off) | 36 |
| `EDEN_UP_AREA_BUDGET=1` | stutter when the pause menu closes (about 1,000 textures thrown away and remade) | **works for the menu-close stutter**: worst frame at a close 350-466 -> 157-313 ms, same batch, no overlap (`t126-results-2026-11-11.md`). **Memory side open in 2 batches**: t126 menu route (2 fix runs b1/b2 against 2 controls, c1 and the v1 run that turned out to be a control) had the lowest largest free block worse with the fix, 181-201 against 255-393 MiB; the T130 menu batch is too close to call (281/285 against 267/231, 8 switches on together). t126b door/exit runs: no sign of lower memory | no fps cost; memory open, and Vampinity's crashes are memory-wall crashes | no (T126, off) | 38 |
| `EDEN_UP_AHEAD_READ_SYNC=1` | the too-bright second after a door or cut | 4 of 4 controls too bright, 0 of 5 with it (Fisher p=0.008, `t128-door-fix-2026-11-11.md`) | about 20% after the door: **not for play**; the cheap version `EDEN_UP_AHEAD_READ_SYNC_AUTO` (T131) is queued (5 starts in `queue-t131a`) | no | 3 (+5 with the auto version) |
| `EDEN_GBB_NAN_GUARD=1` + `EDEN_GBB_POSITION_INVARIANT=1` | one-frame bright flash | candidate: without the copy guard, bright flash 3 of 3 controls, 0 of 3 with the pair (t112-n, 10 Nov); with the guard no clear difference (t114-g1, t114-g2); the all-white flash at the overlook survives the guard and the pair was not in that env. Needs one test | not measured on its own | no (T112, off) | 0 |

Aimed at crashes but **not proven here** (never fired, or untested), so not counted: `EDEN_UP_HEAP_STEAL`,
`EDEN_UP_NEW_WAIT_MS`, `EDEN_UP_JIT_SITE_SHARDS`, `EDEN_UP_ASTC_SCAN_CHUNKS`, `EDEN_PE_TRANSCODE_BOUND` (T129-T130: "the
crash fixes never had to act"), `EDEN_UP_JIT_LEND_UNDER_FLOOR` (T132), `EDEN_UP_RESUME_KEEP_COPY` (T133),
`EDEN_UP_HLE_REPLY_BUFFER` / `_OOM_RETRY` (T134). waveydude's three removed his crashes on his console; on ours they did no
harm and never acted.

### In the play file v2.7 (keep)

| Lines | What it fixes | Evidence | Build default | Queued on |
|---|---|---|---|---|
| `EDEN_UP_AHEAD_GUARD=3` (new in v2.7) | icons on screen jumping or flashing for one frame while walking; small dark flashes standing | walk-hud: 2 runs per arm in one batch, mixed order (control, tracker, guard, guard, tracker, control): 41 / 44 / 0 moments; 0 means none found, not proved none (`hud-count-walk-hud-2026-11-11.md`); standing dark flashes 3 of 5 runs without, 0 of 5 with (`guard-cost-2026-11-11.md`). **Cost**: about 3% fps (0.7 fps at the village); it does **not** remove the one-frame all-white flash at the overlook (1 of 2 runs without the guard, 2 of 2 with). It does **not** cause the too-bright second after a door: that comes from frame-ahead itself, which v2.6 already ran (project log 10 Nov 07:25: full wait 0 of 45, frame-ahead without guard 8 of 20, guard=3 4 of 12; "the copy guard neither causes nor fixes it") | no (T91, off) | all 70 frame-ahead starts |
| `EDEN_GBB_TRUST_COPY=1` + `EDEN_NX2_RESNAPSHOT=0` | frame race; on a first start, the black screen after the opening | first start past the black screen 2 of 2 with the pair, 0 of 4 without (project log 02:46) | no; not in the shipped `env.txt` either | 72 |
| `EDEN_UP_HEAP_WAIT_MS=2000` | shader builder threads crashing when memory is short | starve test 3 of 3 through, 0 lost (ledger) | no | 72 |
| `EDEN_UP_SHADER_PREP=1` | first-visit freezes (4.2 s -> 1.0 s, t85-c) | ledger, v2.4 | no | 72 |
| `EDEN_NX2_RADV_MESH_COMPUTE_LONE=1` | missing leaves and plants (T47) | memory note | no | 72 |
| `EDEN_NX2_AREA_EVICT=40` + `EDEN_NX2_CRAM_RESERVE_MIB=256` | New Game crash at the first area change (8 Nov) | 3 of 3 / 4 of 4 against crashing controls | no | 72 / 65 (7 = reserve 64 on purpose) |

## 2. Drift of the queued tests

Counted by `env-drift.py` against v2.7. The tool reads `<queue>.state.json` and leaves out items that are done or
running. At 03:31 the chain was cut to the alpha blockers (project log 03:31): `night-steps.txt` now holds 8 queues, 82
starts, all on T134; 17 steps are parked in `night-steps.later.txt`. The **Where** column says which list a plan is in
(active / parked / ran).

| Where: queue plan (starts) | Difference | Judged | Why |
|---|---|---|---|
| ran: t130a: t130-auto (2) | no tracker | ACCIDENTAL | old door-walk env |
| active, running now: door-wall-t134 (10) | no frame-ahead, submit thread, GPU transcode, tracker (so the guard does nothing and is not compared) | deliberate | default-settings new game (shipped `env.txt` + trust-copy pair) |
| active, running now: door-wall-t134 k1, a1, a2 (3) | no keep-arenas | deliberate | the arm without keep-arenas |
| active: decode-bound-door (4) | no tracker | ACCIDENTAL | the exit half of the same queue has it |
| active: t131a t131-lean-ssbo (4) | no tracker | ACCIDENTAL | old door-walk env |
| active: t132a t132-h1-jit (7) | reserve 64 (play: 256) | deliberate | forces the JIT crash (queue note) |
| active: village-shadows n1, n2 (2) | no frame-ahead | deliberate | the "no frame ahead" arm |
| parked: t129b t129-prep-flip, t129-counts-door (2) | no tracker | ACCIDENTAL | old door-walk env |
| parked: 6 gate queues, stand-gate-t122 | no tracker | deliberate now, accidental in origin | same plan since T122 so builds compare with older gates; it cannot see a cost that needs the tracker |
| parked: t122b stand-clean (9) | no trust copy, resnapshot, frame-ahead, submit thread, GPU transcode; tracker only in its arm | deliberate | clean mode: control = shipped `env.txt` |
| parked: t122b four live-t121 plans (4) | no tracker | ACCIDENTAL | live plans written before v2.6 |
| parked: t122b stand-speed (8), stand-layout (8) | no tracker | ACCIDENTAL | written before v2.6 |
| parked: t122b stand-speed nomax (2), stand-layout 6 arms | no max resolution / other thread placement | deliberate | the arms under test |
| parked: t122b t116-h (10), t116-d (9), t118-s (5) | no tracker | ACCIDENTAL | T116/T118 plans from 10-11 Nov |
| parked: t122b t111-s (2) | no trust copy, resnapshot, frame-ahead, submit thread, GPU transcode, heap wait, tracker | ACCIDENTAL | a v2.4-era filler from 10 Nov; my inference, not its note: nothing in its purpose needs full wait |

Totals, active chain (82 starts): 10 running (door wall, differences all deliberate); of the 72 ahead, 55 same as v2.7,
9 only deliberate (reserve 64 x7, no frame-ahead x2), **8 accidental** (tracker missing: `t131-lean-ssbo` 4,
`decode-bound-door` 4). Exit 1.

Totals, parked steps (189 starts, `--steps night-steps.later.txt`): 99 same, 42 only deliberate, **48
accidental** (tracker 48; `t111-s` also 6 more lines each). Exit 1. Fix these before a parked step goes back in the chain.

Before the cut (03:30, the full chain): 286 starts / 164 same / 64 deliberate / 58 accidental, the same numbers an
independent recount got; 15 of them (`queue-t130a`) have run since, 2 of the 58 (`t130-auto`) without the tracker.

Proven fixes that are not play-file lines are not drift by this measure: in the 72 starts ahead the shader hitch fix is off
in 36 and the pause-menu fix in 34 (`--fixes` shows them).

### Queued starts that may test nothing (VERIFY without its main switch)

The drift check cannot judge extra test lines, but it flags the failure class of the t126 check run (v1 had
`EDEN_UP_AREA_BUDGET_VERIFY=1` without `EDEN_UP_AREA_BUDGET=1` and tested nothing). Five starts, **all in parked steps** (none in the active chain), have a
`_VERIFY` switch on and the switch of the same name without `_VERIFY` unset. Each may be meant to run alone; check before it
runs:
- `queue-t129b` t129-counts-door s1: `EDEN_UP_STALE_BACKING_FIX_VERIFY=1`
- `queue-t128b` t128-translate-1 v1: `EDEN_UP_FAST_TRANSLATE_VERIFY=1`
- `queue-t128b` t128-exit-mem-1 g2: `EDEN_UP_GC_WRITEBACK_SKIP_VERIFY=1`
- `queue-stack` stack-verify v1 and stack-heavy v2: `EDEN_NX2_SPLIT_VERIFY=1`

### Runs of the last 48 hours whose verdict is in doubt

Read from `notes/runs.jsonl` (env per run) for batches from 10 Nov 03:12 on. A line counts as missing only if it was in the
play file of that moment (heap wait from 10 Nov 22:25, tracker from 11 Nov 06:15) or was a proven fix.

| Runs | Accidental difference | Verdict | In doubt? | Rerun |
|---|---|---|---|---|
| t130-allfixes-exit (4), 12 Nov | frame-ahead without the guard | crash fixes: no harm; hitch fix: same pipelines 64-88 -> 3-7 ms | **yes, partly: control c1 was lost to the guard-less HUD blank** (the script took the blank for the talk starting, project log 01:00), leaving 1 valid control | 1 more control with the guard on |
| t130-allfixes-menu (4), 12 Nov | frame-ahead without the guard | crash fixes: no harm; menu fix likely works | the "bars, wedges and heart shapes in the stills" are the icon glitch the guard removes; dark-flicker counts include guard-less faults (like for like, so "not caused by the fixes" holds) | 1 fix + 1 control on the menu route with the guard would close the picture question |
| t126-menu, t126-exit + verify (11), 11 Nov | guard off | menu fix works, picture intact | no for the stutter; picture checks were guard-less | none |
| t126-doors (2), t126-doors-6 (6), t126-doors-verify (1), t129-prep-door (6), pipes-preload (4), t129-counts (2), t130-auto (2) | guard on, no tracker | hitch fix, area budget at the door, preload | no: the tracker changes fps by 0.4-1.45, not shader rebuilds or texture deletes; absolute fps about 1 low | none |
| about 25 live and standing fps runs at the heavy spot, 11 Nov (live-heavy-*, live-prof-*, the small-wins singles) | guard off | "neutral alone" for many speed switches | yes, mildly: a switch about uploads or page tracking can act differently with the guard copying pages. The small-wins stack now runs with the guard, so it will show it | let `queue-stack` (now with the guard) decide; no single reruns |
| hogcal (5), 10-11 Nov | no tracker, no heap wait | hog levels | yes, mildly: the heap wait changes when a builder gives up under a memory hog, so its hog level may sit differently | recalibrate the hog only if a hog test misbehaves |
| t112-n (12), t114-g1 (6), t114-g2 (9), t100-c2 (3), 10-11 Nov | no heap wait | NaN pair, GBB switches under the guard | no: the picture verdicts do not depend on the heap wait | none |
| stand-gate legs (all) | no tracker | build gates | no: same plan in every leg | none |

## 3. How it happened

1. **Each plan freezes a copy.** A new plan is made by copying the env list of an older plan or file. When the play file
   gains a line (tracker on 11 Nov 06:15), every plan copied from before keeps the old list. 8 starts in tonight's chain and 48
   parked ones still carry the v2.5 list.
2. **Nothing compares.** The runner checks keys and syntax (`PLAN_KEYS`), not content. `postprocess.py --reference-env`
   can diff a control against a file, but no queued queue sets `reference_env`, and it only reports after the run.
   `switch-ledger.py` tracks switches that are off, not whether the play file or the plans have them; the pause-menu
   fix and read sync have no entry in `switch-reasons.json` at all.
3. **A proven fix stays a line in one note.** The guard was proven 11 Nov 11:10. Its own note said "opt-in, not the
   default yet, Vampinity's call". It went into the one-evening file `env-play-tonight-A.txt` (11 Nov 23:40) and nowhere else.
   At 03:03 I then told you it was "on in your play settings": that was wrong (corrected 03:11, fixed 03:14 with v2.7).
4. **Open questions were not put to you again.** "Does the fast file ship with the guard?" (guard-cost note, 11 Nov)
   waited until tonight. "Shader hitch fix on by default after its last check" (P8) and "pause-menu fix opt-in until a
   clean test" (P9) are still open in `alpha-release/OPEN-POINTS.md`. The last checks for P8 (`queue-t129b`) sit near the
   end of the chain, behind newer work.
5. **Every new switch ships off.** Since T82 every build adds switches "off by default", so a fix only reaches a player
   or a test through a file line.

## 4. The cure

### (a) `env-drift.py`

Standalone, read only, does not import or change the runner. `python3 env-drift.py --all-queued` (or a queue or plan
path). Compares every start with the play file that `put-owner-back.sh` installs (read from that script, so v2.8 or later
is picked up the day it is installed; `--reference` to pick another), subtracts the differences declared in
`drift-declared.json`, prints per plan `ok` or `DRIFT` with the lines, exits 1 on undeclared drift, 2 on an
unreadable file or a malformed start.

- Leaves out queue items that `<queue>.state.json` marks done, skipped, stopped, interrupted or running
  (`--include-finished` counts them).
- `play_line_needs` in the declared file: the guard is only compared in starts with frame-ahead on (the same rule
  `proven_fixes` already used). That covers the 21 starts ahead without frame-ahead (door-wall-t134 10, stand-clean 9,
  village-shadows n1/n2 2) without hiding a missing guard anywhere it matters.
- Declarations are matched exactly: `-NAME` (left out) or `NAME=VALUE`; a declared reserve of 64 no longer hides
  another reserve value or a missing line. Unused declarations are named per start, not per plan.
- `--fixes` lists proven fixes that are off (info), `--strict-fixes` counts them as drift.
- Warns on a `_VERIFY` switch without its main switch (`--strict-verify` makes it drift).
- Limit: it only compares lines that are in the play file; extra test lines are not judged.

Checked: exit 0 on `batch-t132-h1-jit` (declared only) and `batch-stack-heavy`, 1 on `batch-t111-s` and with
`--strict-verify` on `batch-stack-heavy`, 2 on a missing file and on a plan whose start is not an object. Same counts with
`--reference env-play-v26-fast-docked.txt` (the guard rule makes v2.6 and v2.7 equal for these plans).

Run at about 03:35 on the cut chain, `--all-queued --fixes --summary`:

```
Reference: .../env-play-v27-fast-docked.txt (82 lines)
Not counted (already run or running, per <queue>.state.json; --include-finished counts them): running 10
Starts: 72; same as the reference: 55; only declared differences: 9; with undeclared drift: 8
Undeclared, by line (starts): EDEN_UP_FRITCHII_USAGE_TRACKER 8
Declared, by line (starts): EDEN_NX2_CRAM_RESERVE_MIB 7, EDEN_NX2_FRAMES_AHEAD 2
Proven fixes off (starts, info): EDEN_UP_PREP_UNREAD_HANDLE=1 36, EDEN_UP_AREA_BUDGET=1 34
exit 1
```

With `--include-finished` (the running door wall counted too): 82 / 55 / 19 / 8, and the guard is "not compared" in the
10 door-wall starts (no frame-ahead). With `--steps night-steps.later.txt`: 189 / 99 / 42 / 48, guard not
compared in 11, plus the five VERIFY warnings above. No declaration in a scanned plan matched nothing. Declarations of
plans not in the scanned lists (the T133 `batch-door-wall.json` fallback, the finished `t130-auto`) are not judged.

Proposed use, needs your OK because it touches the running set-up: run it (both step lists) before every new queue goes
into `night-steps.txt`; add the tracker to `t131-lean-ssbo` and `decode-bound-door` before they run (they are the last two
steps of the cut chain, several hours away), and to the 48 parked starts before their steps come back (or retire `t111-s`).

### (b) `drift-declared.json`

The deliberate differences above with exact values and reasons, the guard-needs-frame-ahead rule, and the two proven
fixes not yet in play for `--fixes`.

### (c) `env-play-v28-proposed.txt` (not installed)

v2.7-fast (your play file) plus two lines, nothing removed or changed:
- `EDEN_UP_PREP_UNREAD_HANDLE=1`: fewer hitches at doors and exits; no cost seen; its fault-injection check has not run.
- `EDEN_UP_AREA_BUDGET=1`: smoother pause-menu close; no fps cost; open memory question (lower largest free block in one
  menu batch, too close to call in another). The riskier of the two, since your crashes are memory crashes.
Left out: read sync (20% cost), the NaN pair (needs one test), the unproven crash fixes. Needs T129 or newer. You played
these lines with the guard on T130 for 8.5 minutes (`env-play-tonight-A.txt`, the same non-comment lines as v2.8); that
session's crash was the JIT code store running out of memory, not these lines.

### (d) Make build defaults in the next build (so no file can forget them)

1. `EDEN_UP_AHEAD_GUARD=3` whenever `EDEN_NX2_FRAMES_AHEAD=1` (decided 03:03), `=0` to opt out.
2. `EDEN_UP_PREP_UNREAD_HANDLE=1`, once `queue-t129b` (fault flip + exit check) shows 0 differ: move that queue up.
3. `EDEN_GBB_TRUST_COPY=1` + `EDEN_NX2_RESNAPSHOT=0` for the first start (black screen 2 of 2 through vs 0 of 4), or
   T133's root fix if it proves itself first.
4. Later: `EDEN_UP_AREA_BUDGET=1` after a memory test with it alone (3 on, 3 off) on the menu route.

## In plain words (written for the project owner)

- Forgotten: the icon fix (in your file since 03:14, v2.7) and 2 proven fixes still not in it: shader hitch, pause menu.
- Until 03:03 the icon fix was off in 154 of 285 queued tests. Now on in every test that uses the fast setting.
- Tonight's cut list: 8 of 72 tests still to run miss your usage tracker by accident; the parked list has 48 more.
- Cost so far: one control run lost (the script took an icon glitch for a conversation starting); no verdict overturned.
- Why: every test keeps a frozen copy of the settings, and nothing checked it against your file.
- New: a drift check that compares every queued test with your file and flags any difference without a written reason.
- Your call: v2.8 = v2.7 + those 2 fixes. No speed cost seen; the menu fix has one open memory question.
