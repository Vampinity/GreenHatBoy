#!/usr/bin/env python3
"""anatomy.py: what the game asks the emulator for, against what each stage spends supplying it.

    anatomy.py table  RUNDIR [RUNDIR ...]   per-window demand and supply, per frame
    anatomy.py fit    RUNDIR [RUNDIR ...]   frame time regressed on demand by class
    anatomy.py budget RUNDIR [RUNDIR ...]   measured cost per unit against the 30 fps budget

Why a fit and not a ratio (13 Nov 2026): cost per unit of demand is not one number. One method id
takes 1.05 us and another 0.03; a compute dispatch takes 17.9. Marginal cost also differs from fixed
cost -- draw-end is 15-37 us at five draws a frame and 1.05 us at 13,300. A single average hides both,
so this fits frame time against demand by class and reports marginal cost, fixed cost and the residual.

Instrument cost is real and this tool will not hide it: runRD1 stands at 24.5 fps against runRX1/RX2 at
27.8/27.9, so its timers cost about 12%, and EDEN_NX2_GPU_PROFILE costs about 20% (LOGS.md). Counts
survive instrumentation; times do not. Collect counts and times in separate runs and say which is which.

Spine: EDEN_GBB_VITALS, one line a second with frames, fps, frame percentiles, present wait, back busy,
front wait and waits, ring kwords, GPU busy, submissions, fence pops. Everything else is joined onto it.
"""

import argparse
import io
import os
import re
import sys
from collections import defaultdict

try:
    import numpy as np
except ImportError:
    np = None

TARGET_FPS = 30.0
TARGET_MS = 1000.0 / TARGET_FPS

TS = re.compile(r"^\[ *([0-9]+\.[0-9]+)\]")

VITALS = re.compile(
    r"EDEN_GBB_VITALS t_ms=(\d+) frames=(\d+) fps=([\d.]+) frame_p50_ms=([\d.]+) "
    r"frame_p99_ms=([\d.]+) frame_max_ms=([\d.]+) present_wait_ms=([\d.]+) "
    r"back_busy_ms_s=([\d.]+) front_wait_ms_s=([\d.]+) front_waits_s=(\d+) "
    r"ring_kwords_s=(\d+) gpu_busy_ms_s=([\d.]+) gpu_subs_s=(\d+) shaders=(\d+) "
    r"shader_ms=([\d.]+) fence_pops_s=(\d+)"
)
BACK = re.compile(
    r"EDEN_GBB_BACK 5 s \(ms per s\): busy ([\d.]+), waiting ([\d.]+), idle hook ([\d.]+) \((\d+)/s\);(.*?); anchor"
)
BACK_KIND = re.compile(r"(\w+) ([\d.]+) \((\d+)/s\)")
BACK_METHODS = re.compile(r"EDEN_GBB_BACK methods \(engine:method, inclusive ms per s\): (.*)")
METHOD_ITEM = re.compile(r"(e\d+:0x[0-9a-f]+) ([\d.]+) \((\d+)/s, ([\d.]+) us\)")
SPLIT = re.compile(r"GPU split per second: back idle ([\d.]+) ms, (\d+) ring words, front waited ([\d.]+) ms")
TEXCACHE = re.compile(
    r"Texture cache last (\d+) frames: created (\d+) images, deleted (\d+).*?(\d+) async decodes, "
    r"ASTC (\d+) opaque / (\d+) alpha"
)
UPLOADS = re.compile(r"(\d+) uploads, (\d+) MiB")
SVCPROF = re.compile(
    r"EDEN_GBB_SVCPROF (t\d+) (\d+) ms, (\d+) frames \([\d.]+ ms/frame\): in svc (\d+) ms "
    r"\(([\d.]+)/frame\), outside (\d+) ms \(([\d.]+)/frame\)"
)
FPS5 = re.compile(r"nx2:vi2 5 s: (\d+) frames, ([\d.]+) fps, mean ([\d.]+) ms, 1% low ([\d.]+) ms, worst ([\d.]+) ms")

