#!/usr/bin/env python3
"""flashdet.py: find flashes in the saved frame grids, offline. SUPERSEDED -- read this first.

**Use `tools/Vampinity/flash-counter/count_flashes.py` in the shared repo instead.** It is a calibrated
objective flash meter that works on capture video, has its thresholds in `rule.py`, is validated against
the game's own light stretches, and has already run on 418 runs. This file was written in ignorance of
it. Its one lasting result is negative and still useful: the emulator's own 120x67 grid holds no signal
for this artefact at one-frame resolution, so do not build on the grids.

    flashdet.py score  RUNDIR [RUNDIR ...]        one line per run at the current thresholds
    flashdet.py sweep  RUNDIR [RUNDIR ...]        the same over a grid of thresholds
    flashdet.py frames RUNDIR                     the worst events in one run, with times

Why this exists (13 Nov 2026): the live flash counter (0928, EDEN_GBB_FLASH) does not work. From about
135 s into every run it flags 83-95% of frames, and it cannot separate a no-lookahead run from a
two-ahead-plus-read-sync run, so it is tracking camera motion rather than the artefact. But
EDEN_GBB_FLASH=2 also wrote every grid to disk, and those files are a real 120x67 brightness picture of
every presented frame. So the detector can be developed offline, against twelve runs with by-eye
verdicts, with no console and no rebuild.

What a flash is, as a test: a ONE-FRAME EXCURSION THAT REVERTS. Frame n differs from its neighbours and
frame n+1 comes back to where n-1 was. Requiring the revert is what the live counter never did -- 96% of
its events were labelled one-frame, but nothing checked that the picture returned, so an ordinary cut or
a camera turn counted.

File format (0928's Writer): "GBBFL1\\0\\0", then per frame u32 width, u32 height, u64 present, u64 ns,
then width*height brightness bytes, each (29B + 150G + 77R) / 256 over that cell.

Provenance: a run's grid file is the pid its own log names ("writing every grid to
.../gbb-flash-<pid>.bin"). The same filename appears in other run folders as a stale copy of an earlier
session, so never glob the folder -- always take the pid from the log.
"""

import argparse
import io
import os
import re
import struct
import sys

try:
    import numpy as np
except ImportError:
    np = None

HDR = struct.Struct("<IIQQ")
PID = re.compile(r"EDEN_GBB_FLASH: writing every grid to \S*gbb-flash-(\d+)\.bin")

# By-eye verdicts from the 12 Nov session, for scoring a detector against something.
BY_EYE = {
    "runDC1": "flash", "runDC2": "flash", "runDC3": "flash",
    "runDX1": "flash", "runDX2": "flash", "runDX3": "flash",
    "runDS1": "clean", "runDS2": "clean", "runDS3": "clean",
    "runDXS1": "clean", "runDXS2": "clean", "runDXS3": "clean",
}


