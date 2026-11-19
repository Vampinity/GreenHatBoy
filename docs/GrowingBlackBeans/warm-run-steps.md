# A warm control start (GrowingBlackBeans, 18-19 Nov 2026)

How our warm controls were run: runWB1-4, runWK1-4 (PR #19) and runWF2-5, runWV2-5 (19 Nov). The same as a cold
control start (`RUN-CONTRACT.md`: env from the run folder, logs aside, test-boot-once, press nothing, test-quit, copy
back flat), with one difference: **instead of setting the caches aside, put back the whole cache as it was right
after the store was built** (the whole cache: the store, and the app's and the driver's pipeline files, among them
`vulkan_pipelines.bin`).

Each of us builds the store on our own console (shader set prepass on the alpha, from the recipe). No store or cache
is shared between people; what is shared is how it is built and the number a warm start must log.

## Once: copy the cache after the store build

Right after the build (our runWS2), with the app closed, copy both cache folders off the console whole:
`/data/eglantineps5/user/cache` and `/data/eglantineps5/cache` (ours: 27 files, about 2.1 GB), with a SHA-256 list.
Check the copy against the list before each use.

## Before every warm start (app fully closed)

0. **Restore the whole cache.** Delete `/data/eglantineps5/user/cache` and `/data/eglantineps5/cache`, whole, and
   upload both folders from the copy. Nothing is picked file by file.
1. Rename `/data/eglantineps5/logs` to `logs.before-<run>`. The app makes a new one. If it isn't renamed, the
   previous start's files stay beside the new ones (`*.prev.*`, an old `mkw-vma-<pid>-*.json`).
2. Create an empty `/data/eglantineps5/test-boot-once`.
3. The route's save as the newest entry, its script in `/data/eglantineps5/`, the run's env over `PPSA98515/env.txt`.

## The start, and after

4. Open the app, press nothing.
5. Quit with `test-quit` only after the script's END. Late is free: the scorer cuts every number at script_done +
   10 s (the after-the-load window too, since 19 Nov; before that it ran to the log's end). Early voids the start. **Count from a fixed event in the route, not from a load finishing:** a warm load
   is short, so a cold-start rule like "4 minutes after the area past the field shows" lands before END
   (our runWF1). For the field route: 6 minutes or more after the screen goes black at the gate.
6. Copy back, flat: `user/log/eden_log.txt` and everything in the new `logs/`.

## What makes it count

The boot lines must read:
- `store prep_<id> reused (N pipelines)`, with the same N in every warm start (ours: 80,770);
- `N pipelines known, 0 left to prepare`;
- `3 records read (3 own` (what our copy held; yours may differ, but it must be the same every start);
- `Total Pipeline Count: 4`.

Then `control_eligible: true` from stk, as for a cold start. Anything else, and that start isn't a control.

## Why the whole cache (18-19 Nov)

- Play grows the app's own pipeline files. After runWB1, runWB2 read 820 own records and built 6 shaders in play
  (`runWB2-played`). N didn't show it: N counts only the store.
- After a restore of those growing files only, the store itself read 80,798 (`runWB2-n80798`), with no log line.
- Check on 19 Nov: after runWV1, all eight store files, both large `.bin` files included, were byte-identical to the
  copy. **That doesn't settle it** (Vampinity, PR #20): WV1's close never finished, so the app never wrote its cache
  at shutdown. Whether a normal start changes the store is still open; the check is to be repeated after a start
  that closes cleanly. The whole restore stays either way: it is what makes every start alike.

## A crash at quit (seen 19 Nov)

About 1 quit in 6 (10 of 55 logged quits since 16 Nov, cold and warm, four routes) ends with the game's own abort
during the shutdown (`Userspace PANIC`, backtrace through `nn::diag::detail::Abort`). Usually the close still
finishes and the start counts. In 3 of the 10 it didn't (`end_kind: log_cut`), and that start was replaced.
