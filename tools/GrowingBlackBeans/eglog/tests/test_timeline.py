#!/usr/bin/env python3
"""Tests for timeline.py on a synthetic file. Run: python3 tests/test_timeline.py."""
import os, struct, sys, tempfile, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import timeline  # noqa: E402

def main():
    ms = 1_000_000
    first = 10_000 * ms
    ev = []
    def e(ns, t, th, a, b): ev.append(struct.pack("<QIIQ", ns, t | (th << 8), a, b))
    for k in range(4):                         # 4 presents 50 ms apart, fence (1, 100+k)
        b0 = first + k * 50 * ms
        e(b0, 1, 1, k, (1 << 32) | (100 + k))
        e(b0 + 20 * ms, 2, 1, k, 20 * ms)
        e(b0 + 22 * ms, 3, 1, k, 0)
        e(b0 + 30 * ms, 5, 3, 5000, b0 + 5 * ms)        # back busy 25 ms
        e(b0 + 12 * ms, 4, 2, 17, b0 + 10 * ms)         # front wait 2 ms, dma snapshot miss
        e(b0 + 40 * ms, 6, 3, 1, 100 + k)               # fence signalled 40 ms after present
    data = b"GBBTL1\0\0" + struct.pack("<4Q", len(ev), first, first, first + 200 * ms) + b"".join(ev)
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(data)
    tl = timeline.read(f.name)
    fr = timeline.frames(tl)
    checks = [("events", len(tl["events"]) == 24), ("frames", len(fr) == 3),
              ("interval", fr[0]["interval_ms"] == 50.0), ("wait", fr[0]["present_wait_ms"] == 20.0),
              ("back busy", fr[0]["back_busy_ms"] == 25.0), ("front wait", fr[0]["front_wait_ms"] == 2.0),
              ("site", fr[0]["top_wait_site"] == "dma snapshot miss"),
              ("fence lag", fr[0]["fence_signalled_after_present_ms"] == 40.0),
              ("perfetto (present ends are not drawn)", len(timeline.perfetto(tl)["traceEvents"]) == 20)]
    os.unlink(f.name)
    for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
    return 0 if all(ok for _, ok in checks) else 1

if __name__ == "__main__":
    sys.exit(main())
