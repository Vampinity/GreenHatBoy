#!/usr/bin/env python3
"""build_v9.py V6_SCRIPT > v9: the baseline route with the camera swing at the house door removed. No picture check.

Why (17 Nov 2026): v8's door-view check never passed on the console (runBX1: best 55 against the 85 needed, in 82
looks, so Link turned in circles). Its fingerprint was cut from a PS5 capture, and a dark interior read from the
capture doesn't correlate with the same view read from the app's own frame (outdoor Kokiri fingerprints made the same
way score 67-89 live). Both captures (BC1, BD2) show Link loading in facing the door, so the check isn't needed for the
fix. The miss (BD2) came from the timed swing: ZL and the push came while the camera was still turning, and Link ran
in at an angle and stopped just left of the door.

v9 replaces v6 lines 110-114 with: ZL at 5.0 s (after "Saving..." clears), the same 4 s push at 6.5 s once the camera
has settled behind Link, and the same A Open MAYBE. The fallback, the A presses and the END are v6's.
"""
import sys
def main(v6):
    lines = open(v6).read().split("\n")
    assert lines[109].startswith("5.5 RSTICK 255 128 1500") and lines[113].startswith("9.5 MAYBE 5 LOOK 568 782"), "not v6"
    aopen = lines[113].split(" ", 3)[3]
    new = ["# v9 (17 Nov 2026): no camera swing and no picture check. Link loads in facing the door (BC1, BD2): ZL puts the",
           "# camera behind him, 1.5 s for it to settle, then v6's push and A Open check.",
           "5.0 ZL 200",
           "6.5 LSTICK 128 0 4000",
           f"6.5 MAYBE 5 {aopen}"]
    head = ["# zelda-first-start-watch-wait-30s.v9.txt: v6 with the house door's camera swing removed (build_v9.py)."]
    out = head + lines[:108] + [lines[108].replace("then the camera swing, ZL behind the player, run to the door (as the old route) [G].",
                                                     "then (v9) ZL, 1.5 s, run to the door.")] + new + lines[114:]
    sys.stdout.write("\n".join(out))
if __name__ == "__main__":
    main(sys.argv[1])
