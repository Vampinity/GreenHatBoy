# R × C: pack on refusal and reclaim off together, 4 against 4 (GrowingBlackBeans, 22 Nov 2026)

**Confirmed.**

**Corrected after the merge (22 Nov):** the distinct column was 10-23 against 5-8. It also added one for each
image refusal with no shape line, so it wasn't a floor. Shapes alone are 8-20 against 3-6 (Vampinity, on #37).
Still no overlap; the rule reads tries, so the verdict is unchanged.

Alpha T186 (01.219.028), base PS5, 13.60, handheld 1x, the warm field route, whole-cache restore before every start, ABBA (C4 rerun at the end).
Pair out = the control minus `EDEN_UP_PACK_ON_REFUSAL=1` and `EDEN_GUEST_SWAP_RECLAIM=1`.

**The rule, written before any start:** confirmed if all four pair-out starts have more graphics refusals (to `script_end`) than every control in the batch, and more than 15.

| start | arm | graphics refusals (tries) | failed image tries | distinct requests, at least | at the black MiB | s under 16 MiB | load s | worst after the black ms | fps median | field walk | after the field |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | control | 6 | 3 | 3 | 1254 | 24 | 21.3 | 1278.7 | 14.1 | 18.9 | 13.9 |
| X1 | pair out | 101 | 91 | 18 | 1303 | 20 | 25.4 | 4800.6 | 14.0 | 19.09 | 13.9 |
| X2 | pair out | 26 | 24 | 9 | 1038 | 26 | 21.3 | 3263.9 | 14.2 | 19.2 | 14.1 |
| C2 | control | 10 | 8 | 6 | 1256 | 44 | 24.7 | 1892.7 | 14.2 | 19.15 | 14.0 |
| C3 | control | 11 | 10 | 4 | 1022 | 30 | 20.1 | 3129.4 | 14.2 | 19.13 | 14.0 |
| X3 | pair out | 66 | 59 | 20 | 1250 | 38 | 24.6 | 4324.1 | 14.2 | 19.09 | 14.1 |
| X4 | pair out | 26 | 24 | 8 | 1149 | 26 | 22.4 | 2597.2 | 14.2 | 18.6 | 13.95 |
| C4r | control | 19 | 16 | 6 | 1174 | 72 | 24.5 | 2868.3 | 14.2 | 19.19 | 14.0 |

| number | controls | pair out | |
|---|---|---|---|
| graphics refusals (the rule) | 6-19 | 26-101 | no overlap |
| failed image tries | 3-16 | 24-91 | no overlap |
| distinct requests, at least | 3-6 | 8-20 | no overlap |
| at the black MiB | 1022-1256 | 1038-1303 | overlap |
| s under 16 MiB | 24-72 | 20-38 | overlap |
| load s | 20.1-24.7 | 21.3-25.4 | overlap |
| worst after the black ms | 1278.7-3129.4 | 2597.2-4800.6 | overlap |
| field walk fps | 18.9-19.19 | 18.6-19.2 | overlap |

**What this does and does not say**

- The rule reads tries. With both lines out a refused request gets nothing back, fails, and is asked again, so part of
  the rise is retries (Vampinity, #35). The distinct column is the floor without repeats (failed image shapes
  only: one per shape, buffers and refusals with no shape line left out): read the size of the effect there, not in the tries.
- Every valid start got through the load, and every one reached the bottom of memory in it.
- The worst frame after the black was added after seeing the data. It is reported, and decides nothing.
- The margin is small at the bottom: the lowest pair-out start is 26 against the highest control's 19, and 8 against 6
  on distinct requests. A control can pass 15 by itself (C4r did), so 15 is not a line between healthy and not.
- If the lines made no difference, four against four would separate this way round 1 time in 70 by chance.
- This batch takes the two lines out together. It did not retest either alone (that is M1A-S, #33).
- C4 is out by the boot rule in its header, written before the start. Counting it would not change the call:
  0 graphics refusals before its crash.
- Handheld, this route, a fresh start. Nothing is adopted.

**Not counted, kept as data**

- C4: cold boot, crashed (its NOTE.md).
