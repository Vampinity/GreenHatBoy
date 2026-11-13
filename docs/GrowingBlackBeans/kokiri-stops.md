# The benchmark stops

The fixed places used for per-place measurements on the Kokiri benchmark route. At every stop:
tap the targeting button so the camera swings behind Link, leave the stick alone, stand still for at
least 60 s. **Facing matters as much as position**: what is on screen is what is being measured.

| stop | where | facing | repeatable? |
|---|---|---|---|
| **A** | out of Link's house, hopped down to the ground | down the main path | **yes** — 0.4% across three runs |
| **B** | the back of the forest, where a Kokiri blocks the path | the Kokiri | **yes** — 1.2% across three runs |
| **C** | after the ivy wall, where the path before the cliff ends at a **large rock on the right**, looking out over the whole cliff | out over the cliff | new on 13 Nov (`runGS1`); not yet repeated |
| **D** | the shop sign at the end of the route | the sign | **no** — 12% drift, falling every run |

## History, so nobody repeats it

- **C at the cliff edge does not work.** Anywhere near the edge, pressing target pans the camera down,
  and the camera then holds the lower view. It happened in `runGP1` and `runGT1`. One step back is not
  enough. The large rock is far enough back to be stable.
- **D drifted 189k, 177k, 169k ring words a frame** over `runGP1`, `runGT1`, `runGS1`. The logs cannot
  say whether that is the facing, the exact position, or something moving in the scene.

## How a stop is checked

`anatomy.py stops RUNDIR` finds the standing stretches from the data. It **cannot** see a camera pan
that settles. The check that catches a bad stop is comparing ring words per frame for the same stop
across runs: over about 3% apart means it was not the same view.
