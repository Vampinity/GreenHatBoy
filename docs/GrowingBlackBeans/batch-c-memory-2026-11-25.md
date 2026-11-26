# Batch C: four more memory parts, and the waits probe (GrowingBlackBeans, 25 Nov 2026)

**Table reserve out moved: more room at the black (p 0.0011). Scratch release, keep arenas and report thread out: quiet,
no harm seen. The waits probe makes batch D three arms.**

Phase 4, memory first. Batch C was Vampinity's in the 22 Nov split; they handed it over on 25 Nov, and it ran on our
console under the split's conditions. Alpha T186 (01.219.028) + play v4.0 with swap ahead 2048, base PS5, 13.60, handheld
1x, the warm field route (c4fada64155f), the shared warm store (prep_5093ab9e, 80,770), the whole cache restored before
every start. 4 starts of each arm against 12 controls, interleaved (C w x C y z C C z y C x w C C x w C z y C C y z C w x C),
then start 29, the waits probe.

Rules frozen 25 Nov before start 1 (sha1 4d083ca2d204), with batch D's decision written beside them (`waits.py`):
[`batch-c-rules/`](batch-c-rules/). No amendments.

**Moved:** a crash in an arm when no control crashed, or a two-sided permutation p < 0.01 on any of the six numbers. Read
needs 10 or more eligible controls.

| number | 12 controls | w, table reserve out | x, scratch release out | y, keep arenas out | z, report thread out |
|---|---|---|---|---|---|
| graphics refusals, to script_end (tries) | 1-28 | 0-15 (p 0.97) | 1-5 (p 0.21) | 1-21 (p 0.98) | 0-18 (p 0.68) |
| distinct failed shapes (beside refusals) | 0-7 | 0-4 (p 0.88) | 0-1 (p 0.20) | 0-4 (p 0.80) | 0-6 (p 0.91) |
| largest free block at the black, MiB | 1056-1270 | **1244-1331 (p 0.0011)** | 1124-1312 (p 0.059) | 1009-1305 (p 0.21) | 909-1111 (p 0.12) |
| s under 16 MiB | 12-44 | 20-32 (p 1.00) | 10-24 (p 0.084) | 10-50 (p 0.64) | 10-38 (p 0.76) |
| worst frame after the black, ms | 1,082-8,634 | 1,259-4,430 (p 0.66) | 1,282-1,426 (p 0.17) | 1,246-7,000 (p 0.91) | 1,110-3,021 (p 0.64) |
| load s | 17.3-25.8 | 8.3-24.3 (p 0.25) | 11.4-22.1 (p 0.065) | 17.1-29.3 (p 0.80) | 19.2-26.4 (p 0.23) |
| field walk fps | 18.75-19.56 | 18.83-19.59 (p 0.93) | 18.77-19.60 (p 0.53) | 18.61-19.35 (p 0.25) | 19.13-19.47 (p 0.40) |

**Verdicts**
- **w, table reserve out: moved**, more room at the black: median 1,290 MiB against 1,118 in the controls. Its proof held:
  the two `EDEN_UP_TABLE_RESERVE on: 8 blocks` lines are in every control and every x, y and z start, and in no w start. No
  table wait and no `EDEN_UP_TABLE_REFUSED` line anywhere (0 in all 28).
- **x, y, z: removed, no harm seen** (none prints a line of its own, so that is their best verdict).

**What this does and does not say**
- **Read w with care.** The reserve is 8 blocks, about 16 MiB, and the gain is about 170 MiB, so it isn't the reserve's own
  memory coming back. Either something else lays out differently without it, or it's a false move: identical controls give
  one in about 1 batch in 7 at four arms. Two things point that way:
  - this batch's controls sat low: batch B's 11 eligible controls ran 1088-1296 MiB (median 1,245), and w's 1244-1331 sits
    inside that. Batches aren't pooled, so that is context, not a read;
  - x and y lean the same way (medians 1,223 and 1,245, p 0.059 and 0.21).
  Before anyone leans on it, w wants a repeat against fresh controls, and a look at what the free block is made of.
- **y acted:** with keep arenas out, 12-24 arenas were given back by the last `EDEN_HEAP_GROWTH` line (24, 20, 12, 22),
  against 0 in every control. The room at the black didn't follow (p 0.21). That settles the old pair one way on this
  route: T51 (878 against 623 MiB, one run each) is not what this batch sees.
- **x leans** toward more room and a shorter load (p 0.059, 0.065), not called.
- **z** has the lowest single room at the black of any start (Z2, 909 MiB), but the arm doesn't move (p 0.12), and its
  worst frame after the black doesn't lengthen (p 0.64).
- **No start crashed or hung**; 28 of 28 completed and all 12 controls are eligible.
- **Every start was checked for the whole-cache restore** in the runner's own log before the import: 29 of 29 (27 files,
  2.1 GiB, 203-218 s each), and all booted warm (80,770 known, 3 own records, Total Pipeline Count 4). The owner's caches
  were put back at the end, each listing the same as before.
