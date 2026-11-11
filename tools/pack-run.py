#!/usr/bin/env python3
"""pack-run.py: turn one test-run folder into the shared layout GrowingBlackBeans proposed (11 Nov 2026):

    runs/<author>/<date>-<run-id>/
        eden_log.txt.gz     the emulator's log, redacted, compressed
        env.txt             the settings file of that run
        run.json            build, firmware, console, route, ending, fps summary, impressions
        stderr.log.gz       (extra, optional) the memory census and gate lines live here in our builds

  pack-run.py <run folder> --out <repo root> [--author Vampinity] [--row '<json line from runs.jsonl>']
  pack-run.py --all <logs root> --runs-file <runs.jsonl> --out <repo root>      (backfill)

Redaction is built in and counted (the counts go into run.json under "redacted" and are summed at the end):
home folders in local paths, LAN addresses, MAC addresses, e-mail addresses, this machine's login name, and every
word listed in ~/.eglantine-private (first name, console name, serials). Nothing is sent anywhere: this only writes files under --out.
A provisional packer for our own backfill; when the shared repo's own pack-run.py exists, run that instead.
Standard library only.
"""
import argparse, gzip, json, pathlib, re, sys

REDACT = [
    ("home_path", re.compile(r"/(Users|home)/[^/\s\"']+"), r"/\1/USER"),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "EMAIL"),
    ("lan_ip", re.compile(r"\b(?:192\.168|10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b"), "LAN_IP"),
    ("mac", re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b"), "MAC"),
    ("console_user", re.compile(r"(?i)\b(user(?:_?id)?)\s*=\s*(?:0x[0-9a-f]{4,}|\d{4,})"), r"\1=REDACTED"),   # EDEN_PAD_OPEN ... user=<number>
    ("other_dump", re.compile(r"(No cover extracted from )[^\n]*?\.(nup|nsp|xci)\b"), r"\1<other title>.\2"),   # file names of other game dumps
    ("psn_id", re.compile(r"(?i)\b(online[_ ]?id|account[_ ]?id|psn[_ ]?id|np[_ ]?id)\s*[=:]\s*\S+"), r"\1=REDACTED"),
    ("serial", re.compile(r"(?i)\b(serial(?:[_ ]?number)?)\s*[=:]\s*\S+"), r"\1=REDACTED"),
]

# Words that are private to whoever runs this (login name, first name, console name, serials) never go into the tool:
# the login name is taken from this machine, the rest from ~/.eglantine-private, one word or phrase per line.
import os
_private = [os.path.basename(os.path.expanduser("~"))]
try:
    _private += [w.strip() for w in open(os.path.expanduser("~/.eglantine-private")) if w.strip() and not w.startswith("#")]
except OSError:
    pass
for _w in sorted(set(_private), key=len, reverse=True):
    if len(_w) >= 3:
        REDACT.append(("private_word", re.compile(r"(?<![A-Za-z])" + re.escape(_w) + r"(?![a-z])", re.I), "owner"))


_PAD_ID = re.compile(r"(?i)EDEN_PAD[^\n]*?\b(?:user|foreground|initial)=(\d{4,})")
_PAD_FIELD = re.compile(r"(?i)\b(foreground|initial)\s*=\s*(?:0x[0-9a-f]{4,}|\d{4,})")


def redact(text, counts):
    # the console's user number: taken from the EDEN_PAD lines, then removed wherever it occurs, decimal or hex
    for number in set(_PAD_ID.findall(text)):
        for form in {number, "%x" % int(number), "%X" % int(number), "%08x" % int(number), "%08X" % int(number)}:
            text, n = re.subn(r"(?<![0-9A-Za-z])(?:0x)?" + re.escape(form) + r"(?![0-9A-Za-z])", "REDACTED", text)
            if n:
                counts["console_user"] = counts.get("console_user", 0) + n
    text, n = _PAD_FIELD.subn(r"\1=REDACTED", text)
    if n:
        counts["console_user"] = counts.get("console_user", 0) + n
    for name, pattern, repl in REDACT:
        text, n = pattern.subn(repl, text)
        if n:
            counts[name] = counts.get(name, 0) + n
    return text


def scrub(value, counts):
    """Redact every string inside a JSON value."""
    if isinstance(value, str):
        return redact(value, counts)
    if isinstance(value, list):
        return [scrub(v, counts) for v in value]
    if isinstance(value, dict):
        return {k: scrub(v, counts) for k, v in value.items()}
    return value


