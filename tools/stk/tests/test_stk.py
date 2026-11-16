"""Tests for the run-contract scorer. Synthetic cases always run; the packed control starts are read from
this repo's runs/ (or $STK_TEST_GHB), and skipped if they are not there."""
import gzip
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from stk_score import score_run  # noqa: E402

# The packed control starts in this repo (or a clone named by $STK_TEST_GHB).
GHB = os.environ.get("STK_TEST_GHB") or str(Path(__file__).resolve().parents[3])
V = Path(GHB) / "runs" / "Vampinity"


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

    def test_capped_oom_count_is_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "stderr.log").write_text("EDEN_RADV_OUT_OF_MEMORY 4608 KiB asked: 0 MiB given back\n" * 64)
            r = score_run(td, None)
            self.assertEqual(r["radv_oom_events"], ">=64")   # a floor, never a count
            self.assertTrue(r["radv_oom_capped"])


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
        self.assertEqual(keys[0], "new-game-v6|13.60|src0123456789|prep_5093ab9e|cold")
        self.assertEqual(keys[1], "new-game-v6|13.60|src0123456789|prep_5093ab9e|warm")


@unittest.skipUnless(V.is_dir(), "no runs/Vampinity here; set STK_TEST_GHB to a GreenHatBoy clone")
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
        want = {"run1590": (18.96, 14.00), "run1591": (18.76, 13.40), "run1604": (19.12, 14.00),
                "run1607": (19.16, 14.10), "run1613": (19.39, 13.30), "run1615": (19.59, 13.80),
                "run1616": (19.39, 13.60)}
        for key, (walk, after) in want.items():
            run = next(p for p in V.iterdir() if f"-{key}-" in p.name)
            r = score_run(run, None)
            self.assertEqual(r["win_field_walk_fps"], walk, key)
            self.assertEqual(r["win_after_field_fps"], after, key)
            self.assertEqual(r["cache_class"], "warm", key)


if __name__ == "__main__":
    unittest.main()
