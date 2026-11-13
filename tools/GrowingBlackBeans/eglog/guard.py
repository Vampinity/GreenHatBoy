#!/usr/bin/env python3
"""guard.py: read the copy guard's own counters, which no tool has ever read.

    guard.py show    RUNDIR [RUNDIR ...]   per run: arming, exposure, two-frame evidence
    guard.py compare RUNDIR [RUNDIR ...]   the same as one table, with each run's arm from env.txt
    guard.py windows RUNDIR                per-window detail for one run

Why (13 Nov 2026): `EDEN_UP_AHEAD_GUARD` has printed two lines every 300 presents in 77 of our runs
since 9 Nov, and nothing read them. They answer, from the logs we already have, questions we spent
three days asking the wrong way:

  - Are both frames guarded with two frames in flight?  "armed N (M while one was still armed)".
    M is the presents that armed while a guard was still up, i.e. frames left unguarded.
  - Is the second slot being used?  "C copies served both slots, R reads took a newer frame's copy".
  - How exposed are we?  "of P pages first read with a guard up, U were not in it".

**Read the exposure figure carefully, because I got this wrong.** U counts pages read while
unprotected, where a guest write to one would go unseen. It does NOT say such a write happened, so a
high U is not harm and a low U is not safety. On 13 Nov I used U to rule out the copy guard as the
mechanism behind our flicker; that inference does not follow, and the direct test is
`EDEN_UP_AHEAD_GUARD_ALL_WRITES=1`, which removes the exposure and has never been set in any run.

Also: the aggregate exposure percentage is dominated by the load-in window (one spike of 21-31% around
75-80 s), so compare steady windows, which `show` does by default with --skip.
"""

import argparse
import io
import os
import re
import sys

TS = re.compile(r"^\[ *([0-9]+\.[0-9]+)\]")

ARM = re.compile(
    r"EDEN_UP_AHEAD_GUARD: last (\d+) presents \(to #(\d+)\): armed (\d+) "
    r"\((\d+) while one was still armed\)"
)
ARM_SLOTS = re.compile(r"(\d+) slots, (\d+) armed beside another")
ARM_WAITED = re.compile(r"(\d+) writes waited, ([\d.]+) us each")
ARM_LIFTED = re.compile(r"lifted early (\d+) \((\d+) for a waiting GPU channel\)")

COPIES = re.compile(
    r"EDEN_UP_AHEAD_GUARD copies: (\d+) pages copied before a write "
    r"\((\d+) a guard, most (\d+) of (\d+)\), the pool was full (\d+) times"
)
EXPOSED = re.compile(r"of (\d+) pages first read with a guard up, (\d+) were not in it")
BOTH = re.compile(r"(\d+) copies served both slots, (\d+) reads took a newer frame's copy")
OUTSIDE = re.compile(r"(\d+) pages outside the guard copied before a write")

ARM_SWITCHES = ("EDEN_UP_AHEAD_TWO", "EDEN_UP_AHEAD_GUARD_SLOTS", "EDEN_UP_AHEAD_GUARD",
                "EDEN_UP_AHEAD_READ_SYNC", "EDEN_GBB_READ_SYNC_ONCE",
                "EDEN_GBB_READ_SYNC_ESCAPE", "EDEN_UP_AHEAD_GUARD_ALL_WRITES",
                "EDEN_NX2_FRAMES_AHEAD")


