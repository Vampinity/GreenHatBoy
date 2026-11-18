# kokiri-four-stops: the Kokiri benchmark route, scripted

`kokiri-four-stops.txt` is a test-harness script (`test_harness.h`, t120 and later) that loads the house
save and walks the four standing stops in `docs/GrowingBlackBeans/kokiri-stops.md` with no hands on the
pad. At each stop Link stands still for 62 s. Those windows are what we compare between builds and envs.

## Files

| File | What it is |
|---|---|
| `kokiri-four-stops.txt` | the script |
| `build.py` | makes the script from a recorded walk (KW2) and its capture video |
| `lint.py` | reads a script the way `test_harness.h` does, and stops on any line the harness would reject |
| `points.png` | the STEER points over the KW2 minimap, to check by eye |

## How it works

- **The walk:** 12 STEER lines, three per stop. The points come from Vampinity's
  `tools/Vampinity/steer/steer-route.py` on the KW2 capture.
  1. The leg to a point about 10 per mille before the stop, taken on the line KW2 walked.
  2. That point again with r=2.
  3. The stop itself with r=3.
- **The facing:**
  1. L2, then one stick tap that turns Link to KW2's facing, then L2 again.
  2. Then 15° taps, each followed by L2, under a `MAYBE` that looks for KW2's view (16x9 fingerprint,
     min 60). The taps left over are dropped once it matches.
- **The stand:** 62 s with no input. A fingerprint of KW2's view at each end (min 100, so it never
  matches) puts a `wait_skipped ... best=` line in the log at the start and the end of the stand. That
  marks the window, and `best` is a facing check.

## Running it

1. Copy the script to `/data/eglantineps5/` next to `env.txt`.
2. Add `EDEN_TEST_SCRIPT=kokiri-four-stops.txt` and `EDEN_TEST_DISCARD_SAVE=1` to the env.
3. Start from the house save. A start takes about 7 minutes.

## Results (t134-gbb9, GS1's counts, 14 Nov 2026)

All three starts met all 12 STEER lines with no timeouts. KS1 ran the first version, which had no search.

Facing (`best` at the start and end of each stand):

| stop | KS1 | KS2 | KS3 |
|---|---|---|---|
| A | 87 / 83 | 97 / 95 | 95 / 91 |
| B | 77 / 66 | 72 / 87 | 80 / 68 |
| C | 87 / 78 | 89 / 84 | 86 / 79 |
| D | 15 / 10 | 65 / 57 | 60 / 55 |

D's last approach point is inside r=3, so Link's heading on arrival is never set. The planned turn
then lands somewhere different each time. The search took 1 tap at D in KS2 and 4 in KS3, and A-C
matched on the first look.

Ring words a frame in the stand windows, against the hand-walked KW2:

| stop | KW2 | KS1 | KS2 | KS3 | spread of KS1-3 |
|---|---|---|---|---|---|
| A | 160,411 | -1.3% | +0.4% | -1.2% | 1.7% |
| B | 90,747 | +0.4% | +0.9% | +0.2% | 0.7% |
| C | 169,896 | +0.8% | +1.5% | +1.7% | 0.9% |
| D | 186,081 | -2.6% | -0.4% | -1.6% | 2.3% |

Two hand walks at the same stops (KW2 against GS1) differed by -0.9%, 0.0%, +8.5% and +9.9%.

Runs: `runs/GrowingBlackBeans/2026-11-14-KW2`, `-KS1`, `-KS2`, `-KS3`.

## v2 (17 Nov 2026)

`kokiri-four-stops.v2.txt` (sha1 `d40196a1a1d0`, built by the same `build.py`). Across KC1–KC5 on the control,
stop C started on KW2's view (fingerprint 81–89) but drifted during the stand (end 63–83): on the raised ground by
the cliff the camera pans by itself. Stop D only just passed its search (60–69). v2 re-centres C's camera with L2
every 10 s during the stand, and searches D's facing in 7.5° steps until the view scores 75. A and B are
byte-identical to v1. **Result (KV1, KV2, KV4, KV5; KV3 quit before END):** C's drift during the stand is reduced, but C's
starting facing still varies: C passes its search on the first look at any score of 60 or more, and the start score
predicts the work (85–91 → 169–172k ring words a frame, 78–82 → 176–180k, across all nine KC and KV starts). C spread
5.7%, D 5.6%. v2 floors: A 19.20, B 29.73, C 17.47, D 17.66 fps (sd 0.9–1.8%). A v3 would give C D's finer search with a
higher bar. Until then per-unit-of-work analysis pools A and B only.
