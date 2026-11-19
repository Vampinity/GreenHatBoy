"""Tests for stk_gate.py on made-up rows: the key, the floor, each stage, and the verdict order."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import stk_gate  # noqa: E402


def row(run, fps, low=300, route="r-v1", cache="cold", survived=True, flashes=None, worst=30000.0, **kw):
    r = {"run_id": run, "route_key": route, "firmware": "13.60", "cache_class": cache, "control_eligible": True,
         "survival_result": "completed" if survived else "stopped_early", "crash_class": "none",
         "route_completed": True, "end_kind": "app_closed", "win_lap_fps": fps, "fps_median": fps + 4, "largest_free_block_min_mib": low,
         "largest_free_block_driver_min_mib": low + 40, "radv_oom_events": 0, "flashes_per_min": flashes,
         "hitch_ms_per_min": None, "worst_frame_ms": worst, "shader_store": "prep_x", "store_pipelines": 0,
         "build_key": "01.219.028 (Nov 14 2026 23:24:15)", "env_hash": "57c08732c8ee", "translation_id": "t1",
         "script_sha1": "s1"}
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
        self.assertEqual(rep["verdict"], "PROVISIONAL")      # 3 valid: short of 4, not blocked
        self.assertEqual(rep["leaning"], "PASS")
        self.assertEqual(rep["valid_starts"], 3)
        self.assertIn("provisional", rep)
        self.assertTrue(any(n.startswith("INVALID x2") for n in rep["notes"]))

    def test_a_freeze_before_end_blocks(self):
        """Vampinity's second review: every required leg met, then the log stops in the load (MAYBEs only), with no
        crash file and no normal close. That is a freeze, not a quit, so it counts against the candidate."""
        hung = row("x2", 8.7, survived=False, end_kind="log_cut")
        rep = self.verdict([row("x1", 8.7), hung, row("x3", 8.8), row("x4", 8.6)])
        self.assertEqual(rep["verdict"], "BLOCK")
        surv = rep["stages"]["stable"][0]
        self.assertIn("x2 HUNG", surv["detail"])
        self.assertEqual(stk_gate.start_status(hung)[0], "HUNG")

    def test_a_skipped_anchor_is_invalid(self):
        """Review point 4: a window placed by a skipped MAYBE is not scored, and the start is rerun."""
        rep = self.verdict([row("x1", 8.7, anchors_skipped=["field:54"])])
        self.assertEqual(rep["verdict"], "INVALID")

    def test_a_two_start_candidate_is_provisional_and_cannot_be_real(self):
        rep = self.verdict([row("x1", 7.0), row("x2", 7.1)])
        self.assertEqual(rep["verdict"], "PROVISIONAL")
        self.assertEqual(rep["leaning"], "EXPLAIN")
        lap = [x for x in rep["stages"]["fast"] if x["number"] == "win_lap_fps"][0]
        self.assertGreaterEqual(lap["p"], 0.05)       # 4 v 2: the smallest p is 2/15
        self.assertEqual(lap["verdict"], "worse (likely)")

    def test_a_real_memory_loss_blocks(self):
        rep = self.verdict([row(f"x{i}", 8.7, low=100) for i in range(4)])
        self.assertEqual(rep["verdict"], "BLOCK")

    def test_one_slightly_worse_start_is_a_watch_not_a_verdict(self):
        """One start can't show anything (smallest p with 4 and 1 is 0.4): beyond the noise is only 'watch'."""
        rep = self.verdict([row("x1", 8.2)])
        self.assertEqual(rep["verdict"], "PROVISIONAL")
        self.assertEqual(rep["leaning"], "PASS")
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
        self.assertIn("radv_oom_events (unusable)", rep["not_cleared"])

    def test_point3_a_capped_candidate_counts_as_worse(self):
        fl = self.floors([300] * 4, oom=[9, 10, 11, 10])
        rep = stk_gate.check([row(f"x{i}", 8.7, low=300, radv_oom_events=">=64") for i in range(4)], fl)[0]
        oom = [x for x in rep["stages"]["stable"] if x["number"] == "radv_oom_events"][0]
        self.assertEqual(oom["verdict"], "worse (real)")
        self.assertEqual(oom["capped"], 4)
        self.assertEqual(rep["verdict"], "BLOCK")