# Demand classes the fit uses, in the order they are reported.
CLASSES = [
    ("methods", "GPU command-stream methods"),
    ("calls", "ring-entry call thunks"),
    ("ring_words", "ring words"),
    ("gpu_subs", "host GPU submissions"),
    ("fence_pops", "fence pops"),
    ("front_waits", "front drains"),
]


def read_lines(path):
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = TS.match(line)
            yield (float(m.group(1)) if m else None), line


def collect(rundir):
    """Pull every demand and supply signal out of one run, keyed by log second."""
    log = os.path.join(rundir, "eden_log.txt")
    if not os.path.exists(log):
        return None
    out = {
        "run": os.path.basename(rundir.rstrip("/")),
        "vitals": [],
        "back": [],
        "methods": [],
        "split": [],
        "tex": [],
        "svc": defaultdict(list),
        "fps5": [],
        "build": None,
    }
    for t, line in read_lines(log):
        if out["build"] is None and "contentVersion" in line:
            m = re.search(r"contentVersion[^0-9]*([0-9.]+)", line)
            if m:
                out["build"] = m.group(1)
        m = VITALS.search(line)
        if m:
            g = m.groups()
            out["vitals"].append(
                dict(t=t, frames=int(g[1]), fps=float(g[2]), p50=float(g[3]), p99=float(g[4]),
                     worst=float(g[5]), present_wait=float(g[6]), back_busy_s=float(g[7]),
                     front_wait_s=float(g[8]), front_waits_s=int(g[9]), ring_kwords_s=int(g[10]),
                     gpu_busy_s=float(g[11]), gpu_subs_s=int(g[12]), shaders=int(g[13]),
                     fence_pops_s=int(g[15])))
            continue
        m = BACK.search(line)
        if m:
            kinds = {k: (float(ms), int(n)) for k, ms, n in BACK_KIND.findall(m.group(5))}
            out["back"].append(dict(t=t, busy=float(m.group(1)), waiting=float(m.group(2)),
                                    kinds=kinds))
            continue
        m = BACK_METHODS.search(line)
        if m:
            items = [(mid, float(ms), int(n), float(us)) for mid, ms, n, us in METHOD_ITEM.findall(m.group(1))]
            out["methods"].append(dict(t=t, items=items))
            continue
        m = SPLIT.search(line)
        if m:
            out["split"].append(dict(t=t, back_idle=float(m.group(1)), ring_words_s=int(m.group(2)),
                                     front_waited=float(m.group(3))))
            continue
        m = TEXCACHE.search(line)
        if m:
            up = UPLOADS.search(line)
            out["tex"].append(dict(t=t, over=int(m.group(1)), created=int(m.group(2)),
                                   deleted=int(m.group(3)), decodes=int(m.group(4)),
                                   astc=int(m.group(5)) + int(m.group(6)),
                                   uploads=int(up.group(1)) if up else None,
                                   mib=int(up.group(2)) if up else None))
            continue
        m = SVCPROF.search(line)
        if m:
            out["svc"][m.group(1)].append(dict(t=t, frames=int(m.group(3)),
                                               insvc=float(m.group(5)), outside=float(m.group(7))))
            continue
        m = FPS5.search(line)
        if m:
            out["fps5"].append(dict(t=t, frames=int(m.group(1)), fps=float(m.group(2)),
                                    mean=float(m.group(3)), p99=float(m.group(4)),
                                    worst=float(m.group(5))))
    return out


def nearest(rows, t, span=6.0):
    """The row closest in time to t, within span seconds."""
    best, bd = None, span
    for r in rows:
        if r["t"] is None:
            continue
        d = abs(r["t"] - t)
        if d <= bd:
            best, bd = r, d
    return best


