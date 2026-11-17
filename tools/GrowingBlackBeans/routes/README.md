# zelda-first-start-watch-wait-30s.v7.txt — the baseline route, with the door step retried

**v6's problem.** Ten starts of Vampinity's `zelda-first-start-watch-wait-30s.v6.txt` on a base PS5,
13.60, on the alpha T186 and its own `env.txt` (one line changed, `EDEN_GUEST_SWAP_AHEAD_MIB=2048`, as
the release notes prescribe for 13.x). Three never reached the house door, so three starts of about nine
minutes each scored nothing:

| start | line 114 (MAYBE) | line 117 (WAIT) | lowest fps, line 108 met → +11.5 s |
|---|---|---|---|
| 8 that reached the door | 98–99 | 98–99 | 15.2 – 22.9 |
| runCC4 | 20 skipped | **−14 timeout** | 11.2 |
| 17 Nov, first | 21 skipped | **10 timeout** | 12.7 |
| 17 Nov, second | 61 skipped | **60 timeout** | 16.7 |

Nothing sits between 61 and 98, so this is not a threshold to widen: Link is not at the door. Two of the
three failures dipped to 11–13 fps across the `ZL` and the start of the push, below anything the eight
good starts saw there; the third ran at a normal 16.7 and still missed, scoring 61 — near the door but
not square to it.

**Why that step and no other.** Lines 110–113 are the only open-loop part of the route:

    5.5 RSTICK 255 128 1500      swing the camera right
    7.2 RSTICK 0 128 1500        swing it back
    8.9 ZL 200                   put it behind Link
    9.5 LSTICK 128 0 4000        run forward for four seconds

Every other step waits on the screen (`LOOK`) or corrects itself against the minimap (`STEER`). Here the
camera angle is whatever 1500 ms of stick and one 200 ms `ZL` produced, and input is delivered per frame,
so at 11 fps those deliver roughly half the samples they do at 21. Then "forward" is not the direction
the route assumes. A single dropped `ZL` does the same thing at any frame rate, which is the third start.

**What v7 changes.** Two more rounds of the same idiom, and nothing else:

    # --- round 2
    0.5 ZL 200
    1.1 LSTICK 128 0 2500
    0.4 MAYBE 4 LOOK <the A Open fingerprint, v6's own>

Each round's `MAYBE` starts looking at +0.4, **before** that round's own `ZL` at +0.5 and push at +1.1.
A met `WAIT`/`MAYBE` drops the lines of its section that have not started (`test_harness.h`), so when the
prompt is already up the round is dropped unstarted and the start behaves exactly as v6 did. When it is
not up, the round re-centres the camera and pushes again, and the hard `WAIT` at the end is v6's.

**What is not changed.** Lines 1–114 are v6 byte for byte, round 1 included, as are the nine lines from
the door press on. The fingerprint is v6's. The scoring window — the door press, the fly-over, the stand
— is v6's content, on v6's definition.

**Scoring.** The hard door `WAIT` moved from line 117 to line 129, so the window needs re-anchoring.
This entry goes in `tools/stk/windows.json` when that file lands (PR #11):

```json
"new-game-v7": {
  "sha1": ["996dec64c0ec"],
  "names": ["zelda-first-start-watch-wait-30s.v7.txt"],
  "windows": {
    "village":      {"kind": "stamped", "anchor_line": 129, "from_s": 57, "to_s": 72, "stat": "mean"},
    "village_late": {"kind": "stamped", "anchor_line": 129, "from_s": 62, "to_s": 77, "stat": "mean"}
  }
}
```

Being a different script it is a different route key, so v7 rows do not pool with v6 rows until someone
decides they may. The case for deciding they may: the window's content is identical and the change is
confined to getting Link to the door. The case against: it is a different file, and the rule exists so
that nobody has to take that on trust. We would rather it be Vampinity's call than ours.

**State: linted, not yet run.** `lint.py` reads it as the harness does and it passes with 0 STEER lines.
It has not been on a console. The next baseline start here runs it, and this README gets the result.

**The stronger fix, for later.** Steering the door approach by minimap would remove the open loop
altogether rather than retrying it, and the minimap works indoors — the Kokiri route steers from the
house floor at 829,900. It needs the door's points from a recording (`steer-route.py`), which nobody has
cut yet, and a `STEER` timeout stops a script, so it would be a hard dependency on the minimap being
readable during the opening. That is worth proving before it replaces a retry that costs nothing.
