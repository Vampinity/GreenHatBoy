# M1A-S: the guest swapper's five parts, split (GrowingBlackBeans, 21 Nov 2026; corrected 22 Nov)

Alpha T186 (01.219.028), base PS5, 13.60, handheld 1x, warm (store `prep_5093ab9e` reused, 80,770), the field route.
12 splits on a 12-start Plackett-Burman table, interleaved with controls, whole-cache restore before every start.
Runs: `runs/GrowingBlackBeans/2026-11-21-runM1-*`, each with a NOTE.md.

**Nine eligible controls:** C1, C2, C5, C6, C7, C8, C11, C12, C3r. C3 ran cold. The logs of C4, C9 and C10 show no finished
close (`end_kind: log_cut`, `control_eligible: false`), so by `warm-run-steps.md` they don't count. That is one short of the
ten that condition 4 on #27 asks for. All four are kept as data.

**Corrected 22 Nov** (from Vampinity's review of #33):
- The control count was twelve; it is nine.
- "Refused pool events" (`EDEN_REFUSED_POOL`) is not a count: the line prints only when the retry failed, and it is
  throttled (the first 32 at most ten a second, then one every 5 s). The number here is now **graphics refusals**: lines
  up to `script_end` that start `EDEN_GRAPHICS_MEMORY an image was refused:` or `EDEN_GRAPHICS_MEMORY a buffer was refused:`.
  A plain search for "was refused" counts each buffer twice, because the heap's line repeats it.
- R × C is a possible pair until it is confirmed.
- "Frames unchanged" for P meant fps.
- The controls' reclaim calls were given as 2-4; the eligible ones made 1-6.

Parts: P pressure pack (`EDEN_UP_PACK_PRESSURE_*`), R pack on refusal (`EDEN_UP_PACK_ON_REFUSAL`), C reclaim
(`EDEN_GUEST_SWAP_RECLAIM`), A swap ahead (`EDEN_GUEST_SWAP_AHEAD_MIB`), T cold time (`EDEN_GUEST_SWAP_COLD_S`). Every
removed part's log line was absent and every kept one present (T has none). Effect = mean of the 6 splits with the part
out minus the 6 with it in. "At the black" = the last `RADV_PS5_MEMORY available_mib` before the script's line-92 mark.

| | at the black (MiB) | graphics refusals | worst frame (ms) |
|---|---|---|---|
| controls, 9 eligible | 1,191 (986-1,366, sd 106) | 2.1 (0-5) | 3,780 (3,736-3,858) |
| P out − in | **−304** (928 v 1,232, the splits don't overlap) | +72 | +1,082 |
| R out − in | +59 | +84 | +1,227 |
| C out − in | −67 | +78 | +1,176 |
| A out − in | −49 | +37 | +141 |
| T out − in | +66 | +65 | +1,023 |

Three starts (S6, S7, S12) make almost all of the refusal column, and two (S6, S12) most of the worst-frame column, so
neither column reads as five separate effects.

- **24 of 24 got through the load** (the 12 splits and 12 warm control-env starts, C4, C9 and C10 included),
  the start with all five parts out too. Every start fell to 0-8 MiB in the load and recovered. With the swapper off
  whole (M1A, 20 Nov) three clean starts crashed, so on this route the load rests on the swapper's base, as far as one
  all-five-out start shows.
- **P is the one main effect:** ~300 MiB more room on arrival, about 3 control sds. It didn't change survival or fps on
  this route. The long worst frames in its column are S6 and S12; the other four P-out starts had 3,746-3,874 ms.
  Recorded, nothing adopted.
- **R × C is a possible pair:** the three starts with both out had 144 (S6), 41 (S7) and 320 (S12) graphics refusals;
  the other 21 had 0-15. S7, the one with P in, is well below the other two. Each alone looks covered by the other
  (with R out, reclaim ran 149 times in S11, against 1-6 on the eligible controls).
- **Next:** R and C out together, 4 against 4. The rule, written 22 Nov before any start: confirmed if all four pair-out
  starts have more graphics refusals than every control in that batch, and more than 15.
- **Long worst frames** came only in S6 (6.9 s) and S12 (7.4 s), both with P, R and C out; S7 (P in) had 4.2 s. A lead
  from two starts; T's +1,023 rides on the same two.
- **A and T:** screened, no harm seen (T has no log line: set in 12 starts, no harm seen). Handheld, this route only.
- No part moves fps (±0.2) or load time beyond the controls' spread.

## Refusals per start, to script_end

`run.json`'s `refused_pool_events` is the last column, the throttled one.

| start | images | buffers | graphics refusals | pool report lines |
|---|---|---|---|---|
| C1 | 1 | 0 | 1 | 1 |
| S1 | 8 | 1 | 9 | 9 |
| C2 | 3 | 1 | 4 | 4 |
| S2 | 11 | 4 | 15 | 12 |
| S3 | 6 | 1 | 7 | 6 |
| C4 (not eligible) | 2 | 0 | 2 | 0 |
| S4 | 1 | 0 | 1 | 0 |
| C5 | 4 | 1 | 5 | 1 |
| S5 | 7 | 8 | 15 | 14 |
| C6 | 1 | 1 | 2 | 1 |
| S6 | 138 | 6 | 144 | 33 |
| C7 | 0 | 1 | 1 | 1 |
| S7 | 33 | 8 | 41 | 32 |
| C8 | 0 | 0 | 0 | 0 |
| S8 | 3 | 0 | 3 | 3 |
| C9 (not eligible) | 10 | 1 | 11 | 9 |
| S9 | 1 | 0 | 1 | 0 |
| C10 (not eligible) | 1 | 1 | 2 | 2 |
| S10 | 3 | 0 | 3 | 2 |
| C11 | 2 | 0 | 2 | 2 |
| S11 | 7 | 1 | 8 | 6 |
| C12 | 2 | 1 | 3 | 1 |
| S12 | 314 | 6 | 320 | 32 |
| C3r | 1 | 0 | 1 | 0 |
