# Control starts on T185 and T186, 14 and 15 Nov 2026 (runs 1559 to 1638)

The eleven scripted starts behind the speed chart in "How fast it runs" on the front page, packed so that anyone can
score them or compare against them. Logs as they came off the console, packed with `tools/pack-run.py`. The only
changes are the redactions listed under "redacted" in each run.json: the console user number, the profile id in the
save path and in config.json, the save's name in the field script's comment, and the other titles (names and ids) in
config.json. The timestamps and numbers are unchanged.

## The runs

| run | build | route | batch (start) | on the front page |
|---|---|---|---|---|
| 1590 | T186 | field | gate-cb-t186 (15 Nov 02:30) | field walk 18.96, area after the field 14.00 |
| 1591 | T186 | field | gate-cb-t186 (15 Nov 02:30) | field walk 18.76, area 13.40 |
| 1604 | T186 | field | dp-nohog-t186b (15 Nov 04:49) | field walk 19.12, area 14.00 |
| 1607 | T186 | field | dp-nohog-t186b (15 Nov 04:49) | field walk 19.16, area 14.10 |
| 1613 | T186 | field | w20-cb-t186b (15 Nov 06:08) | field walk 19.39, area 13.30 |
| 1615 | T186 | field | w20-cb-t186b (15 Nov 06:08) | field walk 19.59, area 13.80 |
| 1616 | T186 | field | pre188-cb-t186 (15 Nov 10:23) | field walk 19.39, area 13.60 |
| 1559 | T185 | new game | calibb-first-t185 (14 Nov 16:03) | village 21.63 |
| 1588 | T185 | new game | calibb-first2-t185 (15 Nov 00:56) | village 22.32 |
| 1637 | T186 | new game, first start of the alpha | alpha-fs-01-t186 (15 Nov 17:17) | village 22.57 |
| 1638 | T186 | new game, first start of the alpha | alpha-fs-02-t186 (15 Nov 17:30) | village 22.43 |

All numbers in fps. Base PS5, firmware 12.40, handheld, 1x, frame ahead off in all eleven.

- **Builds.** T186 is the alpha build: eboot sha16 97bdd9ecea13cfe2 (01.219.028, Nov 14 2026 23:24:15). T185 is the
  build before it: eboot sha16 44d85b399e25c38c (01.219.028, Nov 14 2026 06:51:12). See `docs/Vampinity/BUILDS.md`.
- **Settings.** The nine CB starts (1559, 1588 and the seven field starts) have the same env.txt except for the
  `EDEN_TEST_SCRIPT` line: play settings v4.0 plus `EDEN_TEST_DISCARD_SAVE=1` (writes go to a copy, never to the
  save) and `EDEN_UP_FAULT_LOG=1`. The shader store of earlier starts was in place (the log says
  `store prep_5093ab9e reused`, with 78723 pipelines, 78735 in 1616). 1637 and 1638 are first starts of the alpha
  the way a newcomer gets it: the zip's env.txt (play settings v4.0) plus `EDEN_TEST_DISCARD_SAVE=1`, with the
  shader folder, driver cache and jit list set aside by the test runner. Their logs show the shader store starting
  empty: `store prep_5093ab9e new (0 pipelines)`.
- **Field route** (`script.txt`, route-field-to-past-field.works-run1397.txt, the same script as the W-20 runs 1469
  to 1472): a save in the field, walked by minimap steering to the gate, then the load into the next area, then
  about 300 s in the area after the field. The packed script.txt is byte-identical to the W-20 runs' copies (sha1
  fe9a3ed5049b, which is also the `script_sha` in these runs' run.json).
- **New-game route** (`script.txt`, zelda-first-start-watch-wait-30s.v6.txt, sha1 e68ac8b551b2, as run and as
  packed): title, New Game, the opening played out, control in the house, out of the door, then about a minute in
  the village with no input.

## Files per run

`eden_log.txt.gz` (app clock, with the 5 s fps lines `nx2:vi2 5 s:`), `stderr.log.gz` (the EDEN_TEST script marks
and the memory lines), `heap.log.gz`, `env.txt`, `script.txt`, `config.json`, `report.txt`, `result.json`,
`boot-trace.txt`, `run.json`. Not packed: the recordings, the frame grabs and the bench's picture checks made from
them. This repo keeps text logs and settings.

## Two clocks

- The EDEN_TEST lines in stderr.log (`at=`) are on the script clock. It starts at the `EDEN_GUEST_START` line in
  eden_log.txt.
- eden_log.txt's `[ seconds]` are on the app clock, and so are the 5 s fps lines. A 5 s line is stamped at the end of
  its 5 seconds.
- App time = script time + the GUEST_START time below. All times in this note are on the app clock.

| run | GUEST_START | line 46 met (last look before the walk) | line 92 met (minimap gone, the load starts) | lowest 5 s line in the load | script end |
|---|---|---|---|---|---|
| 1590 | 40.2 | 118.7 | 195.7 | 225 | 495.7 |
| 1591 | 37.5 | 114.8 | 208.8 | 230 | 508.8 |
| 1604 | 37.5 | 114.8 | 191.7 | 214 | 491.7 |
| 1607 | 37.3 | 116.0 | 207.0 | 231 | 507.0 |
| 1613 | 37.4 | 115.2 | 183.1 | 205 | 483.1 |
| 1615 | 37.4 | 114.7 | 194.2 | 225 | 494.2 |
| 1616 | 51.0 | 129.4 | 203.9 | 233 | 503.9 |

| run | GUEST_START | line 108 met (control in the house) | line 117 met (the house door) | script end |
|---|---|---|---|---|
| 1559 | 37.6 | 471.0 | 482.1 | 542.1 |
| 1588 | 38.0 | 470.9 | 482.0 | 542.0 |
| 1637 | 10.6 | 521.5 | 532.6 | 592.6 |
| 1638 | 10.2 | 512.0 | 523.3 | 583.3 |

## How the front-page numbers were taken

From the 5 s fps lines in eden_log.txt, one number per start. The chart shows the slowest and the fastest start.

- **Field walk:** the mean of the 5 s lines whose whole 5 seconds lie between the start of the steering (line 46
  met + 8 s) and line 92 met.
- **Area after the field:** the median of the 5 s lines from 70 s after the lowest line in the load to the end of
  the log. The lowest line is taken within 45 s after the last line of 55 fps or more that follows the field walk.
- **Village:** the mean of the 5 s lines at app 530-555 s (1559) and 531-556 s (1588), and of the last three 5 s
  lines in 1637 (593-603 s) and 1638 (584-594 s). That is 48 to 74 s after the door. "Standing" rests on the
  script, which presses nothing after the door. A short scene plays on arrival; that the player was in control in
  these windows was not checked against the picture.

## Before you use them

- `fps.mean` in run.json is the whole run (menus, loads and the fast stretch inside the load), not one of the
  front-page numbers.
- `control` in run.json is true only where the batch also ran a second arm (1604, 1607, 1613, 1615). The other
  seven ran the same control settings.
- 1590, 1615 and 1616 have `valid: false`. The bench's check flagged one stall in play in each (10, 32 and 20 s),
  and in all three it starts inside the load (at about 215, 213 and 222 s, after line 92). All three ran to the end,
  and all three are in the front-page numbers.
- The village bar mixes builds: 2 starts on T185 and 2 on T186. The two T186 starts alone give 22.43 to 22.57.
- Two to seven starts per place: a count, not a verdict.