- A screen on this route, handheld, from a fresh start, at 4 against 12. Nothing is adopted or removed: phase 4 explains
  the control and changes nothing until the programme ends.

**The waits probe (start 29) and batch D**

Control env + `EDEN_UP_FAULT_LOG=1`, log-only on this control. Not read for numbers.

| wait | seen | batch D |
|---|---|---|
| guest-write | 2 in the probe, both on the cpu-jit thread near 175 s: 2 ms and 95 ms, both got a block | active: an arm |
| block wait trim | acts only inside a guest-write wait, so active with them | active: an arm |
| JIT commit | 1, in control C2 (`JIT code cache: no memory for its next part`); 0 in the probe | active: an arm |
| new-handler | never, in the probe or any control | never acted on this route (handheld, field): no arm |

By the rule frozen before start 1, batch D has three arms, one at a time, each with 12 controls of its own. In the
split, D was Vampinity's: who runs it is yours to say.

**Every start** (all warm; all ended at script done)

| # | start | arm | refusals | shapes | at the black MiB | s < 16 MiB | worst after the black ms | load s | field walk fps |
|---|---|---|---|---|---|---|---|---|---|
| 1 | C1 | control | 7 | 2 | 1188 | 26 | 1785.3 | 19.4 | 19.54 |
| 2 | W1 | table reserve out | 15 | 4 | 1285 | 28 | 4430.2 | 22.1 | 18.89 |
| 3 | X1 | scratch release out | 2 | 0 | 1230 | 10 | 1287.2 | 19.2 | 19.60 |
| 4 | C2 | control | 6 | 5 | 1132 | 40 | 5072.1 | 24.5 | 19.56 |
| 5 | Y1 | keep arenas out | 2 | 0 | 1305 | 10 | 1245.9 | 17.1 | 18.98 |
| 6 | Z1 | report thread out | 15 | 6 | 1111 | 36 | 3020.9 | 26.3 | 19.37 |
| 7 | C3 | control | 1 | 0 | 1088 | 18 | 1588.3 | 18.5 | 19.01 |
| 8 | C4 | control | 28 | 7 | 1082 | 42 | 8633.7 | 25.8 | 19.12 |
| 9 | Z2 | report thread out | 0 | 0 | 909 | 10 | 1110.2 | 19.2 | 19.13 |
| 10 | Y2 | keep arenas out | 21 | 4 | 1212 | 50 | 6999.8 | 29.3 | 18.61 |
| 11 | C5 | control | 5 | 3 | 1072 | 14 | 1245.7 | 21 | 18.75 |
| 12 | X2 | scratch release out | 1 | 1 | 1216 | 16 | 1282.3 | 11.4 | 19.01 |
| 13 | W2 | table reserve out | 12 | 4 | 1244 | 20 | 2335.9 | 24.3 | 19.59 |
| 14 | C6 | control | 2 | 0 | 1270 | 30 | 1082.0 | 21.2 | 19.05 |
| 15 | C7 | control | 6 | 2 | 1104 | 44 | 3190.2 | 23 | 19.15 |
| 16 | X3 | scratch release out | 5 | 0 | 1124 | 24 | 1321.8 | 22.1 | 18.77 |
| 17 | W3 | table reserve out | 4 | 2 | 1295 | 32 | 1448.1 | 19.8 | 18.83 |
| 18 | C8 | control | 1 | 0 | 1191 | 28 | 1201.4 | 17.3 | 18.87 |
| 19 | Z3 | report thread out | 18 | 3 | 1104 | 16 | 2800.6 | 21.9 | 19.47 |
| 20 | Y3 | keep arenas out | 1 | 1 | 1009 | 16 | 1278.2 | 18.3 | 18.99 |
| 21 | C9 | control | 10 | 1 | 1060 | 22 | 2615.9 | 20.8 | 19.27 |
| 22 | C10 | control | 1 | 0 | 1226 | 12 | 1151.0 | 20.6 | 19.00 |
| 23 | Y4 | keep arenas out | 7 | 2 | 1278 | 18 | 1363.6 | 19 | 19.35 |
| 24 | Z4 | report thread out | 8 | 1 | 1108 | 38 | 2411.2 | 26.4 | 19.16 |
| 25 | C11 | control | 17 | 5 | 1056 | 26 | 4621.0 | 21.3 | 19.28 |
| 26 | W4 | table reserve out | 0 | 0 | 1331 | 30 | 1259.0 | 8.3 | 19.41 |
| 27 | X4 | scratch release out | 2 | 1 | 1312 | 16 | 1425.8 | 18.9 | 18.85 |
| 28 | C12 | control | 13 | 2 | 1146 | 24 | 3174.9 | 24 | 19.37 |

Runs: `runs/GrowingBlackBeans/2026-11-25-runM1C-01-C1` to `-28-C12`, and `-29-PROBE`, each with a NOTE.md. Read with the
batch kit (`batch_kit.py read`, exact two-sided permutation on means), scorer stk_score 10; batch D's decision with
`waits.py`. The runner's result folder is not posted: it holds the console's network address. Each start's logs came
from it, flat, through a checked import (the env and the route that ran are the folder's).
