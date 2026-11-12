#!/usr/bin/env python3
"""abcompare.py: is B really different from A, or is it run-to-run noise?

    abcompare.py --a RUN [RUN ...] --b RUN [RUN ...] [--metric play|light|heavy|heavy_share|worst|shaders|...]

Each run gives one number per metric (its mean over play windows of that regime); groups are compared run against
run, never window against window (windows inside one run are not independent). Prints mean ± sd per group, the
difference, a permutation p-value, and a verdict:
    real          p < 0.05 and the difference exceeds the noise floor
    likely        p < 0.2
    noise         otherwise
    consistent    3+ runs a side, the runs don't overlap and the gap exceeds the noise floor, p not yet < 0.05
    screen only   2 runs on a side and the runs split: noise does that 1 time in 3, so only a lead
Noise floor (our hand-played route, same build and env): sd about 1.14 fps between runs, pairs up to 3.6 apart;
with one run per side nothing under about 2-3 fps can be called. The heavy share of a run swings 0.3-0.9 with where
you walk, so compare per regime.

    abcompare.py --live RUN [RUN ...]
compares the labelled phases of in-run live-switch schedules (EDEN_UP_LIVE_SWITCHES): phases interleave within one
run, so place and session are shared. In-run A/A noise is about +-0.5 fps; pairs phases by round.
Standard library only.
"""
import argparse
import itertools
import os
import random
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eglog  # noqa: E402

METRICS = {
    "play": lambda s: s["play_fps"],
    "light": lambda s: s["regimes"]["light"]["fps"],
    "mid": lambda s: s["regimes"]["mid"]["fps"],
    "heavy": lambda s: s["regimes"]["heavy"]["fps"],
    "queued": lambda s: s["regimes"]["queued"]["fps"],
    "standing": lambda s: s["standing"]["fps"],
    "walking": lambda s: s["walking"]["fps"],
    "heavy_share": lambda s: s["regimes"]["heavy"]["share"],
    "heavy_back": lambda s: s["regimes"]["heavy"]["back_busy_ms"],
    "heavy_gpu": lambda s: s["regimes"]["heavy"]["gpu_ms"],
    "heavy_front_wait": lambda s: s["regimes"]["heavy"]["front_waited_ms"],
    "worst": lambda s: s["worst_ms"],
    "shaders": lambda s: s["pipelines_in_play"],
}
# Run-to-run sd on our hand-played route (same build and env): about 1.14 fps, pairs up to 3.6 apart (Fable review,
# 11 Nov). In-run live-switch A/A: about +-0.5 fps.
NOISE_FLOOR = {"play": 1.2, "standing": 1.0, "walking": 1.2, "light": 1.0, "queued": 1.0, "mid": 1.2, "heavy": 1.2}
LIVE_NOISE = 0.5


def perm_p(a, b, rounds=20000):
    obs = abs(st.mean(b) - st.mean(a))
    pool, na = a + b, len(a)
    combos = list(itertools.combinations(range(len(pool)), na))
    if len(combos) <= rounds:
        diffs = []
        for c in combos:
            ga = [pool[i] for i in c]
            gb = [pool[i] for i in range(len(pool)) if i not in c]
            diffs.append(abs(st.mean(gb) - st.mean(ga)))
    else:
        rnd = random.Random(1)
        diffs = []
        for _ in range(rounds):
            rnd.shuffle(pool)
            diffs.append(abs(st.mean(pool[na:]) - st.mean(pool[:na])))
    return sum(d >= obs - 1e-9 for d in diffs) / len(diffs)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a", nargs="+")
    ap.add_argument("--b", nargs="+")
    ap.add_argument("--live", nargs="+", help="runs with live-switch phases: compare their labels")
    ap.add_argument("--metric", nargs="*", default=["standing", "walking", "light", "heavy", "heavy_share", "worst",
                                                    "shaders"])
    a = ap.parse_args()
    if a.live:
        return live(a.live)
    if not a.a or not a.b:
        ap.error("--a and --b, or --live")
    sa = [eglog.load(p).summary() for p in a.a]
    sb = [eglog.load(p).summary() for p in a.b]
    print(f"A: {', '.join(s['run'] for s in sa)}\nB: {', '.join(s['run'] for s in sb)}\n")
    print(f"{'metric':17s} {'A mean±sd':>14s} {'B mean±sd':>14s} {'B-A':>7s} {'p':>6s}  verdict")
    for m in a.metric:
        va = [METRICS[m](s) for s in sa if METRICS[m](s) is not None]
        vb = [METRICS[m](s) for s in sb if METRICS[m](s) is not None]
        if not va or not vb:
            print(f"{m:17s} {'(missing)':>14s}")
            continue
        sd = lambda v: st.stdev(v) if len(v) > 1 else 0.0
        d = st.mean(vb) - st.mean(va)
        p = perm_p(va, vb) if len(va) + len(vb) > 2 else 1.0
        floor = NOISE_FLOOR.get(m, 0)
        separated = max(va) < min(vb) or max(vb) < min(va)
        verdict = "real" if p < 0.05 and abs(d) > floor else ("likely" if p < 0.2 and abs(d) > floor else "noise")
        smallest = min(len(va), len(vb))
        if verdict == "noise" and separated and abs(d) > floor:
            # With 2 runs a side, a full split happens by chance 1 time in 3: a screen, not evidence.
            verdict = ("consistent (every B run beyond every A run; add runs to confirm)" if smallest >= 3
                       else "screen only (the runs split, but with 2 a side noise does that 1 time in 3)")
        if smallest < 2:
            verdict += " (one run on a side: can't call it)"
        print(f"{m:17s} {st.mean(va):7.2f}±{sd(va):5.2f} {st.mean(vb):7.2f}±{sd(vb):5.2f} {d:+7.2f} {p:6.3f}  {verdict}")
    na, nb = len(sa), len(sb)
    from math import comb
    print(f"\nWith {na} and {nb} runs the smallest possible p is {1 / comb(na + nb, na) if na != nb else 2 / comb(na + nb, na):.3f}; "
          "'consistent' needs 3 or more runs a side, 'real' needs p < 0.05.")


def live(paths):
    phases = []
    for p in paths:
        run = eglog.load(p)
        phases += [dict(ph, run=run.name) for ph in run.live_phases]
    labels = sorted({ph["label"] for ph in phases})
    if len(labels) < 2:
        print("need at least two phase labels; found", labels)
        return 1
    base = labels[0]
    print(f"{len(phases)} phases in {len(paths)} run(s); labels {labels}; baseline '{base}'")
    for lab in labels[1:]:
        va = [ph["fps"] for ph in phases if ph["label"] == base]
        vb = [ph["fps"] for ph in phases if ph["label"] == lab]
        d = st.mean(vb) - st.mean(va)
        p = perm_p(va, vb) if len(va) + len(vb) > 2 else 1.0
        verdict = "real" if p < 0.05 and abs(d) > LIVE_NOISE else ("likely" if p < 0.2 and abs(d) > LIVE_NOISE else "noise")
        print(f"'{lab}' vs '{base}': {st.mean(vb):.2f} vs {st.mean(va):.2f} fps ({len(vb)}/{len(va)} phases), "
              f"{d:+.2f}, p {p:.3f}: {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
