"""Tests for the run-contract scorer. Synthetic cases always run; real packed runs run when
$STK_TEST_GHB points at a GreenHatBoy clone (they are skipped otherwise)."""
import gzip
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from stk_score import score_run  # noqa: E402

GHB = os.environ.get("STK_TEST_GHB")
V = Path(GHB) / "runs" / "Vampinity" if GHB else None


def stamp(state, pipes):
    return (f"[  10.5] Render.Vulkan <Info> x.cpp:1:LoadDiskResources: EDEN_UP_SHADER_PREP_SOURCE_STAMP: id src0123456789 "
            f"(files 418) devabc, store prep_5093ab9e {state} ({pipes} pipelines), build 84698430.17\n")


def write_run(d: Path, eden: str, stderr: str = "", boot: str = "", env: str = "", layout="flat"):
    base = d / "logs" if layout == "logs" else d
    base.mkdir(parents=True, exist_ok=True)
    (d / "eden_log.txt").write_text(eden)
    (base / "stderr.log").write_text(stderr)
    if boot:
        (base / "boot-trace.txt").write_text(boot)
    if env:
        (d / "env.txt").write_text(env)


class WindowsFile(unittest.TestCase):
    """Every route's windows must use a window kind the scorer implements: a route whose entry the
    scorer cannot read would score null windows silently (how waveydude's route sat unscored)."""

    def test_every_window_kind_is_implemented(self):
        import json
        routes = json.loads((Path(__file__).resolve().parent.parent / "windows.json").read_text())["routes"]
        known = {"stamped", "whole", "between", "after_load_low"}
        self.assertIn("wavey-kokiri-field-town", routes)
        for route, defn in routes.items():
            self.assertTrue(defn.get("sha1"), route)
            for name, w in defn["windows"].items():
                self.assertIn(w["kind"], known, f"{route}.{name}")
                self.assertIn(w.get("stat"), ("mean", "median"), f"{route}.{name}")


