# t134-gbb6: region-limited read sync (patch 0933)

GrowingBlackBeans, 13 Nov 2026. Built on t134-gbb5; **01.219.922**, in `EglantinePS5-package/t134-gbb6`.
Commit `c1e8929`. Unstripped symbols at `/work2/keep/t134-gbb6-llvm-pie.elf` in the build container.
Built the documented development way, with `EDEN_SKIP_SOURCE_CHECKS=1`, as gbb1-gbb5 were.

| Switch | What |
|---|---|
| `EDEN_GBB_READ_SYNC_REGIONS=<list>` | With `EDEN_UP_AHEAD_READ_SYNC=1`, only a read inside one of the listed regions is synced; every other one takes guest memory as it is. List is `base[+size]` comma-separated, base hex, size with K/M, default 1M, at most 16. Unset: one bool test, and the build behaves exactly as gbb5. |
| `EDEN_GBB_READ_SYNC_REGIONS_AUDIT=1` | Needs the list and `EDEN_UP_AHEAD_READ_SYNC_VERIFY=1`. Syncs **everything** anyway and counts how many reads with changed bytes fell outside the list. That count must be 0. As slow as a full read sync; a measurement mode, not a setting. |

## Why

`runRC1`'s census (0930): of 167,681 synced reads, **under 1%** came back with different bytes. Read
sync waits on all of them and costs 7-8 fps for it.

The 104 changed reads the verify logged are not spread out. They are five 1 MiB regions, 71 distinct
cache lines, all 4-byte reads of float triples at a 256-byte stride — transform or position records.

**And the regions are stable across sessions and builds**, which is what makes a fixed list worth
trying at all:

| 1 MiB region | `runDV1` (12 Nov, 01.219.918) | `runRC1` (13 Nov, 01.219.920) |
|---|---|---|
| `0x30400000` | 52 | 50 |
| `0x2b600000` | 24 | 34 |
| `0x2b700000` | 12 | 15 |
| `0x30500000` | 12 | 4 |
| `0x30700000` | 2 | 1 |
| `0x2b800000` | 2 | - |

The shipped list, `0x2b600000+4M,0x30400000+4M`, is 8 MiB and covers every changed read in both runs
with margin.

## The risk, stated plainly

The list is an address list taken from two sessions. If the game places these records elsewhere on
another route, another save or another firmware, reads that should sync will not, and the flicker
comes back **silently**. That is exactly what the audit mode is for, and it is why `runGA1` runs first.
This switch should not go in anyone's everyday env until an audit run on their own console reads
`changed OUTSIDE 0`.

## Tested so far

Parser only, on the host, against the shipped code extracted from the header (`test-regions.cpp`,
`regions_core.inc`): 17 cases — defaults, hex and K/M sizes, blank and unparseable entries, the
MaxRegions cap, and the boundary cases of the overlap test. All pass. **Nothing is tested on a console
yet.**

## Run plan

| # | Folder | Arm | What it answers |
|---|---|---|---|
| 1 | `runGA1` | list + audit + read sync + verify | **is the list complete?** `changed OUTSIDE` must be 0 |
| 2-4 | `runGR1-3` | list + read sync, two ahead | does it give RX speed with RO cleanliness? |

Controls in hand: `runRX1`/`runRX2` 26.65 / 26.65, flashes. `runRO1`/`runRO2` 19.30 / 19.35, clean.

Decision rules:
1. **`runGA1` reports `changed OUTSIDE` above 0:** stop. Widen the list from the addresses the verify
   lines name, rebuild, audit again. The GR runs mean nothing until this is 0.
2. **GR within ~2 fps of RX and clean by eye:** this is the fix. Two frames ahead at full speed with
   no flicker, and read sync becomes a narrow guard rather than a tax.
3. **GR fast but flashes:** the flicker is not only the read-back race on these records; the eye and
   the census disagree, and the next move is the blinded `runZ` set rather than more patching.
4. **GR as slow as RO:** the cost is not per-synced-read after all. That would contradict the census
   and would need the `EDEN_GBB_READ_SYNC_REGIONS` counters (`inside` vs `outside`) to explain it.

## Outcome (13 Nov)

**Decision rule 1 fired, then rule 4.**

`runGA1` (audit, 01.219.922): `inside 74,247 outside 91,603, changed inside 1,580, changed OUTSIDE 6`.
The list leaks — 99.6% coverage, not 100% — and the audit could not say *where*, because read sync's
own verify logging caps at 8 lines a window. gbb7 (01.219.923) fixes that; `runGA3` re-runs it.

`runGR1` (list only): **19.00 fps** against a pre-registered prediction of 23.4, and against
`runGA1`'s 18.77 and `runRO`'s 19.30/19.35. Syncs fell 78.9 -> 33.3 a frame and the waiting did not
move (30.3 -> 28.7 fence waits a frame). By eye: **no flashes**, worst frame 158 ms against RO's 276.

So the list is enough for correctness and buys no speed. Why, and what that rules out, is in
[findings-2026-11-13-read-sync-is-a-fence-wait.md](../findings-2026-11-13-read-sync-is-a-fence-wait.md).
0933 stays as the foundation for a CPU-side shadow of these regions, not as a filter.
