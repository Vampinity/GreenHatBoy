# The run contract, v1

**Status: proposed, for review** (16 Nov 2026). waveydude has agreed to the principle — share the run,
not the workspace — and to the four points he asked for (marked below). Vampinity to review. Implemented
in [`tools/stk/`](../tools/stk/), which scores the 1,332 packed runs in `runs/` under it.

Why: two people's numbers can only be compared when the runs say, in data, what they were. Each of us
keeps our own folders, names and routine; what is shared is the run folder, what it records, and how a
control start is taken.

## Shared, and only this

**1. The run folder.** Flat, this run's files only: `eden_log.txt`, `stderr.log`, `env.txt`,
`boot-trace.txt`, `heap.log`, `script.txt` (the route as run; `route.txt` accepted), this run's `crash-*` set if it crashed, `config.json` if
available, `declared.json`. Packed, the same names with logs `.gz`. One reader opens both.

**2. What a person declares** (`declared.json`, intent only): `author`, `run_id`, `batch`, `arm`,
`control` (meant as a control start), `route`, `intended_cache` (`cold`/`warm`/`any`), `runner`,
`console` (a label, never an address), `notes`.

**3. What is derived from the logs, never typed** (waveydude's four points in **bold**):

| field | from |
|---|---|
| firmware | `sdk_version` in the boot trace |
| build | the version line with its compile time (T185 and T186 share `01.219.028`) and the store's build number |
| **translation id** (+ device id) | the shader store line. **A new build can start a new store with an identical env** (W-34, the alpha zip) |
| **store** | name, `new`/`reused`, its pipeline count; plus `Total Pipeline Count` and whether a driver cache loaded |
| **cache class** | `cold` (new store, 0 pipelines, no driver cache), `warm` (reused store), `half` (anything between — never a control) |
| start, end | `test_boot`/`launcher`; `app_closed`/`log_cut`/`crash`, and the seconds after the script |
| **route proof** | waveydude's `route_check`: `route_result` = `completed` / `tail_unverified` (moves after the last check that nothing confirms) / `failed` / `unknown` / `manual`, counting every STEER leg and required WAIT by line against the route file; the route's hashes. **`failed` and `unknown` are invalid and not scored.** END is not a check. Today every control route ends `tail_unverified`; the gate can require `completed` once each route ends on a check in its destination |
| **out-of-memory count** | `EDEN_RADV_OUT_OF_MEMORY` lines; **at 64 written `>=64`** (the log stops counting there) |
| memory | the census minimum (his chain), and the driver line's minimum as its own column |
| scoring windows | per route, from `windows.json` (village, field walk, after the field, Kokiri stands) |

**4. Control starts.** Two controls, never mixed (waveydude): **cold** (a first start, measures building
the shaders) and **warm** (a kept store, measures the game). A control start boots the game directly
(`EDEN_TEST_BOOT` + `test-boot-once`), plays on a copy of the save, closes with `test-quit` after the script ends (the time is recorded, not judged: whole-run figures
are cut at the script's end + 10 s, so nothing depends on it — our proposal, after runCC1–CC3), and
keeps one flat folder. Every one of those is checked from the log.

**5. The gate compares two rows only with the same comparison key:**
`route | firmware | translation id | store | cold-or-warm`. It refuses a row whose route didn't complete,
whose cache didn't match its declared intent, or whose settings differ from the control by more than
the one line under test, and it never compares two `>=64` counts. Its numbers are the route windows,
never whole-run figures. Noise floors are measured per key from control starts.

**6. Tools** live in GHB `tools/stk/` (the scorer under waveydude's name; Vampinity's packer,
generalised, with his own path unchanged). A tool joins when it takes a run folder as an argument,
reads through the shared reader, writes JSON with `null` + a reason for anything missing, and has a
test against a packed run.

## Personal, and staying that way

Workspace layout, hand-offs and filing, build names, run names, how a runner is built, which assistant.

## Open

- **The true out-of-memory count** for control runs: a log-only uncapped counter (proposal drafted,
  tabled). Until then `>=64` is a floor.
- **The stamp guard** (`stk check`, waveydude's `stamp_guard.py`) before every start: to come.
- **Vampinity**: confirm the route windows as data, review the generalised packer, and whether his runner
  can be shared.
