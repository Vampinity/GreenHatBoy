# Batch A: three memory parts of the control, one at a time (GrowingBlackBeans, 22-23 Nov 2026)

**Drain moved. Load hold and heap hold at load are quiet.**

Phase 4, memory first: our batch A of the split (D2). Alpha T186 (01.219.028) + play v4.0 with swap ahead 2048, base PS5,
13.60, handheld 1x, the warm field route (c4fada64155f), the shared warm store (prep_5093ab9e, 80,770), whole-cache
restore before every start. Each arm takes one part out of the control; 12 controls interleaved.

Rules frozen before start 1 (sha1 ffbf5cface7f), plus amendment 1 (sha1 a0a7f3176378, frozen before start 15): two
sittings, and the controls pooled only if the two sittings' controls agree. Both files are in
[`batch-a-rules/`](batch-a-rules/), byte for byte, so the hashes can be checked. **Moved:** a crash in an arm when no
control crashed, or a two-sided permutation p < 0.01 on any of six numbers, either direction. The six are refusals,
largest free block at the black, s under 16 MiB, worst frame after the black, load s and field walk fps; distinct
failed shapes is reported beside refusals and is not one of them. **Quiet:** nothing moved, and the part's own log line
is in every control and in no arm start.

**When amendment 1 was written.** After sitting 1 was packed: the first commit (84fc377) called the batch short. The
amendment's outline was pushed at 04:58 UTC on 23 Nov (cb48288), before sitting 2's counted starts; its frozen text,
its hash and the "agree" bar (no sitting difference under 0.01) were first pushed with this read. That matters for z:
0.0016 needs sitting 1's starts. Sitting 2's two drain-out starts (1054, 1000) sit below all seven of its controls,
but 2 against 7 can't reach 0.01 on its own.

| arm: what is out | call | |
|---|---|---|
| x, load hold (`EDEN_UP_LOAD_HOLD`, `_FREE_MIB`) | quiet: removed, no change seen (handheld, field) | lowest p 0.133 (worst after the black) |
| y, heap hold at load (`EDEN_UP_HEAP_HOLD_AT_LOAD`, `_REFILL_MIB`, `_SPARE_MIB`) | quiet: removed, no change seen (handheld, field) | lowest p 0.128 (s under 16 MiB) |
| z, drain (`EDEN_UP_PRESSURE_DRAIN`, `_PENDING_MIB`, `EDEN_UP_DRAIN_AT_AREA`) | **moved** | at the black p 0.0016; s under 16 MiB p 0.0022 |

z is three things, not one: drain at area and load hold's drain step both run only inside pressure drain
(vk_rasterizer.cpp:3357, 3482). The one split there can be is drain at area out alone.

