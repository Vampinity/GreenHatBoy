# Kokiri 30 fps: an adversarial re-analysis of both log datasets

Scope: our 132 runs (hand-played Kokiri route, base PS5 13.60) and the collaborator's 1,087 runs (scripted routes, base PS5 12.40). All numbers below were recomputed from the packed logs with my own code (`parse.py`, `heavy.py`, `gpu.py`, `chain2.py`, `vsplit.py`, `vbatch.py`, `vtreat.py`, `liveswitch.py`, `stutter.py` in this folder). Nothing in the repo clone or the run folders was modified.

Short version:

- Claims 2, 3 and 4 reproduce. Claim 1 reaches a defensible conclusion by an invalid route: the frame-vs-ring-words regression is mostly an arithmetic artifact, the back is 77% busy (not saturated), and the cleaner statement is **heavy frame = game chain (33.6 ms) + present fence wait, where the fence wait ≈ 0.89 × back busy/frame + 0.60 × host-GPU ms/frame − 31 ms**. The back's per-frame cost is still the biggest single term, so the plan's direction survives; the "improve front/back overlap by cutting handshakes" leg does not, because the collaborator already tested every drain-cutting switch and none moved fps.
- The biggest thing missed: on the collaborator's data the regime classifier breaks. Their steady heavy stand runs at 16-19 fps with a present fence wait under 1 ms (the game is throttled through the command queue, not at present). "fence < 1 ms" is not the same as "game-CPU bound".
- Second biggest: pipelining depth is the one env lever that has ever moved heavy views by more than noise (FRAMES_AHEAD=1: +7.4 fps; full frame wait: −4.7; AHEAD_ALWAYS: +1.5 to +3). A true two-frames-ahead present has never been run on this core (the setting parses '2' as 0).
- Stutter: 71% of our runtime builds are pipelines that are already on disk but were not built at boot. That is a prep-policy bug, not non-convergence. The collaborator's scripted route converges to a median of 3 runtime builds per run; ours has 41.

---

## 1. Data and method

### 1.1 What was parsed

| | Ours | Collaborator |
|---|---|---|
| Runs | 132 | 1,087 |
| With `nx2:vi2 5 s` windows | 102 | 775 |
| With `GPU split per second` lines | 115 | 81 (73 usable after the door) |
| With `EDEN_GPU_TIME` on stderr | 36 | 0 (no stderr in most runs; none has the line) |
| With in-run "Live switches" A/B phases | 0 | 48 (432 phases) |
| With `EDEN_GBB_SVCPROF` | 8 | 0 |
| Firmware | 13.60 | 12.40 |
| Builds | T83/T85/T120 + patches 0901-0921 | T52…T125 stock |

Format facts that affect any analysis:

- `GPU split per second` is printed every **10 s**, not every second, and reports **per-second averages** over the interval (back idle ≤ 1000 ms; ring words ≈ 3.4 M/s). I aligned each 5 s window to the split record whose 10 s interval contains the window midpoint.
- `EDEN_GPU_TIME` aligns to the eden windows by session end, as you assumed, but a cross-correlation of GPU busy% against fps over all offsets picks `end_offset − 1` in about 60% of the 36 runs (the correlation is −0.8 to −0.96 either way). Treat GPU-per-window numbers as ±1 window. AF1 has 50 GPU lines against 36 windows (stale stderr).
- Phases: door = first window after 35 s with a worst frame ≥ 300 ms (door at 57-75 s in 100 of our runs; later in 42/48/51/AF1). Standing = door+10 to door+60 s, walking = door+70 s onward, play windows = fps < 45 and ≥ 40 frames. This matches your "standing 76-130 s" for the typical run and fixes the runs where the door came late.
- Both datasets render the main pass at 1920×1080 and blit to 2560×1440 through the upscale fallback ("Upscale fallback 1920x1080 -> 2560x1440 blitted" in both logs). Resolution is not a confounder between the datasets.
- The collaborator's `run.json` `fps.mean` is not our metric: it correlates 0.75 with my after-door play mean and sits 3.3 fps lower on average (different window selection). I used my own per-window metrics for both datasets throughout.

### 1.2 Run-to-run noise (needed before judging any A/B)