def arm_of(rundir):
    """A short description of the frame-ahead arm, read from env.txt."""
    env = os.path.join(rundir, "env.txt")
    if not os.path.exists(env):
        return "?"
    vals = {}
    with io.open(env, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.strip().partition("=")
            if k in ARM_SWITCHES:
                vals[k] = v
    if vals.get("EDEN_NX2_FRAMES_AHEAD") == "0":
        return "no ahead"
    parts = ["2 ahead" if vals.get("EDEN_UP_AHEAD_TWO") == "1" else "1 ahead"]
    if vals.get("EDEN_UP_AHEAD_GUARD_SLOTS") == "2":
        parts.append("2 slots")
    if vals.get("EDEN_UP_AHEAD_READ_SYNC") == "1":
        parts.append("read sync")
    if vals.get("EDEN_GBB_READ_SYNC_ONCE") == "1":
        parts.append("once")
    if "EDEN_GBB_READ_SYNC_ESCAPE" in vals:
        parts.append(f"escape {vals['EDEN_GBB_READ_SYNC_ESCAPE']}us")
    if vals.get("EDEN_UP_AHEAD_GUARD_ALL_WRITES") == "1":
        parts.append("ALL_WRITES")
    return " + ".join(parts)


def collect(rundir, skip=0.0):
    """Both guard lines, per window, from this run's log."""
    log = os.path.join(rundir, "eden_log.txt")
    if not os.path.exists(log):
        return None
    arm_rows, copy_rows = [], []
    with io.open(log, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = TS.match(line)
            t = float(m.group(1)) if m else None
            if t is not None and t < skip:
                continue
            a = ARM.search(line)
            if a:
                row = dict(t=t, presents=int(a.group(1)), to=int(a.group(2)),
                           armed=int(a.group(3)), overlaps=int(a.group(4)))
                s = ARM_SLOTS.search(line)
                row["slots"] = int(s.group(1)) if s else None
                row["beside"] = int(s.group(2)) if s else None
                w = ARM_WAITED.search(line)
                row["writes_waited"] = int(w.group(1)) if w else None
                lf = ARM_LIFTED.search(line)
                row["lifted"] = int(lf.group(1)) if lf else None
                row["lifted_gpu"] = int(lf.group(2)) if lf else None
                arm_rows.append(row)
                continue
            c = COPIES.search(line)
            if c:
                row = dict(t=t, copied=int(c.group(1)), per_guard=int(c.group(2)),
                           pool_peak=int(c.group(3)), pool_size=int(c.group(4)),
                           pool_full=int(c.group(5)))
                e = EXPOSED.search(line)
                row["read_with_guard"] = int(e.group(1)) if e else None
                row["not_in_guard"] = int(e.group(2)) if e else None
                b = BOTH.search(line)
                row["both_slots"] = int(b.group(1)) if b else None
                row["newer_copy"] = int(b.group(2)) if b else None
                o = OUTSIDE.search(line)
                row["outside_copied"] = int(o.group(1)) if o else None
                copy_rows.append(row)
    if not arm_rows and not copy_rows:
        return None
    return dict(run=os.path.basename(rundir.rstrip("/")), arm=arm_of(rundir),
                arms=arm_rows, copies=copy_rows)


def totals(data):
    a, c = data["arms"], data["copies"]
    def s(rows, key):
        vals = [r[key] for r in rows if r.get(key) is not None]
        return sum(vals) if vals else None
    out = dict(
        windows=len(a),
        armed=s(a, "armed"), overlaps=s(a, "overlaps"), beside=s(a, "beside"),
        writes_waited=s(a, "writes_waited"), lifted=s(a, "lifted"),
        copied=s(c, "copied"), outside_copied=s(c, "outside_copied"),
        read_with_guard=s(c, "read_with_guard"), not_in_guard=s(c, "not_in_guard"),
        both_slots=s(c, "both_slots"), newer_copy=s(c, "newer_copy"),
        pool_peak=max([r["pool_peak"] for r in c], default=None),
        pool_size=c[0]["pool_size"] if c else None,
        pool_full=s(c, "pool_full"),
        slots=next((r["slots"] for r in a if r.get("slots") is not None), None),
    )
    rg, nig = out["read_with_guard"], out["not_in_guard"]
    out["exposed_pct"] = (100.0 * nig / rg) if rg else None
    return out


def cmd_show(args):
    for rundir in args.rundirs:
        data = collect(rundir, args.skip)
        if data is None:
            print(f"\n{os.path.basename(rundir.rstrip('/'))}: no guard lines (guard off, or run not done)")
            continue
        t = totals(data)
        print(f"\n=== {data['run']} — {data['arm']} ===")
        print(f"  windows after t={args.skip:.0f}s: {t['windows']}  (300 presents each)")
        print(f"  arming:    {t['armed']:,} presents armed, "
              f"**{t['overlaps']:,} while one was still armed** (frames left unguarded)")
        if t["slots"] is not None:
            print(f"  slots:     {t['slots']}, {t['beside']:,} armed beside another")
        if t["both_slots"] is not None:
            print(f"  two in flight: {t['both_slots']:,} copies served both slots, "
                  f"{t['newer_copy']:,} reads took a newer frame's copy")
        if t["exposed_pct"] is not None:
            print(f"  exposure:  {t['not_in_guard']:,} of {t['read_with_guard']:,} pages first read "
                  f"with a guard up were not in it ({t['exposed_pct']:.2f}%)")
            print(f"             exposure is not harm — see this file's header")
        print(f"  copies:    {t['copied']:,} pages copied before a write; pool peak "
              f"{t['pool_peak']} of {t['pool_size']}, full {t['pool_full']} times")
        print(f"  waits:     {t['writes_waited']:,} writes waited, {t['lifted']:,} guards lifted early")


def cmd_compare(args):
    rows = []
    for rundir in args.rundirs:
        data = collect(rundir, args.skip)
        if data is None:
            continue
        rows.append((data["run"], data["arm"], totals(data)))
    if not rows:
        print("no runs with guard lines")
        return 1
    print(f"{'run':9}{'arm':34}{'unguarded':>10}{'beside':>8}{'newer copy':>11}{'exposed':>9}")
    for run, arm, t in rows:
        pct = t["exposed_pct"]
        pct_text = "-" if pct is None else f"{pct:.2f}%"
        print(f"{run:9}{arm[:33]:34}{t['overlaps']:10,}{(t['beside'] or 0):8,}"
              f"{(t['newer_copy'] or 0):11,}{pct_text:>9}")
    print(f"\n  unguarded = presents that armed while a guard was still up: the one-slot gap 0927 fixed.")
    print(f"  beside / newer copy = evidence two frames really were in flight.")
    print(f"  exposed = pages read unprotected. NOT harm. The direct test is ALL_WRITES, never run.")
    return 0


def cmd_windows(args):
    data = collect(args.rundirs[0], args.skip)
    if data is None:
        print("no guard lines")
        return 1
    print(f"=== {data['run']} — {data['arm']} ===")
    print(f"  {'t':>7}{'armed':>7}{'unguard':>8}{'beside':>8}{'read w/ guard':>14}{'not in it':>10}{'%':>7}")
    for a, c in zip(data["arms"], data["copies"]):
        rg, nig = c.get("read_with_guard"), c.get("not_in_guard")
        pct = (100.0 * nig / rg) if rg else float("nan")
        print(f"  {a['t']:7.1f}{a['armed']:7d}{a['overlaps']:8d}{(a['beside'] or 0):8d}"
              f"{(rg or 0):14,}{(nig or 0):10,}{pct:6.2f}%")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("show", cmd_show), ("compare", cmd_compare), ("windows", cmd_windows)):
        q = sub.add_parser(name)
        q.add_argument("rundirs", nargs="+")
        q.add_argument("--skip", type=float, default=110.0,
                       help="drop windows before this (default 110: the load-in spike sits at 75-80 s)")
        q.set_defaults(fn=fn)
    a = ap.parse_args()
    return a.fn(a) or 0


if __name__ == "__main__":
    sys.exit(main())
