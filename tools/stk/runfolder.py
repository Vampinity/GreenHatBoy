"""One reader for every run folder, raw or packed, whoever made it (the run contract, 16 Nov 2026).

A run's files are found by name, in this order: the folder itself, the folder as `.gz`, `logs/`, and
`logs/` as `.gz`. So one call reads a packed GHB run (`stderr.log.gz` beside `eden_log.txt.gz`), a
contract raw folder (everything flat) and an older folder of ours (dumps under `logs/`).

Crash files are matched to THIS run, never just globbed: a `crash-*.txt` belongs to the run when its
`version:` equals the boot trace's build and its "N s after the app started" is within a minute after
the run's last log timestamp. Other sessions' crash files in the same folder are ignored and counted.

After a crash the app starts itself again, so the main logs are the relaunch's (after_crash=1, and no script or game
started). Then the run's crash is the newest one of its build, and its logs are that crash's copies (22 Nov).

Standard library only. Reads; never writes.
"""
from __future__ import annotations

import gzip
import re
from pathlib import Path

_TS = re.compile(r"^\[\s*([\d.]+)\]")
_CRASH_VER = re.compile(r"^version:\s*(\S+)", re.M)
_CRASH_AGE = re.compile(r",\s*(\d+)\s*s after the app started")
_BOOT_VER = re.compile(r"diagnostic build\s+(\S+)")


class RunFolder:
    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()
        if not self.path.is_dir():
            raise FileNotFoundError(f"Run directory not found: {self.path}")
        self._cache: dict[str, str] = {}

    def find(self, name: str) -> Path | None:
        for base in (self.path, self.path / "logs"):
            for cand in (base / name, base / (name + ".gz")):
                if cand.is_file():
                    return cand
        return None

    def text(self, name: str) -> str:
        if name in self._cache:
            return self._cache[name]
        p = self.find(name)
        if p is None:
            out = ""
        elif p.suffix == ".gz":
            with gzip.open(p, "rt", errors="replace") as f:
                out = f.read()
        else:
            out = p.read_text(errors="replace")
        self._cache[name] = out
        return out

    def lines(self, name: str) -> list[str]:
        t = self.text(name)
        return t.splitlines() if t else []

    def has(self, name: str) -> bool:
        return self.find(name) is not None

    def last_app_time(self) -> float | None:
        for line in reversed(self.lines("eden_log.txt")[-400:]):
            m = _TS.match(line)
            if m:
                return float(m.group(1))
        return None

    def boot_version(self) -> str | None:
        m = _BOOT_VER.search(self.text("boot-trace.txt"))
        return m.group(1) if m else None

    def is_relaunch(self) -> bool:
        """The main logs are the app starting again after a crash: no script and no game ran in them."""
        head = self.lines("stderr.log")[:5]
        return (any("EDEN_CRASH_REPORT" in l and "after_crash=1" in l for l in head)
                and "EDEN_TEST script_start" not in self.text("stderr.log")
                and "EDEN_GUEST_START" not in self.text("eden_log.txt"))

    def crash_files(self) -> tuple[list[Path], int]:
        """This run's crash reports, and how many other crash reports were in the folder."""
        found: list[Path] = []
        for base in (self.path, self.path / "logs"):
            if base.is_dir():
                found += [p for p in base.glob("crash-*.txt")
                          if re.fullmatch(r"crash-\d{8}-\d{6}\.txt", p.name)]
        if not found:
            return [], 0
        ver, last = self.boot_version(), self.last_app_time()
        relaunch = self.is_relaunch()
        if relaunch:
            last = None          # the relaunch's clock says nothing about when the crashed session died
        mine, others = [], 0
        for p in sorted(found):
            t = p.read_text(errors="replace")
            v, a = _CRASH_VER.search(t), _CRASH_AGE.search(t)
            same_build = ver is None or (v is not None and v.group(1) == ver)
            near_end = last is None or (a is not None and last - 5 <= float(a.group(1)) <= last + 60)
            if same_build and near_end:
                mine.append(p)
            else:
                others += 1
        # A packed run holds only its own crash file; trust it when nothing else can be checked.
        if not mine and len(found) == 1 and ver is None and last is None:
            return found, 0
        if relaunch and len(mine) > 1:      # names are crash-<date>-<time>: the newest is the one just before it
            others += len(mine) - 1
            mine = mine[-1:]
        return mine, others
