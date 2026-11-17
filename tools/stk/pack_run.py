#!/usr/bin/env python3
"""pack_run.py: pack any run folder into the shared layout, under the run contract (17 Nov 2026).

    python3 -I pack_run.py RUN --out <GreenHatBoy clone> [--id ID] [--author NAME] [--date YYYY-MM-DD]
                               [--alpha-env <the control's env.txt>] [--dry-run]

What it is, and what it is not:

- The **facts are derived from the logs**, by the shared scorer (`stk_score.score_run`): firmware, build,
  route and its proof, store, cache class, the windows, survival. Nothing about the run's conditions is
  typed in. That is the run contract's first rule, and the reason this exists: Vampinity's
  `tools/pack-run.py` takes them from a row in his own `runs.jsonl` and writes `"firmware": "12.40"`
  literally, which is right on his console and wrong everywhere else.
- **Redaction is his**, imported from `tools/pack-run.py` (home paths, e-mail, LAN and MAC addresses, the
  console user number in decimal and hex, the login name, every word in `~/.eglantine-private`). Two
  rules of ours are added: the save-profile id under `user/save/...`, and the launcher's profile name.
  His file is not modified, so his own clean-up of it can land without a conflict.
- It **writes only under --out**, and audits what it wrote: if any private pattern survives, the packed
  folder is deleted and the exit code is 2.

Standard library only.
"""
from __future__ import annotations
import argparse, datetime, gzip, importlib.util, json, os, pathlib, re, shutil, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stk_score  # noqa: E402
from runfolder import RunFolder  # noqa: E402

PACKER_VERSION = "pack_run 1 (Vampinity's pack-run.py redaction + the run contract, 17 Nov 2026)"

# Ours, on top of his: a save-profile id is 32 hex under user/save/<title>/, and the launcher prints the
# profile's name, which can be an account name.
EXTRA = [
    ("save_profile", re.compile(r"(user/save/\d{16}/)[0-9A-Fa-f]{32}"), r"\1<profile>"),   # the console writes it in upper case
    ("profile_name", re.compile(r"(launch: Profile ).*"), r"\1<redacted>"),
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

    run_id = run_id or run.name
    date = date or datetime.date.fromtimestamp(log.stat().st_mtime).isoformat()
    time = datetime.datetime.fromtimestamp(log.stat().st_mtime).strftime("%H:%M:%S")
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
            text = redact(source.read_text(errors="replace"), ghb, counts)
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
            "game": "0400486024DEC000",
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
    ap.add_argument("--date", help="YYYY-MM-DD (default: the eden_log's file date)")
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