class Synthetic(unittest.TestCase):
    def test_cold_start_stamp_new_is_read(self):
        with tempfile.TemporaryDirectory() as td:
            write_run(Path(td), stamp("new", 0) + "[  10.6] x: Total Pipeline Count: 0\n")
            r = score_run(td, None)
            self.assertEqual(r["shader_store"], "prep_5093ab9e")
            self.assertEqual(r["store_state"], "new")
            self.assertEqual(r["store_pipelines"], 0)
            self.assertEqual(r["build"], "build_84698430")
            self.assertEqual(r["cache_class"], "cold")

    def test_half_warm_is_not_cold(self):
        with tempfile.TemporaryDirectory() as td:
            write_run(Path(td), stamp("new", 0)
                      + "[   6.0] x: Loaded Vulkan driver pipeline cache: /data/x/vulkan_pipelines.bin\n"
                      + "[   6.5] x: Total Pipeline Count: 921\n")
            self.assertEqual(score_run(td, None)["cache_class"], "half")

    def test_other_sessions_crash_files_are_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            write_run(d, "[ 500.0] x: last line\n", "[EglantinePS5] test: EDEN_TEST script_done at=400.0\n",
                      boot="[EglantinePS5 diag] +0ms diagnostic build 01.219.028 (Nov 14 2026 23:24:15), firmware sdk_version 0x13600007, pid 1\n",
                      layout="logs")
            (d / "logs" / "crash-20261109-114313.txt").write_text(
                "EglantinePS5 crash report\nversion: 01.219.900 (x)\ntime: 2026-11-09 11:43:13, 77 s after the app started\nwhat: SIGSEGV\n")
            r = score_run(td, None)
            self.assertEqual(r["survival_result"], "completed")
            self.assertEqual(r["crash_files_ignored"], 1)
            self.assertEqual(r["firmware"], "13.60")
            self.assertEqual(r["firmware_source"], "boot-trace.sdk_version")

    def test_this_runs_crash_is_matched(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            write_run(d, "[ 107.0] x: last line\n", "",
                      boot="[EglantinePS5 diag] +0ms diagnostic build 01.219.926 (Nov 15 2026 01:00:00), firmware sdk_version 0x13600007, pid 1\n",
                      layout="logs")
            (d / "logs" / "crash-20261116-064954.txt").write_text(
                "EglantinePS5 crash report\nversion: 01.219.926 (x)\ntime: 2026-11-16 06:49:54, 108 s after the app started\nwhat: SIGSEGV (invalid memory access)\n")
            r = score_run(td, None)
            self.assertEqual(r["survival_result"], "crashed")
            self.assertTrue(r["crash_class"].startswith("SIGSEGV"))

    def test_gz_files_are_read(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            with gzip.open(d / "eden_log.txt.gz", "wt") as f:
                f.write(stamp("reused", 100))
            with gzip.open(d / "stderr.log.gz", "wt") as f:
                f.write("RADV_PS5_MEMORY t_s=12 pool_mib=12352 available_mib=42 driver_mib=1 retired_mib=0\n")
            r = score_run(td, None)
            self.assertEqual(r["cache_class"], "warm")
            self.assertEqual(r["largest_free_block_min_mib"], 42)
            self.assertEqual(r["largest_free_block_driver_min_mib"], 42)

    def test_missing_is_null_never_zero(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "stderr.log").write_text("RADV_PS5_MEMORY t_s=12.0 pool_mib=12352 available_mib=42\n")
            r = score_run(td, None)
            for k in ("fps_mean", "fps_median", "shader_builds_in_play", "hitch_ms_per_min", "flashes_per_min",
                      "game_speed", "firmware", "shader_store", "cache_class"):
                self.assertIsNone(r[k], k)
            json.dumps(r)

    def test_crash_class_unknown_when_survival_unknown(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "eden_log.txt").write_text("[   1.0] x: a log with no end line\n")
            r = score_run(td, None)
            self.assertEqual(r["survival_result"], "unknown")
            self.assertIsNone(r["crash_class"])
            self.assertEqual(r["crash_source"], "missing_survival_unknown")

    def test_capped_oom_count_is_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "stderr.log").write_text("EDEN_RADV_OUT_OF_MEMORY 4608 KiB asked: 0 MiB given back\n" * 64)
            r = score_run(td, None)
            self.assertEqual(r["radv_oom_events"], ">=64")   # a floor, never a count
            self.assertTrue(r["radv_oom_capped"])

    def test_memory_at_the_wall(self):
        """19 Nov: refusals, seconds under 16 MiB, and what is stranded at the lowest census."""
        census = ("EDEN_MEM_CENSUS n=1 why=low t_s=10.0 largest=40 low=40\n"
                  "EDEN_MEM_CENSUS_POOL n=1 out=1 heap=1 (pieces=1 live=1 free_pages=100 idle_arenas=1 fragmented=200 "
                  "large=0 in_use=1) vma_blocks=1 vma_used=1 vma_slack=300 rest=1 (MiB)\n"
                  "EDEN_MEM_CENSUS n=2 why=low t_s=12.0 largest=2 low=2\n"
                  "EDEN_MEM_CENSUS_POOL n=2 out=1 heap=1 (pieces=1 live=1 free_pages=110 idle_arenas=1 fragmented=280 "
                  "large=0 in_use=1) vma_blocks=1 vma_used=1 vma_slack=560 rest=1 (MiB)\n"
                  "EDEN_MEM_CENSUS n=3 why=low t_s=14.0 largest=9 low=2\n"
                  "EDEN_REFUSED_POOL 4 MiB\nEDEN_REFUSED_POOL 8 MiB\n")
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "stderr.log").write_text(census)
            r = score_run(td, None)
            self.assertEqual(r["refused_pool_events"], 2)
            self.assertEqual(r["seconds_under_16_mib"], 4.0)         # two census lines under 16, 2 s each
            self.assertEqual(r["stranded_at_low_mib"], 110 + 280 + 560)  # the pool line of the lowest census
            self.assertIsNone(r["load_s"])                            # no route, no load window


