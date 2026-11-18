# The cold floor for all five scopes, and the gate tool (18 Nov 2026)

**Every scope of breadth now has four eligible cold starts on the alpha control** (T186 + play settings v4.0,
swap-ahead 2048, 13.60, handheld 1x), and `tools/stk/stk_gate.py` reads a candidate against them in the agreed order:
stable, then the picture, then fast, then smooth (MEASURING.md, PR #17).

## The cold floor (`tools/stk/floors-cold-2026-11-18.json`)

"Floor" in the table = the spread of one start (max - min of the four). The gate reads a candidate's **mean** against
the noise of a mean, which is smaller (see the gate, below; revised after Vampinity's review of PR #18).

| scope (route) | starts | the gate's best numbers: mean, floor | lowest largest free block (census) |
|---|---|---|---|
| baseline (`new-game-v9`) | BW1, 2, 4, 5 | median fps 26.74, floor 0.45 (1.7%) | 165-362 MiB |
| Kokiri (`kokiri-four-stops-v2`) | KV1, 2, 4, 5 | stops A 19.20 / B 29.74 / C 17.47 / D 17.66, floors 0.41-0.74 | 219-479 MiB |
| field, after the field (`field-to-past-field`) | FC2-FC5 | after the field 13.90, floor 0.15 (1.1%); field walk 13.42, floor 1.17 | 0-1 MiB |
| a later area (`later-area-village-lap-v2`) | LV2, 3, 4, 6 | lap 8.73, floor 0.31 (3.6%); field stand 12.88, floor 0.40 | 3-18 MiB |

- **The baseline village windows are too noisy to gate on** (floor 6.56 fps, 34%: the two-speed village, a phase 4
  lead). Until that is explained, the baseline is gated on its whole-run median.
- **Memory is tightest after the field (0-1 MiB) and in the later area (3-18 MiB).** Both are census lows.
- **The field's out-of-memory count is unusable as a gate number:** FC4's counter hit its cap (">=64"), so the
  control's own value is unknown (9, 10, 10 and at least 64). The floor file marks it `usable: false`.
- **The worst frame is a load black** (11-55 s) on every route. It sits in "smooth" only until a hitch trace exists.
- **Not measured on the alpha: flashes and hitches.** The gate prints both as "not measured" in every report.

## The gate (`tools/stk/stk_gate.py`)

    python3 tools/stk/stk_gate.py floors CONTROL_RUNS... -o floors.json --alpha-env ALPHA_ENV
    python3 tools/stk/stk_gate.py check CANDIDATE_RUNS... --floors floors.json --alpha-env ALPHA_ENV

`ALPHA_ENV` is the alpha release's `env.txt`; the scorer reads each run's env against it.

- **The key:** route | firmware | cold or warm (plus the store and its pipeline count when warm). The build is not
  in the key.
- **A number is worse** when the candidate's mean is on the bad side of the control's mean by more than the noise of
  a mean, 2 x sd x sqrt(1/n_control + 1/n_candidate). The first version used one start's spread here, which let four
  candidate starts all below the worst control start pass (Vampinity's example: baseline memory at 120-150 MiB against
  a control low of 165). It changes the verdict only with the permutation test behind it (p < 0.05 "real", p < 0.2
  "likely", abcompare.py's rule); beyond the noise without that is "watch". A number is also "real" when p < 0.05 and
  every candidate start is worse than the control's worst start.
- **Capped counters:** a candidate start at the out-of-memory counter's cap counts at the cap (a lower bound), so it
  reads as worse than any uncapped control. A control start at the cap makes that number unusable for its key.
- **Each start is sorted first.** CRASHED, LOST (a WAIT or STEER timed out) or HUNG (the log stops before the
  script's END with no normal close) counts against the candidate. INVALID says nothing about it and is left out, to
  be rerun: the app was closed normally before the script's END, or a window's
  anchor line was skipped (a `MAYBE` that timed out; the scorer no longer takes a skipped line as a mark, except where a
  window declares its lines clock marks, as the Kokiri stands do).
- **Each side must be one thing** (waveydude's review). The starts pooled on one side must share the build, the
  settings (env hash), the translation id and the script. The control and the candidate may differ. A mixed candidate
  arm is MIXED, naming the runs that differ, and a mixed control arm can't make a floor.
- **Verdicts and exit codes:**
  - BLOCK, 4: a start crashed or lost its route, or memory or the picture is really worse. This applies even with
    fewer than 4 starts.
  - MIXED or INVALID, 3: no valid start.
  - PROVISIONAL, 2: fewer than 4 valid starts on either side, a gated memory reading on fewer than 4 candidate
    starts, or an unidentified build. It shows what the starts lean to.
  - EXPLAIN, 1: a number is worse with p < 0.2. A trade is fine if it can be explained.
  - PASS, 0.
  - Only 0 is cleared. PASS lists what it could not clear (on the alpha: flashes and hitches; on the field: the
    out-of-memory count).
- **Where memory can't block yet:** on the field route. Its control lows are already at 0-1 MiB (census) and 0-2 MiB
  (driver), and its out-of-memory count is unusable (FC4 capped). A candidate at 0 MiB on all four starts comes out
  worse (likely) on the census (p 0.143), so EXPLAIN, but it can't reach BLOCK: with a control start already at 0,
  no candidate is below every control start. On the baseline, Kokiri and the later area it can: four starts at 0 MiB in the later area block
  (p 0.029), and so do Vampinity's 120-150 MiB on the baseline. The field needs another memory number before memory is
  gated there.
- **Checked:** 16 of 16 control starts lean PASS against a floor built from the other three in their scope (leave one
  out). They read PROVISIONAL, because one start against three is short on both sides. **This checks the code, not the
  floors:** with one start against three, the smallest p is 0.25, so a left-out start can only pass or be "watch" (6
  of 16 were "watch"). The three starts that didn't reach the script's END (KV3, LV5, FC1) didn't lose their route:
  every leg was met and the app closed normally, the quit came before the END. They now read INVALID (rerun), not
  BLOCK. INVALID needs that normal close: a start whose log stops before END with no close is HUNG (a freeze) and
  blocks. runLV1 (route v1, a STEER timeout) is LOST. 40 gate tests on made-up rows, including each of both reviews'
  cases and the CLI's exit codes, and 3 for the skipped anchor. Rescored, all 21 starts keep every window value. Not
  yet seen: a real four-start regression on these routes, because the archive has none.
