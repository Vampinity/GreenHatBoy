#!/usr/bin/env python3
"""stk_gate.py: the regression gate (MEASURING.md §4), read in the agreed order: stable, picture, fast, smooth.

    stk_gate.py floors CONTROL_RUN [...] -o floors.json --alpha-env ALPHA_ENV
        Score each control start (stk_score.score_run) and keep the control-eligible ones. Group them by gate key and
        write, per key and per number: the values, mean, sd, min, max and the spread of one start (max - min). A
        number with a control start at a counter's cap (">=64") is marked unusable for that key.

    stk_gate.py check CANDIDATE_RUN [...] --floors floors.json --alpha-env ALPHA_ENV [--json]
        Score the candidate starts and read them against the floor of their gate key, stage by stage.

    ALPHA_ENV is the alpha release's env.txt (the control's settings); the scorer reads each run's env against it.

The gate key is route | firmware | cache class, plus the store and its pipeline count for warm starts (waveydude's
same-store condition, 16 Nov). The build is NOT in it: a candidate is a different build or env by definition.

The candidate's mean is compared with the control's mean, so the noise it is read against is the NOISE OF A MEAN,
not one start's spread (PR #18 review, point 1): 2 x sd x sqrt(1/n_control + 1/n_candidate), from the control's sd.
A number is WORSE when the candidate's mean is on the bad side by more than that, and the permutation p
(abcompare.py's test) says how sure: "real" under 0.05, "likely" under 0.2, else "beyond the noise, not yet shown".
It is also "real" when p < 0.05 and every candidate start is worse than the control's worst start, whatever the
means (point 2: a later-area start at 0 MiB on all four). With 4 a side the smallest p is 0.029, which only complete
separation reaches.

A counter at its cap (">=64" out-of-memory callbacks) is a lower bound: a capped candidate start counts at the cap,
so it reads as worse than any uncapped control; a control start at the cap makes that number unusable for its key,
since the control's own value is unknown (point 3).

Stages and what each can do today (18 Nov, the alpha):
  1 stable   every start survived its route (no crash, script done); the memory floor (lowest largest free block,
             census and driver) and the driver's out-of-memory callbacks. A gate: a start that did not survive, or a
             memory floor that is really worse, blocks.
  2 picture  flashes per minute. A gate. NOT MEASURED on the alpha: needs a full-rate capture counted, or an
             in-emulator counter. The gate says so instead of passing it silently.
  3 fast     each route window's fps, and the whole run's median fps. Worse needs an explanation.
  4 smooth   hitch ms per minute (NOT MEASURED on the alpha: no hitch trace) and the worst frame.

Each start is first sorted (point 5): CRASHED (a crash, or the log's out-of-device-memory), LOST (a WAIT or STEER
timed out: the route did not get where it was going) or HUNG (stopped before the script's END without a normal close:
the log just ends, a freeze) count against the candidate; INVALID (the app was closed normally before the script's
END, or a window's anchor line was skipped) says nothing about the candidate, so the start is left out and should be
rerun.

Each arm must be one thing (waveydude's review of PR #18, 18 Nov). The starts pooled on one side of a key must share
the build (the boot trace's version and compile time), the effective settings (the env hash, harness lines left out),
the shader translation id and the script. The control and the candidate may differ; a side may not. A mixed candidate
arm is MIXED, with the runs that differ named; a mixed control arm is refused when the floor is built. A start whose
build can't be read leaves the arm unverified, which is PROVISIONAL.

Verdicts, in this order, with the exit code check returns:
  BLOCK        4  a start crashed or lost its route, or a stable or picture number is really worse. Blocks even
                  when the arm is short: a crash is a crash.
  MIXED        3  the candidate arm pools different builds, settings, translation ids or scripts.
  INVALID      3  no candidate start is valid (all quit early or skipped an anchor); also NO KEY and NO FLOOR.
  PROVISIONAL  2  the arm is incomplete: fewer than 4 valid candidate starts, a floor of fewer than 4, a stable
                  number the floor gates on read on fewer than 4 candidate starts, or an unverified build. The
                  report still shows what the starts so far say ("leaning").
  EXPLAIN      1  a number is worse with p < 0.2: a trade is allowed if it can be explained (MEASURING §4).
  PASS         0  nothing worse that the test supports, on what the gate could measure. Numbers it could not
                  (flashes and hitches on the alpha, a counter at its cap on the floor) are listed as NOT CLEARED:
                  PASS clears only the checks it names.
A number beyond the noise without the test's support is listed as "watch". With several keys, the exit code is the
highest of theirs, so the worst verdict wins. Anything but 0 is not cleared.
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
# What a side of a comparison must share to be pooled (waveydude, PR #18 review): field -> what it names.
ARM_FIELDS = {"build_key": "build", "env_hash": "settings (env hash)", "translation_id": "translation id",
              "script_sha1": "script"}
EXIT = {"PASS": 0, "EXPLAIN": 1, "BLOCK": 4, "PROVISIONAL": 2, "MIXED": 3, "INVALID": 3, "NO KEY": 3, "NO FLOOR": 3}


def arm_of(rows: list[dict]) -> tuple[dict, list[str], list[str]]:
    """The arm's identity, the ways it is mixed, and the ways it can't be verified.
    identity: field -> the one value (or None); mixed: one line per field with more than one value, naming the runs."""
    ident, mixed, unverified = {}, [], []
    for field, label in ARM_FIELDS.items():
        by: dict = {}
        for r in rows:
            by.setdefault(r.get(field), []).append(str(r.get("run_id")))
        known = {v: rs for v, rs in by.items() if v not in (None, "")}
        if len(known) > 1:
            mixed.append(f"{label} differs: " + "; ".join(f"{v} ({', '.join(rs)})" for v, rs in sorted(known.items(), key=str)))
        if field == "build_key" and (None in by or "" in by):
            unverified.append("build not identified on " + ", ".join(by.get(None, []) + by.get("", [])))
        ident[field] = next(iter(known)) if len(known) == 1 else None
    return ident, mixed, unverified


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


def cap_of(v) -> float | None:
    """A counter at its cap is written ">=N" (radv_oom_events): its true value is N or more."""
    if isinstance(v, str) and v.startswith(">="):
        try:
            return float(v[2:])
        except ValueError:
            return None
    return None


def number_value(row: dict, name: str):
    """The number, or None. A capped counter gives its cap (a lower bound): see capped()."""
    v = row.get(name)
    c = cap_of(v)
    if c is not None:
        return c
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def capped(row: dict, name: str) -> bool:
    return cap_of(row.get(name)) is not None


def start_status(row: dict) -> tuple[str, str]:
    """ok / CRASHED / LOST / HUNG (all count against the candidate) / INVALID (says nothing about it: rerun)."""
    if row.get("survival_result") == "crashed" or row.get("crash_class") not in (None, "none"):
        return "CRASHED", f"{row.get('survival_result')}, crash class {row.get('crash_class')}"
    if row.get("route_completed") is False:
        return "LOST", f"route {row.get('route_result')}: {row.get('route_reason')}"
    if row.get("anchors_skipped"):
        return "INVALID", "window anchor skipped (" + ", ".join(row["anchors_skipped"]) + "): rerun"
    if row.get("survival_result") != "completed":
        # Only a normal close before END is a quit that says nothing (KV3, LV5, FC1). A log that just stops, with no
        # crash file, is a freeze: on the field route everything after the WAIT at line 92 is MAYBEs, so a hang in
        # that load meets every required leg (Vampinity's second review of PR #18).
        if row.get("end_kind") != "app_closed":
            return "HUNG", (f"stopped before the script's END with no normal close ({row.get('survival_result')}, "
                            f"end {row.get('end_kind')}): a freeze")
        return "INVALID", f"quit before the script's END ({row.get('survival_result')}, closed normally): rerun"
    return "ok", ""


def survived(row: dict) -> bool:
    return start_status(row)[0] == "ok"


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


class MixedArm(ValueError):
    pass


def build_floors(rows: list[dict]) -> dict:
    groups: dict[str, list[dict]] = {}
    skipped = []
    for r in rows:
        k = gate_key(r)
        if not r.get("control_eligible") or k is None:
            skipped.append({"run": r.get("run_id"), "why": "not control_eligible" if k else "no gate key"})
            continue
        groups.setdefault(k, []).append(r)
    out = {"_doc": "stk_gate.py floors: per gate key, the control's values per number; floor = the spread of one "
                   "start (max - min); check reads means against the noise of a mean, from sd. usable: false = a "
                   "control start at a counter's cap.",
           "keys": {}, "skipped": skipped}
    for k, rs in sorted(groups.items()):
        ident, mixed, _ = arm_of(rs)
        if mixed:
            raise MixedArm(f"control arm {k} is mixed: " + " | ".join(mixed))
        nums = {}
        names = set()
        for r in rs:
            names |= set(numbers_of(r))
        for name in sorted(names):
            stage, direction = numbers_of(rs[0]).get(name, NUMBERS.get(name, ("fast", +1)))
            at_cap = [r.get("run_id") for r in rs if capped(r, name)]
            vals = [number_value(r, name) for r in rs if not capped(r, name)]
            vals = [v for v in vals if v is not None]
            if not vals and not at_cap:
                nums[name] = {"stage": stage, "direction": direction, "values": [], "measured": False}
                continue
            nums[name] = {"stage": stage, "direction": direction, "measured": True, "values": vals,
                          "mean": round(st.mean(vals), 3) if vals else None,
                          "sd": round(st.stdev(vals), 3) if len(vals) > 1 else 0.0,
                          "min": min(vals) if vals else None, "max": max(vals) if vals else None,
                          "floor": round(max(vals) - min(vals), 3) if vals else None}
            if at_cap:
                nums[name].update(usable=False, why=f"control start(s) at the counter's cap: {', '.join(at_cap)}; "
                                                    "the control's own value is unknown")
        out["keys"][k] = {"n": len(rs), "runs": [r.get("run_id") for r in rs], "arm": ident, "numbers": nums}
    return out


def noise_of_mean(ctrl: dict, n_cand: int) -> float:
    """The noise a difference of means is read against: 2 x sd x sqrt(1/n_control + 1/n_candidate)."""
    a = ctrl["values"]
    sd = st.stdev(a) if len(a) > 1 else 0.0
    return 2.0 * sd * math.sqrt(1.0 / len(a) + 1.0 / n_cand)


def judge_number(ctrl: dict, cand_vals: list[float], n_capped: int = 0) -> dict:
    """One number: candidate values against the control's entry from floors.json. n_capped of cand_vals are a
    counter's cap (a lower bound)."""
    if not ctrl.get("measured") or not cand_vals:
        return {"verdict": "not measured"}
    if ctrl.get("usable") is False:
        return {"verdict": "unusable", "detail": ctrl.get("why", "")}
    a, b, d = ctrl["values"], cand_vals, ctrl["direction"]
    diff = st.mean(b) - st.mean(a)
    worse_by = -diff * d               # > 0 means worse
    p = perm_p(a, b) if len(a) + len(b) > 2 and len(a) > 0 and len(b) > 0 else 1.0
    noise = noise_of_mean(ctrl, len(b))
    worst_ctrl = min(x * d for x in a)                         # the control's worst start, on the "higher is better" scale
    all_beyond = all(x * d < worst_ctrl for x in b)            # every candidate start worse than every control start
    if worse_by > 0 and (worse_by > noise or all_beyond):
        if p < 0.05:
            verdict = "worse (real)"
        elif worse_by > noise:
            verdict = "worse (likely)" if p < 0.2 else "worse beyond the noise, not yet shown"
        else:
            verdict = "within the noise"
    elif -worse_by > noise:
        verdict = "better (real)" if p < 0.05 else ("better (likely)" if p < 0.2 else "better beyond the noise, not yet shown")
    else:
        verdict = "within the noise"
    out = {"verdict": verdict, "control_mean": ctrl["mean"], "candidate_mean": round(st.mean(b), 3),
           "diff": round(diff, 3), "noise": round(noise, 3), "p": round(p, 3), "n_control": len(a), "n_candidate": len(b)}
    if n_capped:
        out["capped"] = n_capped
    return out


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
        ident, mixed, unverified = arm_of(rs)
        rep["arm"] = ident
        if mixed:
            rep.update(verdict="MIXED", why="the candidate arm pools different things; check each on its own: "
                                            + " | ".join(mixed))
            reports.append(rep)
            continue
        # Stage 1, survival first. A crash or a lost route counts against the candidate; a start quit before END, or
        # with a window's anchor skipped, says nothing about it and is left out (rerun it).
        status = {r.get("run_id"): start_status(r) for r in rs}
        failed = [f"{k} {v[0]}" for k, v in status.items() if v[0] in ("CRASHED", "LOST", "HUNG")]
        invalid = [k for k, v in status.items() if v[0] == "INVALID"]
        alive = [r for r in rs if status[r.get("run_id")][0] == "ok"]
        rep["stages"]["stable"].append({"number": "survival", "verdict": "ok" if not failed else "FAILED",
                                        "detail": f"{len(alive)} of {len(rs)} ran their route"
                                                  + (f"; failed: {', '.join(failed)}" if failed else "")
                                                  + (f"; invalid: {', '.join(invalid)}" if invalid else "")})
        for k in invalid:
            rep["notes"].append(f"INVALID {k}: {status[k][1]}")
        rep["valid_starts"] = len(alive)
        for name, ctrl in f["numbers"].items():
            vals = [v for v in (number_value(r, name) for r in alive) if v is not None]
            j = judge_number(ctrl, vals, sum(1 for r in alive if capped(r, name)))
            j["number"] = name
            rep["stages"][ctrl["stage"]].append(j)
        # Verdict in the agreed order. Only a test-backed "worse" moves the verdict (real: p < 0.05, likely: p < 0.2,
        # as in abcompare.py): beyond the noise alone happens to genuine control starts (leave-one-out, 18 Nov: 6 of
        # 16 had a "watch"), so it is reported as "watch", not as a verdict.
        def bad(stage, verdicts):
            return [x for x in rep["stages"][stage] if x["verdict"] in verdicts]
        blocking = bad("stable", {"FAILED", "worse (real)"}) + bad("picture", {"worse (real)"})
        explain = (bad("stable", {"worse (likely)"}) + bad("picture", {"worse (likely)"})
                   + bad("fast", {"worse (real)", "worse (likely)"}) + bad("smooth", {"worse (real)", "worse (likely)"}))
        watch = [x["number"] for s in STAGES for x in rep["stages"][s]
                 if x["verdict"] == "worse beyond the noise, not yet shown"]
        unusable = [f"{x['number']} ({x['detail']})" for s in STAGES for x in rep["stages"][s] if x["verdict"] == "unusable"]
        # Is the arm complete? The 4-a-side rule, on the starts and on each stable number the floor gates on.
        short = []
        if len(alive) < MIN_STARTS:
            short.append(f"{len(alive)} valid candidate start(s)")
        if f["n"] < MIN_STARTS:
            short.append(f"a floor of {f['n']}")
        for name, ctrl in f["numbers"].items():
            if ctrl["stage"] != "stable" or not ctrl.get("measured") or ctrl.get("usable") is False:
                continue
            n_read = sum(1 for r in alive if number_value(r, name) is not None)
            if n_read < MIN_STARTS:
                short.append(f"{name} read on {n_read} of {len(alive)} start(s)")
            if len(ctrl["values"]) < MIN_STARTS:
                short.append(f"{name} on {len(ctrl['values'])} control start(s)")
        short += unverified
        if short:
            rep["provisional"] = "; ".join(short) + f": the rule is {MIN_STARTS} a side"
        # What a PASS could not clear: numbers the floor has no reading of, or can't use.
        not_cleared = sorted({f"{x['number']} ({'not measured' if x['verdict'] == 'not measured' else 'unusable'})"
                              for s in STAGES for x in rep["stages"][s]
                              if x["verdict"] in ("not measured", "unusable")})
        rep["not_cleared"] = not_cleared
        if blocking:
            rep["verdict"] = "BLOCK"
        elif not alive:
            rep["verdict"] = "INVALID"
        elif short:
            rep["verdict"] = "PROVISIONAL"
            rep["leaning"] = "EXPLAIN" if explain else "PASS"
        elif explain:
            rep["verdict"] = "EXPLAIN"
        else:
            rep["verdict"] = "PASS"
        if watch:
            rep["notes"].append("watch (beyond the noise, not shown by the test; add starts): " + ", ".join(watch))
        if unusable:
            rep["notes"].append("unusable for this key: " + "; ".join(unusable))
        unseen = sorted({x["number"] for s in STAGES for x in rep["stages"][s] if x["verdict"] == "not measured"})
        if unseen:
            rep["notes"].append("not measured: " + ", ".join(unseen))
        reports.append(rep)
    return reports