Ours, walking mean fps among runs with identical build+env (7 groups): pooled sd **1.14 fps**, but pairs differ by up to 3.6 fps (C1 27.9 vs C2 24.3) and the heavy-window fraction among identical envs ranges 0.3-0.9. The "54% heavy" figure is a property of where the hand walked, not a stable constant.

Collaborator, in-run A/A (32 runs, no switch changed between interleaved 20 s phases): mean delta **+0.09 fps**, spread about ±0.5. This is the only instrument in either dataset that resolves effects under 2 fps. Their cross-run scripted controls on the same route and build repeat to about ±0.5 fps on standing and ±1 fps on the post-door walk, except the "owner-spot" steering scripts (stand-hud, view-light/heavy), which sometimes stand in a different place (controls at 38 fps where the note says 17.6); I excluded those from lever conclusions.

Eras in our data: before D5 (9 Nov) runs used the full frame wait (standing fence 25-32 ms, 21-23 fps); D5 onward uses frame-ahead 1 (standing fence 0, 31-33 fps). Pooling the two eras in one "heavy" set is a confounder; your 103-window regression almost certainly mixed them. I report the frame-ahead-era, no-AHEAD_ALWAYS, no-profiler subset ("std") separately.

---

## 2. Claim by claim, on our data

### Claim 1: heavy views are bound by the GPU thread's per-frame work, mostly the back

**Reproduced numbers (std walking, frame-ahead era, 666 windows):**

| Regime | n | fps | frame ms | fence ms | ring words/s | words/frame | back idle ms/s | back busy/frame | front waited ms/s | front wait/frame |
|---|---|---|---|---|---|---|---|---|---|---|
| H (fence ≥ 5) | 376 | 21.1 | 49.1 | 15.5 | 3.20 M (cv 0.11) | 155 k | 227 | 38.1 ms | 555 | 27.7 ms |
| M (1-5) | 177 | 27.5 | 36.7 | 3.1 | 3.28 M | 120 k | 233 | 28.1 | 538 | 19.8 |
| L (< 1) | 113 | 30.7 | 32.8 | 0.2 | 3.55 M | 116 k | 289 | 23.4 | 467 | 15.4 |

Recent std walking windows (T120-era builds, 229 windows): H 62% at 21.5 fps, M 23% at 27.5, L 15% at 30.4. Your "54% / 21.6 fps" is in range; the fraction moves with the route.

Front-wait sites per heavy frame (std H): dma snapshot miss 8.6 ms (75 waits × 115 µs), list writers 7.6 ms (184 × 41 µs), acquire check 4.0 ms (93 × 43 µs), macro dma read 3.9 ms (109 × 35 µs), acquire 1.9, acquire poll 0.9, map 0.7. Total ≈ 27.7 ms/frame in ≈ 600 waits. Your figures reproduce.

**Where the methodology fails:**

1. *The regression is mostly arithmetic.* Words per frame is computed as (words/s) ÷ fps and frame ms = 1000 ÷ fps, so the two are coupled by construction. Permutation test: shuffle the per-second word rates across windows (so words/frame carries no real information) and refit. Observed r² = 0.48 (std H), slope 0.315 ms/1k words; the null r² median is **0.81**, slope 0.251. The observed fit is *worse* than the null. The same holds for every subset (all walking: 0.30 vs 0.64; AHEAD_ALWAYS: 0.62 vs 0.75; full-wait era: 0.51 vs 0.71; P5: 0.58 vs 0.70). The same coupling inflates "back busy = 0.229 ms per 1k words" and "host GPU ms per frame". Any per-frame quantity derived from a per-second rate ÷ fps correlates with frame time for free when the per-second rate is roughly constant, and here every per-second rate is roughly constant (words/s cv 0.11, GPU busy 53-58% in every fps quartile, back idle 227-253 ms/s).
2. *What the per-second rates actually say:* across heavy windows, lower fps goes with **lower** words/s (corr +0.57), more front waiting (−0.52), and about the same back idle (+0.21). A saturated back would show constant words/s and fps ∝ 1/(words per frame). Instead the whole pipeline slows together, with the back 77% busy (p90 83%, >85% in only 6% of heavy windows), the front 45% busy and the host GPU 56% busy. No stage is saturated; the frame is set by serial latency through the stages.
3. *"Back busy" from `back idle` is a usable but coarse measure.* It counts everything that is not waiting for ring entries, including time the back blocks inside work (fences, buffer-cache lock, staging ring, runtime pipeline builds on the GPU thread). P5's profile shows ≥ 25% of the back's time as "other (unattributed)". Treat 38 ms/frame as an upper bound on the back's CPU work.