def grid_path(rundir):
    """The grid file this run's own log names, not whatever is lying in logs/."""
    log = os.path.join(rundir, "eden_log.txt")
    if not os.path.exists(log):
        return None
    with io.open(log, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = PID.search(line)
            if m:
                p = os.path.join(rundir, "logs", f"gbb-flash-{m.group(1)}.bin")
                return p if os.path.exists(p) else None
    return None


def frames(path):
    """Yield (present, ns, grid) for every frame, streaming."""
    with io.open(path, "rb") as fh:
        if fh.read(8) != b"GBBFL1\0\0":
            return
        while True:
            hdr = fh.read(HDR.size)
            if len(hdr) < HDR.size:
                return
            w, h, present, ns = HDR.unpack(hdr)
            if w == 0 or h == 0 or w * h > 1 << 22:
                return
            body = fh.read(w * h)
            if len(body) < w * h:
                return
            yield present, ns, np.frombuffer(body, dtype=np.uint8).reshape(h, w)


def detect(path, excursion=4.0, revert=2.0, cell_delta=24, cell_revert=12, min_cells=4, skip_s=30.0):
    """Two detectors over the same stream.

    mean:  |mean(n) - (mean(n-1)+mean(n+1))/2| >= excursion, and |mean(n+1) - mean(n-1)| <= revert.
    cells: cells that move by >= cell_delta against n-1 AND are back within cell_revert at n+1,
           counted; a flash needs at least min_cells of them.

    The revert condition is the whole point: it is what separates an artefact from a scene change.
    """
    prev2 = prev1 = None
    t0 = None
    n = 0
    mean_hits, cell_hits = [], []
    for present, ns, g in frames(path):
        if t0 is None:
            t0 = ns
        t = (ns - t0) / 1e9
        gf = g.astype(np.int16)
        if prev2 is not None and t >= skip_s:
            n += 1
            a, b, c = prev2, prev1, gf  # n-1, n, n+1
            ma, mb, mc = float(a.mean()), float(b.mean()), float(c.mean())
            if abs(mb - (ma + mc) / 2.0) >= excursion and abs(mc - ma) <= revert:
                mean_hits.append((present - 1, t, mb - (ma + mc) / 2.0))
            moved = np.abs(b - a) >= cell_delta
            back = np.abs(c - a) <= cell_revert
            cnt = int(np.count_nonzero(moved & back))
            if cnt >= min_cells:
                cell_hits.append((present - 1, t, cnt))
        prev2, prev1 = prev1, gf
    return n, mean_hits, cell_hits


def cmd_score(args):
    print(f"{'run':9}{'eye':>7}{'frames':>8}{'mean hits':>11}{'per 1k':>8}{'cell hits':>11}{'per 1k':>8}")
    rows = []
    for rundir in args.rundirs:
        run = os.path.basename(rundir.rstrip("/"))
        p = grid_path(rundir)
        if p is None:
            print(f"{run:9}{'':>7}  no grid file named by this run's log")
            continue
        n, mh, ch = detect(p, args.excursion, args.revert, args.cell_delta,
                           args.cell_revert, args.min_cells, args.skip)
        eye = BY_EYE.get(run, "?")
        print(f"{run:9}{eye:>7}{n:8d}{len(mh):11d}{1000 * len(mh) / max(n, 1):8.1f}"
              f"{len(ch):11d}{1000 * len(ch) / max(n, 1):8.1f}")
        rows.append((run, eye, 1000 * len(mh) / max(n, 1), 1000 * len(ch) / max(n, 1)))
    verdict(rows)


def verdict(rows):
    """Does either detector separate the arms? Say so plainly, including when it does not."""
    for name, idx in (("mean", 2), ("cells", 3)):
        f = sorted(r[idx] for r in rows if r[1] == "flash")
        c = sorted(r[idx] for r in rows if r[1] == "clean")
        if not f or not c:
            continue
        gap = min(f) - max(c)
        print(f"\n  {name}: flashing {min(f):.1f}-{max(f):.1f} per 1k, clean {min(c):.1f}-{max(c):.1f}")
        if gap > 0:
            print(f"  {name}: SEPARATES — every flashing run above every clean one, gap {gap:.1f} per 1k")
        else:
            print(f"  {name}: does not separate — the ranges overlap by {-gap:.1f} per 1k")


def cmd_sweep(args):
    if np is None:
        print("numpy needed")
        return 1
    print("excursion/revert sweep on the whole-frame mean test\n")
    for exc in (2.0, 3.0, 4.0, 6.0, 8.0):
        for rev in (1.0, 2.0, 3.0):
            rows = []
            for rundir in args.rundirs:
                run = os.path.basename(rundir.rstrip("/"))
                p = grid_path(rundir)
                if p is None:
                    continue
                n, mh, _ = detect(p, exc, rev, args.cell_delta, args.cell_revert,
                                  args.min_cells, args.skip)
                rows.append((run, BY_EYE.get(run, "?"), 1000 * len(mh) / max(n, 1), 0.0))
            f = [r[2] for r in rows if r[1] == "flash"]
            c = [r[2] for r in rows if r[1] == "clean"]
            if not f or not c:
                continue
            gap = min(f) - max(c)
            mark = "SEPARATES" if gap > 0 else f"overlap {-gap:5.1f}"
            print(f"  excursion {exc:4.1f}  revert {rev:3.1f}  "
                  f"flash {min(f):6.1f}-{max(f):6.1f}  clean {min(c):6.1f}-{max(c):6.1f}  {mark}")
    return 0


def cmd_frames(args):
    p = grid_path(args.rundirs[0])
    if p is None:
        print("no grid file named by this run's log")
        return 1
    n, mh, ch = detect(p, args.excursion, args.revert, args.cell_delta,
                       args.cell_revert, args.min_cells, args.skip)
    print(f"{os.path.basename(args.rundirs[0].rstrip('/'))}: {n} frames tested")
    print(f"\n  whole-frame mean events ({len(mh)}):")
    for present, t, d in sorted(mh, key=lambda x: -abs(x[2]))[:15]:
        print(f"    present {present:6d}  t={t:7.1f}s  mean moved {d:+6.1f} and came back")
    print(f"\n  cell events ({len(ch)}):")
    for present, t, cnt in sorted(ch, key=lambda x: -x[2])[:15]:
        print(f"    present {present:6d}  t={t:7.1f}s  {cnt:5d} cells moved and came back")
    return 0


def main():
    if np is None:
        print("numpy is needed")
        return 1
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("score", cmd_score), ("sweep", cmd_sweep), ("frames", cmd_frames)):
        q = sub.add_parser(name)
        q.add_argument("rundirs", nargs="+")
        q.add_argument("--excursion", type=float, default=4.0)
        q.add_argument("--revert", type=float, default=2.0)
        q.add_argument("--cell-delta", type=int, default=24)
        q.add_argument("--cell-revert", type=int, default=12)
        q.add_argument("--min-cells", type=int, default=4)
        q.add_argument("--skip", type=float, default=30.0)
        q.set_defaults(fn=fn)
    a = ap.parse_args()
    return a.fn(a) or 0


if __name__ == "__main__":
    sys.exit(main())