def windows(data, skip_before=60.0, min_fps=8.0):
    """Per-second vitals joined with the slower reports, as per-frame demand and supply.

    Rows before skip_before are dropped: the first minute is boot and load-in, where the method
    count per frame is not the game's steady demand (13 Nov: 2.2 M/s in the load-in window against
    3.2 M/s standing, which is where the 96k-per-frame error came from).
    """
    rows = []
    for v in data["vitals"]:
        if v["t"] is None or v["t"] < skip_before or v["fps"] < min_fps:
            continue
        fps = v["fps"]
        b = nearest(data["back"], v["t"])
        s = nearest(data["split"], v["t"], span=11.0)
        row = dict(t=v["t"], fps=fps, frame_ms=1000.0 / fps, p99=v["p99"], worst=v["worst"],
                   present_wait=v["present_wait"])
        # Supply, per frame
        row["back_busy"] = v["back_busy_s"] / fps
        row["front_wait"] = v["front_wait_s"] / fps
        row["gpu_busy"] = v["gpu_busy_s"] / fps
        # Demand, per frame
        row["ring_words"] = v["ring_kwords_s"] * 1000.0 / fps
        row["gpu_subs"] = v["gpu_subs_s"] / fps
        row["fence_pops"] = v["fence_pops_s"] / fps
        row["front_waits"] = v["front_waits_s"] / fps
        row["methods"] = (b["kinds"].get("method", (0, 0))[1] / fps) if b else None
        row["calls"] = (b["kinds"].get("call", (0, 0))[1] / fps) if b else None
        row["method_ms"] = (b["kinds"].get("method", (0, 0))[0] / fps) if b else None
        row["back_idle"] = (s["back_idle"] / fps) if s else None
        rows.append(row)
    return rows


def critical_path(row):
    """The busiest stage as a share of the frame, named with that share.

    Stages run in parallel, so only the critical path buys frames. A hard threshold is the wrong
    test: the back can be the pace-setter at 87% of the frame, which no sensible cut-off catches.
    So report the largest share and let the number carry the confidence. Anything under half the
    frame means no stage we time accounts for the pace, which points at the guest's own chain.
    """
    f = row["frame_ms"]
    stages = [("back", row["back_busy"]), ("host GPU", row["gpu_busy"]),
              ("present fence", row["present_wait"])]
    stages = [(n, v) for n, v in stages if v is not None]
    if not stages:
        return "unmeasured"
    name, val = max(stages, key=lambda nv: nv[1])
    share = val / f if f else 0.0
    if share < 0.5:
        return f"guest CPU or unattributed (busiest timed stage {name} {share:.0%})"
    return f"{name} {share:.0%}"


