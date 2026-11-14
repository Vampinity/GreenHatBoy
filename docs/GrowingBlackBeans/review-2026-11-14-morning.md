# Review, regroup, rethink, replan — 14 Nov 2026, morning

**Goal:** steady 30 fps on a base PS5, Kokiri route first. **Constraints:** the two-ahead flicker is
parked; the anatomy plan agreed with the independent review is finished before anything new. Previous cycle: 13 Nov night (`review-2026-11-13-night.md`).

## 1. What happened (13 Nov, after the night review)

| run | build, what differs | result | status |
|---|---|---|---|
| `runGP1` | gbb9, `EDEN_GBB_GPFIFO=1`, four stops | ring/GPFIFO 0.74-0.86: the demand is the game's own. frame = 10.2 ms + 0.195 ms per 1k ring words, R^2 0.968 | adopted |
| `runGT1` | gbb9, `EDEN_GBB_BACK_CALLS=1` | heavy places cost more **per draw** (0.67 → 1.51 us), not more draws (+25%). The timer costs ~25% of back time | adopted (ratios; not the us) |
| `runGS1` | gbb9, GPFIFO + `EDEN_UP_SUBMIT_STATS` | ratio repeats; stats cost ~2%; fence waits are on the fencing thread, off the back's path | adopted |
| `runKW1` | gbb9, recorder + discard-save | inputs recorded, four stops visible (51/63/62/62 s); **no video** (a screenshot) and **no eden_log copied** | incomplete |

Per regime (`eglog.py summary`; GT1 carries a timer, don't compare its fps):

| run | walking fps | light (CPU-paced) | queued | heavy | back ms in heavy windows |
|---|---|---|---|---|---|
| `runRX1/RX2` (.920, same arm, no stops) | 25.5 / 26.4 | 27.1 / 26.5 | 26.6 / 26.9 | 24.9 / 24.8 | 33.0 / 32.8 |
| `runGP1` | 27.0 | 31.8 | 24.1 | 18.1 | 44.9 |
| `runGS1` | 26.2 | 30.2 | 23.5 | 21.3 | 36.9 |

GP1/GS1 aren't comparable with RX1/RX2 overall: the stops change the regime mix (20+ light windows at
B against 6-7). That's the point of stops, not a gain.

**Also done:** anatomy close-out against its four rules; scripted-route plan; STK roadmap and `LOGS.md`
brought up to date with measured instrument costs; steer tools (synthetic tests only); 19 runs packed
and pushed (`3e7e0dd`); 20 GB freed losslessly (identical copies hard-linked). Posts: D5 close-out + GS1,
and the ask to Vampinity.

## 2. Overnight on GHB

- **Vampinity shared both Kokiri STEER scripts** (`village-tunnel-mouth.txt`, `village-exit.txt`) and
  **his steer tool** (`tools/Vampinity/steer/`), checked on real recordings: 13 points matching a working
  script, marker read in 90% of frames; his host test passes. Advice: check points by eye.
- **The Lichii draw and wait ports are in his next test build**, and he named our B and D stops as the
  test for them. This is item 1 on our ranked list.
- His draws per frame are late: his console dropped off the network with `EDEN_UP_GPU_PASS_TIME` on.
- `EDEN_TEST_DISCARD_SAVE` is patch 0547 (T119+); his README is fixed.
- waveydude: a 2.3-hour session on T183 with no crash; W-23 had eight hits; W-24 follows. Memory at
  loads is their thread, not ours.

## 3. Where things stand

