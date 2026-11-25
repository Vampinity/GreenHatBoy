# Batch AS: drain at area out alone (GrowingBlackBeans, 24 Nov 2026)

**Drain at area moved: without it there is less room at the black (p 0.0020).**

Phase 4, memory first: the split of batch A's drain arm (#43). Batch A's z took out pressure drain, which also stops
drain at area and load hold's drain step (vk_rasterizer.cpp:3357, 3482). The one split there can be is drain at area
alone, so this batch's arm, w, removes one line, `EDEN_UP_DRAIN_AT_AREA=1`; pressure drain and load hold's drain step
stay on. Alpha T186 (01.219.028) + play v4.0 with swap ahead 2048, base PS5, 13.60, handheld 1x, the warm field route
(c4fada64155f), the shared warm store (prep_5093ab9e, 80,770), whole-cache restore before every start. 4 arm starts,
8 controls, interleaved, one sitting.

Rules frozen 23 Nov (sha1 133e19b181fb, batch A's rules resized) and pushed with the arms, order and a cut-short rule
before start 1, as #43 asked: [`batch-as-rules/`](batch-as-rules/). **Moved:** a crash in the arm when no control
crashed, or a two-sided permutation p < 0.01 on any of the six numbers. Read needs 7 or more eligible controls, and
fewer than 4 arm starts is a hold.

| number | 8 controls | w, drain at area out | p |
|---|---|---|---|
| graphics refusals, to script_end (tries) | 0-18 | 12-23 | 0.0242 |
| distinct failed shapes (beside refusals, not one of the six) | 0-5 | 2-8 | 0.0364 |
| largest free block at the black, MiB (driver's available figure, as in #37 and #43) | 1140-1360 | **983-1094** | **0.0020** |
| s under 16 MiB | 18-60 | 26-48 | 0.3111 |
| worst frame after the black, ms | 1,245-6,038 | 1,915-4,825 | 0.2000 |
| load s | 17.4-24.8 | 24.5-26.2 | 0.0182 |
| field walk fps | 18.88-19.40 | 18.82-19.37 | 0.5697 |

Proof lines: drain at area's on-line and its count line (`EDEN_UP_DRAIN_AT_AREA drain`, 31-41 a control) are in every
control and in no arm start; `EDEN_UP_PRESSURE_DRAIN mode 1:` is in every start, arm included.

**What this does and does not say**

- All four arm starts have a smaller largest free block at the black than any control (983-1094 against 1140 and up).
  That is about where batch A's whole drain arm sat (956-1130): the drain at an area change is the part of the drain
  that keeps the room at the load. Pressure drain alone doesn't make it up.
- On the allocator census's largest piece (the last census line before the black; our recount, as Vampinity's on
  #43): arm 1012-1094, controls 1140-2504. Lowest on ranks (p 0.0040), not on means (p 0.093): two controls (C5, C7)
  read over 2,300 MiB there. The same shape as batch A's recount.
- Unlike batch A's z, time under 16 MiB doesn't move (p 0.31): the controls run 18-60 s. So the longer time near
  empty in batch A comes from the rest of the drain, or needs more starts to show.
- Load (p 0.018) and refusals (p 0.024) lean the arm's way but stay above the line, so they aren't called. Every arm
  load is 24.5 s or longer; six of eight controls are 22.0 s or shorter.
- The VMA dumps (`EDEN_UP_AREA_VMA_SNAPSHOT=1`, on in every start): every arm start wrote them (two each, three in W4),
  and no control did. Still a sign of drain at area being out, not a cause.
- No start crashed. **One control hung:** C7's first try (pid 237, control env) got through the load at the black,
  then the app stopped (no frames from about 200 s, the next wait skipped at 3,328 s, closed by hand, no crash file).
  The rules rerun such a start at the end of the sitting; it was rerun at once, in start 10's place, and that rerun is
  the C7 counted here. The try isn't packed: the app kept no eden_log.txt for it, and the packer needs one. Its
  stderr, heap and boot trace are kept locally.
- A launcher sit before C6 (pid 234, `boot_skipped reason=not_armed`) left `.prev` files that are not a start; set
  aside, not packed.
- A screen on this route, handheld, from a fresh start, at 4 against 8. Nothing is adopted or removed: phase 4
  explains the control and changes nothing until the programme ends.
- Next, ours: batch B, rules pushed before its start 1.

**Every start** (all warm: 80,770 known, 3 own records, Total Pipeline Count 4; all closed normally)

| # | start | arm | refusals | shapes | at the black MiB | s < 16 MiB | worst after the black ms | load s | field walk fps |
|---|---|---|---|---|---|---|---|---|---|
| 1 | C1 | control | 3 | 1 | 1360 | 22 | 1346.7 | 18.9 | 19.03 |
| 2 | W1 | drain at area out | 13 | 6 | 1044 | 38 | 1914.5 | 24.5 | 19.06 |
| 3 | C2 | control | 1 | 0 | 1223 | 28 | 1582.3 | 17.4 | 18.97 |
| 4 | C3 | control | 0 | 0 | 1186 | 18 | 1248.3 | 20.1 | 19.15 |
| 5 | W2 | drain at area out | 12 | 2 | 983 | 26 | 3329.6 | 26.0 | 18.90 |
| 6 | C4 | control | 2 | 0 | 1202 | 18 | 1245.3 | 19.7 | 19.35 |
| 7 | C5 | control | 18 | 5 | 1218 | 26 | 2761.2 | 24.8 | 19.18 |
| 8 | W3 | drain at area out | 13 | 4 | 1094 | 38 | 4824.5 | 26.2 | 18.82 |
| 9 | C6 | control | 6 | 1 | 1140 | 36 | 6038.1 | 24.7 | 18.88 |
| 10 | C7 | control (rerun after a hang) | 10 | 3 | 1258 | 24 | 2550.9 | 21.5 | 18.94 |
| 11 | W4 | drain at area out | 23 | 8 | 1041 | 48 | 4510.7 | 25.4 | 19.37 |
| 12 | C8 | control | 6 | 3 | 1227 | 60 | 1493.8 | 22.0 | 19.40 |

Runs: `runs/GrowingBlackBeans/2026-11-24-runM1AS-01-C1` to `-12-C8`, each with a NOTE.md. Read with the batch kit
(`batch_kit.py read`, exact two-sided permutation on means, every 4-of-12 split), scorer stk_score 10.
