#!/usr/bin/env python3
"""stk_gate.py: the regression gate (MEASURING.md §4), read in the agreed order: stable, picture, fast, smooth.

    stk_gate.py floors CONTROL_RUN [...] -o floors.json [--alpha-env ENV]
        Score each control start (stk_score.score_run) and keep the control-eligible ones. Group them by gate key and
        write, per key and per number: the values, mean, sd, min, max and the NOISE FLOOR = the control's own spread
        (max - min), as MEASURING.md asks ("measured from the control arm, not guessed"; 16 Nov: village 0.67 fps).

    stk_gate.py check CANDIDATE_RUN [...] --floors floors.json [--alpha-env ENV] [--json]
        Score the candidate starts and read them against the floor of their gate key, stage by stage.

The gate key is route | firmware | cache class, plus the store and its pipeline count for warm starts (waveydude's
same-store condition, 16 Nov). The build is NOT in it: a candidate is a different build or env by definition.

A number is WORSE when the candidate's mean is on the bad side of the control's mean by more than the noise floor.
It is "real" when the permutation p (abcompare.py's test) is also under 0.05, "likely" under 0.2, otherwise it is
"beyond the floor, not yet shown" (too few starts). With 4 a side the smallest p is 0.029.

Stages and what each can do today (18 Nov, the alpha):
  1 stable   every start survived its route (no crash, script done); the memory floor (lowest largest free block,
             census and driver) and the driver's out-of-memory callbacks. A gate: a start that did not survive, or a
             memory floor that is really worse, blocks.
  2 picture  flashes per minute. A gate. NOT MEASURED on the alpha: needs a full-rate capture counted, or an
             in-emulator counter. The gate says so instead of passing it silently.
  3 fast     each route window's fps, and the whole run's median fps. Worse needs an explanation.
  4 smooth   hitch ms per minute (NOT MEASURED on the alpha: no hitch trace) and the worst frame.

Verdict: BLOCK (a start lost its route, or a stable or picture number is worse with p < 0.05); EXPLAIN (a number is
worse with p < 0.2: a trade is allowed if it can be explained, MEASURING §4); PASS (nothing worse that the test
supports). A number beyond the floor without that support is listed as "watch": against a 3-start floor a genuine
control start lands there about half the time (leave-one-out, 18 Nov). PROVISIONAL when the candidate has fewer than
4 starts (our 4-a-side rule), or when the floor itself has fewer than 4.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import random
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# number -> (stage, direction): +1 = higher is better, -1 = lower is better
NUMBERS = {
    "largest_free_block_min_mib": ("stable", +1),
    "largest_free_block_driver_min_mib": ("stable", +1),
    "radv_oom_events": ("stable", -1),
    "flashes_per_min": ("picture", -1),
    "fps_median": ("fast", +1),
    "hitch_ms_per_min": ("smooth", -1),
    "worst_frame_ms": ("smooth", -1),
}
STAGES = ("stable", "picture", "fast", "smooth")
MIN_STARTS = 4


def gate_key(row: dict) -> str | None:
    cc = row.get("cache_class")
    if cc not in ("cold", "warm") or not row.get("route_key") or not row.get("firmware"):
        return None
    key = f"{row['route_key']}|{row['firmware']}|{cc}"
    if cc == "warm":
        key += f"|{row.get('shader_store')}|{row.get('store_pipelines')}"
    return key


def numbers_of(row: dict) -> dict[str, tuple[str, int]]:
    """The gate's numbers for one row: the fixed ones plus every route window (win_<name>_fps, fast)."""
    out = dict(NUMBERS)
    for k in row:
        if k.startswith("win_") and k.endswith("_fps"):
            out[k] = ("fast", +1)
    return out


def number_value(row: dict, name: str):
    v = row.get(name)
    if isinstance(v, str) and v.startswith(">="):   # radv_oom_events at its cap: a floor, not a count
        return None
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def survived(row: dict) -> bool:
    return (row.get("survival_result") == "completed" and row.get("crash_class") in (None, "none")
            and row.get("route_completed") is True)


