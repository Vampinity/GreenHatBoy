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

    def test_a_lost_start_blocks(self):
        rep = self.verdict([row("x1", 8.7), row("x2", 8.7, survived=False), row("x3", 8.8), row("x4", 8.6)])
        self.assertEqual(rep["verdict"], "BLOCK")

    def test_a_real_memory_loss_blocks(self):
        rep = self.verdict([row(f"x{i}", 8.7, low=100) for i in range(4)])
        self.assertEqual(rep["verdict"], "BLOCK")

    def test_one_slightly_worse_start_is_a_watch_not_a_verdict(self):
        """One start can't show anything (smallest p with 4 and 1 is 0.2): beyond the floor is only 'watch'."""
        rep = self.verdict([row("x1", 8.3)])
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


if __name__ == "__main__":
    unittest.main()