**What the data supports instead (and it is simpler):**

- In heavy windows **frame − fence = 33.6 ms** (p10 26.9, p90 42.4) and the slope of frame time on fence wait is **0.90**; in mid windows frame − fence = 33.6 as well. The heavy frame is the game's ~33 ms chain plus the present's wait for the previous frame's fence, almost additively.
- On the 36-run GPU subset (180 std heavy windows): **fence ≈ −31.4 + 0.89 × back busy/frame + 0.60 × host-GPU ms/frame, r² = 0.85.** Read: the GPU-side latency of one frame is roughly the back's recording time plus 60% of the host GPU's time (the tail that runs after the back finishes), and the game waits for whatever exceeds its own ~31-33 ms.
- Slowest-quartile heavy windows: 17.6 fps, fence 27 ms, back busy 44 ms/frame, host GPU 30.6 ms/frame at 53% busy, 67 submissions/frame.

So the conclusion "the back's per-frame cost must come down" stands, but the quantitative framing changes:

- Perfect overlap alone (a deep enough pipeline so the game never waits) would make heavy views back-throughput-bound at ≈ 1000 / (773 ms/s ÷ 21 fps) ≈ **27 fps**, not 30. Back cost reduction is necessary regardless.
- Back cost reduction alone, with today's one-frame-ahead present, gives frame ≈ 0.89·back + 0.6·GPU + 2: a 25% back cut (38 → 28.5 ms) lands around 38 ms ≈ 26 fps; a 44% cut is needed for 33 ms, as you computed.
- Both together (back −25% and a two-deep pipeline) is the first combination that reaches 30 in heavy views on paper.
- "12 ms not overlapped" is better named "GPU tail + one-deep pipeline". A3 did not test pipelining depth; it removed the `gpu_behind` extra wait and left the depth at one. The collaborator's note on upstream's FRAMES_AHEAD=2 says their core parses '2' as 0 (full wait), so a two-deep present has never run on this emulator.

**Confounders checked:** build era (full-wait vs frame-ahead) changes H fps from 18.1 to 21.1 and fence from 39 to 15.5; AHEAD_ALWAYS runs have a lower heavy fraction by construction (the wait moves out of the fence metric) with +0.7 to +1.5 fps at matched route offsets; the profiler run P5 has back idle 243 but 14.8 fps and 37 ms/frame of front waits (profiler distortion, as you said). Thread priorities (X3) and fast draw (G1): no effect, agreed.

### Claim 2: light views and standing sit on the game's own 33 ms CPU chain

**Valid.** Standing L windows (427): 32.3 fps, 31.0 ms, fence 0.0; frame vs words/frame slope −0.03 (flat). Light walking: 30.7 fps, 32.8 ms, 5th percentile 26.0. The collaborator's T120-era standing phase (offsets 8-10 after the door, 20+ runs, 12.40 firmware, stock T120) is 30.5-33 fps at fence 0.2. The floor is not a firmware or patch artifact.

The 8 SVC-profiled runs (C1-C3, P4*, B1) show the chain concretely (per frame, standing / heavy walking):

| Thread | outside SVC (work) | main wait | signalled by |
|---|---|---|---|
| t86 main | 8.5 / 10.4 ms | 18.1 / 25.5 ms at …5604 | pool A (t152, t154) |
| t152 pool A lead | 9.1 / 10.8 | 12.2 / 15.7 at …961c + 5.3 / 6.6 at …583c + 1.0 / 5.0 at …5700 | pool B completion / pool A members / main |
| t153 pool A | 6.6 / 7.3 | 19.3 / 25.9 at …c384 | t152, t86 |
| t157 pool B lead | 8.0 / 10.0 | 17.5 / 27.2 at …9480 + 5 / 8 at …95bc | (mostly unprofiled) / pool B members |