def print_report(reports: list[dict]) -> None:
    for rep in reports:
        print(f"== {rep.get('key')}  ({', '.join(str(x) for x in rep['runs'])})")
        if "stages" not in rep or rep.get("verdict") in ("NO FLOOR", "NO KEY", "MIXED"):
            print(f"   {rep['verdict']}: {rep.get('why')}\n")
            continue
        for s in STAGES:
            for x in rep["stages"][s]:
                if x["verdict"] in ("not measured", "unusable"):
                    continue
                if "control_mean" in x:
                    cm = (">=" if x.get("capped") else "") + str(x["candidate_mean"])
                    print(f"   {s:7s} {x['number']:34s} control {x['control_mean']:>9} cand {cm:>9} "
                          f"diff {x['diff']:+9} noise {x['noise']:>7}  p {x['p']:.3f}  {x['verdict']}")
                else:
                    print(f"   {s:7s} {x['number']:34s} {x['detail']}  {x['verdict']}")
        for n in rep["notes"]:
            print(f"   ({n})")
        line = f"   VERDICT: {rep['verdict']}"
        if rep["verdict"] == "PROVISIONAL":
            line += f" (leaning {rep['leaning']}): {rep['provisional']}"
        if rep["verdict"] in ("PASS", "PROVISIONAL") and rep.get("not_cleared"):
            line += "\n   NOT CLEARED (the gate could not measure these): " + ", ".join(rep["not_cleared"])
        print(line + "\n")


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
        try:
            fl = build_floors(rows)
        except MixedArm as e:
            print(f"refused: {e}", file=sys.stderr)
            return 3          # run ids only: no run_path, so the file carries no local paths
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
    return max((EXIT.get(r.get("verdict"), 3) for r in reps), default=3)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