def perm_p(a: list[float], b: list[float], rounds: int = 20000) -> float:
    """Two-sided permutation test on the difference of means (abcompare.py's, exact when small)."""
    obs = abs(st.mean(b) - st.mean(a))
    pool, na = a + b, len(a)
    combos = list(itertools.combinations(range(len(pool)), na))
    if len(combos) <= rounds:
        diffs = [abs(st.mean([pool[i] for i in range(len(pool)) if i not in c]) - st.mean([pool[i] for i in c]))
                 for c in combos]
    else:
        rnd, diffs = random.Random(1), []
        for _ in range(rounds):
            rnd.shuffle(pool)
            diffs.append(abs(st.mean(pool[na:]) - st.mean(pool[:na])))
    return sum(d >= obs - 1e-9 for d in diffs) / len(diffs)


def build_floors(rows: list[dict]) -> dict:
    groups: dict[str, list[dict]] = {}
    skipped = []
    for r in rows:
        k = gate_key(r)
        if not r.get("control_eligible") or k is None:
            skipped.append({"run": r.get("run_id"), "why": "not control_eligible" if k else "no gate key"})
            continue
        groups.setdefault(k, []).append(r)
    out = {"_doc": "stk_gate.py floors: per gate key, the control's values per number; floor = max - min.",
           "keys": {}, "skipped": skipped}
    for k, rs in sorted(groups.items()):
        nums = {}
        names = set()
        for r in rs:
            names |= set(numbers_of(r))
        for name in sorted(names):
            stage, direction = numbers_of(rs[0]).get(name, NUMBERS.get(name, ("fast", +1)))
            vals = [number_value(r, name) for r in rs]
            vals = [v for v in vals if v is not None]
            if not vals:
                nums[name] = {"stage": stage, "direction": direction, "values": [], "measured": False}
                continue
            nums[name] = {"stage": stage, "direction": direction, "measured": True, "values": vals,
                          "mean": round(st.mean(vals), 3), "sd": round(st.stdev(vals), 3) if len(vals) > 1 else 0.0,
                          "min": min(vals), "max": max(vals), "floor": round(max(vals) - min(vals), 3)}
        out["keys"][k] = {"n": len(rs), "runs": [r.get("run_id") for r in rs], "numbers": nums}
    return out


def judge_number(ctrl: dict, cand_vals: list[float]) -> dict:
    """One number: candidate values against the control's entry from floors.json."""
    if not ctrl.get("measured") or not cand_vals:
        return {"verdict": "not measured"}
    a, b, d = ctrl["values"], cand_vals, ctrl["direction"]
    diff = st.mean(b) - st.mean(a)
    worse_by = -diff * d               # > 0 means worse
    p = perm_p(a, b) if len(a) + len(b) > 2 and len(a) > 0 and len(b) > 0 else 1.0
    floor = ctrl["floor"]
    if worse_by > floor:
        verdict = "worse (real)" if p < 0.05 else ("worse (likely)" if p < 0.2 else "worse beyond the floor, not yet shown")
    elif -worse_by > floor:
        verdict = "better (real)" if p < 0.05 else ("better (likely)" if p < 0.2 else "better beyond the floor, not yet shown")
    else:
        verdict = "within the noise"
    return {"verdict": verdict, "control_mean": ctrl["mean"], "candidate_mean": round(st.mean(b), 3),
            "diff": round(diff, 3), "floor": floor, "p": round(p, 3), "n_control": len(a), "n_candidate": len(b)}