def census(n, t, largest, free_pages=100, fragmented=200, slack=300):
    return (f"EDEN_MEM_CENSUS n={n} why=low t_s={t} largest={largest} low={largest}\n"
            f"EDEN_MEM_CENSUS_POOL n={n} out=1 heap=1 (pieces=1 live=1 free_pages={free_pages} idle_arenas=1 "
            f"fragmented={fragmented} large=0 in_use=1) vma_blocks=1 vma_used=1 vma_slack={slack} rest=1 (MiB)\n")


DONE = "[EglantinePS5] test: EDEN_TEST script_done at=400.0\n"
REFUSED = ("EDEN_REFUSED_POOL 12352 MiB in all, 7 MiB free in 314 blocks after 629 questions: the largest {} MiB, "
           "0 MiB in blocks of 2 MiB or more\n")


class MemoryAfterPR24(unittest.TestCase):
    """Vampinity's review of PR #24 (20 Nov): where the memory numbers stop, what a refusal is, ties at the low."""

    def score(self, stderr):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "stderr.log").write_text(stderr)
            return score_run(td, None)

    def test_memory_stops_ten_census_seconds_after_script_done(self):
        # Census clock behind the script's: cut by log order, then 10 s on the census clock (lines at 380..388).
        log = (census(1, 300.0, 40) + REFUSED.format(0) + DONE + census(2, 380.0, 2) + REFUSED.format(1)
               + "".join(census(n, 380.0 + 2 * (n - 2), 3) for n in range(3, 7))   # 382, 384, 386, 388
               + census(7, 390.0, 0) + REFUSED.format(0) + REFUSED.format(0))       # past the cut
        r = self.score(log)
        self.assertEqual(r["memory_window"], "to_script_done+10s")
        self.assertEqual(r["refused_pool_events"], 2)            # one before script_done, one in the 10 s
        self.assertEqual(r["seconds_under_16_mib"], 10.0)        # lines 2-6, 2 s each; line 7 is past the cut
        self.assertEqual(r["largest_free_block_min_mib"], 0)     # the old minimum still reads the whole log

    def test_no_census_after_script_done_stops_at_its_line(self):
        r = self.score(census(1, 300.0, 4) + DONE + REFUSED.format(0))
        self.assertEqual(r["memory_window"], "to_script_done_line")
        self.assertEqual(r["refused_pool_events"], 0)

    def test_without_script_done_the_whole_log_counts(self):
        r = self.score(census(1, 300.0, 4) + REFUSED.format(0) + census(2, 302.0, 4))
        self.assertEqual(r["memory_window"], "to_log_end")
        self.assertEqual(r["refused_pool_events"], 1)
        self.assertEqual(r["seconds_under_16_mib"], 4.0)

    def test_a_pool_walk_line_with_room_is_not_a_refusal(self):
        # EDEN_NX2_POOL_WALK=1 prints the pool line every 20 s with nothing refused (his run215).
        r = self.score(REFUSED.format(16) + REFUSED.format(7680) + REFUSED.format(15) + REFUSED.format(0))
        self.assertEqual(r["refused_pool_events"], 2)

    def test_stranded_is_the_median_of_the_ties_at_the_low(self):
        log = (census(1, 10.0, 0, 100, 200, 300) + census(2, 12.0, 5, 1, 1, 1)
               + census(3, 14.0, 0, 100, 200, 500) + census(4, 16.0, 0, 100, 200, 900))
        self.assertEqual(self.score(log)["stranded_at_low_mib"], 100 + 200 + 500)


def vi(t, fps):
    return f"[ {t:7.1f}] x nx2:vi2 5 s: {int(fps * 5)} frames, {fps} fps, mean 30.0 ms, 1% low 40.0 ms, worst 50.0 ms\n"