class IncompleteAndMixedArms(unittest.TestCase):
    """waveydude's review of PR #18 at 281d22b (18 Nov): three cases that printed PASS and exited 0."""

    def setUp(self):
        self.floors = stk_gate.build_floors(CONTROL)

    def test_case1_one_start_is_provisional_not_pass(self):
        rep = stk_gate.check([row("x1", 8.7)], self.floors)[0]
        self.assertEqual(rep["verdict"], "PROVISIONAL")
        self.assertIn("1 valid candidate start", rep["provisional"])

    def test_case2_missing_memory_readings_are_provisional(self):
        gone = dict(largest_free_block_min_mib=None, largest_free_block_driver_min_mib=None, radv_oom_events=None)
        rep = stk_gate.check([row(f"x{i}", 8.7, **gone) for i in range(4)], self.floors)[0]
        self.assertEqual(rep["verdict"], "PROVISIONAL")
        for name in gone:
            self.assertIn(f"{name} read on 0 of 4", rep["provisional"])

    def test_case2_one_missing_reading_of_four_is_short_too(self):
        cands = [row(f"x{i}", 8.7) for i in range(3)] + [row("x3", 8.7, largest_free_block_min_mib=None)]
        rep = stk_gate.check(cands, self.floors)[0]
        self.assertEqual(rep["verdict"], "PROVISIONAL")
        self.assertIn("largest_free_block_min_mib read on 3 of 4", rep["provisional"])

    def test_case3_two_builds_in_one_arm_are_mixed(self):
        cands = [row("x1", 8.7), row("x2", 8.7), row("y1", 8.7, build_key="other"), row("y2", 8.7, build_key="other")]
        rep = stk_gate.check(cands, self.floors)[0]
        self.assertEqual(rep["verdict"], "MIXED")
        self.assertIn("build differs", rep["why"])
        self.assertIn("other (y1, y2)", rep["why"])

    def test_case3_two_settings_in_one_arm_are_mixed(self):
        cands = [row(f"x{i}", 8.7) for i in range(3)] + [row("x3", 8.7, env_hash="ffffffffffff")]
        rep = stk_gate.check(cands, self.floors)[0]
        self.assertEqual(rep["verdict"], "MIXED")
        self.assertIn("settings (env hash) differs", rep["why"])

    def test_control_and_candidate_may_differ(self):
        rep = stk_gate.check([row(f"x{i}", 8.7, build_key="cand", env_hash="e2") for i in range(4)], self.floors)[0]
        self.assertEqual(rep["verdict"], "PASS")

    def test_a_mixed_control_arm_is_refused(self):
        with self.assertRaises(stk_gate.MixedArm):
            stk_gate.build_floors(CONTROL[:3] + [row("c4", 8.8, build_key="other")])

    def test_the_floor_records_its_arm(self):
        self.assertEqual(self.floors["keys"]["r-v1|13.60|cold"]["arm"]["env_hash"], "57c08732c8ee")

    def test_an_unidentified_build_is_provisional(self):
        rep = stk_gate.check([row(f"x{i}", 8.7, build_key=None) for i in range(4)], self.floors)[0]
        self.assertEqual(rep["verdict"], "PROVISIONAL")
        self.assertIn("build not recorded on x0, x1, x2, x3", rep["provisional"])

    def test_one_missing_identity_field_is_provisional(self):
        """waveydude's second review: four valid rows, one identity field missing on the fourth, printed PASS."""
        for field, label in stk_gate.ARM_FIELDS.items():
            with self.subTest(field=field):
                cands = [row(f"x{i}", 8.7) for i in range(3)] + [row("x3", 8.7, **{field: None})]
                rep = stk_gate.check(cands, self.floors)[0]
                self.assertEqual(rep["verdict"], "PROVISIONAL")
                self.assertIn(f"{label} not recorded on x3", rep["provisional"])

    def test_a_control_missing_identity_makes_every_check_provisional(self):
        floors = stk_gate.build_floors(CONTROL[:3] + [row("c4", 8.8, env_hash=None)])
        self.assertEqual(floors["keys"]["r-v1|13.60|cold"]["arm_unverified"], ["settings (env hash) not recorded on c4"])
        rep = stk_gate.check([row(f"x{i}", 8.7) for i in range(4)], floors)[0]
        self.assertEqual(rep["verdict"], "PROVISIONAL")
        self.assertIn("control: settings (env hash) not recorded on c4", rep["provisional"])

    def test_a_crash_blocks_even_when_short(self):
        rep = stk_gate.check([row("x1", 8.7, survival_result="crashed", crash_class="oom")], self.floors)[0]
        self.assertEqual(rep["verdict"], "BLOCK")

    def test_pass_names_what_it_could_not_clear(self):
        rep = stk_gate.check([row(f"x{i}", 8.7) for i in range(4)], self.floors)[0]
        self.assertEqual(rep["verdict"], "PASS")
        self.assertIn("flashes_per_min (not measured)", rep["not_cleared"])
        self.assertIn("hitch_ms_per_min (not measured)", rep["not_cleared"])