def check(rows: list[dict], floors: dict) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    unkeyed = []
    for r in rows:
        k = gate_key(r)
        (groups.setdefault(k, []) if k else unkeyed).append(r)
    reports = []
    for r in unkeyed:
        reports.append({"key": None, "runs": [r.get("run_id")], "verdict": "NO KEY",
                        "why": f"cache class {r.get('cache_class')!r}: a half-warm or unknown start can't be gated"})
    for k, rs in sorted(groups.items()):
        rep = {"key": k, "runs": [r.get("run_id") for r in rs], "stages": {s: [] for s in STAGES}, "notes": []}
        f = floors["keys"].get(k)
        if f is None:
            rep.update(verdict="NO FLOOR", why="no control floor for this key")
            reports.append(rep)
            continue
        # Stage 1, survival first: every start must survive its route.
        lost = [r.get("run_id") for r in rs if not survived(r)]
        rep["stages"]["stable"].append({"number": "survival", "verdict": "ok" if not lost else "FAILED",
                                        "detail": f"{len(rs) - len(lost)} of {len(rs)} survived the route"
                                                  + (f"; not: {', '.join(lost)}" if lost else "")})
        alive = [r for r in rs if survived(r)]
        for name, ctrl in f["numbers"].items():
            vals = [v for v in (number_value(r, name) for r in alive) if v is not None]
            j = judge_number(ctrl, vals)
            j["number"] = name
            rep["stages"][ctrl["stage"]].append(j)
        # Verdict in the agreed order. Only a test-backed "worse" moves the verdict (real: p < 0.05, likely: p < 0.2,
        # as in abcompare.py): beyond the floor alone happens to a genuine control start about half the time against
        # a 3-start floor (leave-one-out, 18 Nov: 8 of 16), so it is reported as "watch", not as a verdict.
        def bad(stage, verdicts):
            return [x for x in rep["stages"][stage] if x["verdict"] in verdicts]
        blocking = bad("stable", {"FAILED", "worse (real)"}) + bad("picture", {"worse (real)"})
        explain = (bad("stable", {"worse (likely)"}) + bad("picture", {"worse (likely)"})
                   + bad("fast", {"worse (real)", "worse (likely)"}) + bad("smooth", {"worse (real)", "worse (likely)"}))
        watch = [x["number"] for s in STAGES for x in rep["stages"][s]
                 if x["verdict"] == "worse beyond the floor, not yet shown"]
        if blocking:
            rep["verdict"] = "BLOCK"
        elif explain:
            rep["verdict"] = "EXPLAIN"
        else:
            rep["verdict"] = "PASS"
        if watch:
            rep["notes"].append("watch (beyond the floor, not shown by the test; add starts): " + ", ".join(watch))
        unseen = sorted({x["number"] for s in STAGES for x in rep["stages"][s] if x["verdict"] == "not measured"})
        if unseen:
            rep["notes"].append("not measured: " + ", ".join(unseen))
        if len(rs) < MIN_STARTS or f["n"] < MIN_STARTS:
            rep["provisional"] = f"candidate {len(rs)} start(s), floor {f['n']}: the rule is {MIN_STARTS} a side"
        reports.append(rep)
    return reports


def print_report(reports: list[dict]) -> None:
    for rep in reports:
        print(f"== {rep.get('key')}  ({', '.join(str(x) for x in rep['runs'])})")
        if "stages" not in rep or rep.get("verdict") in ("NO FLOOR", "NO KEY"):
            print(f"   {rep['verdict']}: {rep.get('why')}\n")
            continue
        for s in STAGES:
            for x in rep["stages"][s]:
                if x["verdict"] == "not measured":
                    continue
                if "control_mean" in x:
                    print(f"   {s:7s} {x['number']:34s} control {x['control_mean']:>9} cand {x['candidate_mean']:>9} "
                          f"diff {x['diff']:+9} floor {x['floor']:>7}  p {x['p']:.3f}  {x['verdict']}")
                else:
                    print(f"   {s:7s} {x['number']:34s} {x['detail']}  {x['verdict']}")
        for n in rep["notes"]:
            print(f"   ({n})")
        print(f"   VERDICT: {rep['verdict']}" + (f"  PROVISIONAL: {rep['provisional']}" if rep.get("provisional") else "") + "\n")


def main(argv: list[str]) -> int:
    import stk_score
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("floors"); a.add_argument("runs", nargs="+"); a.add_argument("-o", "--out", required=True)
    a.add_argument("--alpha-env", default=stk_score.DEFAULT_ALPHA_ENV)
    c = sub.add_parser("check"); c.add_argument("runs", nargs="+"); c.add_argument("--floors", required=True)
    c.add_argument("--alpha-env", default=stk_score.DEFAULT_ALPHA_ENV); c.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    rows = [stk_score.score_run(r, args.alpha_env) for r in args.runs]
    if args.cmd == "floors":
        fl = build_floors(rows)          # run ids only: no run_path, so the file carries no local paths
        Path(args.out).write_text(json.dumps(fl, indent=1) + "\n")
        for k, v in fl["keys"].items():
            print(f"{k}: n={v['n']} ({', '.join(v['runs'])})")
        for s in fl["skipped"]:
            print(f"skipped {s['run']}: {s['why']}")
        return 0
    reps = check(rows, json.loads(Path(args.floors).read_text()))
    if args.json:
        print(json.dumps(reps, indent=1))
    else:
        print_report(reps)
    return 0 if all(r.get("verdict") == "PASS" for r in reps) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
