#!/usr/bin/env python3
"""pack_run.py: pack any run folder into the shared layout, under the run contract (17 Nov 2026).

    python3 -I pack_run.py RUN --out <GreenHatBoy clone> [--id ID] [--author NAME] [--date YYYY-MM-DD]
                               [--alpha-env <the control's env.txt>] [--dry-run]

    The date comes from the batch folder's name (`auto-YYYYMMDD-HHMMSS-batch-<name>`, as his runner
    writes them). A run not in such a folder needs --date: a file's modified time changes when a folder
    is copied or unzipped, so it is never used.

What it is, and what it is not:

- The **facts are derived from the logs**, by the shared scorer (`stk_score.score_run`): firmware, build,
  route and its proof, store, cache class, the windows, survival. Nothing about the run's conditions is
  typed in. That is the run contract's first rule, and the reason this exists: Vampinity's
  `tools/pack-run.py` takes them from a row in his own `runs.jsonl` and writes `"firmware": "12.40"`
  literally, which is right on his console and wrong everywhere else.
- **Redaction is his**, imported from `tools/pack-run.py` (home paths, e-mail, LAN and MAC addresses, the
  console user number in decimal and hex, the login name, every word in `~/.eglantine-private`). Rules
  of ours are added: the save-profile id under `user/save/...` (either case), the launcher's profile
  name, and the save's name in a route's comments (`a plain copy of <save>`). `config.json` gets the
  same treatment his packs gave it: profile ids, and every other game's title. The run id is redacted
  in the folder name too. His file is not modified, so his own clean-up of it can land without a
  conflict.
- It **writes only under --out**, and audits what it wrote: if any private pattern survives, the packed
  folder is deleted and the exit code is 2.

Standard library only.
"""
from __future__ import annotations
import argparse, gzip, importlib.util, json, os, pathlib, re, shutil, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stk_score  # noqa: E402
from runfolder import RunFolder  # noqa: E402

PACKER_VERSION = "pack_run 2 (Vampinity's pack-run.py redaction + the run contract, 17 Nov 2026)"
GAME_ID = "0400486024DEC000"