def pack(run, out, author, row):
    run = pathlib.Path(run)
    batch = run.parent.name                       # auto-YYYYMMDD-HHMMSS-batch-<name>
    m = re.match(r"auto-(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})-batch-(.+)", batch)
    date = f"{m[1]}-{m[2]}-{m[3]}" if m else "unknown-date"
    target = pathlib.Path(out) / "runs" / author / f"{date}-{redact(run.name, {})}"      # folder names are redacted too
    log = run / "eden_log.txt"
    if not log.exists():
        return None, {}
    target.mkdir(parents=True, exist_ok=True)
    counts = {}
    for name in ("eden_log.txt", "stderr.log"):
        source = run / name
        if source.exists():
            text = redact(source.read_text(errors="replace"), counts)
            with gzip.open(target / (name + ".gz"), "wt", compresslevel=9) as handle:
                handle.write(text)
    env = run / "env.txt"
    env_lines = []
    if env.exists():
        text = redact(env.read_text(errors="replace"), counts)
        (target / "env.txt").write_text(text)
        env_lines = [l for l in text.splitlines() if l.strip() and not l.startswith("#")]
    result = json.loads((run / "result.json").read_text()) if (run / "result.json").exists() else {}
    row = row or {}
    build, fps, ending, valid = row.get("build") or {}, row.get("fps") or {}, row.get("ending") or {}, row.get("validity") or {}
    flick, stut = row.get("flicker") or {}, row.get("stutter") or {}
    info = {
        "format": 0,
        "author": author,
        "run_id": run.name,
        "date": date,
        "time": f"{m[4]}:{m[5]}:{m[6]}" if m else None,
        "batch": m[7] if m else batch,
        "test": row.get("test") or result.get("name"),
        "game": "0400486024DEC000",
        "build": {"tag": build.get("name"), "commit": build.get("commit"), "version": build.get("version"),
                  "eboot_sha256_16": build.get("eboot_hash")},
        "firmware": "12.40",
        "console": "PS5 (base model)",
        "route": {"script": row.get("script"), "script_sha": row.get("script_sha")},
        "menu_settings": None,
        "env_lines": len(env_lines),
        "env_hash": row.get("env_hash"),
        "control": row.get("is_control"),
        "ending": {"kind": ending.get("kind") or result.get("ending"), "class": ending.get("class"),
                   "seconds": ending.get("seconds") or result.get("seconds"), "crash_app_s": ending.get("crash_app_s")},
        "valid": valid.get("valid"),
        "gameplay_s": valid.get("gameplay_s"),
        "fps": {"mean": fps.get("mean"), "source": fps.get("source"),
                "p99_ms": (fps.get("stutter") or {}).get("p99_ms_median"), "worst_ms": (fps.get("stutter") or {}).get("worst_ms")},
        "worst_frame_ms": stut.get("worst_frame_ms"),
        "runtime_pipeline_builds": stut.get("pipelines"),
        "flashes_per_min": flick.get("flashes_per_min"),
        "note": row.get("note"),
        "impressions": "",
        "flash_times": [],
    }
    info = scrub(info, counts)
    info["redacted"] = counts
    (target / "run.json").write_text(json.dumps(info, indent=1, ensure_ascii=False) + "\n")
    return target, counts


def main():
    p = argparse.ArgumentParser()
    p.add_argument("run", nargs="?")
    p.add_argument("--all")
    p.add_argument("--runs-file")
    p.add_argument("--row")
    p.add_argument("--out", required=True)
    p.add_argument("--author", default="Vampinity")
    p.add_argument("--console", help='for example "PS5 base 13.60" (written into run.json)')
    p.add_argument("--route", help="where you played or which script ran")
    p.add_argument("--notes", help="what you saw, rough flash times")
    a = p.parse_args()
    if a.run:
        target, counts = pack(a.run, a.out, a.author, json.loads(a.row) if a.row else None)
        if target and (a.console or a.route or a.notes):
            f = target / "run.json"; info = json.loads(f.read_text()); extra = {}
            if a.console: info["console"] = a.console; info["firmware"] = None
            if a.route: info["route"]["script"] = redact(a.route, extra)
            if a.notes: info["impressions"] = redact(a.notes, extra)
            f.write_text(json.dumps(info, indent=1, ensure_ascii=False) + "\n")
        print(target, counts)
        return
    rows = {}
    for line in open(a.runs_file):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        rows[(r.get("batch"), r.get("run"))] = r          # the last (newest) line for a run wins
    total, packed = {}, 0
    for (batch, run), row in sorted(rows.items()):
        folder = pathlib.Path(a.all) / batch / run
        if not folder.is_dir():
            continue
        target, counts = pack(folder, a.out, a.author, row)
        if target:
            packed += 1
            for k, v in counts.items():
                total[k] = total.get(k, 0) + v
    print(f"packed {packed} runs; redactions: {total}")


if __name__ == "__main__":
    sys.exit(main())
