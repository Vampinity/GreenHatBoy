# run1211-01-on: the smoke start; passed, with one correction (20 Nov 2026)

- **Build:** 01.219.928 in the boot trace. A clean boot: 3 own records, Total Pipeline Count 4.
- **Store:** `prep_b7b2dd9e new (0 pipelines)`, not the warm `prep_5093ab9e`. The build's translation id is
  `0f221957…` (its build log says so), not the release's as the README first claimed. That README is corrected, and
  so are BUILDS.md and 1211-COST.md. Every start on this build is in the same state, so on against off still compares.
- **Route:** completed. It got through the load past the gate (black at 158.6 s, script_done at 458.6 s); no crash.
- **Speed:** field 14.8 fps, heavy-limited; as WF2-3 (14.9, 15.1). 71 shaders built in play (1.7 s).
- **The counter:** the init line, then **52 summaries**, 10,007 frames probed and 0 skipped (slot busy), and **2
  candidates** with 2 `EDEN_UP_FLASH frame=` lines. That meets waveydude's gate rule: the summaries show frames were
  probed, so the low count is a real low. They're candidates, not flashes; the picture isn't checked.
