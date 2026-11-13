# The saved frame grids hold no brightness signal for our flicker (13 Nov, desk)

> **Corrected the same evening.** The title claim stands; the conclusion I drew from it does not. See
> section "Correction" at the end: `tools/Vampinity/flash-counter/` in the shared repo is a calibrated
> objective flash meter, already run on 418 runs, and it works on capture video rather than the
> emulator's grid. "Our flicker is probably not a brightness event" is retracted.

GrowingBlackBeans. No console. Tool: `eglog/flashdet.py` (new), over the grid files `EDEN_GBB_FLASH=2`
wrote on 12 Nov. Twelve runs, build 01.219.918, the full one-ahead/two-ahead x read-sync 2x2, with
by-eye verdicts from that session.

## The data

Each grid file is a 120x67 brightness picture of **every presented frame**: `GBBFL1\0\0`, then per
frame u32 width, u32 height, u64 present, u64 ns, then width*height bytes, each
(29B + 150G + 77R) / 256 over that cell. `runDXS2` is 5,582 consecutive presents over 184 s.

**Provenance**, which matters because my own dedup pass hard-linked identical files across run folders:
a run's grid file is the pid its **own log** names ("writing every grid to .../gbb-flash-<pid>.bin").
All twelve named distinct pids, each present in its own folder. Never glob `logs/` for these.

## What was tested

A flash as a test: **a one-frame excursion that reverts** — frame n differs from its neighbours and
frame n+1 returns to where n-1 was. Requiring the revert is what the live counter (0928) never did,
which is why 96% of its events were labelled one-frame while nothing checked that the picture came back.

- Whole-frame mean, 5th percentile, 95th percentile, and the count of cells under 16/255.
- Excursion thresholds 1 to 6 (mean), 4 to 32 (percentiles), 20 to 400 cells (dark count).
- Revert tolerances 0.5 to 3 (mean), 2 to 8 (percentiles), 10 to 50 (dark count).
- Directions: any, darker only, brighter only.
- Per cell: cells moving by 16/24/32/48/64 against n-1 and back within half that at n+1, with a
  minimum of 2 to 128 such cells.
- First 30 s dropped in every case.

## The result

**Nothing separates the arms. At any setting.**

Whole-frame statistics: no threshold on mean, p05, p95 or dark-cell count puts every flashing run above
every clean run.

Per cell (subset `runDX1`, `runDX3` against `runDXS1`, `runDXS3`), the only "separating" setting was a
gap of **1.1 per 1,000 frames out of about 240** — noise. At every meaningful threshold the **clean**
arms score *higher*:

| cell delta | min cells | flashing, per 1k | clean, per 1k | gap |
|---|---|---|---|---|
| 24 | 32 | 213.1-219.0 | 231.3-232.9 | **-19.8** |
| 48 | 4 | 213.8-221.5 | 233.4-236.8 | **-23.0** |
| 48 | 32 | 72.7-77.1 | 110.5-118.3 | **-45.6** |

The clean arms are also the slower arms, so they sample more motion per frame, which is the likely
reason they score higher. Either way: there is no brightness signal here to build a metric on.

## What that means, and the hypothesis it raises

Three readings, in order of how much they would change:

1. **The artefact is not a brightness event.** A 120x67 luminance grid would barely register geometry
   popping — an object drawn in the wrong place, or not drawn, for one frame. "Flashes at the forest
   hotspots" is as consistent with geometry flicker as with luminance flicker, and nobody has ever
   checked which.
2. The artefact is too small or too brief for this grid, even localised.
3. The by-eye labels do not correspond to a per-frame event at all.

**Reading 1 is the one to act on, because it reconnects evidence I had written off.** `runRC1`'s census
says the reads whose bytes change are **4-byte reads of float triples at a 256-byte stride** — that is
the shape of position or transform records, not of a brightness sum. Stale transforms for one frame
would put geometry briefly in the wrong place: a visible flicker with no luminance signature.

If that is right:
- Vampinity's brightness-from-capture method will not catch this symptom either. It was built for the
  too-bright second after a cut from black, which **is** a luminance event, and measures it well. Ours
  may simply be a different artefact.
- The copy-guard page hazard should not have been struck off. Fable was right to reject that step: the
  guard's counter measures **exposure, not harm**, and `EDEN_UP_AHEAD_GUARD_ALL_WRITES=1` — the one
  switch that removes the exposure — has never appeared in any env we have run.

## What to do instead

1. **Run `EDEN_UP_AHEAD_GUARD_ALL_WRITES=1` once.** One live-switched run, no build. If the flicker
   goes, the copy guard was the mechanism and the exposure was harm after all.
2. **Capture frames, not grids.** `EDEN_TEST_SHOTS` writes lossless pictures at script seconds. A
   geometry flicker is visible in a picture pair and invisible in a luminance mean.
3. **Stop trying to build a brightness detector for this symptom.** Six hours of threshold sweeping over
   real data says there is nothing to find.

0928 is retracted twice over now: its live counter saturates, and its saved grids contain no signal for
this artefact. It remains useful for the cut-from-black symptom, where the brightness curve is real.


---

## Correction, 13 Nov evening

`tools/Vampinity/flash-counter/count_flashes.py` exists in the shared repo, is documented, has its
thresholds in `rule.py`, is calibrated against the game's own light stretches (26 cells or under across
100 runs, against 60-190 for the glitch), and **has already run on 418 runs** — that is the
`flashes_per_min` column of `index.csv`. This document reinvented it, worse, on the wrong input.

Why mine could not work, against his:

| | mine | `count_flashes.py` |
|---|---|---|
| input | emulator's 120x67 grid | capture video, game picture found and cropped |
| compares | n against n-1 and n+1 | medians of 0.2 s windows 0.15 s apart, agreeing within 12% |
| masking | none | outer ring skipped, cells under 30/255 skipped |
| falling leaves | indistinguishable | excluded by design (leaves give under 40 cells) |

**Retracted: "our flicker is probably not a brightness event."** The defensible claim is narrower — the
artefact is not detectable in the emulator's own 120x67 grid at one-frame resolution. Vampinity's
description of the artefact is unmistakably a brightness event.

**What survives:** the copy-guard retraction (exposure is not harm; `ALL_WRITES` still never run), and
the provenance rule for the grid files.

**What is now the actual next step:** of the 418 runs with a flash rate, every one is **one frame ahead
with no read sync**. Zero are two-ahead; zero have read sync. The meter has never been pointed at the
arms the argument is about. The flicker question is blocked on **capture video of a two-ahead run**, not
on building anything.