| number | 12 controls | x, load hold out | y, heap hold out | z, drain out | p (z) |
|---|---|---|---|---|---|
| graphics refusals, to script_end (tries) | 0-27 | 3-5 | 6-20 | 4-50 | 0.0137 |
| distinct failed shapes | 0-9 | 0-2 | 1-4 | 0-12 | 0.0214 |
| largest free block at the black, MiB (driver's available figure, as in #37) | 1100-1354 | 1109-1311 | 1171-1339 | **956-1130** | **0.0016** |
| s under 16 MiB | 2-42 | 24-44 | 10-108 | **38-92** | **0.0022** |
| worst frame after the black, ms | 1,246-5,397 | 2,127-7,012 | 1,399-3,125 | 1,590-9,130 | 0.0489 |
| load s | 9.3-26.6 | 19.8-33.1 | 18.8-24.3 | 20.5-32.2 | 0.0379 |
| field walk fps | 18.74-19.48 | 18.72-19.13 | 18.88-19.42 | 18.82-19.12 | 0.3308 |

**The sitting check** (amendment 1): sitting 1's five eligible controls against sitting 2's seven, on the same six
numbers: p 0.146-0.896, none under 0.01. The pooled read stands.

**What this does and does not say**

- With drain out there is less room at the load: three of four drain-out starts have a smaller largest free block
  than any control (956, 1000, 1054 against 1100 and up; the fourth is 1130), and three of four spend longer under
  16 MiB than any control (50, 56, 92 against 42 at most). Refusals and failed shapes lean
  the same way but stay above the line, so they are not called.
- "At the black" is the driver's available figure (as in #37). On the allocator census's largest piece, z is still
  lowest on ranks (p 0.0044) but not on means (p 0.052) (Vampinity's recount, #43).
- The VMA dumps (`EDEN_UP_AREA_VMA_SNAPSHOT=1`, on in every start) fire when over 512 MiB of the allocator sits outside
  the census. Each drain-out start wrote three (two before the black, one after), but Y4 and C8's cold first try wrote
  one each, so they are not drain-out only. They read as a sign of drain out, not a cause.
- z's refusals lean up (p 0.0137, not called). On the alpha each graphics refusal triggers a flat 64 MiB pack on the
  asking thread, the source of waveydude's walk freezes on 9.40 and 13.60, so refusals are a lead for the split
  (waveydude, #43).
- "Quiet" is a screen on this route, handheld, from a fresh start, at 4 against 12. It is not "cleared" and says
  nothing about long play or docked.
- No start crashed, in any arm or control. Every start got through the load.
- Nothing is adopted or removed: phase 4 explains the control; it changes nothing until the programme ends.
- Next, under the rules: split z where it can be (drain at area out alone), and batch B. The order is still to be decided.

**Every start**

| # | start | arm | day | refusals | shapes | at the black MiB | s < 16 MiB | worst after the black ms | load s | field walk fps |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | C1 | control | 22 Nov | 3 | 1 | 1295 | 28 | 1629.3 | 23.9 | 19.08 |
| 2 | X1 | load hold out | 22 Nov | 5 | 1 | 1270 | 44 | 7012.3 | 33.1 | 19.1 |
| 3 | C2 | control | 22 Nov | 0 | 0 | 1100 | 2 | 1245.7 | 9.3 | 18.96 |
| 4 | Y1 | heap hold out | 22 Nov | 7 | 1 | 1339 | 10 | 2486.5 | 20.7 | 18.88 |
| 5 | C3 | control | 22 Nov | 4 | 1 | 1219 | 26 | 1311.4 | 21.4 | 19.04 |
| 6 | Z1 | drain out | 22 Nov | 4 | 0 | 1130 | 38 | 1590.1 | 20.5 | 19.12 |
| 7 | C4r | control | 23 Nov | 8 | 4 | 1282 | 22 | 1771 | 23.8 | 18.96 |
| 8 | Z2 | drain out | 22 Nov | 50 | 12 | 956 | 92 | 9129.7 | 32.2 | 18.86 |
| 9 | C5 | control | 22 Nov | 27 | 9 | 1150 | 36 | 4356.9 | 26.6 | 19.18 |
| 10 | Y2 | heap hold out | 22 Nov | 6 | 1 | 1274 | 108 | 1399.1 | 18.8 | 19.03 |
| 11 | C6r | control | 23 Nov | 0 | 0 | 1208 | 14 | 1347.3 | 18.8 | 19.07 |
| 12 | X2 | load hold out | 22 Nov | 5 | 1 | 1309 | 44 | 2778 | 20.6 | 19.13 |
| 13 | C7 | control | 22 Nov | 11 | 2 | 1354 | 32 | 2229.1 | 19.9 | 19.48 |
| 14 | X3 | load hold out | 22 Nov | 3 | 0 | 1109 | 24 | 2345.8 | 25.7 | 18.72 |
| 15 | C8 | control | 23 Nov | 8 | 3 | 1233 | 42 | 5397.4 | 24.2 | 18.79 |
| 16 | Y3 | heap hold out | 23 Nov | 20 | 4 | 1171 | 38 | 3125 | 24.3 | 18.93 |
| 17 | C9 | control | 23 Nov | 0 | 0 | 1134 | 10 | 1285.1 | 18.6 | 18.74 |
| 18 | Z3 | drain out | 23 Nov | 28 | 7 | 1054 | 56 | 5182.7 | 27.4 | 18.93 |
| 19 | C10 | control | 23 Nov | 9 | 3 | 1208 | 38 | 2011.8 | 19.9 | 19.03 |
| 20 | Z4 | drain out | 23 Nov | 18 | 10 | 1000 | 50 | 2094.1 | 26.4 | 18.82 |
| 21 | C11 | control | 23 Nov | 8 | 3 | 1178 | 16 | 2734 | 22.1 | 19.29 |
| 22 | Y4 | heap hold out | 23 Nov | 7 | 1 | 1225 | 34 | 1611.4 | 20.1 | 19.42 |
| 23 | C12 | control | 23 Nov | 0 | 0 | 1127 | 40 | 1262.5 | 18.3 | 18.92 |
| 24 | X4 | load hold out | 23 Nov | 3 | 2 | 1311 | 34 | 2127 | 19.8 | 18.97 |

C4r and C6r are the reruns that count (23 Nov). Runs: `runs/GrowingBlackBeans/2026-11-22-runM1A-*` and
`2026-11-23-runM1A-*`; each has a NOTE.md.

**Not counted, kept as data**

- C4, 22 Nov (`2026-11-22-runM1A-07-C4`) and its second try (`2026-11-23-runM1A-07-C4-try2`): logs copied before the
  app closed (`log_cut`). Warm, completed.
- C6, 22 Nov: never booted (the launcher waited: `test-boot-once` missing). No logs to pack.
- C8, first try (`2026-11-23-runM1A-15-C8-try1`): booted cold (the cache upload had not landed).

**Deviations** (none changes a call): Y3 ran before C8's good rerun; a launch before Z3 sat in the launcher and was
relaunched; C6's rerun came back with its logs in a subfolder, moved up flat before reading; C4's third try closed from
the app rather than the game's own quit (a clean close).
