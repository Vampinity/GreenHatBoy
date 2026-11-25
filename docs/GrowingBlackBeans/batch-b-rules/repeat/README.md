# Batch B, a repeat on your consoles (waveydude)

Same rules as ours, read against your own controls. Your 13.60 is the like-for-like repeat; your 9.40 would be its own
batch, with its own 12 controls.

- **Rules:** `docs/GrowingBlackBeans/batch-b-rules/BATCH-B-RULES.md` (sha1 9e13ca644841, frozen 24 Nov before our start 1).
  The arms, what counts, and the calls are all in there. Nothing in them changes for a repeat.
- **What it tests:** three memory lines of the control, each taken out on its own. x = `EDEN_GUEST_RESERVE_FLOOR`,
  y = `EDEN_UP_RESERVE_TABLES`, z = `EDEN_UP_DMA_SCRATCH_MIB`. There are 4 starts of each and 12 controls, interleaved.
- **Build and route:** the alpha T186 (01.219.028) as released, with no launcher update; handheld at 1x. The route is
  `tools/Vampinity/routes/field-to-past-field.txt` (sha1 c4fada64155f), copied to the console as `field-to-past-field.txt`.
- **Envs:** `env/NN-ARM.env.txt`, one per start, run in number order (`SHA1SUMS` beside them). Each env is the control
  env with one line taken out, or none for a control. The swap-ahead line is 2048 (the release's value for 13.x). We'd
  keep it at 2048 on 9.40 too, so that the firmware is the only difference, but that's your call.

## Yours, not ours
- **A warm cache of your own.** Restore the same copy before every start: delete `user/cache` and `cache` whole, then
  upload your copy. Your start 1's boot lines become the check for 2 to 24: the same store, the same pipeline count,
  the same own records and Total Pipeline Count. Our numbers (80,770 / 3 / 4) are our console's.
- **A field save** at the route's start: on the dirt path south-south-east of the bridge, with the player at minimap
  about 936,841. It must be the newest entry.

## Every start
1. Close the app fully, then restore the cache.
2. Rename `/data/eglantineps5/logs` to `logs.before-NN`.
3. Create an empty `/data/eglantineps5/test-boot-once`.
4. Copy that start's env over `PPSA98515/env.txt`.
5. Open the app and press nothing. The game should start by itself within a few seconds.
6. 6 to 8 minutes after the screen goes black at the gate, create an empty `test-quit`. If it crashes, leave it.
7. Wait for the home screen, then copy back, flat: `user/log/eden_log.txt` and everything in the new `logs/`,
   plus any `crash-*` files.

**If a start hangs** (no movement for more than 2 minutes), close the app and copy its files, `eden_log.txt` included,
into a `hang-try/` folder before launching anything else. Rerun it at the end of the sitting. Two sittings are fine:
pick up at the next number.

## Back to us
Pack each start with `tools/stk/pack_run.py` and push them, or send the folders and we'll pack them. We'll read your
batch with the same kit and the same six numbers, against your own controls, and post the read beside ours. If you'd
rather read it yourself, the rules are all you need.

| # | arm | # | arm | # | arm | # | arm |
|---|---|---|---|---|---|---|---|
| 01 | C1 | 07 | C4 | 13 | C7 | 19 | C10 |
| 02 | X1 | 08 | Z2 | 14 | X3 | 20 | Z4 |
| 03 | C2 | 09 | C5 | 15 | C8 | 21 | C11 |
| 04 | Y1 | 10 | Y2 | 16 | Y3 | 22 | Y4 |
| 05 | C3 | 11 | C6 | 17 | C9 | 23 | C12 |
| 06 | Z1 | 12 | X2 | 18 | Z3 | 24 | X4 |
