"""Tests for pack_run.py. The redaction engine itself is Vampinity's and lives in a GreenHatBoy clone,
so the full pack runs only when $STK_TEST_GHB points at one; the rules and the audit always run."""
import gzip
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pack_run  # noqa: E402

GHB = os.environ.get("STK_TEST_GHB")


class Fake:
    """Stands in for his module: no redaction, so only our own rules are under test."""
    @staticmethod
    def redact(text, counts):
        return text


class Rules(unittest.TestCase):
    def test_save_profile_id_goes(self):
        counts = {}
        out = pack_run.redact("opened user/save/0000000000000000/0123456789abcdef0123456789abcdef ok", Fake, counts)
        self.assertIn("user/save/0000000000000000/<profile>", out)
        self.assertEqual(counts["save_profile"], 1)

    def test_profile_name_goes(self):
        counts = {}
        out = pack_run.redact("launch: Profile Someone's PS5 account\nnext line\n", Fake, counts)
        self.assertIn("launch: Profile <redacted>", out)
        self.assertNotIn("account", out.splitlines()[0])
        self.assertIn("next line", out)


class Audit(unittest.TestCase):
    def write(self, d: Path, text: str, name="eden_log.txt.gz"):
        with gzip.open(d / name, "wt") as h:
            h.write(text)

    def test_audit_catches_what_must_not_ship(self):
        for text, want in (
            ("/Users/someone/Desktop/run", "home path"),
            ("mail me at a.b@example.com", "e-mail"),
            ("connected to 192.168.1.42", "LAN address"),
            ("EDEN_PAD_OPEN pads=1 user=1234567", "pad user line"),
            ("user/save/0000000000000000/0123456789abcdef0123456789abcdef", "save profile id"),
            ("cloned waveydude/ocarina-private", "private repo"),
        ):
            with tempfile.TemporaryDirectory() as td:
                d = Path(td)
                self.write(d, text)
                problems = pack_run.audit(d, set())
                self.assertTrue(any(want in p for p in problems), f"{want} not caught in {problems}")

    def test_audit_passes_a_clean_run(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            self.write(d, "[ 10.5] nx2:vi2 5 s: 150 frames, 22.67 fps\n/Users/USER/ok\n")
            self.assertEqual(pack_run.audit(d, set()), [])

    def test_audit_catches_a_private_word(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            self.write(d, "the console is called Thornfield\n")
            self.assertTrue(pack_run.audit(d, {"Thornfield"}))


@unittest.skipUnless(GHB and (Path(GHB) / "tools/pack-run.py").is_file(), "set STK_TEST_GHB to a GreenHatBoy clone")
class FullPack(unittest.TestCase):
    def test_facts_come_from_the_log(self):
        stamp = ("[  10.5] Render.Vulkan <Info> x.cpp:1:LoadDiskResources: EDEN_UP_SHADER_PREP_SOURCE_STAMP: "
                 "id src0123456789 (files 418) devabc, store prep_5093ab9e new (0 pipelines), build 84698430.17\n")
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as out:
            run = Path(td) / "runZZ1"
            run.mkdir()
            (run / "eden_log.txt").write_text(stamp + "[  10.6] x: Total Pipeline Count: 0\n")
            (run / "stderr.log").write_text("[EglantinePS5] test: EDEN_TEST script_done at=90.0\n")
            (run / "boot-trace.txt").write_text("[EglantinePS5 diag] +0ms diagnostic build 01.219.028 "
                                                "(Nov 14 2026 23:24:15), firmware sdk_version 0x13600007, pid 1\n")
            (run / "env.txt").write_text("EDEN_TEST_SCRIPT=zelda-first-start-watch-wait-30s.v6.txt\n")
            (run / "declared.json").write_text(json.dumps({"control": True, "intended_cache": "cold"}) + "\n")
            os.makedirs(Path(out) / "tools", exist_ok=True)
            (Path(out) / "tools/pack-run.py").write_bytes((Path(GHB) / "tools/pack-run.py").read_bytes())
            target, counts = pack_run.pack(run, out, author="GrowingBlackBeans", alpha_env=None)
            self.assertIsNotNone(target, "the audit refused a clean synthetic run")
            info = json.loads((target / "run.json").read_text())
            self.assertEqual(info["format"], 1)
            self.assertEqual(info["declared"]["intended_cache"], "cold")
            self.assertEqual(info["derived"]["firmware"], "13.60")          # from the log, not typed
            self.assertEqual(info["derived"]["build_key"], "01.219.028 (Nov 14 2026 23:24:15)")
            self.assertEqual(info["derived"]["cache_class"], "cold")
            self.assertNotIn("run_path", info["derived"])                    # no local path ships
            self.assertTrue((target / "declared.json").is_file())


if __name__ == "__main__":
    unittest.main()
