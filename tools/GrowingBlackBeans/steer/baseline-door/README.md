# baseline-door: the house door on the baseline route

The baseline route (`zelda-first-start-watch-wait-30s.v6.txt`) missed the house door 3 times in 12 starts on the
control at swap-ahead 2048 (9 of them cold by the scorer; the three misses, CC4, BD1, BD2, were all cold). BD2's capture shows why: v6 swings the camera right then left for 1.5 s
each, then presses ZL and pushes forward. A timed swing turns by a frame-rate-dependent amount. When the push came
while the camera was still turning, Link ran in at an angle and stopped just left of the door, outside the spot
where "Open" shows. There is no minimap inside the house, so it can't be steered by minimap.

| File | What it is |
|---|---|
| `build_v9.py` | v6 → **v9**: the swing removed. ZL 5 s after "Saving...", 1.5 s to settle, then v6's push and A Open check. |
| `zelda-first-start-watch-wait-30s.v9.txt` | sha1 `d6e6b8d4cf42`. **5 of 5 doors** (BW1–BW5), A Open 8.0–8.6 s after "Saving...". |
| `build_v8.py`, `...v8.txt` | the first try, kept for the record: ZL then a picture check against a door view cut from a PS5 capture. **Failed** (BX1: best 55 against 85). A dark interior read from a capture doesn't correlate with the app's own frame. A picture check here needs a reference cut from the app's own screenshot. |

Everything outside lines 110–114 is v6 byte for byte. The scorer's windows for v9 are in `tools/stk/windows.json`
(`new-game-v9`; v6's line 117 is v9's 118).