FIELD_MARKS = ("[EglantinePS5] test: EDEN_TEST steer_met line=46 point=1/1 at=10.0\n"
               "[EglantinePS5] test: EDEN_TEST wait_met line=92 at=100.0\n"
               "[EglantinePS5] test: EDEN_TEST script_end line=102 at=390.0\n"
               "[EglantinePS5] test: EDEN_TEST script_done at=390.0\n")


class LoadSeconds(unittest.TestCase):
    """load_s on a made-up field start (Vampinity, PR #24, point 5): the black, the stall, a false start, the hold."""

    def score(self, eden):
        with tempfile.TemporaryDirectory() as td:
            write_run(Path(td), eden, FIELD_MARKS, env="EDEN_TEST_SCRIPT=field-to-past-field.txt\n")
            return score_run(td, None)

    BEFORE = "".join(vi(t, 20.0) for t in range(5, 100, 5))
    BLACK = "".join(vi(t, 58.0) for t in range(105, 125, 5))           # the load's black: 55 fps or more

    def test_the_load_ends_where_play_holds_for_15_s(self):
        stall = vi(125, 3.0) + vi(130, 3.0) + vi(135, 9.0) + vi(140, 4.0)  # 135 is good, but 140 drops: not settled
        r = self.score(self.BEFORE + self.BLACK + stall + "".join(vi(t, 14.0) for t in range(145, 400, 5)))
        self.assertEqual(r["win_after_field_fps"], 14.0)
        self.assertEqual(r["load_s"], 40.0)     # the mark at 100 s to the start of the 145 s line (140 s)

    def test_fewer_than_three_settled_lines_never_settle(self):
        # Play swings 14 / 4 fps: the window's median is 9, half of it 4.5, so no 15 s ever holds (two lines at most).
        tail = "".join(vi(t, 14.0 if (t // 5) % 2 else 4.0) for t in range(125, 400, 5))
        r = self.score(self.BEFORE + self.BLACK + tail)
        self.assertIsNone(r["load_s"])
        self.assertEqual(r["load_source"], "missing_play_never_settled")

    def test_two_good_lines_before_the_cut_are_not_a_hold(self):
        # A late load: the black at 300-320, the stall to 390, then 14 fps at 395 and 400 only (script_done + 10 s
        # = 400 ends play). The window's median is 14, and two lines are short of the 3-line minimum.
        eden = ("".join(vi(t, 20.0) for t in range(5, 300, 5)) + "".join(vi(t, 58.0) for t in range(300, 325, 5))
                + "".join(vi(t, 3.0) for t in range(325, 395, 5)) + vi(395, 14.0) + vi(400, 14.0)
                + "".join(vi(t, 14.0) for t in range(405, 430, 5)))
        r = self.score(eden)
        self.assertEqual(r["win_after_field_fps"], 14.0)
        self.assertIsNone(r["load_s"])
        self.assertEqual(r["load_source"], "missing_play_never_settled")

    def test_no_black_no_load(self):
        r = self.score(self.BEFORE + "".join(vi(t, 14.0) for t in range(105, 400, 5)))
        self.assertIsNone(r["load_s"])
        self.assertTrue(r["load_source"].startswith("missing_"))


class WarmBootLines(unittest.TestCase):
    def test_warm_boot_lines_are_read(self):
        """PR #23 review: the two boot regexes, on the alpha's own wording."""
        eden = (stamp("reused", 80770)
                + "[   3.83] Render.Vulkan <Info> x.cpp:5793:PrepareKept: Shader preparation: 80770 pipelines known, 0 left "
                  "to prepare (0 of this console's own records, 0 predicted), 0 struck out\n"
                + "[   3.84] Render.Vulkan <Info> x.cpp:5803:PrepareKept: Shader preparation stats: 3 records read (3 own, 0 "
                  "predicted): 0 not taken by the boot\n"
                + "[   3.90] Render.Vulkan <Info> x.cpp:1:Load: Total Pipeline Count: 4\n")
        with tempfile.TemporaryDirectory() as td:
            write_run(Path(td), eden)
            r = score_run(td, None)
            self.assertEqual((r["pipelines_known"], r["left_to_prepare"], r["own_records"], r["total_pipeline_count"]),
                             (80770, 0, 3, 4))

    def test_missing_boot_lines_are_null(self):
        with tempfile.TemporaryDirectory() as td:
            write_run(Path(td), stamp("reused", 80770))
            r = score_run(td, None)
            self.assertIsNone(r["pipelines_known"])
            self.assertIsNone(r["own_records"])


class ContractV1(unittest.TestCase):
    """waveydude's four points for run.json v1."""

    def test_translation_id_and_device_are_read(self):
        with tempfile.TemporaryDirectory() as td:
            write_run(Path(td), stamp("new", 0))
            r = score_run(td, None)
            self.assertEqual(r["translation_id"], "src0123456789")
            self.assertEqual(r["device_id"], "devabc")
            self.assertEqual(r["translation_files"], 418)

    def test_route_that_stopped_is_invalid_and_not_scored(self):
        script = "# a route\n0 WAIT 5 LOOK 1 1 1 1 1x1:00\n1.0 A 150\n0 END\n"
        new_game_village_script = None
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            write_run(d, stamp("new", 0) + "[  10.0] x: EDEN_GUEST_START the test script's clock starts here\n"
                      + "".join(f"[{t:7.1f}] Service <Info> nx2_gsv.h:1:PresentClientBuffer: nx2:vi2 5 s: 110 frames, 22.0 fps, mean 45 ms, 1% low 60 ms, worst 70 ms\n" for t in range(20, 300, 5)),
                      "[EglantinePS5] test: EDEN_TEST script_start file=r.txt events=2 waits=1\n"
                      "[EglantinePS5] test: EDEN_TEST wait_timeout line=2 at=5.0\n"
                      "[EglantinePS5] test: EDEN_TEST script_stopped at=5.0\n")
            (d / "script.txt").write_text(script)
            r = score_run(td, None)
            self.assertFalse(r["route_completed"])
            self.assertIn("wait_timeout", r["route_reason"])
            self.assertFalse(r["window_comparable"])

    def test_steer_points_must_all_be_met(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            write_run(d, stamp("new", 0),
                      "[EglantinePS5] test: EDEN_TEST script_start file=r.txt events=2 waits=2\n"
                      "[EglantinePS5] test: EDEN_TEST steer_met line=1 at=50.0 point=2/2 looks=9 seen=9\n"
                      "[EglantinePS5] test: EDEN_TEST script_done at=90.0\n")
            (d / "script.txt").write_text("0 STEER 150 1,1 2,2\n0 STEER 150 3,3 4,4\n0 END\n")
            r = score_run(td, None)
            self.assertFalse(r["route_completed"])
            self.assertEqual(r["route_result"], "unknown")
            self.assertIn("STEER lines [2]", r["route_reason"])

    def test_comparison_key_separates_cold_from_warm(self):
        keys = []
        for state, pipes in (("new", 0), ("reused", 78723)):
            with tempfile.TemporaryDirectory() as td:
                write_run(Path(td), stamp(state, pipes) + f"[  10.6] x: Total Pipeline Count: {0 if state == 'new' else 2923}\n",
                          "[EglantinePS5] test: EDEN_TEST script_start file=x events=1 waits=0\n[EglantinePS5] test: EDEN_TEST script_done at=1.0\n",
                          boot="[EglantinePS5 diag] +0ms diagnostic build 01.219.028 (Nov 14 2026 23:24:15), firmware sdk_version 0x13600007, pid 1\n",
                          env="EDEN_TEST_SCRIPT=zelda-first-start-watch-wait-30s.v6.txt\n")
                keys.append(score_run(td, None)["comparison_key"])
        want = "new-game-v6|13.60|01.219.028 (Nov 14 2026 23:24:15)|src0123456789|prep_5093ab9e"
        self.assertEqual(keys[0], want + "|cold")
        self.assertEqual(keys[1], want + "|warm")

    def test_comparison_key_separates_two_builds_that_share_a_store(self):
        """waveydude, PR #11: with the translation id forced to keep a store, his A186-keep ... keep4
        all carry one id and one store with different code. The build has to split them."""
        keys = []
        for compiled in ("Nov 15 2026 09:12:40", "Nov 16 2026 18:03:11"):
            with tempfile.TemporaryDirectory() as td:
                write_run(Path(td), stamp("reused", 80999) + "[  10.6] x: Total Pipeline Count: 80999\n",
                          "[EglantinePS5] test: EDEN_TEST script_start file=x events=1 waits=0\n"
                          "[EglantinePS5] test: EDEN_TEST script_done at=1.0\n",
                          boot=f"[EglantinePS5 diag] +0ms diagnostic build 01.219.028 ({compiled}), "
                               "firmware sdk_version 0x13600007, pid 1\n",
                          env="EDEN_TEST_SCRIPT=zelda-first-start-watch-wait-30s.v6.txt\n")
                r = score_run(td, None)
                self.assertEqual(r["shader_store"], "prep_5093ab9e")
                self.assertEqual(r["cache_class"], "warm")
                keys.append(r["comparison_key"])
        self.assertNotEqual(keys[0], keys[1])

    def test_comparison_key_is_none_without_a_build(self):
        """No boot trace and no declared build: the run cannot be compared, rather than being
        compared on four fields out of five."""
        with tempfile.TemporaryDirectory() as td:
            write_run(Path(td), stamp("new", 0) + "[  10.6] x: Total Pipeline Count: 0\n"
                      + "[   0.1] x: sdk_version 0x13600007\n",
                      "[EglantinePS5] test: EDEN_TEST script_start file=x events=1 waits=0\n"
                      "[EglantinePS5] test: EDEN_TEST script_done at=1.0\n",
                      env="EDEN_TEST_SCRIPT=zelda-first-start-watch-wait-30s.v6.txt\n")
            r = score_run(td, None)
            self.assertEqual(r["build_source"], "eden_log.SOURCE_STAMP")
            self.assertIsNone(r["build_key"])
            self.assertIsNone(r["comparison_key"])


@unittest.skipUnless(V and V.is_dir(), "set STK_TEST_GHB to a GreenHatBoy clone")
class PackedControlStarts(unittest.TestCase):
    """His published figures (runs/Vampinity/2026-11-15-t186-control-README.md)."""

    def test_new_game_village(self):
        for run, want in (("2026-11-15-run1637-alphafs-S01-first", 22.57), ("2026-11-15-run1638-alphafs-S02-first", 22.43)):
            r = score_run(V / run, None)
            self.assertEqual(r["win_village_fps"], want, run)
            self.assertEqual(r["cache_class"], "cold", run)
            self.assertEqual(r["start_method"], "test_boot", run)
            self.assertEqual(r["end_kind"], "app_closed", run)

    def test_field_and_after_field(self):
        # After the field as cut at script_done + 10 s (PR #20): run1591 13.40 -> 13.35, run1604 14.00 -> 13.95 and
        # run1613 13.30 -> 13.35 against his published values, which read to the log's end.
        want = {"run1590": (18.96, 14.00), "run1591": (18.76, 13.35), "run1604": (19.12, 13.95),
                "run1607": (19.16, 14.10), "run1613": (19.39, 13.35), "run1615": (19.59, 13.80),
                "run1616": (19.39, 13.60)}
        for key, (walk, after) in want.items():
            run = next(p for p in V.iterdir() if f"-{key}-" in p.name)
            r = score_run(run, None)
            self.assertEqual(r["win_field_walk_fps"], walk, key)
            self.assertEqual(r["win_after_field_fps"], after, key)
            self.assertEqual(r["cache_class"], "warm", key)


if __name__ == "__main__":
    unittest.main()
