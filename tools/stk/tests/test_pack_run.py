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

    def test_save_profile_id_goes_in_upper_case(self):
        """The console writes the id in upper case. A lower-case-only pattern let it through into 11
        packed runs on 16 Nov, and the audit, with the same pattern, did not see it."""
        counts = {}
        out = pack_run.redact("open user/save/0000000000000000/5AD607EE29E2CB028954A68B08B6629A ok", Fake, counts)
        self.assertNotIn("5AD607EE", out)
        self.assertEqual(counts["save_profile"], 1)

    def test_profile_name_goes(self):
        counts = {}
        out = pack_run.redact("launch: Profile Someone's PS5 account\nnext line\n", Fake, counts)
        self.assertIn("launch: Profile <redacted>", out)
        self.assertNotIn("account", out.splitlines()[0])
        self.assertIn("next line", out)

    def test_save_name_in_a_route_comment_goes(self):
        """Vampinity's field route names the save in a comment; his packs carry `a plain copy of <save>`."""
        counts = {}
        line = "# Save: console/save-backups/test-field (a plain copy of Somebody's save 3),\n"
        out = pack_run.redact(line, Fake, counts)
        self.assertIn("(a plain copy of <save>),", out)
        self.assertEqual(counts["save_name"], 1)
        self.assertEqual(pack_run.redact(out, Fake, {}), out)            # already redacted: left alone


CONFIG = {
    "games": {"0400486024DEC000": {"console_mode": "handheld"}, "0100AAAABBBBC000": {"console_mode": "docked"},
              "0100DDDDEEEEF000": {}},
    "library": {"last_game": "The Legend of Zelda Ocarina of Time [0400486024DEC000].nup",
                "recent": ["The Legend of Zelda Ocarina of Time [0400486024DEC000].nup",
                           "Some Other Game [0100AAAABBBBC000].nsp"]},
    "profiles": {"current": "5AD607EE29E2CB028954A68B08B6629A", "first": "5AD607EE29E2CB028954A68B08B6629A"},
    "version": 1,
}


class Config(unittest.TestCase):
    def test_config_is_redacted_the_way_his_packs_are(self):
        counts = {}
        out = json.loads(pack_run.redact_config(json.dumps(CONFIG), Fake, counts))
        self.assertEqual(out["profiles"], {"current": "<profile>", "first": "<profile>"})
        self.assertEqual(sorted(out["games"]), ["0400486024DEC000", "<other title 1>", "<other title 2>"])
        self.assertEqual(out["games"]["<other title 1>"], {"console_mode": "docked"})   # settings kept
        self.assertEqual(out["library"]["recent"][1], "<other title>")
        self.assertIn("0400486024DEC000", out["library"]["last_game"])
        self.assertEqual(counts, {"config_profile": 2, "config_other_title": 3})
        self.assertEqual(pack_run.config_problems(json.dumps(out)), [])

    def test_audit_catches_an_unredacted_config(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "config.json").write_text(json.dumps(CONFIG))
            problems = pack_run.audit(Path(td), set())
            self.assertIn("config.json: a profile id", problems)
            self.assertIn("config.json: another game's title", problems)


class Dates(unittest.TestCase):
    def test_date_from_his_batch_folder(self):
        run = Path("/x/auto-20261115-214502-batch-alphafs/run1637-alphafs-S01-first")
        self.assertEqual(pack_run.date_from_batch(run), ("2026-11-15", "21:45:02"))

    def test_no_batch_folder_no_date(self):
        self.assertEqual(pack_run.date_from_batch(Path("/x/runKC1")), (None, None))


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
            ("user/save/0000000000000000/0123456789ABCDEF0123456789ABCDEF", "save profile id"),
            ("cloned someone/thing-private", "private repo"),
            ("# (a plain copy of Somebody's save 3)", "save name"),
            ("No cover extracted from Some Other Game [0100AAAABBBBC000].nsp", "other game's title"),
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
            run = Path(td) / "runZZ1-a.b@example.com"
            run.mkdir()
            (run / "eden_log.txt").write_text(stamp + "[  10.6] x: Total Pipeline Count: 0\n")
            (run / "stderr.log").write_text("[EglantinePS5] test: EDEN_TEST script_done at=90.0\n")
            (run / "boot-trace.txt").write_text("[EglantinePS5 diag] +0ms diagnostic build 01.219.028 "
                                                "(Nov 14 2026 23:24:15), firmware sdk_version 0x13600007, pid 1\n")
            (run / "env.txt").write_text("EDEN_TEST_SCRIPT=zelda-first-start-watch-wait-30s.v6.txt\n")
            (run / "declared.json").write_text(json.dumps({"control": True, "intended_cache": "cold"}) + "\n")
            os.makedirs(Path(out) / "tools", exist_ok=True)
            (Path(out) / "tools/pack-run.py").write_bytes((Path(GHB) / "tools/pack-run.py").read_bytes())
            with self.assertRaises(SystemExit):                              # no batch folder, no --date
                pack_run.pack(run, out, author="GrowingBlackBeans", alpha_env=None)
            (run / "config.json").write_text(json.dumps(CONFIG))
            target, counts = pack_run.pack(run, out, author="GrowingBlackBeans", date="2026-11-17", alpha_env=None)
            self.assertIsNotNone(target, "the audit refused a clean synthetic run")
            info = json.loads((target / "run.json").read_text())
            self.assertEqual(info["format"], 1)
            self.assertEqual(info["declared"]["intended_cache"], "cold")
            self.assertEqual(info["derived"]["firmware"], "13.60")          # from the log, not typed
            self.assertEqual(info["derived"]["build_key"], "01.219.028 (Nov 14 2026 23:24:15)")
            self.assertEqual(info["derived"]["cache_class"], "cold")
            self.assertNotIn("run_path", info["derived"])                    # no local path ships
            self.assertTrue((target / "declared.json").is_file())
            self.assertEqual(target.name, "2026-11-17-EMAIL")              # the id is redacted in the folder name, as his packs do
            self.assertEqual(json.loads((target / "config.json").read_text())["profiles"]["current"], "<profile>")


if __name__ == "__main__":
    unittest.main()
