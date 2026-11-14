#!/usr/bin/env python3
"""Read a harness script the way test_harness.h (ocarina-dev-t120) does, for the commands we use.
A line it cannot read would stop the whole script on the console, so check before copying it over."""
import re, sys
BUTTONS = {"CROSS","CIRCLE","SQUARE","TRIANGLE","L1","R1","L2","R2","L3","R3","OPTIONS","CREATE","TOUCHPAD",
           "UP","DOWN","LEFT","RIGHT","A","B","X","Y","L","R","ZL","ZR","PLUS","MINUS","LEFT_STICK","RIGHT_STICK"}
INT = re.compile(r"\d+$"); SEC = re.compile(r"\d+(\.\d+)?$")
def num(w, hi): return INT.match(w) and 0 <= int(w) <= hi
bad = 0; steers = 0
for n, raw in enumerate(open(sys.argv[1]), 1):
    line = raw.split("#")[0].split()
    if not line: continue
    err = None
    if not SEC.match(line[0]): err = "bad seconds"
    elif len(line) < 2: err = "no command"
    else:
        c = line[1]
        if c in ("LSTICK", "RSTICK"):
            if len(line) != 5 or not all(num(w, 255) for w in line[2:4]) or not INT.match(line[4]): err = "stick: x y 0-255, hold ms"
        elif c in ("WAIT", "MAYBE"):
            if len(line) not in (9, 10) or not SEC.match(line[2]) or line[3] not in ("LOOK", "GONE"): err = "wait form"
            else:
                if not all(num(w, 1000) for w in line[4:8]): err = "region 0-1000"
                m = re.match(r"(\d+)x(\d+):([0-9a-f]+)$", line[8])
                if not m or len(m.group(3)) != 2 * int(m.group(1)) * int(m.group(2)) or int(m.group(1)) * int(m.group(2)) > 256: err = "grid"
                if len(line) == 10 and not (num(line[9], 100) and int(line[9]) > 0): err = "min 1-100"
        elif c == "STEER":
            steers += 1
            ws = line[3:]; r = ws[-1] if ws and ws[-1].startswith("r=") and len(ws) > 1 else None
            ptsw = ws[:-1] if r else ws
            if not SEC.match(line[2]) or float(line[2]) == 0: err = "timeout"
            elif r and not (num(r[2:], 100) and int(r[2:]) > 0): err = "r=1-100"
            elif not 1 <= len(ptsw) <= 64: err = "1-64 points"
            elif not all("," in p and all(num(v, 1000) for v in p.split(",", 1)) for p in ptsw): err = "points must be whole x,y in 0-1000"
        elif c == "END":
            if len(line) != 2: err = "END takes nothing"
        elif c in BUTTONS:
            if len(line) != 3 or not INT.match(line[2]): err = "button hold ms"
        else: err = "unknown command"
    if err: bad += 1; print(f"line {n}: {err}: {' '.join(line)[:100]}")
print(f"{sys.argv[1]}: {'OK' if not bad else str(bad) + ' bad lines'} ({steers} STEER lines)")
sys.exit(1 if bad else 0)
