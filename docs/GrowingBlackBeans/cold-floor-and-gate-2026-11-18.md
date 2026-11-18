# The cold floor for all five scopes, and the gate tool (18 Nov 2026)

**Every scope of breadth now has four eligible cold starts on the alpha control** (T186 + play settings v4.0,
swap-ahead 2048, 13.60, handheld 1x), and `tools/stk/stk_gate.py` reads a candidate against them in the agreed order:
stable, then the picture, then fast, then smooth (MEASURING.md, PR #17).

## The cold floor (`tools/stk/floors-cold-2026-11-18.json`)

Noise floor = the control's own spread (max - min of four starts), as MEASURING.md asks.

| scope (route) | starts | the gate's best numbers: mean, floor | lowest largest free block (census) |
|---|---|---|---|
| baseline (`new-game-v9`) | BW1, 2, 4, 5 | median fps 26.74, floor 0.45 (1.7%) | 165-362 MiB |
| Kokiri (`kokiri-four-stops-v2`) | KV1, 2, 4, 5 | stops A 19.20 / B 29.74 / C 17.47 / D 17.66, floors 0.41-0.74 | 219-479 MiB |
| field, after the field (`field-to-past-field`) | FC2-FC5 | after the field 13.90, floor 0.15 (1.1%); field walk 13.42, floor 1.17 | 0-1 MiB |
| a later area (`later-area-village-lap-v2`) | LV2, 3, 4, 6 | lap 8.73, floor 0.31 (3.6%); field stand 12.88, floor 0.40 | 3-18 MiB |

- **The baseline village windows are too noisy to gate on** (floor 6.56 fps, 34%: the two-speed village, a phase 4
  lead). Until that is explained, the baseline is gated on its whole-run median.
- **Memory is tightest after the field (0-1 MiB) and in the later area (3-18 MiB).** Both are census lows.
- **The worst frame is a load black** (11-55 s) on every route. It sits in "smooth" only until a hitch trace exists.
- **Not measured on the alpha: flashes and hitches.** The gate prints both as "not measured" in every report.

## The gate (`tools/stk/stk_gate.py`)

    python3 tools/stk/stk_gate.py floors CONTROL_RUNS... -o floors.json
    python3 tools/stk/stk_gate.py check CANDIDATE_RUNS... --floors floors.json

- **The key:** route | firmware | cold or warm (plus the store and its pipeline count when warm). The build is not
  in the key.
- **A number is worse** when it is on the bad side of the control's mean by more than the floor. It changes the verdict
  only with the permutation test behind it (p < 0.05 "real", p < 0.2 "likely", abcompare.py's rule). Beyond the floor
  without that is listed as "watch".
- **Verdicts:** BLOCK (a start lost its route, or memory or the picture really worse), EXPLAIN (a number worse with
  p < 0.2: a trade is fine if it can be explained), PASS. Provisional under 4 starts a side.
- **Checked:** 16 of 16 control starts PASS against a floor built from the other three in their scope (leave one out).
  All three starts that lost their route block (KV3, LV5, FC1). 14 unit tests on made-up rows. Not yet seen: a real
  four-start regression on these routes, because the archive has none. The first candidate is the first real use.