Every thread works 6-11 ms and waits 18-27 ms; the chain main → pool A → pool B → main is serial. Two costs you did not list: every chain thread makes ≈ 130 `SleepThread` yields per frame (2.0-2.4 ms/frame each, ≈ 16 µs per SVC round trip) and ≈ 24 `WaitForAddress` calls per frame. The yields are the game's job system spinning; whether removing their cost shortens the chain depends on whether they are on the critical path (they are busy-waits for workers, so partly yes). Summed guest CPU is ≈ 108 ms per 33 ms frame across the six emulated cores (≈ 55% utilisation), so the emulated cores are neither idle nor saturated. Note EDEN_PS5_PLACE puts the six guest cores on host threads 0-5; if those are three SMT pairs, the chain threads share physical cores. I could not verify topology from logs; the collaborator's PIN/PLACE A/B (+2.5 fps, 4 runs, T80-81) says placement matters.

Gap in the claim: "fence < 1 ms" is treated as "game-bound". Ten of our 113 light walking windows run under 27 fps, and on the collaborator's side the steady heavy stand (runs 1083/1084/1085/1097/1098, 26 windows) runs at **16-19 fps with fence 0.2-1.1 ms**, back idle 130-170 ms/s (busy 83-87%), front waiting ~500 ms/s, 3.8-4.0 M words/s (220 k words/frame). There the game is held by the command queue (the front blocks on the back, the game blocks on the front), not at present. In their fence-free windows overall (475), fps correlates +0.86 with back idle and −0.91 with front waiting. The present fence is one of at least two places the emulator throttles the game; the regime label should use fence *and* back idle (or words/s) together.

### Claim 3: stutter comes from runtime pipeline builds

**Valid, with a wrong mechanism.** Play windows after the door (ours, 2,327): 30% have a frame ≥ 100 ms; of those, **72%** contain ≥ 50 ms of GPU-thread builds (you said 66%). P(≥100 ms frame | ≥ 50 ms builds) = 0.90 vs 0.11 without. Median 41 builds per run after the door (p90 142), median 888 ms of build time per run.

But: of 7,056 runtime builds after the door, **4,987 (71%) are "on disk, not built at boot"**, 1,566 "mesh, not in the disk cache", 503 "new". Across all runs, 658 of 1,247 distinct hashes recur in 3+ runs; in the 13 T120 runs, 86 of 265 hashes recur. The shader store does converge; the boot prep is choosing not to build what it already has (the 1,220 gate you noted). The collaborator's scripted route has a median of **3** runtime builds per run after the door (p90 31) with the same kinds; on their side only 17% of ≥100 ms windows coincide with builds, so their big frames come from streaming, not shaders.

The one env lever with a large measured effect here: EDEN_UP_ASYNC_TRANSLATION=1 on T99 with cold pipelines took the post-door walk from 13.3 to 26.1 fps (2 vs 2 runs, 400 → 45 builds). It moves translation off the GPU thread. It is not in our env and I did not find it set in any later build's env; check whether T120 carries it.

### Claim 4: host GPU at 15.8 / 25.7 ms per frame is the next wall

**Numbers reproduce** (36 runs, 768 aligned windows, std): standing L 15.3 ms/frame at 49% busy (max 56%); walking L 17.9 at 54%; H 26.5 ms/frame (p90 31.0) at 56% busy, p90 61%, max 67%; 61 submissions per frame, longest submission median 7.9 ms (20 ms outliers in the slowest windows). The GPU never approaches saturation in any window of any run. "Next wall" is a projection, consistent with: SKIP_AA (collaborator, 2 runs) +0.15; lower resolution (K2) no gain; handheld mode (T77-79) no gain. Pixel work is not a lever today. Caveat: the 0.6 coefficient on GPU time in the fence model means GPU time already contributes to heavy frames through the tail, so it is not irrelevant either.

### Claim 5: flashes mostly solved by the copy guard; 0919 fixes residual stale reads

Not testable from logs. The guard's cost is measurable: ours −1.8 fps standing (R120g vs R120a/b); collaborator −1.85 (7 runs, guard=3), −2.0 (guard=2, 4 runs), −2.9 (guard=3 + granule 16, 5 runs), −3.8 (all-writes), −13 (guard=1). AHEAD_ALWAYS + guard 3: +0.7 (2 runs, T91); their fps-ahead2b batch on T120: AHEAD_ALWAYS +1.4 on the walk, standing unchanged. The guard is a 6% tax on the standing floor that sits right on the 30 fps line; shrinking its scope is worth about 2 fps everywhere.

