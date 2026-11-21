# M1A-S: the guest swapper's five parts, split (GrowingBlackBeans, 21 Nov 2026)

Alpha T186 (01.219.028), base PS5, 13.60, handheld 1x, warm (store `prep_5093ab9e` reused, 80,770), the field route.
12 counted controls and 12 splits on a 12-start Plackett-Burman table, interleaved, whole-cache restore before every
start. Runs: `runs/GrowingBlackBeans/2026-11-21-runM1-*`, each with a NOTE.md. C3 ran cold (restore not uploaded) and is
kept but not counted; C3r replaces it.

Parts: P pressure pack (`EDEN_UP_PACK_PRESSURE_*`), R pack on refusal (`EDEN_UP_PACK_ON_REFUSAL`), C reclaim
(`EDEN_GUEST_SWAP_RECLAIM`), A swap ahead (`EDEN_GUEST_SWAP_AHEAD_MIB`), T cold time (`EDEN_GUEST_SWAP_COLD_S`). Every
removed part's log line was absent and every kept one present. Effect = mean of the 6 splits with the part out minus
the 6 with it in. "At the black" = the last `RADV_PS5_MEMORY available_mib` before the script's line-92 mark.

| | at the black (MiB) | refused pool events | worst frame (ms) |
|---|---|---|---|
| controls, 12 | 1,195 (986-1,366, sd 95) | 1.8 (0-9) | 3,815 (3,736-4,063) |
| P out − in | **−304** (928 v 1,232, no overlap) | +6 | +1,082 |
| R out − in | +59 | +16 | +1,227 |
| C out − in | −67 | +12 | +1,176 |
| A out − in | −49 | +6 | +141 |
| T out − in | +66 | +1 | +1,023 |

- **24 of 24 got through the load**, the start with all five parts out included; every start, controls too, reached
  ~0 MiB in the load and recovered. With the swapper off whole (M1A, 20 Nov) three starts crashed, so the swapper's
  base carries this load, not its five tuning parts.
- **P is the one main effect:** ~300 MiB more room on arrival, about 3 control sds, no overlap. It didn't change
  survival or frames on this route. Recorded, nothing adopted.
- **R × C is a pair:** the three starts with both out (S6, S7, S12) had 32-33 refused pool events; the other 21 had
  0-14. Each alone is covered by the other (with R out, reclaim ran 149 times in S11 against 2-4 on controls). R's and
  C's effects in the table come from those three starts. Next: R and C out together, 4 against 4.
- **Long worst frames** came only in S6 (6.9 s) and S12 (7.4 s), both with P, R and C out; S7 (P in) had 4.2 s. A lead
  from two starts; T's +1,023 rides on the same two.
- **A and T:** screened, no harm seen (T has no log line: set in 12 starts, no harm seen). Handheld, this route only.
- No part moves fps (±0.2) or load time beyond the controls' spread.
