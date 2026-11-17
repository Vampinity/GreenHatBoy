# How we measure

One control, controlled routes, one scorer, one gate. This file exists because all four were agreed in
chat and nowhere here, so anyone reading this repo — including a new assistant — would conclude they
were never agreed at all.

`AGENTS.md` says what to do before and after a job. `docs/WORKFLOW.md` says how a run, a build and a
session are shaped. This file is the shorter, harder thing: what makes two people's numbers
comparable.

**Status.** The control, the routes and the scorer: agreed by all three of us, 15 Nov 2026. The gate:
agreed by all three of us for changes to the shared base — `main`, the alpha, the control (§4). Each
person's own test builds follow their own rules. Pieces of all four already exist and are named below.

## 1. One control

**T186 with play settings v4.0** — the alpha, `envs/Vampinity/play-v40.env.txt`, `source/T186`. Frozen,
and nobody edits it in place.

**A test changes exactly one line from it.** Two lines is two tests. If a switch only acts with another
switch, say so in the run notes and treat the pair as the unit.

What is frozen is the **base**, not anyone's own work: builds and tests continue, with everything new
off by default.

Known wrinkle, so nobody trips on it: v4.0 is frame-ahead-off — it drops `EDEN_NX2_FRAMES_AHEAD`,
`EDEN_UP_AHEAD_GUARD` and `EDEN_GBB_GUARD_EARLY`. Builds before T134 have no `EDEN_GBB_GUARD_EARLY` at
all, so two envs that look identical are not. This is the kind of thing the control is meant to end.

**It has a baseline now:** eleven packed starts on T185/T186, with the exact scoring windows written
out, in `runs/Vampinity/2026-11-15-t186-control-README.md`.

## 2. Controlled routes

Not one route — **four scopes, each controlled**. They are not interchangeable: each answers a
different question, has its own script and its own metric, and is in a different state. What is shared
is the control on them. A route is scripted, it runs on the control build and env, and it repeats.

**A route is a control only if it repeats.** Scripted starts hold their stop-to-stop spread to
0.7–2.3%; the same stops played by hand drift up to 9.9%. That spread is itself the check, and
`stopdrift.py` is what measures it.

| scope | what it answers | the metric | where it stands |
|---|---|---|---|
| **Kokiri**, four stops | where a frame's time goes, and whether a difference is real at all | scripted starts on the control, and the stop-to-stop spread | deep; the only place with enough repeat starts to call a difference |
| **The field** | whether a start survives the load — this is where the memory wall shows up | starts reaching the load, n of N | 44 scripted starts, 4 of them packed; one long play |
| **After the field** | the slowest measured place in the game | median fps, and list-wait ms a frame | dozens of starts at ~14 fps; no list-wait data in any run yet |
| **Later areas** | whether what we found earlier holds anywhere else | scripted starts per area, on the control | four areas run, never on one control |

**Breadth is itself a measurement.** Four areas run on four different builds tells us nothing we can
compare, which is why the scopes are named here rather than left to whoever happens to be playing.

The scripts: the field and the area after it are
`tools/Vampinity/routes/field-to-past-field.txt`, which we have adopted; Kokiri is
`tools/GrowingBlackBeans/steer/kokiri-four-stops/`. Saves stay each person's own; the scripts are the
shared part. Each route carries timestamps at the points we care about, so a flash, a hitch or a crash
can be placed rather than only counted.

**Four starts a side for a verdict, three for a screen** — "four where there's room", because console
time is real.

## 3. One scorer

**It exists:** [`tools/stk/`](../tools/stk/) — waveydude's scorer and route check, with the run-contract
changes ([`docs/RUN-CONTRACT.md`](RUN-CONTRACT.md)). It reads any run folder, raw or packed, and scores all
1,332 packed runs.

One command that reads a whole **run folder** — not just `eden_log`, because the memory lines are in
`stderr.log` and the crash class is in the crash file — and prints the same row every time:

| column | from |
|---|---|
| median fps, p10 fps, worst frame ms | the 5 s `nx2:vi2` windows, play windows only |
| shader builds in play | `pipeline built on the GPU thread` |
| largest free block at the peak | see the note below |
| hitch ms a minute | the flight recorder, plus `frame_max` |
| flashes a minute | `tools/Vampinity/flash-counter/count_flashes.py`, from capture video |
| game speed | patches 0950/0951 |
| survival, n of N | did the start get through the load |
| crash class | the crash report, plus `EDEN_HEAP_FAILURE` counts |

Plus the conditions, so two rows can be told apart: build hash, firmware, env hash, cache state,
session age, handheld or docked, in-game time.

**waveydude has built this** — `stk_score.py` and `stk_index.py`, with `NULL` for a missing number and
never 0, and a `*_source` column saying which instrument each number came from. That is the
implementation; this table is the contract it implements.

### The one column with a trap in it

**`available_mib` is the largest free block, not the total free.** `headless/performance.cpp` says so
in its own comment. Two different lines carry it, and they are not interchangeable:

| line | in how many of the 1,324 packed runs | sampled |
|---|---|---|
| `EDEN_MEM_CENSUS ... largest=` (read by `tools/Vampinity/anatomy/memmap.py`) | 91 | every ~2 s **and on every low** |
| `RADV_PS5_MEMORY ... available_mib=` (read by `tools/GrowingBlackBeans/eglog/memfree.py`) | 1,160 | about every 10 s |

Checked against each other on the 90 runs that carry both: **at the same moment they agree** — median
difference 0 MiB over 2,888 paired readings. **Over a whole run their minima do not**, by up to
300 MiB, because the census samples about five times more often and catches dips the driver line
misses. So the driver line's minimum is biased high.

**The rule: a row records which line its number came from, and the two are never mixed inside one
comparison.**

They are also on different clocks. `EDEN_MEM_CENSUS t_s=` is the script clock (the one
`EDEN_TEST ... at=` uses); `RADV_PS5_MEMORY t_s=` is the app clock (the one `eden_log.txt`'s
`[ seconds]` uses). The offset is the `EDEN_GUEST_START` stamp in `eden_log.txt` — about forty seconds
in a field start.

## 4. The gate — for changes to the shared base

**A change goes into the base if the row can be explained.**

Not "nothing may get worse": frame ahead off costs 1.5–3 fps and removes the flashes, and under an
absolute rule the alpha itself would not have shipped. A trade across columns is fine. An unexplained
loss is not.

"Worse" needs a **noise floor per number, measured from the control arm, not guessed**. A 3% threshold
at one of our Kokiri stops would have manufactured results, because that stop's own control spread is
5.6%. Our widest same-setup spread so far is 3.6 fps.

Vampinity already runs a gate of this kind on every T-build — new switches unset, against the build
before. What is missing is that it is his rather than shared.

It is the rule that decides what gets rejected from the base. It does not reach anyone's own test
builds.

**16 Nov:** waveydude — yes, with the condition that a row counts against the control only on the same
shader store. The run contract makes that a comparison key (route, firmware, translation id, store, cold
or warm; [`docs/RUN-CONTRACT.md`](RUN-CONTRACT.md) §5). The first noise floors, from five cold control
starts on 13.60 on the new-game route: village ±0.67 fps (door + 62…77 s), lowest largest free block
±99 MiB.

**Vampinity:** fine in principle, for the shared base only — not for his own test builds. So the gate
covers changes to `main` (the base, the alpha, the control); how anyone screens their own test builds
is theirs to decide.

## What is shared, and what is each person's

| | shared | each person's own |
|---|---|---|
| privacy rules, decision rules written before the run, scripted places, four runs a side | **yes** | — |
| the control, the four route scopes, the scorer | **yes** | — |
| the gate | **yes**, for changes to the shared base (`main`) | rules for your own test builds |
| `develop` and pull requests for build changes | **yes** | — |
| working folder layout, build names, session routine, filing | — | yours |

## How a change gets in

Start from the control → change one line → run the route for the scope you are claiming something
about → score it → check the gate → pull request
into `develop` → one other person reads it → it goes in. `develop` is for build changes; notes, runs
and docs go straight to `main`.