def cmd_table(args):
    for rundir in args.rundirs:
        data = collect(rundir)
        if data is None:
            print(f"{rundir}: no eden_log.txt")
            continue
        rows = windows(data, skip_before=args.skip)
        print(f"\n=== {data['run']} ===")
        if not rows:
            print("  no vitals rows after the skip window (EDEN_GBB_VITALS not set?)")
            continue
        have_back = any(r["methods"] is not None for r in rows)
        print(f"  {len(rows)} seconds after t={args.skip:.0f}s"
              + ("" if have_back else "   [no EDEN_GBB_BACK_CALLS: no method or call counts]"))
        print(f"\n  {'t':>6} {'fps':>6} {'frame':>7} | demand per frame"
              f"{'':>22} | supply per frame      | critical path")
        print(f"  {'':>6} {'':>6} {'ms':>7} | {'methods':>9} {'calls':>7} {'ring':>8} {'subs':>6} {'fence':>6}"
              f" | {'back':>6} {'gpu':>6} {'front':>6} |")
        for r in rows[:: max(1, len(rows) // args.rows)]:
            print(f"  {r['t']:6.0f} {r['fps']:6.2f} {r['frame_ms']:7.1f} |"
                  f" {(r['methods'] or 0):9,.0f} {(r['calls'] or 0):7,.0f} {r['ring_words']:8,.0f}"
                  f" {r['gpu_subs']:6.0f} {r['fence_pops']:6.0f} |"
                  f" {(r['back_busy'] or 0):6.1f} {r['gpu_busy']:6.1f} {r['front_wait']:6.1f} |"
                  f" {critical_path(r)}")
        # steady summary
        fps = [r["fps"] for r in rows]
        print(f"\n  steady: fps {min(fps):.1f}-{max(fps):.1f}; "
              f"methods/frame "
              + (f"{min(r['methods'] for r in rows if r['methods']):,.0f}-"
                 f"{max(r['methods'] for r in rows if r['methods']):,.0f}" if have_back else "unknown")
              + f"; ring words/frame {min(r['ring_words'] for r in rows):,.0f}-"
                f"{max(r['ring_words'] for r in rows):,.0f}")
        missing = []
        if not have_back:
            missing.append("method and call counts (EDEN_GBB_BACK_CALLS)")
        if not data["methods"]:
            missing.append("per-method breakdown (EDEN_GBB_BACK_CALLS methods line)")
        if not data["svc"]:
            missing.append("guest thread times (EDEN_GBB_SVC_PROFILE)")
        if not data["tex"]:
            missing.append("texture churn and uploads (EDEN_NX2_TC_LOG)")
        print("  GPFIFO entries and words: never measured by any switch we have (needs a counter)")
        if missing:
            print("  also missing: " + "; ".join(missing))


def cmd_methods(args):
    """The per-method breakdown: cost per unit really is per class, not per method on average."""
    for rundir in args.rundirs:
        data = collect(rundir)
        if data is None or not data["methods"]:
            print(f"{os.path.basename(rundir.rstrip('/'))}: no EDEN_GBB_BACK methods lines")
            continue
        agg = defaultdict(lambda: [0.0, 0, 0])
        n = 0
        for w in data["methods"]:
            if w["t"] is None or w["t"] < args.skip:
                continue
            n += 1
            for mid, ms, cnt, _us in w["items"]:
                a = agg[mid]
                a[0] += ms
                a[1] += cnt
                a[2] += 1
        if not n:
            print(f"{data['run']}: no method windows after the skip")
            continue
        print(f"\n=== {data['run']}: back-thread method cost, {n} windows after t={args.skip:.0f}s ===")
        print(f"  {'engine:method':>16} {'ms/s':>9} {'count/s':>12} {'us each':>10}")
        rank = sorted(agg.items(), key=lambda kv: -kv[1][0])
        for mid, (ms, cnt, w) in rank[: args.top]:
            per = (ms * 1000.0 / cnt) if cnt else float("nan")
            print(f"  {mid:>16} {ms / n:9.1f} {cnt / n:12,.0f} {per:10.3f}")
        tot_ms = sum(v[0] for v in agg.values()) / n
        print(f"  {'total':>16} {tot_ms:9.1f}")
        print("  Cost per method spans orders of magnitude, which is why the fit is per class and an")
        print("  average cost per method is a category error.")


def cmd_fit(args):
    """frame_ms ~ fixed + sum_c (count_c x marginal_cost_c), across windows and runs."""
    if np is None:
        print("numpy is needed for the fit")
        return 1
    X, y, names, used = [], [], [], []
    for rundir in args.rundirs:
        data = collect(rundir)
        if data is None:
            continue
        for r in windows(data, skip_before=args.skip):
            if r["methods"] is None:
                continue
            X.append([r[k] for k, _ in CLASSES])
            y.append(r["frame_ms"])
            used.append(data["run"])
    if len(X) < len(CLASSES) + 2:
        print(f"only {len(X)} usable windows; need more than {len(CLASSES) + 1}."
              " Add runs, or lower --skip, or the runs lack EDEN_GBB_BACK_CALLS.")
        return 1
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    keep = [i for i in range(X.shape[1]) if X[:, i].std() > 1e-9]
    dropped = [(CLASSES[i][0], "no variation") for i in range(X.shape[1]) if i not in keep]
    # Collinearity. Methods, calls and ring words move together (ring words are about 1.11x methods
    # in every window), so a plain least squares cannot separate them: it hands one a large positive
    # cost and another a large negative one that cancels. A negative marginal cost is not a finding,
    # it is an unidentified model. Drop the later member of any pair correlated above the cut and say
    # so, rather than printing a coefficient nobody should believe.
    collinear = []
    for a_i in list(keep):
        for b_i in list(keep):
            if b_i <= a_i or b_i not in keep or a_i not in keep:
                continue
            r = float(np.corrcoef(X[:, a_i], X[:, b_i])[0, 1])
            if abs(r) >= args.collinear:
                keep.remove(b_i)
                collinear.append((CLASSES[b_i][0], f"r={r:+.3f} with {CLASSES[a_i][0]}"))
    dropped += collinear
    A = np.column_stack([np.ones(len(y))] + [X[:, i] for i in keep])
    cond = float(np.linalg.cond(A))
    # Scale the columns before solving. The raw matrix mixes counts of 2 with counts of 160,000, and
    # an unscaled solve overflows in the back-substitution; scaling changes nothing about the model.
    scale = np.where(np.abs(A).max(axis=0) > 0, np.abs(A).max(axis=0), 1.0)
    coef_s, *_ = np.linalg.lstsq(A / scale, y, rcond=None)
    coef = coef_s / scale
    pred = A @ coef
    resid = y - pred
    ss_res = float((resid ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    print(f"\n=== fit over {len(y)} windows from {len(set(used))} run(s) ===")
    print(f"  frame time {y.min():.1f}-{y.max():.1f} ms, mean {y.mean():.1f}")
    print(f"\n  {'class':>24} {'count/frame mean':>18} {'marginal us/unit':>18} {'ms/frame at mean':>18}")
    print(f"  {'fixed cost':>24} {'':>18} {'':>18} {coef[0]:18.2f}")
    for j, i in enumerate(keep):
        name = CLASSES[i][0]
        mean = X[:, i].mean()
        us = coef[j + 1] * 1000.0
        print(f"  {name:>24} {mean:18,.0f} {us:18.4f} {coef[j + 1] * mean:18.2f}")
    print(f"\n  R^2 {1 - ss_res / ss_tot if ss_tot else float('nan'):.3f}; "
          f"residual rms {float(np.sqrt((resid ** 2).mean())):.2f} ms "
          f"({100 * float(np.sqrt((resid ** 2).mean())) / y.mean():.0f}% of mean frame); "
          f"condition number {cond:,.0f}")
    for name, why in dropped:
        print(f"  dropped {name}: {why}")
    neg = [CLASSES[i][0] for j, i in enumerate(keep) if coef[j + 1] < 0]
    if neg:
        print(f"  NEGATIVE marginal cost for {', '.join(neg)} -- the model is still not identified."
              " Raise --collinear, add places with different demand mixes, or fit one class at a time.")
    if cond > 1e4:
        print(f"  Condition number over 10,000: treat every coefficient as indicative only.")
    rms_share = float(np.sqrt((resid ** 2).mean())) / y.mean()
    # One class at a time. When the joint fit is not identified -- which is the normal state until we
    # have several places with different demand mixes -- a simple regression per class still gives an
    # UPPER BOUND on that class's marginal cost, because it charges all the shared variance to it.
    print(f"\n  One class at a time (upper bound: all shared variance charged to that class)")
    print(f"  {'class':>24} {'marginal us/unit':>18} {'ms/frame at mean':>18} {'R^2 alone':>11}")
    for i in range(X.shape[1]):
        col = X[:, i]
        if col.std() <= 1e-9:
            continue
        sa = np.column_stack([np.ones(len(y)), col])
        sc = np.where(np.abs(sa).max(axis=0) > 0, np.abs(sa).max(axis=0), 1.0)
        c_s, *_ = np.linalg.lstsq(sa / sc, y, rcond=None)
        c = c_s / sc
        r = y - sa @ c
        r2 = 1 - float((r ** 2).sum()) / ss_tot if ss_tot else float('nan')
        print(f"  {CLASSES[i][0]:>24} {c[1] * 1000.0:18.4f} {c[1] * col.mean():18.2f} {r2:11.3f}")

    print("\n  Decision rule: a residual over about 25% of frame time means the demand classes are")
    print("  wrong or something unmeasured dominates. "
          + ("THAT IS THE CASE HERE." if rms_share > 0.25 else "Not the case here."))
    if len(set(used)) < 2:
        print("  Caution: one run only. The fit needs several places to separate marginal from fixed")
        print("  cost; with one place the design matrix barely varies and the split is not identified.")
    return 0


def cmd_budget(args):
    """Measured cost per unit against what 30 fps can afford."""
    if np is None:
        print("numpy is needed for the budget")
        return 1
    rows = []
    for rundir in args.rundirs:
        data = collect(rundir)
        if data is None:
            continue
        rows += [r for r in windows(data, skip_before=args.skip) if r["methods"] is not None]
    if not rows:
        print("no usable windows (EDEN_GBB_BACK_CALLS not set in these runs?)")
        return 1
    print(f"\n=== 30 fps budget, {len(rows)} windows ===")
    print(f"  frame budget {TARGET_MS:.1f} ms; measured mean frame "
          f"{sum(r['frame_ms'] for r in rows) / len(rows):.1f} ms")
    print("\n  Shares are of measured stage time, so they say where the frame goes now, not where it")
    print("  should go. A class only becomes a work item once its own cost is measured separately.")
    print(f"\n  {'stage':>22} {'ms/frame':>10} {'share of 33.3ms':>17}")
    for key, label in (("back_busy", "back busy"), ("gpu_busy", "host GPU"),
                       ("front_wait", "front waiting"), ("present_wait", "present fence")):
        vals = [r[key] for r in rows if r[key] is not None]
        if not vals:
            continue
        mean = sum(vals) / len(vals)
        print(f"  {label:>22} {mean:10.2f} {100 * mean / TARGET_MS:16.0f}%")
    print(f"\n  {'demand class':>22} {'count/frame':>13} {'affordable us/unit':>20}")
    print("  (if that class alone had the whole 33.3 ms budget)")
    for key, label in CLASSES:
        vals = [r[key] for r in rows if r[key] is not None]
        if not vals:
            continue
        mean = sum(vals) / len(vals)
        if mean <= 0:
            continue
        print(f"  {label:>22} {mean:13,.0f} {TARGET_MS * 1000.0 / mean:20.3f}")
    print("\n  Put the fit's marginal us/unit beside the affordable us/unit. Classes where measured")
    print("  exceeds affordable are the ranked problem list, by how much of the budget each overspends.")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("table", cmd_table), ("methods", cmd_methods), ("fit", cmd_fit), ("budget", cmd_budget)):
        q = sub.add_parser(name)
        q.add_argument("rundirs", nargs="+")
        q.add_argument("--skip", type=float, default=60.0,
                       help="drop log seconds before this (default 60: boot and load-in)")
        q.add_argument("--rows", type=int, default=12, help="table: how many rows to print")
        q.add_argument("--top", type=int, default=14, help="methods: how many to print")
        q.add_argument("--collinear", type=float, default=0.95,
                       help="fit: drop a class correlated above this with an earlier one (default 0.95)")
        q.set_defaults(fn=fn)
    a = p.parse_args()
    return a.fn(a) or 0


if __name__ == "__main__":
    sys.exit(main())
