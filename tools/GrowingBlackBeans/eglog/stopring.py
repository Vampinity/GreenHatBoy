"""stopring.py RUN [RUN ...] (17 Nov 2026): stopdrift.py for the control. Per-stop ring words a frame from control logs (no EDEN_GBB_VITALS): GPU split lines (10 s) and nx2:vi2 5 s fps,
inside each stop's script window (wait lines 82/83 ... 268/269), script clock + EDEN_GUEST_START."""
import re, sys, pathlib, statistics as st
STOPS = {"A": (82, 83), "B": (144, 145), "C": (206, 207), "D": (268, 269)}


def stops_from_script(folder):
    """The stand windows from the run's own script.txt: each stand is a pair of 'MAYBE 1 LOOK' lines (the
    fingerprints at its start and end), so v2 (17 Nov), whose lines moved, reads right too."""
    import os
    p = os.path.join(folder, "script.txt")
    if not os.path.exists(p):
        return STOPS
    marks = [n for n, l in enumerate(open(p, errors="replace"), 1) if " MAYBE 1 LOOK " in l and not l.lstrip().startswith("#")]
    if len(marks) != 8:
        return STOPS
    return {k: (marks[2 * i], marks[2 * i + 1]) for i, k in enumerate("ABCD")}
res = {}
for run in sys.argv[1:]:
    run = pathlib.Path(run); log = (run / "eden_log.txt").read_text(errors="replace")
    err = next(p for p in (run / "stderr.log", run / "logs/stderr.log") if p.exists()).read_text(errors="replace")
    off = float(re.search(r"\[\s*([\d.]+)\][^\n]*EDEN_GUEST_START", log)[1])
    marks = {int(l): float(t) + off for l, t in re.findall(r"wait_\w+ line=(\d+) at=([\d.]+)", err)}
    split = [(float(t), int(w)) for t, w in re.findall(r"\[\s*([\d.]+)\][^\n]*GPU split per second: back idle [\d.]+ ms, (\d+) ring words", log)]
    fps = [(float(t), float(f)) for t, f in re.findall(r"\[\s*([\d.]+)\][^\n]*nx2:vi2 5 s: \d+ frames, ([\d.]+) fps", log)]
    row = {}
    for s, (a, b) in stops_from_script(str(run)).items():
        t0, t1 = marks[a], marks[b]
        w = [x for t, x in split if t0 + 5 <= t <= t1]; f = [x for t, x in fps if t0 + 5 <= t <= t1]
        row[s] = (st.mean(w) / st.mean(f), st.mean(f), len(w))
    res[run.name] = row
names = list(res)
print("stop " + "".join(f"{n:>24}" for n in names) + "   spread  verdict")
for s in STOPS:
    vals = [res[n][s][0] for n in names]
    cells = "".join(f"{res[n][s][0]:>12,.0f} {res[n][s][1]:5.1f}fps n{res[n][s][2]}" for n in names)
    sp = (max(vals) - min(vals)) / st.mean(vals) * 100 if len(vals) > 1 else float("nan")
    print(f"{s:4} {cells}  {sp:6.1f}%  {'same view' if sp <= 3 else 'NOT the same view'}")