| # | problem | cost against the goal | certainty | evidence | fix size |
|---|---|---|---|---|---|
| 1 | back-thread cost per draw (draw-time commit) | 2.8-15 ms a frame at the heavy stops | **measured** (ratios, one timer run + 3 counts runs) | GP1/GT1/GS1, V1, RD1 | 17-37% cheaper per word = 30 fps at A, C, D |
| 2 | the later area runs 17-21 ms slower than the Kokiri fit predicts | the worst place in the game so far | inferred (his numbers on our fit) | his ~181k words at 15-16 fps | unknown until measured there |
| 3 | the game's CPU chain (27% unexplained where the back doesn't pace) | small: those frames are mostly at 30 fps already | measured residual, cause inferred | 45 clean runs | unknown |
| — | the flicker (parked) | — | suspected: "flashes where the back can't keep up" | B clean, A/D flash (GP1) | would share lever 1 |

**Ruled out:** the front inflating the demand (ratio 0.73-0.86, GP1 and GS1); fence waits on the back
(they're on `GPUFencingThread`); region-limited read sync (GA1/GR1/GA3 at 18-19 fps).

## 4. Corrections

- **Our steer tool duplicates Vampinity's.** I wrote it because his "isn't public"; shortly after we
  pushed ours, he shared his, and his is checked on real video. For finding points, **use his**. Ours
  adds only the stop assembly (approach point, ZL, fingerprints, a plain hold). The scripted-route plan's
  "missing" list is now empty. Both docs on GHB need that line.
- **`EDEN_GBB_LOG_SESSION` is still untested.** KW1 switched it on, but none of the three writers it
  moves was on, so there was nothing to put in a folder. A real test needs `EDEN_GBB_FLIGHT` or the
  timeline on too.
- Nothing public needs retracting.

## 5. Rethink

1. **Most certain, meaningful next result:** Vampinity's Lichii ports measured at our fixed stops. The
   anatomy gives the metric: the ports should lower **the slope** (ms per 1k ring words) and close the
   per-draw gap between B and D. A and B already repeat within 0.4% and 1.2% by hand, so a hand-played
   A/B at those two stops is enough for a first call. The script makes D usable and runs 4-a-side cheap.
2. **The assumption that changes the plan most:** that the per-draw cost lives in the draw-time commit
   path the ports touch. The ports test it directly; if they don't move the slope, the target is
   elsewhere in the back's dispatch and we need the per-method timer at the stops again.
3. **Measuring the right thing:** counts-only runs at stops, compared by slope. No timer, so fps is real.
   If his port switches are live switches, an in-run on/off at one stop is the most precise A/B we have
   (A/A noise ±0.5 fps). Worth asking.
4. **Independent review:** the plan is a continuation of the agreed one, so it doesn't need a new
   approval gate. Offer it if you want one.
5. **Don't duplicate:** his steer tool and scripts; waveydude's guard probes and memory work.

## 6. What's left of the plan we agreed with Fable

**At the desk (no console):**
1. Point our steer README and the route plan at Vampinity's tool, and keep ours as the stop assembler
   only. 
2. Reply on D5: thanks, the KW plan now uses his tool, and ask whether the Lichii port switches are live
   switches. 
3. After KW2: run his `steer-route.py` on the video, check the points by eye, assemble the script with
   our stops, and join it to his house-door opening.
4. KW1's `eden_log.txt` was lost (the next session overwrote it); its input recording is kept.

**At the console:**
1. **KW2**, the recorded walk with video (about 8 minutes). 
2. **The scripted test**, three starts, once the script exists. Pass mark: all four stops met, ring words
   within ~3%, matching fingerprints.
3. **New and the most valuable:** Vampinity's Lichii ports at stops A, B and D, on and off, counts only,
   when his test build is out. Decision rule: if the slope falls and B-to-D per-draw cost narrows on
   at least 3 runs a side (or one live-switch run), the draw-time path is confirmed as M2's target.

**Waiting on others:** Vampinity's test build with the ports, his draws per frame, his flicker captures.

**Parked with the flicker:** runGW1, capture video for the flash meter, landing trace, live read-sync
switch, read-sync cost buckets, waveydude's W-23/W-24 capture at B and D (he's now folding the probe
into Vampinity's builds).