# Ours, on top of his: a save-profile id is 32 hex under user/save/<title>/, and the launcher prints the
# profile's name, which can be an account name.
EXTRA = [
    ("save_profile", re.compile(r"(user/save/\d{16}/)[0-9A-Fa-f]{32}"), r"\1<profile>"),   # the console writes it in upper case
    ("profile_name", re.compile(r"(launch: Profile ).*"), r"\1<redacted>"),
    ("save_name", re.compile(r"(a plain copy of )(?!<save>)[^)\n]+"), r"\1<save>"),        # his route's comment names the save
]
# What must not survive anywhere in a packed run. Checked after writing.
FORBIDDEN = [
    ("home path", re.compile(r"/(?:Users|home)/(?!USER\b)[^/\s\"']+")),
    ("e-mail", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("LAN address", re.compile(r"\b(?:192\.168|10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b")),
    ("MAC address", re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b")),
    ("pad user line", re.compile(r"EDEN_PAD_(?:OPEN|USERS)[^\n]*?(?:user|foreground|initial)=\d{4,}")),
    ("save profile id", re.compile(r"user/save/\d{16}/[0-9A-Fa-f]{32}")),
    ("private repo", re.compile(r"ocarina-private")),
    ("save name", re.compile(r"a plain copy of (?!<save>)")),
    ("other game's title", re.compile(r"\[(?!" + GAME_ID + r"\])[0-9A-Fa-f]{16}\]\.(?:nup|nsp|xci)\b")),
]

# The contract's files. (name in the run folder, name when packed, gzip?)
FILES = [
    ("eden_log.txt", "eden_log.txt.gz", True),
    ("stderr.log", "stderr.log.gz", True),
    ("heap.log", "heap.log.gz", True),
    ("boot-trace.txt", "boot-trace.txt", False),
    ("env.txt", "env.txt", False),
    ("script.txt", "script.txt", False),
    ("declared.json", "declared.json", False),
    ("config.json", "config.json", False),       # the app's settings; redacted as JSON (redact_config)
]
# Local-only keys of the scorer's row: a path names this machine, and the id is the folder name.
DROP_FROM_ROW = ("run_path",)


def load_his_redaction(repo: pathlib.Path):
    path = repo / "tools" / "pack-run.py"
    if not path.is_file():
        sys.exit(f"{path} not found: --out must be a GreenHatBoy clone (its redaction lives there)")
    spec = importlib.util.spec_from_file_location("ghb_pack", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def redact(text: str, ghb, counts: dict) -> str:
    text = ghb.redact(text, counts)
    for name, pattern, repl in EXTRA:
        text, n = pattern.subn(repl, text)
        if n:
            counts[name] = counts.get(name, 0) + n
    return text


def redact_config(text: str, ghb, counts: dict) -> str:
    """The app's config.json, the way his packs carry it: the profile ids under "profiles" become
    <profile>; every game other than this one becomes <other title N> (a key under "games") or
    <other title> (in "library"); then the text rules run over what is left."""
    data = json.loads(text)

    def bump(name):
        counts[name] = counts.get(name, 0) + 1

    profiles = data.get("profiles")
    if isinstance(profiles, dict):
        for key, value in profiles.items():
            if value not in (None, "", "<profile>"):
                profiles[key] = "<profile>"
                bump("config_profile")
    games = data.get("games")
    if isinstance(games, dict):
        renamed, n = {}, 0
        for key, value in games.items():
            if key == GAME_ID:
                renamed[key] = value
            else:
                n += 1
                renamed[f"<other title {n}>"] = value
                bump("config_other_title")
        data["games"] = renamed
    library = data.get("library")
    if isinstance(library, dict):
        def ours(name):
            return isinstance(name, str) and (GAME_ID in name or name.startswith("<other title"))
        for key, value in library.items():
            if isinstance(value, str) and not ours(value):
                library[key] = "<other title>"
                bump("config_other_title")
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str) and not ours(item):
                        value[i] = "<other title>"
                        bump("config_other_title")
    return redact(json.dumps(data, indent=1, ensure_ascii=False) + "\n", ghb, counts)


def config_problems(text: str) -> list[str]:
    """What the text patterns cannot see in config.json: a profile value or another game's key."""
    try:
        data = json.loads(text)
    except ValueError:
        return ["config.json: not JSON, cannot be checked"]
    problems = []
    if any(v not in (None, "", "<profile>") for v in (data.get("profiles") or {}).values()):
        problems.append("config.json: a profile id")
    if any(k != GAME_ID and not k.startswith("<other title") for k in (data.get("games") or {})):
        problems.append("config.json: another game's title")
    for value in (data.get("library") or {}).values():
        for item in (value if isinstance(value, list) else [value]):
            if isinstance(item, str) and GAME_ID not in item and not item.startswith("<other title"):
                problems.append("config.json: another game's title")
    return problems


def date_from_batch(run: pathlib.Path):
    """(date, time) from his runner's batch folder, auto-YYYYMMDD-HHMMSS-batch-<name>; else (None, None)."""
    m = re.match(r"auto-(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})-batch-", run.parent.name)
    return (f"{m[1]}-{m[2]}-{m[3]}", f"{m[4]}:{m[5]}:{m[6]}") if m else (None, None)


def audit(target: pathlib.Path, secrets: set[str]) -> list[str]:
    problems = []
    for path in sorted(target.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix == ".gz":
            with gzip.open(path, "rt", errors="replace") as handle:
                text = handle.read()
        else:
            text = path.read_text(errors="replace")
        if path.name == "config.json":
            problems += config_problems(text)
        for name, pattern in FORBIDDEN:
            if pattern.search(text):
                problems.append(f"{path.name}: {name}")
        for word in secrets:
            if word and len(word) >= 6 and re.search(r"(?<![A-Za-z0-9])" + re.escape(word) + r"(?![A-Za-z0-9])", text, re.I):
                problems.append(f"{path.name}: a private word")
    return sorted(set(problems))


def private_words(raw: str) -> set[str]:
    secrets = set(re.findall(r"EDEN_PAD_\w+ .*?(?:user|foreground|initial)=(\d{6,})", raw))
    for s in list(secrets):
        secrets |= {hex(int(s))[2:], f"{int(s):08x}"}
    path = os.path.expanduser("~/.eglantine-private")
    if os.path.exists(path):
        secrets |= {l.strip() for l in open(path) if l.strip() and not l.startswith("#") and len(l.strip()) >= 6}
    return secrets


def pack(run_dir, out, author="GrowingBlackBeans", run_id=None, date=None, alpha_env=None, dry_run=False):
    run = pathlib.Path(run_dir).resolve()
    out = pathlib.Path(out).resolve()
    ghb = load_his_redaction(out)
    rf = RunFolder(run)
    log = rf.path / "eden_log.txt"
    if not log.is_file():
        log = next((p for p in (rf.path / "logs").glob("eden_log.txt*")), None) if (rf.path / "logs").is_dir() else None
    if log is None or not log.is_file():
        sys.exit(f"no eden_log.txt in {run}")

    row = stk_score.score_run(run, alpha_env)
    for key in DROP_FROM_ROW:
        row.pop(key, None)
    declared = {}
    if (run / "declared.json").is_file():
        declared = json.loads((run / "declared.json").read_text())

    batch_date, time = date_from_batch(run)
    date = date or batch_date
    if date is None:
        sys.exit(f"{run} is not in a batch folder (auto-YYYYMMDD-HHMMSS-batch-...): pass --date YYYY-MM-DD")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        sys.exit(f"--date {date}: want YYYY-MM-DD")
    run_id = redact(run_id or run.name, ghb, {})          # the id goes into a folder name: redacted too
    target = out / "runs" / author / f"{date}-{run_id}"
    if dry_run:
        print(f"would write {target}")
        print(f"  derived: firmware {row.get('firmware')}, build {row.get('build_key')}, "
              f"route {row.get('route_key')}, {row.get('cache_class')}, key {row.get('comparison_key')}")
        return target, {}
    if target.exists():
        sys.exit(f"{target} exists")

    counts: dict = {}
    secrets = private_words(log.read_text(errors="replace"))
    target.mkdir(parents=True)
    try:
        for name, packed_name, do_gzip in FILES:
            source = rf.path / name
            if not source.is_file() and (rf.path / "logs" / name).is_file():
                source = rf.path / "logs" / name
            if not source.is_file():
                continue
            raw = source.read_text(errors="replace")
            text = redact_config(raw, ghb, counts) if name == "config.json" else redact(raw, ghb, counts)
            if do_gzip:
                with gzip.open(target / packed_name, "wt", compresslevel=9) as handle:
                    handle.write(text)
            else:
                (target / packed_name).write_text(text)
        for crash in sorted(list(rf.path.glob("crash-*")) + list((rf.path / "logs").glob("crash-*") if (rf.path / "logs").is_dir() else [])):
            if crash.is_file():
                (target / crash.name).write_text(redact(crash.read_text(errors="replace"), ghb, counts))

        info = {
            "format": 1,
            "packer": PACKER_VERSION,
            "author": author,
            "run_id": run_id,
            "date": date,
            "time": time,
            "game": GAME_ID,
            "declared": declared,
            "derived": json.loads(redact(json.dumps(row), ghb, counts)),
            "redacted": counts,
        }
        (target / "run.json").write_text(json.dumps(info, indent=1, ensure_ascii=False) + "\n")

        problems = audit(target, secrets)
        if problems:
            shutil.rmtree(target)
            print("REFUSED, nothing written:", *problems, sep="\n  ", file=sys.stderr)
            return None, counts
    except Exception:
        shutil.rmtree(target, ignore_errors=True)
        raise
    return target, counts


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pack one run folder into a GreenHatBoy clone, facts from the logs.")
    ap.add_argument("run")
    ap.add_argument("--out", required=True, help="a GreenHatBoy clone (nothing is pushed)")
    ap.add_argument("--author", default="GrowingBlackBeans")
    ap.add_argument("--id", dest="run_id", help="run id (default: the folder's name)")
    ap.add_argument("--date", help="YYYY-MM-DD; needed unless the run sits in an auto-...-batch- folder")
    ap.add_argument("--alpha-env", default=stk_score.DEFAULT_ALPHA_ENV)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    target, counts = pack(a.run, a.out, a.author, a.run_id, a.date, a.alpha_env, a.dry_run)
    if target is None:
        return 2
    print(target, counts if counts else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
