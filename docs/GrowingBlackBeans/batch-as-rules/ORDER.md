# Batch A split (drain at area alone): arms, order, and a cut-short rule

Written 24 Nov 2026, before start 1. The rules beside this file (`BATCH-AS-RULES.md`, sha1 133e19b181fb) were frozen
23 Nov 15:03 UTC and are copied here byte for byte. This file adds only what the new standard asks for (#43): the
arms, the order, and what happens if the sitting is cut short.

## Arms
- **C, control:** the control env (alpha T186 01.219.028, swap ahead 2048), warm field route, whole cache restored
  before every start.
- **w, drain at area out:** the same env with one line removed, `EDEN_UP_DRAIN_AT_AREA=1`. Pressure drain and load
  hold's drain step stay on.

## Order (one sitting)

| # | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| arm | C1 | w1 | C2 | C3 | w2 | C4 | C5 | w3 | C6 | C7 | w4 | C8 |

Start 1 is checked alone before start 2. A start that doesn't count (and didn't crash) is rerun at the end of the
sitting, as the rules say.

## If the sitting is cut short
- Starts already back are kept and checked. Nothing is read before the batch is finished or called short.
- **A second sitting** picks up the order where it stopped, with any reruns at its end. Before reading, the two
  sittings' eligible controls are compared on the six numbers (two-sided permutation, as batch A's sitting check):
  p < 0.01 on any of them and the arm is **hold**.
- **Called short** if, after at most two sittings, there are fewer than 7 eligible controls or fewer than 4 counted
  arm starts: no call is made, and the runs are packed and posted as they are.
- No controls from another batch or from batch A are borrowed, in any case.