class ExitCodes(unittest.TestCase):
    """The CLI's exit code: 0 only for PASS. waveydude: anything reading just the exit code must not see a short arm
    as cleared."""

    def run_check(self, cands):
        by_name = {r["run_id"]: r for r in cands}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(stk_gate.build_floors(CONTROL), fh)
        import stk_score
        with mock.patch.object(stk_score, "score_run", lambda path, env=None: by_name[path]), \
                contextlib.redirect_stdout(io.StringIO()):
            return stk_gate.main(["check", *by_name, "--floors", fh.name])

    def test_pass_exits_0(self):
        self.assertEqual(self.run_check([row(f"x{i}", 8.7) for i in range(4)]), 0)

    def test_provisional_exits_2(self):
        self.assertEqual(self.run_check([row("x1", 8.7)]), 2)

    def test_a_missing_env_hash_exits_2(self):
        self.assertEqual(self.run_check([row(f"x{i}", 8.7) for i in range(3)] + [row("x3", 8.7, env_hash=None)]), 2)

    def test_explain_exits_1(self):
        self.assertEqual(self.run_check([row(f"x{i}", 7.6 + i / 20) for i in range(4)]), 1)

    def test_mixed_exits_3(self):
        self.assertEqual(self.run_check([row("x1", 8.7), row("x2", 8.7), row("y1", 8.7, build_key="o"),
                                         row("y2", 8.7, build_key="o")]), 3)

    def test_block_exits_4_and_wins_over_another_key(self):
        cands = [row(f"x{i}", 8.7, low=100) for i in range(4)] + [row("z1", 8.7, route="other")]
        self.assertEqual(self.run_check(cands), 4)

    def test_floors_refuses_a_mixed_control(self):
        rows = {r["run_id"]: r for r in CONTROL[:3] + [row("c4", 8.8, build_key="other")]}
        import stk_score
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(stk_score, "score_run", lambda path, env=None: rows[path]), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(stk_gate.main(["floors", *rows, "-o", f"{d}/f.json"]), 3)


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


def warm(run, fps, own=3, total=4, known=80770, left=0, **kw):
    return row(run, fps, cache="warm", store_pipelines=80770, pipelines_known=known, left_to_prepare=left,
               own_records=own, total_pipeline_count=total, **kw)


WARM_CONTROL = [warm("w1", 19.0), warm("w2", 19.2), warm("w3", 19.1), warm("w4", 19.3)]
WKEY = "r-v1|13.60|warm|prep_x|80770"


