#!/usr/bin/env python3
"""timeline.py gbb-timeline-<pid>.bin [--perfetto out.json] [--frames out.csv]

Reads the EDEN_GBB_TIMELINE file (patch 0923) and answers, frame by frame, where the time went:

  present #N   interval to the next present, the present's wait, and on the GPU-thread side:
               back busy ms, front waits on the back (ms, count), shaders built, fence pops,
               and when the frame's own fence was signalled to the guest (fence lag after its present).

Prints a summary (medians, and the slowest frames in detail) and optionally writes a per-frame CSV and a
Perfetto / chrome://tracing JSON (open in ui.perfetto.dev) with one track per thread.

File: 8-byte magic "GBBTL1\\0\\0", 4 × u64 (events, first present ns, window start ns, window end ns), then
events of 24 bytes: u64 ns, u32 type | thread << 8, u32 a, u64 b (see video_core/gbb_trace.h). Standard library.
"""
import argparse
import bisect
import csv
import json
import statistics as st
import struct
import sys

EV = {1: "present_begin", 2: "present_waited", 3: "present_end", 4: "front_wait", 5: "back_busy",
      6: "guest_incr", 7: "fence_pop", 8: "pipeline"}
SITES = ["other", "ring full", "acquire", "fence release", "sem execute", "list writers", "list flush",
         "macro dma read", "map", "front start", "front verify", "acquire check", "acquire recheck", "acquire poll",
         "list gpu-written", "list first drain", "macro dma read ram", "dma snapshot miss", "dma snapshot check",
         "dma read ahead", "map on back", "back register", "back code", "dma snapshot writes"]


def read(path):
    data = open(path, "rb").read()
    if data[:6] != b"GBBTL1":
        raise ValueError("not a GBB timeline file")
    n, first, wstart, wend = struct.unpack_from("<4Q", data, 8)
    events = []
    off = 40
    for _ in range(n):
        ns, tt, a, b = struct.unpack_from("<QIIQ", data, off)
        off += 24
        events.append((ns, tt & 0xff, tt >> 8, a, b))
    events.sort()
    return {"first": first, "start": wstart, "end": wend, "events": events}


def spans(events, kind):
    """(start, end, a) for span events whose start is in b."""
    return [(b, ns, a) for ns, t, th, a, b in events if t == kind]


def overlap(sp, lo, hi):
    tot = 0
    for s, e, _ in sp:
        if e > lo and s < hi:
            tot += min(e, hi) - max(s, lo)
    return tot


def top_site(waits):
    """The drain site with the most wait time among (start, end, site) spans."""
    tot = {}
    for s, e, a in waits:
        name = SITES[a] if a < len(SITES) else str(a)
        tot[name] = tot.get(name, 0) + (e - s)
    return max(tot, key=tot.get) if tot else ""


def frames(tl):
    ev = tl["events"]
    pres = {}
    for ns, t, th, a, b in ev:
        if t in (1, 2, 3):
            pres.setdefault(a, {})[t] = (ns, b)
    order = sorted(n for n, d in pres.items() if 1 in d)
    incr = {}
    for ns, t, th, a, b in ev:
        if t == 6:
            incr.setdefault((a, b), ns)
    back, front, pipes = spans(ev, 5), spans(ev, 4), spans(ev, 8)
    pops = sorted(ns for ns, t, *_ in ev if t == 7)
    out = []
    for i, n in enumerate(order[:-1]):
        d = pres[n]
        begin, fence = d[1]
        nxt = pres[order[i + 1]][1][0]
        waited = d.get(2, (begin, 0))[0]
        fid, fval = fence >> 32, fence & 0xffffffff
        sig = incr.get((fid, fval))
        fw = [x for x in front if x[1] > begin and x[0] < nxt]
        out.append({
            "present": n, "t_s": round((begin - tl["first"]) / 1e9, 3),
            "interval_ms": round((nxt - begin) / 1e6, 2),
            "present_wait_ms": round((waited - begin) / 1e6, 2),
            "back_busy_ms": round(overlap(back, begin, nxt) / 1e6, 2),
            "front_wait_ms": round(overlap(front, begin, nxt) / 1e6, 2),
            "front_waits": len(fw),
            "top_wait_site": top_site(fw),
            "shaders_ms": round(overlap(pipes, begin, nxt) / 1e6, 2),
            "fence_pops": bisect.bisect_left(pops, nxt) - bisect.bisect_left(pops, begin),
            "fence_signalled_after_present_ms": round((sig - begin) / 1e6, 2) if sig else None,
        })
    return out


def perfetto(tl):
    out = []
    for ns, t, th, a, b in tl["events"]:
        ts = (ns - tl["first"]) / 1000.0
        if t in (4, 5, 8):
            name = {4: f"front wait: {SITES[a] if a < len(SITES) else a}", 5: f"back batch ({a} words)",
                    8: "shader build"}[t]
            out.append({"name": name, "ph": "X", "ts": (b - tl["first"]) / 1000.0, "dur": (ns - b) / 1000.0,
                        "pid": 1, "tid": th})
        elif t == 1:
            out.append({"name": f"present #{a}", "ph": "i", "s": "t", "ts": ts, "pid": 1, "tid": th})
        elif t == 2:
            out.append({"name": f"present wait #{a}", "ph": "X", "ts": ts - b / 1000.0, "dur": b / 1000.0,
                        "pid": 1, "tid": th})
        elif t == 6:
            out.append({"name": f"syncpoint {a} = {b}", "ph": "i", "s": "t", "ts": ts, "pid": 1, "tid": th})
        elif t == 7:
            out.append({"name": f"fence pop x{a}", "ph": "X", "ts": (b - tl["first"]) / 1000.0,
                        "dur": (ns - b) / 1000.0, "pid": 1, "tid": th})
    return {"traceEvents": out, "displayTimeUnit": "ms"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--perfetto")
    ap.add_argument("--frames")
    a = ap.parse_args()
    tl = read(a.file)
    fr = frames(tl)
    print(f"{len(tl['events'])} events, {len(fr)} frames, window {(tl['start'] - tl['first']) / 1e9:.1f}-"
          f"{(tl['end'] - tl['first']) / 1e9:.1f} s after the first present")
    if fr:
        med = lambda k: st.median(x[k] for x in fr if x[k] is not None) if any(x[k] is not None for x in fr) else None
        print("median per frame: " + ", ".join(f"{k} {med(k)}" for k in (
            "interval_ms", "present_wait_ms", "back_busy_ms", "front_wait_ms", "front_waits",
            "fence_signalled_after_present_ms")))
        print("\nslowest frames:")
        for x in sorted(fr, key=lambda x: -x["interval_ms"])[:10]:
            print("  " + ", ".join(f"{k}={v}" for k, v in x.items()))
    if a.frames and fr:
        with open(a.frames, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(fr[0].keys()))
            w.writeheader()
            w.writerows(fr)
    if a.perfetto:
        json.dump(perfetto(tl), open(a.perfetto, "w"))
        print(f"perfetto trace: {a.perfetto} (open in ui.perfetto.dev)")


if __name__ == "__main__":
    sys.exit(main())