---

## 3. The collaborator's 1,087 runs

### 3.1 Regimes and routes

Their routes stand in heavier places than our route does. Door-relative medians:

| Route | runs | post-door walk (off 2-7) | stand |
|---|---|---|---|
| newgame-door-wait (T120 era) | ~60 | 19-21 fps, fence 20-38 | 30.5-33 fps, fence 0.2 (off 8-10) |
| newgame-door-wait (T64-T85, full wait) | ~450 | 10-15 fps, fence 45-67 | 12-20 |
| continue-stand-fast-wait "pond" | 79 | — | 17.5 fps, fence 30 (full wait) / 18.4, fence 8 (no wait) / 26, fence 3.3 (one script variant) |
| heavy stand (tunnel mouth, live) | 5 | — | 16-19 fps, **fence 0.2-1.1** |

So the same two regimes exist, with a third one they see and we mostly do not: heavy-at-fence-zero. Their split-line windows (1,040): H 18.3 fps, back idle 323, words 2.44 M/s (mostly full-wait era); L 26.1 fps, back idle 191, words 3.75 M/s. The frame-vs-words regression has the same artifact there (null r² 0.78-0.88 ≥ observed).

### 3.2 What moved fps (natural experiments)

Within-batch treatment vs control on the same route and build, my metric (standing mean after the door, else play mean). Noise floor ±1 fps cross-run, ±0.5 in-run.

| Lever | runs | effect | note |
|---|---|---|---|
| EDEN_NX2_FRAMES_AHEAD=1 (+TRUST_COPY, RESNAPSHOT=0) | 3 (+3 with SUBMIT_THREAD/TRANSCODE) | **+7.4 / +8.4** | T85, door-wait stand 25 → 33 |
| EDEN_UP_OOT_FRAME_WAIT=1 (full wait) | 2+3+3 | **−4.7 / −4.7 / −4.5** | pond 18.1 → 13.4 |
| FRAME_CAP 30 ms instead of full wait | 4 | +3.0 | pond |
| EDEN_UP_AHEAD_ALWAYS=1 | 4 cross-run, 2 live | +3.2 cross-run, **+1.5 live** | T99/T120 |
| EDEN_PS5_PIN=pairs + PLACE | 4 | +2.5 | T80-81; removing it on T83: −3.9 (1 run) |
| EDEN_NX2_SPLIT=0 (no front/back split) | 2 | −3.1 | the split is worth 3 fps |
| EDEN_UP_SKIP_STALE_UPLOADS | 6 | +2.2 | in the full-wait env |
| EDEN_UP_ASYNC_TRANSLATION | 2 | +6.7 | cold pipelines only |
| EDEN_UP_SHADER_PREP | 2 | +3.1 | T85, cold store |
| EDEN_UP_AHEAD_GUARD=3 | 7 | −1.85 | guard tax |
| EDEN_UP_FRITCHII_USAGE_TRACKER | 3 live, 6 cross | +0.8 / +0.4 | marginal |
| EDEN_UP_FAST_DRAW (+OOT_EXEMPT) | 3 live, 2+1 cross | **0.0** live; +2.2 / −0.7 cross | cross-run result is noise; live says nothing |
| EDEN_NX2_DMA_SNAPSHOT off (live) | 1 | −1.3 | keep it on; adding it: +0.3 to +0.5 |
| SEM_FAST + DRAIN_SKIP_SAME (+DMA_SNAPSHOT) | 2+1 | +1.2 / +0.5 | noise-level; ours (G2) −9% walking |
| FRITCHII_LISTSKIP | 3 | +0.1 | |
| FRITCHII_LISTSYNC | 2 | +1.4 (0.0, +2.8) | |
| FRONT_WAIT + UBO_SNAPSHOT | 2 | −1.8 | |
| BIND_ON_BACK + SPLIT_FIRST_DRAIN | 3 | +1.3 (−3.8 … +4.0) | script variance |
| L1056 back macros | 2 | +0.7 | |
| CB_BATCH + INLINE_CNTPCT + LIST_ASYNC ("front group") | 1 | +0.3 | |
| BACK_DRAW_CHEAP | 1 | ≈ 0 | |
| QUERY_LIGHT, QUERY_WAIT_ONCE, COND_BACK, GPU_PAGE_CACHE, NATIVE_ZSTD, POLL_BACKOFF, FAST_LOOKUP (live) | 1 each | −0.4 … +0.1 | |
| JIT_TABLE/FCMP_ADC/CHECKBIT/FREE_MOVES/R13 | 3 | +0.1 | JIT flags do nothing on this route; removing JIT_TABLE on one run −4.8 |
| NX2_OOT_SKIP_AA | 2 | +0.15 | pixel work is not the limit |
| HEAP_LARGE_KIB=256 | 5 | −5.4 | memory knobs can hurt |
| CRAM_RESERVE 256 | 3 | −2.6 | |
| TRANSCODE_THREADS=1 | 3 | −1.3 | |

