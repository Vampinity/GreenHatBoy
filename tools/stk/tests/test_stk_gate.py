"""Tests for stk_gate.py on made-up rows: the key, the floor, each stage, and the verdict order."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import stk_gate  # noqa: E402


def row(run, fps, low=300, route="r-v1", cache="cold", survived=True, flashes=None, worst=30000.0, **kw):
    r = {"run_id": run, "route_key": route, "firmware": "13.60", "cache_class": cache, "control_eligible": True,
         "survival_result": "completed" if survived else "stopped_early", "crash_class": "none",
         "route_completed": True, "win_lap_fps": fps, "fps_median": fps + 4, "largest_free_block_min_mib": low,
         "largest_free_block_driver_min_mib": low + 40, "radv_oom_events": 0, "flashes_per_min": flashes,
         "hitch_ms_per_min": None, "worst_frame_ms": worst, "shader_store": "prep_x", "store_pipelines": 0}
    r.update(kw)
    return r


CONTROL = [row("c1", 8.5), row("c2", 8.7), row("c3", 8.9), row("c4", 8.8)]


class Key(unittest.TestCase):
    def test_build_is_not_in_the_key(self):
        self.assertEqual(stk_gate.gate_key(row("a", 8, build_key="X")), stk_gate.gate_key(row("b", 8, build_key="Y")))

    def test_warm_key_carries_store_and_count(self):
        self.assertTrue(stk_gate.gate_key(row("a", 8, cache="warm", store_pipelines=78723)).endswith("|prep_x|78723"))

    def test_half_warm_has_no_key(self):
        self.assertIsNone(stk_gate.gate_key(row("a", 8, cache="half")))


class Floors(unittest.TestCase):
    def test_floor_is_the_control_spread(self):
        f = stk_gate.build_floors(CONTROL)["keys"]["r-v1|13.60|cold"]
        self.assertEqual(f["n"], 4)
        self.assertAlmostEqual(f["numbers"]["win_lap_fps"]["floor"], 0.4)
        self.assertFalse(f["numbers"]["hitch_ms_per_min"]["measured"])

    def test_ineligible_controls_are_left_out(self):
        fl = stk_gate.build_floors(CONTROL + [row("bad", 5.0, control_eligible=False)])
        self.assertEqual(fl["keys"]["r-v1|13.60|cold"]["n"], 4)
        self.assertEqual(fl["skipped"][0]["run"], "bad")


class Verdicts(unittest.TestCase):
    def setUp(self):
        self.floors = stk_gate.build_floors(CONTROL)

    def verdict(self, cands):
        return stk_gate.check(cands, self.floors)[0]

    def test_same_as_control_passes(self):
        rep = self.verdict([row("x1", 8.6), row("x2", 8.8), row("x3", 8.7), row("x4", 8.75)])
        self.assertEqual(rep["verdict"], "PASS")
        self.assertNotIn("provisional", rep)
        self.assertIn("not measured", rep["notes"][0])

    def test_slower_needs_explaining(self):
        rep = self.verdict([row("x1", 7.6), row("x2", 7.7), row("x3", 7.8), row("x4", 7.65)])
        self.assertEqual(rep["verdict"], "EXPLAIN")
        lap = [x for x in rep["stages"]["fast"] if x["number"] == "win_lap_fps"][0]
        self.assertEqual(lap["verdict"], "worse (real)")

    def test_faster_passes(self):
        rep = self.verdict([row("x1", 11.0), row("x2", 11.2), row("x3", 11.1), row("x4", 11.3)])
        self.assertEqual(rep["verdict"], "PASS")

    def test_a_lost_route_blocks(self):
        lost = row("x2", 8.7, route_completed=False, route_result="failed", route_reason="steer_timeout line=48")
        rep = self.verdict([row("x1", 8.7), lost, row("x3", 8.8), row("x4", 8.6)])
        self.assertEqual(rep["verdict"], "BLOCK")

    def test_a_crash_blocks(self):
        rep = self.verdict([row("x1", 8.7), row("x2", 8.7, survival_result="crashed", crash_class="oom"),
                            row("x3", 8.8), row("x4", 8.6)])
        self.assertEqual(rep["verdict"], "BLOCK")

    def test_quit_before_end_is_invalid_not_block(self):
        """Review point 5 (KV3, LV5, FC1): every leg met, the app closed normally, only END not reached."""
        rep = self.verdict([row("x1", 8.7), row("x2", 8.7, survived=False), row("x3", 8.8), row("x4", 8.6)])
        self.assertEqual(rep["verdict"], "PASS")
        self.assertEqual(rep["valid_starts"], 3)
        self.assertIn("provisional", rep)
        self.assertTrue(any(n.startswith("INVALID x2") for n in rep["notes"]))

    def test_a_skipped_anchor_is_invalid(self):
        """Review point 4: a window placed by a skipped MAYBE is not scored, and the start is rerun."""
        rep = self.verdict([row("x1", 8.7, anchors_skipped=["field:54"])])
        self.assertEqual(rep["verdict"], "INVALID")

    def test_a_two_start_candidate_is_provisional_and_cannot_be_real(self):
        rep = self.verdict([row("x1", 7.0), row("x2", 7.1)])
        self.assertIn("provisional", rep)
        lap = [x for x in rep["stages"]["fast"] if x["number"] == "win_lap_fps"][0]
        self.assertGreaterEqual(lap["p"], 0.05)       # 4 v 2: the smallest p is 2/15
        self.assertEqual(lap["verdict"], "worse (likely)")

    def test_a_real_memory_loss_blocks(self):
        rep = self.verdict([row(f"x{i}", 8.7, low=100) for i in range(4)])
        self.assertEqual(rep["verdict"], "BLOCK")

    def test_one_slightly_worse_start_is_a_watch_not_a_verdict(self):
        """One start can't show anything (smallest p with 4 and 1 is 0.4): beyond the noise is only 'watch'."""
        rep = self.verdict([row("x1", 8.2)])
        self.assertEqual(rep["verdict"], "PASS")
        self.assertTrue(any(n.startswith("watch") and "win_lap_fps" in n for n in rep["notes"]))

    def test_fewer_than_four_is_provisional(self):
        rep = self.verdict([row("x1", 8.7)])
        self.assertIn("provisional", rep)

    def test_no_floor_for_another_route(self):
        rep = self.verdict([row("x1", 8.7, route="other")])
        self.assertEqual(rep["verdict"], "NO FLOOR")

    def test_flashes_when_measured_are_a_gate(self):
        floors = stk_gate.build_floors([row(f"c{i}", 8.7 + i / 10, flashes=0.1 * (i % 2)) for i in range(4)])
        rep = stk_gate.check([row(f"x{i}", 8.8, flashes=5.0 + i / 10) for i in range(4)], floors)[0]
        self.assertEqual(rep["verdict"], "BLOCK")


