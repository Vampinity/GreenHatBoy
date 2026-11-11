#!/usr/bin/env python3
"""abcompare.py: is B really different from A, or is it run-to-run noise?

    abcompare.py --a RUN [RUN ...] --b RUN [RUN ...] [--metric play|light|heavy|heavy_share|worst|shaders|...]

Each run gives one number per metric (its mean over play windows of that regime); groups are compared run against
run, never window against window (windows inside one run are not independent). Prints mean ± sd per group, the
difference, a permutation p-value, and a verdict:
    real          p < 0.05 and the difference exceeds the noise floor
    likely        p < 0.2
    noise         otherwise
    consistent    the runs don't overlap and the gap exceeds the noise floor, but too few runs for a p-value
Noise floor (our data, same build/env, standard route, 7-11 Nov): walking fps sd about 1.0 between runs, so with
one run per arm nothing under about 2 fps can be called. Two runs per arm is the minimum we use.
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
    "heavy_share": lambda s: s["regimes"]["heavy"]["share"],
    "heavy_back": lambda s: s["regimes"]["heavy"]["back_busy_ms"],
    "heavy_gpu": lambda s: s["regimes"]["heavy"]["gpu_ms"],
    "heavy_front_wait": lambda s: s["regimes"]["heavy"]["front_waited_ms"],
    "worst": lambda s: s["worst_ms"],
    "shaders": lambda s: s["pipelines_in_play"],
}
NOISE_FLOOR = {"play": 1.0, "light": 0.8, "mid": 1.0, "heavy": 1.0}


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
    ap.add_argument("--a", nargs="+", required=True)
    ap.add_argument("--b", nargs="+", required=True)
    ap.add_argument("--metric", nargs="*", default=["play", "light", "heavy", "heavy_share", "worst", "shaders"])
    a = ap.parse_args()
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
        if verdict == "noise" and separated and abs(d) > floor:
            verdict = "consistent (every B run beyond every A run; add runs to confirm)"
        if min(len(va), len(vb)) < 2:
            verdict += " (one run on a side: can't call it)"
        print(f"{m:17s} {st.mean(va):7.2f}±{sd(va):5.2f} {st.mean(vb):7.2f}±{sd(vb):5.2f} {d:+7.2f} {p:6.3f}  {verdict}")
    print("\nWith 2 runs per side the smallest possible p is 0.33: treat 2+2 as a screen, confirm with 3+3 or more.")


if __name__ == "__main__":
    main()