The pattern is unambiguous: **every drain-cutting and front/back handshake switch is within noise** (LISTSKIP, LISTSYNC, SEM_FAST, DRAIN_SKIP_SAME, DMA_SNAPSHOT already on, FRONT_WAIT, UBO_SNAPSHOT, BIND_ON_BACK, SPLIT_FIRST_DRAIN, back macros, CB_BATCH, QUERY_*), as is fast draw in the only instrument that can resolve it. What moves heavy views is pipelining depth (frame wait → cap → one ahead → ahead-always: 13.4 → 16.9 → 18.4 → ~20), thread placement, and the split itself. The JIT flags do nothing, which agrees with the chain being wait-dominated rather than code-dominated.

Thermal: 8-20 minute stands are flat (21.4 / 21.8 / 21.5 / 21.8 fps by quarter; fence constant). Firmware: not separable from build, but the T120-era standing floor matches ours on 12.40.

Memory: 609 of their 1,059 runs and 55 of our 129 log `out of memory > 0 MiB` in the margins line at some point; 81 of their runs end in a crash (37 on door-wait, 21 on the pond). This drives crashes and evictions, not the steady fps.

---

## 4. Things not in the interpretation

1. **Pipelining depth is the untested structural lever.** Everything that changed the present's waiting discipline moved heavy views; nothing that changed the front's handshakes did. The present always waits for the previous fence, so the pipeline is one deep. A two-deep present (fix the '2' parsing or port upstream's variant) is the direct test of the latency model in §2.1; expected +3 to +6 fps in heavy views on its own, capped near 27 by back throughput, with the flicker question attached.
2. **The regime classifier misses queue throttling.** Add back idle (or words/s) to the fence when labelling windows; without it, "light" windows at 17 fps are invisible, and on our route they would show up where the view is heaviest (water).
3. **Texture-cache churn while walking.** Ours, per 600 frames: standing 406 images created / 333 deleted / 367 uploads (0.6 GB); walking **2,187 created / 2,049 deleted / 1,431 uploads = 1.3 GB (2.2 MB per frame)**; the slowest walking windows reach 3,200-3,500 created and deleted. The collaborator's post-door walk: 6,300 created / 4,900 uploads / 6.2 GB per 600 frames (10 MB per frame). Images are deleted and recreated at the same rate (collector), i.e. the cache thrashes while streaming. Their steady heavy stand has ~0 churn and still runs at 16-17 fps, so churn is not the steady heavy-view cost; it is a candidate for walking hitches and for part of the back's upload time in our walking windows. Not quantified further here.
4. **Boot prep policy** (§2.3): 71% of runtime builds are pipelines already on disk.
5. **Guard tax** of ~2 fps sits exactly on the standing floor.
6. **Chain costs not listed:** ~130 SleepThread yields per frame per chain thread (2 ms each), ~24 arbitration waits per frame, and possible SMT sharing of the six guest cores (PLACE/PIN worth +2.5 on their side).
7. **Run-to-run and route noise** is larger than most single-run A/Bs you ran (sd 1.1, pairs up to 3.6 apart, heavy fraction 0.3-0.9 at identical env). The collaborator's in-run live-switch harness is the right tool for anything under 2 fps; port it or use theirs.
8. **GPU-time alignment** is off by one window in most runs (minor).
9. **fps.mean is not comparable** across the datasets (different window selection; theirs 3.3 fps lower on average).

---

## 5. Ranked problems on the way to a stable 30 on a base PS5

| # | Problem | Certainty | Evidence | Expected win | Next step |
|---|---|---|---|---|---|
| 1 | Heavy views: GPU-side latency per frame (back ≈ 38-44 ms busy + ~0.6 × host GPU tail) exceeds the game's 33 ms, and the one-deep present serialises the difference | High (frame − fence = 33.6 ms; fence = 0.89·back + 0.60·GPU − 31, r² 0.85) | §2.1 | back −25% ≈ +4-5 fps; two-deep present ≈ +3-6; both ≈ 30 in heavy views | (a) per-frame timeline log (present, fence wait, front done, back done, GPU fence) to replace 5 s aggregates; (b) B2 BACK_CALLS; (c) a true two-frames-ahead present tested in-run A/B at the heavy stand |
| 2 | The game chain at 33 ms (standing 31-33, light walking 28-32) | High (both datasets, both firmwares) | §2.2 | need ~10%; JIT callbacks 2 ms, yields 2 ms/thread, placement +2.5 | HLE fast path for SleepThread yield; verify SMT topology of host threads 0-5; keep Path B |
| 3 | Runtime pipeline builds on the GPU thread | High (72% of ≥100 ms windows; 41 builds/run; 71% already on disk) | §2.3 | 1% lows, not the mean | build all on-disk pipelines at boot; EDEN_UP_ASYNC_TRANSLATION if T120 has it; count builds/run as the metric |
| 4 | Texture-cache thrash while streaming (2k images and 1.3 GB per 600 frames) | Medium (measured; causal share unknown) | §4.3 | unknown; hitches + back upload time | log churn per 5 s window; in-run A/B of TC_KEEP_ASYNC / AREA_EVICT / TEX_TRIM at a walking loop |
| 5 | Copy-guard cost ~2 fps on the floor | High | §2.5, collaborator 16 runs | +2 everywhere | reduce guard scope (granule, pages) with the audit as the correctness gate |
| 6 | Host GPU 26-31 ms per heavy frame | Medium as a future wall; not binding now (≤ 67% busy) | §2.4 | none today | revisit after 1 |

What the interpretation got right: the two regimes exist; the standing floor is the game chain; shader builds explain most hitches; host GPU numbers; flashes vs guard. What it got wrong or unproven: the regression and the "0.213 ms per 1k words" law (artifact); "back saturated" (77%); "front/back overlap via fewer handshakes" as a lever (exhaustively null on 1,087 runs); "prep never converges" (prep policy); A3 as proof against latency (it did not change depth).

---

## 6. Top three experiments

1. **Per-frame timeline, one line per present** (t_present_in, fence wait, t_front_done, t_back_done, t_gpu_fence, builds ms in that frame, images uploaded). Everything in §2.1 is inferred from 5 s and 10 s aggregates; this settles the back-vs-GPU-tail split and the depth question in one walking run.
2. **Two-frames-ahead present**, in-run live A/B (20 s phases, 3 rounds) at the collaborator's heavy stand and on our walking loop, with the 0918/0920 audit on to count stale reads. Prediction from the model: heavy stand 17-19 → 23-27 fps; standing unchanged.
3. **Boot prep that builds every on-disk pipeline + ASYNC_TRANSLATION on**, metric = runtime builds per run after the door (target < 5, collaborator's scripted route is at 3) and the share of ≥100 ms windows.

Then: the guard-scope cut (+2 on the floor), and a texture-churn A/B.

---

## 7. Caveats

- Our phases are time-based and the route is hand-played; "walking" mixes places with different weight (fps falls from 22 to 19 along the walk). The collaborator's scripted routes are tight (p25-p75 within ±2 fps per offset) except the owner-spot steering scripts.
- Split records are 10 s per-second averages aligned to 5 s windows; GPU-time windows are ±1 window.
- "Back busy" includes blocking inside work; I never see the back's CPU time directly except in P5 (profiler-inflated).
- The SVC profile covers 8 runs on T85 builds; thread ids and addresses were stable across them.
- The collaborator's dataset spans 70 builds in six days; treatment effects were taken only within a batch (same day, route, build). Single-run effects (n = 1) are listed for completeness and should not be acted on.
- No visual quality or flash data was available to me; flash claims are untested here.
