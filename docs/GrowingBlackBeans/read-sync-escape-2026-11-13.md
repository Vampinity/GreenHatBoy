# Read sync's cost is a 2 ms give-up timer (13 Nov 2026)

> **Found:** Read sync (Vampinity's 0567) spends 84% of its wait time waiting on fences, and 93% of those
> waits end at a hardcoded 2 ms escape — a give-up that returns without the data having landed. That timer
> is about **77% of everything read sync spends waiting**. Read sync once per frame (0930) removed 28% of
> the syncs, exactly the coverage the census predicted, and bought **1 fps**.
>
> **So:** The design is right and the constant is what we cannot afford. Next build is the escape dial
> (0932, `EDEN_GBB_READ_SYNC_ESCAPE=<us>`, off by default).

GrowingBlackBeans. Base PS5 13.60, t134-gbb4 (01.219.920), Kokiri benchmark v2, profile Player 1,
Handheld 1x, Faster CPU on. Flicker ratings by eye, mine.

## The runs

| # | Folder | Arm | By eye | fps (standing / walking) |
|---|---|---|---|---|
| 1 | `runRC1` | two ahead + read sync + check mode + **census** | diagnostic, not rated | 19.05 |
| 2 | `runRX1` | two ahead + two slots + load wait (control) | flashes, worst at the forest hotspots | 26.65 (27.8 / 25.5) |
| 3 | `runRO1` | the same + **read sync once per frame** | **no flashes**, smoother than RC, not as smooth as RX | 19.30 (19.6 / 18.9) |
| 4 | `runRX2` | control | flashes, as RX1; fast and good to play | 26.65 (27.9 / 26.4) |
| 5 | `runRO2` | once per frame | — | 19.35 (19.8 / 19.0) |

Two runs a side, so "consistent" rather than "real" by our rule, but the gap is 7.3 fps against a cross-run
noise floor of about 1.2, and each side's two runs agree to 0.05 fps.

## What the census says (runRC1, 11 windows, 167,681 synced reads)

| | |
|---|---|
| Fence wait time | **133,609 ms (84.4%)** |
| Flush round trips | 24,614 ms (15.6%) |
| Fence waits | 62,168 (37.1% of reads), **2.15 ms each** |

0567's own counter in the same run: 64,897 fence waits, **60,480 escapes (93.2%)**. At `EscapeAfterNs` = 2 ms
that is 120,960 ms, **91% of the census's fence-wait time**. Two separately written counters agreeing.

The escape is deadlock avoidance: past 2 ms, with a GPU channel suspended on a semaphore acquire, the wait
ends because the frame may be waiting on a release this very thread will make later. It is not a timeout on
the fence (`timeouts` is 0 in every run) — it is a give-up, and it returns the same bytes the read would
have got with no wait at all, only 2 ms later.

### Write age of the range read

| age of the last GPU write | share of reads | of those, changed |
|---|---|---|
| <50 ms | 70.6% | 1.24% |
| <100 ms | 27.9% | 0% |
| <200 ms | 1.4% | 0% |
| older or never | 0.1% | 0% |

Nothing past 200 ms, and changed bytes only ever appear in the freshest bucket — 1,473 changed reads in
167,681. **This kills my narrow read sync (0929) at any window setting**, not just at 200 ms: its measured
skip share was 1.5%, and a 50 ms window would skip under 30%.

### Why once per frame could not win

The census: **28.7%** of synced reads are in the previous present's ranges. Once per frame covers exactly
those; the other 71.3% still sync one at a time. RO1's own counters bear it out — coverage 27-33% per
window, and 57.1 syncs per present against RC1's 79.1, a 28% cut. We removed 28% of the syncs and gained
1 fps, because the timer is charged per fence wait and the rest still pay it.

Flicker-wise once per frame covers the right set: repeat reads changed 2.19%, the rest 0.35%. It is a
correct part-fix, not a wrong one.

## Corrections

- **"The narrow read sync will be cheap" (12 Nov, Discussion #2 and the read-back-race doc).** Wrong. 0929
  skips 1.5% of candidate reads. Measured on the play save 12 Nov evening and again in the census.
- **"RO should land near RX" (13 Nov session plan, written before RC1).** Wrong, and the census said so
  before the runs did: 28.7% coverage cannot buy a 7 fps gap. Revised mid-session to "well short of RX",
  which is what happened.
- **The 12 Nov guess that read sync's cost was the flush round trip.** It is 15.6% of the wait.

## Next

**0932, the escape dial** (`EDEN_GBB_READ_SYNC_ESCAPE=<us>`, unset keeps 0567's 2 ms exactly). Written, not
yet built; patch and test plan in `gbb5/`. The risk is staleness and so flicker, not deadlock — escaping
sooner is the safer side of that wait. Three runs settle it: two of read sync + once per frame + a 250 us
escape, and one of the dial without once per frame, to find out whether 0930 is needed at all.

Credit: the read sync, its wait and the escape counter are Vampinity's 0567. The census, once per frame and
the dial are mine, on top of it.

## Left open

Every run of this session has 2-3 frames of 370-650 ms at 67-74 s, just before the door, with zero shader
time; DX2 and the 12 Nov T134 gate runs had the same. In 3 of 4 the window carries about 400 ASTC GPU
decodes against 19 in the preceding 18 s. `runAS1` is prepared to test it: an exact RX control plus
`EDEN_UP_ASTC_PENDING_STATS=1`, which is log-only and which Vampinity lists as untested.