class WarmBoot(unittest.TestCase):
    """The warm-state check (19 Nov): a warm start must boot in the prepared state, and in the control's."""

    def test_floor_records_the_control_boots(self):
        f = stk_gate.build_floors(WARM_CONTROL)["keys"][WKEY]
        self.assertEqual(f["warm_boot"], {"own 3 / total 4": ["w1", "w2", "w3", "w4"]})

    def test_floor_refuses_a_control_with_two_boots(self):
        with self.assertRaises(stk_gate.MixedArm):
            stk_gate.build_floors(WARM_CONTROL[:3] + [warm("w4", 19.3, own=36, total=37)])

    def test_floor_refuses_a_grown_own_cache_too(self):
        # Vampinity's 14-15 Nov warm runs: exactly N known, but 6,646-7,816 own records.
        with self.assertRaises(stk_gate.MixedArm):
            stk_gate.build_floors(WARM_CONTROL[:3] + [warm("w4", 19.3, own=6646, total=6647)])

    def test_floor_keeps_two_boots_when_allowed_on_purpose(self):
        f = stk_gate.build_floors(WARM_CONTROL[:3] + [warm("w4", 19.3, own=36, total=37)], {WKEY})["keys"][WKEY]
        self.assertEqual(f["n"], 4)
        self.assertEqual(f["warm_boot"]["own 36 / total 37"], ["w4"])
        self.assertTrue(f["warm_boot_mixed_on_purpose"])

    def test_control_without_boot_lines_is_unverified(self):
        f = stk_gate.build_floors(WARM_CONTROL[:3] + [warm("w4", 19.3, own=None)])["keys"][WKEY]
        self.assertIn("warm boot not recorded on w4", f["arm_unverified"])

    def test_candidate_arm_mixing_boots_is_mixed(self):
        cands = [warm(f"c{i}", 19.1) for i in range(3)] + [warm("c3", 19.1, own=36, total=37)]
        fl = stk_gate.build_floors(WARM_CONTROL[:3] + [warm("w4", 19.3, own=36, total=37)], {WKEY})
        rep = stk_gate.check(cands, fl)[0]
        self.assertEqual(rep["verdict"], "MIXED")

    def test_invalid_start_does_not_count_for_the_boot(self):
        cands = [warm(f"c{i}", 19.1 + i / 20) for i in range(4)] + [
            warm("bad", 19.1, own=820, total=821, survival_result="stopped_early")]
        rep = stk_gate.check(cands, stk_gate.build_floors(WARM_CONTROL))[0]
        # Counted, "bad" would make the arm MIXED (two boots); the verdict says it wasn't (Vampinity, PR #24).
        self.assertEqual(rep["verdict"], "PASS")
        self.assertNotIn("820", rep.get("why", "") + rep.get("provisional", ""))

    def test_floor_leaves_out_a_control_not_prepared(self):
        fl = stk_gate.build_floors(WARM_CONTROL + [warm("w5", 19.1, known=80798)])
        self.assertEqual(fl["keys"][WKEY]["n"], 4)
        self.assertIn("warm boot not prepared", fl["skipped"][0]["why"])

    def test_candidate_with_the_control_boot_passes(self):
        rep = stk_gate.check([warm(f"c{i}", 19.1 + i / 20) for i in range(4)], stk_gate.build_floors(WARM_CONTROL))[0]
        self.assertEqual(rep["verdict"], "PASS")

    def test_candidate_with_another_boot_is_provisional(self):
        cands = [warm(f"c{i}", 19.1, own=820, total=821) for i in range(4)]
        rep = stk_gate.check(cands, stk_gate.build_floors(WARM_CONTROL))[0]
        self.assertEqual(rep["verdict"], "PROVISIONAL")
        self.assertIn("c3 warm boot own 820 / total 821", rep["provisional"])

    def test_candidate_not_prepared_is_provisional(self):
        cands = [warm(f"c{i}", 19.1) for i in range(3)] + [warm("c3", 19.1, left=12)]
        rep = stk_gate.check(cands, stk_gate.build_floors(WARM_CONTROL))[0]
        self.assertEqual(rep["verdict"], "PROVISIONAL")
        self.assertIn("12 pipelines left to prepare", rep["provisional"])

    def test_old_floor_without_warm_boot_is_provisional(self):
        fl = stk_gate.build_floors(WARM_CONTROL)
        del fl["keys"][WKEY]["warm_boot"]
        rep = stk_gate.check([warm(f"c{i}", 19.1) for i in range(4)], fl)[0]
        self.assertEqual(rep["verdict"], "PROVISIONAL")
        self.assertIn("control warm boot not recorded", rep["provisional"])

    def test_cold_starts_are_untouched(self):
        rep = stk_gate.check([row(f"c{i}", 8.7) for i in range(4)], stk_gate.build_floors(CONTROL))[0]
        self.assertFalse(any("warm boot" in n for n in rep["notes"]))
        self.assertEqual(rep["verdict"], "PASS")


