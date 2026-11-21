# runM1-05-C3, control 3: NOT a control (cold start) (21 Nov 2026)

- The boot found no store: `store prep_5093ab9e new (0 pipelines)`, 0 known, 0 records read, Total Pipeline Count 0,
  driver cache wrote 0 pipelines at boot. The cache folders were deleted (step 0a) but warm-restore/ was not
  uploaded, or not into /data/eglantineps5/ (step 0b). Env identical to C1's; build 01.219.028.
- So it ran cold: the black came at app 246 s (warm starts: 140-160 s), 430 shader builds in play (C2: 364).
  It got through the load (0 MiB low, recovered) and closed normally.
- Kept as data, not counted in the batch: the gate has no warm key for it. Swap lines for the record: pressure
  passes 1,858 (8,055 MiB), on-refusal 75, reclaim 99 slots, swap ahead set. 833 MiB at the black (cold, not
  comparable).
- The console now holds the store this start built; the next start's step 0 deletes it, so nothing carries over if
  its upload works.
