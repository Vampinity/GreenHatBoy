# The field and later-area warm floors (19 Nov 2026)

GrowingBlackBeans, on the alpha T186 (01.219.028) as released, base PS5, firmware 13.60, handheld 1x. Same store as
the baseline and Kokiri warm floors (`warm-store-floors-2026-11-18.md`): `prep_5093ab9e`, N = 80,770, built on our
own console. Every start restored the whole cache first (`warm-run-steps.md`) and booted at 80,770 reused, 80,770
known, 3 own records, Total Pipeline Count 4. Runs: `runs/GrowingBlackBeans/2026-11-19-runW*`. Floor files:
`tools/stk/floors-warm-{field,village}-2026-11-19.json`.

With these, all five scopes have a cold floor and a warm floor.

Not controls, packed as data with a NOTE.md each:
- **runWF1:** quit 25 s before END. The quit rule "4 minutes after the area past the field shows" was written for
  cold starts; a warm load is short, so it lands before END. Replaced by runWF5.
- **runWV1:** the game aborted during the quit and the close never finished (`end_kind: log_cut`). Replaced by runWV5.

p is the two-sided permutation test on the means, 4 starts a side; 0.029 is the smallest it can give, and it is
nominal (not corrected across the numbers). "Largest free block" is its lowest point in the start.

## The field (field-to-past-field; warm runWF2-5, cold runFC2-5)

| number | cold | warm | p |
|---|---|---|---|
| worst frame, ms | 31,149-33,030 | 3,844-4,138 | 0.029 |
| field walk fps | 12.93-14.10 | 18.82-19.09 | 0.029 |
| after the field fps | 13.85-14.00 | 14.1-14.6 | 0.029 |
| largest free block, MiB | 0-1 | 0-2 | 1.0 |
| radv OOM lines (in the load past the field) | 9, 10, 10, >=64 | >=64, 18, >=64, >=64 | not gateable (cap) |

## The later area (village lap v2; warm runWV2-5, cold runLV2, 3, 4, 6)

| number | cold | warm | p |
|---|---|---|---|
| worst frame, ms | 28,555-55,106 | 3,750-3,882 | 0.029 |
| village lap fps | 8.56-8.87 | 18.97-19.41 | 0.029 |
| field stand fps | 12.7-13.1 | 12.8-13.2 | 0.26 |
| largest free block, MiB | 3-18 | 97-221 | 0.029 |
| radv OOM lines | 0 on all | 0 on all | - |

Hitches and flashes are not measured on the alpha.

## What it says
- **Warm moves steady fps where the route walks through new scenery:** the field walk +5.5 (13.4 -> 18.9) and the
  village lap +10.5 (8.7 -> 19.2). Where the player stands (Kokiri's stops, the field stand, the baseline village)
  it doesn't. Likely: a cold start is still building shaders while it walks. Not shown yet: stk's
  `shader_builds_in_play` reads about 360 on every start of both routes, warm or cold, so it doesn't count what
  the store saves. That goes with the open question on PR #19 (what is still built in play).
- **The worst frame drops to about 4 s on both routes**, as on the baseline and Kokiri.
- **Memory:** in the later area the largest free block goes from about 12 to about 158 MiB. Past the field it
  stays at 0-2 MiB, warm or cold: the store doesn't help that wall.
- **Watch, not a verdict:** the out-of-memory lines in the load past the field reach the log's cap of 64 in 3 of 4
  warm starts against 1 of 4 cold. The cap means the gate can't read it.
- **A crash at quit:** 10 of 55 quits since 16 Nov end with the game's own abort during shutdown, cold and warm.
  In 3 the close didn't finish (WF1 was already void, WS2, WV1).