class ReviewPoints(unittest.TestCase):
    """PR #18 review (Vampinity, 18 Nov), points 1-3, on the real floors' numbers."""

    def floors(self, lows, oom=None):
        return stk_gate.build_floors([row(f"c{i}", 8.7, low=v, radv_oom_events=(oom[i] if oom else 0))
                                      for i, v in enumerate(lows)])

    def mem(self, rep):
        return [x for x in rep["stages"]["stable"] if x["number"] == "largest_free_block_min_mib"][0]

    def test_point1_four_starts_below_the_worst_control_block(self):
        """Baseline control 321/362/165/335 MiB: a candidate at 120-150 on all four passed against one start's
        spread (197). Against the noise of a mean it is worse, and p = 0.029."""
        fl = self.floors([321, 362, 165, 335])
        rep = stk_gate.check([row(f"x{i}", 8.7, low=v) for i, v in enumerate([120, 130, 140, 150])], fl)[0]
        self.assertEqual(self.mem(rep)["verdict"], "worse (real)")
        self.assertEqual(rep["verdict"], "BLOCK")

    def test_point2_zero_on_every_start_blocks_on_the_later_area(self):
        fl = self.floors([17, 18, 3, 9])
        rep = stk_gate.check([row(f"x{i}", 8.7, low=0) for i in range(4)], fl)[0]
        self.assertEqual(self.mem(rep)["verdict"], "worse (real)")
        self.assertEqual(rep["verdict"], "BLOCK")

    def test_point2_a_control_already_at_zero_cannot_show_a_loss(self):
        """Field census 1/1/0/1: a candidate at 0 can't be shown worse (a control start is at 0 too)."""
        fl = self.floors([1, 1, 0, 1])
        rep = stk_gate.check([row(f"x{i}", 8.7, low=0) for i in range(4)], fl)[0]
        self.assertNotIn("real", self.mem(rep)["verdict"])

    def test_point3_a_capped_control_makes_the_number_unusable(self):
        fl = self.floors([300] * 4, oom=[9, 10, ">=64", 10])
        e = fl["keys"]["r-v1|13.60|cold"]["numbers"]["radv_oom_events"]
        self.assertFalse(e["usable"])
        self.assertEqual(e["values"], [9, 10, 10])
        rep = stk_gate.check([row(f"x{i}", 8.7, low=300, radv_oom_events=12) for i in range(4)], fl)[0]
        oom = [x for x in rep["stages"]["stable"] if x["number"] == "radv_oom_events"][0]
        self.assertEqual(oom["verdict"], "unusable")
        self.assertEqual(rep["verdict"], "PASS")
        self.assertTrue(any(n.startswith("unusable") for n in rep["notes"]))

    def test_point3_a_capped_candidate_counts_as_worse(self):
        fl = self.floors([300] * 4, oom=[9, 10, 11, 10])
        rep = stk_gate.check([row(f"x{i}", 8.7, low=300, radv_oom_events=">=64") for i in range(4)], fl)[0]
        oom = [x for x in rep["stages"]["stable"] if x["number"] == "radv_oom_events"][0]
        self.assertEqual(oom["verdict"], "worse (real)")
        self.assertEqual(oom["capped"], 4)
        self.assertEqual(rep["verdict"], "BLOCK")


class SkippedAnchor(unittest.TestCase):
    """Review point 4, in the scorer: a window placed by a skipped line has no value, unless its lines are clock marks."""

    def setUp(self):
        import stk_score
        self.wv = stk_score.window_value
        self.vi = [(t, 0, 13.0) for t in range(100, 300, 5)]

    def test_a_skipped_anchor_gives_no_value(self):
        d = {"kind": "stamped", "anchor_line": 54, "from_s": 30, "to_s": 115, "stat": "median"}
        v, n, why = self.wv(d, self.vi, {}, None, {54})       # skipped lines are never in the met marks
        self.assertIsNone(v)
        self.assertEqual(why, "anchor_skipped_line_54")

    def test_a_met_anchor_still_scores(self):
        d = {"kind": "stamped", "anchor_line": 54, "from_s": 30, "to_s": 115, "stat": "median"}
        v, n, why = self.wv(d, self.vi, {54: 120.0}, None, set())
        self.assertEqual(v, 13.0)

    def test_clock_marks_may_be_skipped(self):
        d = {"kind": "between", "start_line": 83, "end_line": 84, "stat": "mean", "clock_marks": True}
        v, n, why = self.wv(d, self.vi, {83: 120.0, 84: 182.0}, None, {83, 84})
        self.assertEqual(v, 13.0)


if __name__ == "__main__":
    unittest.main()