class AfterPR24(unittest.TestCase):
    """Vampinity's review of PR #24 (20 Nov): zero floors, stranded only at the wall, MIXED never hides a BLOCK."""

    def test_one_stray_refusal_on_a_zero_floor_is_a_watch(self):
        ctrl = [row(f"c{i}", 8.7, refused_pool_events=0) for i in range(4)]
        cands = [row(f"a{i}", 8.7, refused_pool_events=1) for i in range(4)]
        rep = stk_gate.check(cands, stk_gate.build_floors(ctrl))[0]
        self.assertEqual(rep["verdict"], "PASS")
        self.assertTrue(any("refused_pool_events (the control is 0 on every start)" in n for n in rep["notes"]))

    def test_a_nonzero_floor_still_blocks(self):
        ctrl = [row(f"c{i}", 8.7, refused_pool_events=v) for i, v in enumerate((0, 1, 0, 1))]
        cands = [row(f"a{i}", 8.7, refused_pool_events=v) for i, v in enumerate((9, 10, 11, 12))]
        self.assertEqual(stk_gate.check(cands, stk_gate.build_floors(ctrl))[0]["verdict"], "BLOCK")

    def test_stranded_is_not_gated_where_the_control_stays_off_the_wall(self):
        ctrl = [row(f"c{i}", 8.7, low=300, stranded_at_low_mib=500 + i) for i in range(4)]
        f = stk_gate.build_floors(ctrl)["keys"]["r-v1|13.60|cold"]["numbers"]["stranded_at_low_mib"]
        self.assertFalse(f["usable"])
        cands = [row(f"a{i}", 8.7, low=300, stranded_at_low_mib=2000) for i in range(4)]
        self.assertEqual(stk_gate.check(cands, stk_gate.build_floors(ctrl))[0]["verdict"], "PASS")

    def test_stranded_is_gated_at_the_wall(self):
        ctrl = [row(f"c{i}", 8.7, low=i, stranded_at_low_mib=900 + i) for i in range(4)]
        f = stk_gate.build_floors(ctrl)["keys"]["r-v1|13.60|cold"]["numbers"]["stranded_at_low_mib"]
        self.assertNotIn("usable", f)

    def test_a_crash_blocks_even_when_the_arm_boots_differently(self):
        cands = ([warm(f"c{i}", 19.1) for i in range(3)]
                 + [warm("c3", 19.1, own=36, total=37, survival_result="crashed", crash_class="oom")])
        fl = stk_gate.build_floors(WARM_CONTROL[:3] + [warm("w4", 19.3, own=36, total=37)], {WKEY})
        rep = stk_gate.check(cands, fl)[0]
        self.assertEqual(rep["verdict"], "BLOCK")


class GateNotes(unittest.TestCase):
    """Vampinity's two non-blocking notes on PR #18."""

    def test_mixed_lists_what_is_missing_too(self):
        cands = [row("a", 8.7), row("b", 8.7, script_sha1="s2"), row("c", 8.7, env_hash=None), row("d", 8.7)]
        rep = stk_gate.check(cands, stk_gate.build_floors(CONTROL))[0]
        self.assertEqual(rep["verdict"], "MIXED")
        self.assertIn("script differs", rep["why"])
        self.assertIn("settings (env hash) not recorded on c", rep["why"])

    def test_floor_without_arm_unverified_is_provisional(self):
        fl = stk_gate.build_floors(CONTROL)
        del fl["keys"]["r-v1|13.60|cold"]["arm_unverified"]
        rep = stk_gate.check([row(f"c{i}", 8.7) for i in range(4)], fl)[0]
        self.assertEqual(rep["verdict"], "PROVISIONAL")
        self.assertIn("predates the arm check", rep["provisional"])


if __name__ == "__main__":
    unittest.main()
