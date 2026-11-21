# The swapper off (M1A), its split, and patch 1211's cost (20 Nov 2026)

GrowingBlackBeans, base PS5, firmware 13.60, handheld 1x, the field route (`field-to-past-field`, sha1
c4fada64155f) from the restored warm cache (`warm-run-steps.md`). Runs: `runs/GrowingBlackBeans/2026-11-20-runM1A*`,
`2026-11-20-run1211-*`, `2026-11-20-runPlay5`. Nothing here is adopted.

## M1A: the guest swapper and its tuning lines off (alpha T186)

The first memory family of phase 4. M1A removes `EDEN_GUEST_SWAP` and its seven tuning lines from the control.

| start | through the load past the gate | crash | largest free block at the black |
|---|---|---|---|
| M1A2 | no | 41-59 s into the load, ~1 MiB free | 458 MiB |
| M1A3 | no | same | 452 MiB |
| M1A4 | no | same | 582 MiB |
| control (WF2-5) | 4 of 4 | none | 1,030-1,239 MiB |

M1A1 also crashed there, but isn't counted: its cache wasn't restored (179 own records, not 3; NOTE.md). Its block
at the black was 603 MiB.

**Corrected 21 Nov:** the block at the black was first read from the census line, which prints only when something triggers it, so its last value before the black can be ~100 s old (WF3's 2,368 and WF4's 2,239 came from the first area change). Every figure here is now the driver's last `RADV_PS5_MEMORY available_mib` before `wait_met line=92`. The controls arrived with 1.0-1.2 GB, not 1.2-2.4; the swapper-off starts with about half that. The call doesn't change.

**Read:** M1A is worse. The swapper is what gets the control through the field's exit load. By the arm's rule two
early ends were enough to call it; three clean ones did.

## M1A-S: splitting the swapper (set up, not run)

Per the conditions on #27 (split whatever moves; at least ten controls in the same batch, interleaved, from the same
restored cache), the swapper stays on and five of its parts are taken out on the 12-start table from
`docs/Vampinity/grouped-screening-method.md` (first five columns):

| unit | lines removed |
|---|---|
| P pressure pack | `EDEN_UP_PACK_PRESSURE_MS` (+ `_MIB`, `_COLD_S`, read only when MS is set) |
| R on refusal | `EDEN_UP_PACK_ON_REFUSAL` |
| C reclaim | `EDEN_GUEST_SWAP_RECLAIM` |
| A swap ahead | `EDEN_GUEST_SWAP_AHEAD_MIB` |
| T cold time | `EDEN_GUEST_SWAP_COLD_S` (no proof line; rides for harm only) |

Each unit is out in 6 starts and in for 6; 12 controls alternate with the splits (24 starts). The first control is
the smoke start and must show every unit's proof line. Rules, written before any start: a unit is load-bearing if its
6 out-starts crash in the load and its 6 in-starts don't, with the controls clean; a pattern no unit explains is a
pair, confirmed 4 against 4; harm in the splits that the controls don't show stops the batch; a quiet unit is
"screened, no harm seen", handheld, this route.

## Patch 1211's cost (a186-gbb2: the alpha's code + 1211)

`EDEN_UP_FLASH_COUNT=1` on against off on the same build, ABBA, 4 a side. The patch changes a hashed source file, so
the build has its own translation id and every start builds a new store from the restored driver cache (the scorer's
"half" class). Both sides boot the same way; compared with `abcompare.py`, since the gate has no floor for "half".

| | off (4) | on (4) | |
|---|---|---|---|
| walking fps | 14.41 ± 0.20 | 14.42 ± 0.14 | noise (p 1.0) |
| heavy fps | 14.65 ± 0.14 | 14.70 ± 0.12 | noise (p 0.66) |
| worst frame | 391 ± 58 ms | 452 ± 24 ms | p 0.057, inside the 82 ms allowance |
| through the load | 4 of 4 | 4 of 4 | |
| largest free block at the black | 987-1,204 MiB | 1,083-1,457 MiB | |

No speed or memory cost (the black figures corrected 21 Nov, as above; the on side is not lower). The worst frame leans higher with it on; most of the gap is one quiet off start (306 ms).
#29 was approved on this and merged.

## Wear-down in play (not a measured start)

runPlay5: hand play with L1 + park wait on, ~1 h 42 min. The largest free block fell 770 → ~300 (15 min) → ~60
(40 min) → 3 MiB (55 min), and the wall hit at the first town load (refused images, 2-10 s frames, no crash). The
driver's samples agree. Issue #28's Pro logs show the same shape: ~0 MiB at the field's exit load after 8.5 min of
play. A fresh 6-minute start is the best case; a long-session check is noted, not planned.
