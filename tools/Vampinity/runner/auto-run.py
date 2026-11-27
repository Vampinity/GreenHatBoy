#!/usr/bin/env python3
"""Run a list of agreed EglantinePS5 tests on the console with nobody at the controller.

  auto-run.py PLAN.json --host <console>             prints the plan, sends nothing to the console
  auto-run.py PLAN.json --host <console> --go        runs it
  auto-run.py --restore-env --host <console> --go    puts env.txt back after a run that could not

For each test: check the app is closed, write env.txt, start the app through /launch, follow its
logs, save frames from OBS, end on a crash, a freeze, silence or the time limit, close the app with
test-quit, keep everything in a new folder. Then one page: summary.md in the batch folder.

Closed means: ShadowMount took the app's sandbox mounts away, or, for a process it does not track
(it keeps its mounts), the app took test-quit away, --close-floor seconds have passed since, and no
log of it has grown for --close-quiet seconds. Never earlier. With --save the next test's save goes
back right then, while this Mac checks the video and writes the reports; the next /launch waits for
it. --save-late puts it back before each start instead, after the whole --settle pause, as it used
to be; with --close-quiet 0 as well, the time between two tests is what it was.

A test may carry "config": settings laid over the app's eglantineps5.json as it was at the batch
start, for that test only. Tests without it get the batch-start file back once one has changed it,
and it goes back at the end, as env.txt does (--restore-env too).

A test may carry "live": one start of the game that changes switches while it runs (A/B/A/B at one
spot) instead of one setting per start. It needs a build with EDEN_UP_LIVE_SWITCHES (patch 0478):

  "live": {"phases": {"A": ["EDEN_UP_OOT_FRAME_WAIT=1"], "B": ["EDEN_UP_OOT_FRAME_WAIT=0"]},
           "order": "ABBA", "period": 20, "rounds": 3, "settle": 2, "start": 5}

  phases   name -> NAME=VALUE lines, only switches listed in live-switches.json (the ones the app can
           change while it runs). A switch a phase does not name has its env value.
  order    the phases of one round (default: as written). ABBA cancels a slow drift.
  period   seconds per phase; settle: seconds at the start of a phase the app does not count (default 2)
  rounds   how often the order runs (default 1); then every switch goes back to its env value
  start    seconds to wait after the test spot is reached (default 5): the WAIT line with LIVE in its
           comment, else the script's gameplay WAIT (postprocess.py's rule), or the game starting when
           the script has no WAIT line

The tool adds EDEN_UP_LIVE_SWITCHES=1 to env.txt, removes a live-switches.txt left on the console
before the start, writes the whole schedule once when the spot is reached (the app steps through the
phases by its own clock and logs each one), and removes the file after the test. The test ends as any
other: give the script a stand long enough for start + phases x period. postprocess.py compares the
phases. A plan without "live" runs exactly as before.

A freeze, a device-lost, a system error with no crash file, or an app that does not answer stops
the whole batch: notification, env.txt put back, nothing else sent. The next steps are the owner's.

Cold start (18 Nov 2026, shared copy): EDEN_TEST_COLD=1 in a test's env, or --cold for every test.
Right before the start, with the app closed, the shader store (<data>/user/cache/shader/<title>) and
the driver cache (<data>/cache/radv) are renamed to <name>.cold-aside-<time>. After the test, once
the app is closed (also after a crash, a stop or Ctrl-C), what the start built is renamed to
<name>.cold-built-<time> and the old ones go back, checked by a listing. Renames only, nothing is
deleted. Every --go (and --restore-env --go) first puts back any .cold-aside- folder left behind.
The shader set's two input files (*.nx2recipe and shader_set_index.txt) stay in place by default: a
new, empty title folder is made and they are renamed into it, and back before the put-back.
EDEN_TEST_COLD_SET=1 moves the set aside too. Neither line reaches env.txt. See cold_caches.py.

Caches line (21 Nov 2026): after every start, warm or cold, one line says which caches the runner set
aside and put back, and what the boot log says the start reused (the store's name, new or reused, its
pipeline count, the driver pipeline cache). It goes to batch.log, to result.json ("caches") and to
summary.md, and for a cold start to cold.log too. A start that was not asked to be cold moves nothing
and restores nothing: the line only reports what the boot found.

Whole-cache restore (23 Nov 2026, GrowingBlackBeans' warm-run-steps.md step 0): --warm-copy <copy folder>.
At the batch start, with the app closed, the owner's <data>/user/cache and <data>/cache are listed and
renamed to <name>.warm-owner-aside (never deleted). Before every start the copy is checked against its
SHA-256 list, the owner's folders are listed again and must be unchanged, then the two live folders are
renamed aside to <name>.old-<time> (one rename each, nothing walked, nothing deleted) and the copy is
uploaded whole into new folders, listed (same files and sizes) and partly read back byte for byte. At the
end (also after a stop, a crash or Ctrl-C, once the app is closed) the test folders are renamed aside the
same way and the owner's folders are renamed back, checked by a listing. Anything that does not match
refuses. The .old- folders stay on the console (one whole cache per start) for the owner to remove by hand;
summary.md lists them. Make the copy once with --make-warm-copy <folder> --go (reads only), check it with
--check-warm-copy <folder>. Not with a cold start in the same batch. See warm_cache.py.

Launcher (23 Nov 2026, for a console without websrv's /launch): --launcher websrv (default, /launch as
always) or --launcher prosperomgr (ProsperoMgr's POST /api/titles/launch, port 7070 unless set in
runner-config.json "launcher"). --check-launcher --go asks the launcher for the running title (and
ProsperoMgr for its temperatures) and starts nothing. The runner still reads the console's files, logs and
listings through websrv's /fs: --launcher changes only how the app is started. See launchers.py.

Added 12 Nov 2026:
  - <plan>.stop.json next to a plan holds early-stop rules (fired, aid-control, clear; stop-rules.py, which
    is not in this folder: without it every start runs).
    Skipped starts are listed in summary.json "skipped", never in "tests". --no-stop-rules ignores the file.
  - The first network drop of a batch (no answer with a network error) no longer stops it: wait up to
    --net-resume-minutes for the console, close a game that is alive, mark that start "network drop" (not
    counted) and run it once more. A second drop stops the batch as before. --no-net-resume: as before.
  - --launch-fast-check: after the first 503 look for the open app every 0.5 s (up to --poll s).
The plain guide is GUIDE.md beside this file. Standard library only.

Fresh-boot detection by the boot trace and reading crash reports follow the idea of heydemoura's
tools/mkw-bench-console.py (GPL-3.0-or-later), written anew here.
"""
import argparse
import pathlib
import shutil
import base64
import contextlib
import copy
import dataclasses
import fcntl
import ftplib
import hashlib
import http.client
import importlib.util
import io
import json
import math
import os
import posixpath
import re
import signal
import socket
import statistics
import struct
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import runner_config  # noqa: E402  every per-person setting comes from runner-config.json
import cold_caches  # noqa: E402  EDEN_TEST_COLD=1 / --cold: the shader store and driver cache aside for a start
import warm_cache  # noqa: E402  --warm-copy: the whole cache put back from one copy before every start
import launchers  # noqa: E402  --launcher: websrv's /launch (default) or ProsperoMgr's API

SETTINGS = runner_config.load()
APP = SETTINGS["app"]["id"]
DATA = SETTINGS["app"]["data_dir"].rstrip("/")
LOG_DIR = DATA + "/logs"
EDEN_DIR = DATA + "/user/log"
EDEN_LOG = EDEN_DIR + "/eden_log.txt"
BOOT_TRACE = LOG_DIR + "/boot-trace.txt"
RECORDED = LOG_DIR + "/recorded-input.txt"
TEST_QUIT = DATA + "/test-quit"
BOOT_ONCE = DATA + "/test-boot-once"
STDERR_LOG = LOG_DIR + "/stderr.log"
CONFIG = DATA + "/config/eglantineps5.json"
LIVE_FILE = DATA + "/live-switches.txt"  # the app's default EDEN_UP_LIVE_SWITCHES_FILE
SHADOWMOUNT_LOG = SETTINGS["app"]["shadowmount_log"]
ENV_FOLDERS = list(SETTINGS["app"]["env_folders"])  # as set-env.py; settings: app.env_folders

OUT_ROOT = runner_config.folder("out_root")  # settings: folders.out_root
# A copy of this file kept in a subfolder named next/ reads the main folder's data and helpers; the code it
# changes comes from its own folder when it is there. In this folder HERE and TOOLS are the same.
HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent if HERE.name == "next" else HERE
LIVE_LIST = TOOLS / "live-switches.json"  # the switches the app can change while it runs


def code_file(name):
    """A tool file: this folder's copy when it has one (next/), else the tools folder's."""
    return HERE / name if (HERE / name).exists() else TOOLS / name


_rules_module = None


def stop_rules_module():
    """next/stop-rules.py (early stop inside a batch). None when it is not there: every start runs."""
    global _rules_module
    if _rules_module is None and code_file("stop-rules.py").exists():
        spec = importlib.util.spec_from_file_location("stop_rules", code_file("stop-rules.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _rules_module = module
    return _rules_module


# A network drop (11 Nov 11:41, 21:50: "No route to host" for about a minute while the game ran on): the error
# texts that mean one.
NETWORK_ERROR = re.compile(r"No route to host|Network is unreachable|Host is down|timed out|Connection refused|"
                           r"Connection reset")

PLAN_KEYS = {"name", "title", "env", "seconds", "script", "may_hang", "record", "note", "config", "live"}
LIVE_KEYS = {"phases", "order", "period", "rounds", "settle", "start"}
LIVE_NAME = re.compile(r"[A-Za-z0-9_.-]{1,24}")
TITLE = re.compile(r"[0-9a-fA-F]{16}")
ENV_LINE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=[^\n]*")
CRASH_REPORT = re.compile(r"crash-\d{8}-\d{6}\.txt")
CRASH_STEM = re.compile(r"crash-\d{8}-\d{6}")
PAD_BUTTONS = frozenset("CROSS CIRCLE SQUARE TRIANGLE L1 R1 L2 R2 L3 R3 OPTIONS CREATE TOUCHPAD UP DOWN LEFT RIGHT "
                        "A B X Y L R ZL ZR PLUS MINUS LEFT_STICK RIGHT_STICK".split())  # test_harness.h
SCRIPT_TIME = re.compile(r"(\d*)\.?(\d*)")
WAITED = re.compile(rb"has waited (\d+) s")
GAME_STARTED = (b"EDEN_GAME_SESSION_BEGIN", b"guest threads t=")
TRACE_GAME = (b"loading the game", b"game loaded")
OTHER_GAME = re.compile(r"(PPSA|CUSA)\d{5}_\d{3}")
FRAME_LINE = re.compile(r"EDEN_VULKAN_FRAME .*?fps=([\d.]+)")
BUILD = re.compile(r"diagnostic build (\S+ \([^)]*\))")
HEAD = 400  # first bytes of the boot trace: its pid and timings tell one process from the next
CHUNK = 16 << 20  # most of a log to fetch in one look, so a burst cannot run into the timeout

ENDINGS = {
    "time_limit": "reached the time limit",
    "crash": "crash",
    "restart": "app restarted without a crash file",
    "no_game": "game did not start",
    "freeze": "FREEZE",
    "device_lost": "GPU DEVICE LOST",
    "system_error": "SYSTEM ERROR, no crash file",
    "no_answer": "NO ANSWER",
    "interrupted": "stopped by hand",
    "not_started": "did not start",
    "tool_error": "this tool failed",
    "cold_not_back": "COLD START: CACHES NOT BACK",
    "warm_failed": "WHOLE-CACHE RESTORE STOPPED HALF WAY",
    "warm_not_back": "WHOLE-CACHE RESTORE: THE OWNER'S CACHES NOT BACK",
}


class NoAnswer(Exception):
    """The console did not reply to a request."""


class Stop(Exception):
    """This ends the batch. kind is a key of ENDINGS."""

    def __init__(self, kind, detail):
        super().__init__(detail)
        self.kind, self.detail = kind, detail


class Refused(Exception):
    """A write this tool must never do. Reaching this is a bug, so nothing catches it."""


# ---------------------------------------------------------------- plan

@dataclasses.dataclass
class Test:
    number: int
    name: str
    title: str
    seconds: float
    env: list
    script: Path | None
    may_hang: bool
    record: bool
    note: str
    config: dict | None = None  # settings laid over eglantineps5.json for this test only
    live: dict | None = None  # switches changed while the game runs (live_problems made it whole)
    cold: bool = False  # EDEN_TEST_COLD=1 or --cold: shader store and driver cache aside for this start
    cold_set: bool = False  # EDEN_TEST_COLD_SET=1: the shader set (recipe and index) aside too

    @property
    def slug(self):
        return slugify(self.name)

    @property
    def script_name(self):
        return f"auto-run-{self.slug}.txt"

    @property
    def env_text(self):
        # EDEN_TEST_COLD(_SET) is for this runner only: the app's env.txt stays the same as a warm start's.
        lines = [line for line in self.env if not line.startswith(("EDEN_TEST_BOOT=", cold_caches.COLD_LINE + "=",
                                                                   cold_caches.SET_LINE + "="))]
        if self.live is not None and not any(line.startswith("EDEN_UP_LIVE_SWITCHES=") for line in lines):
            lines.append("EDEN_UP_LIVE_SWITCHES=1")
        lines.append(f"EDEN_TEST_BOOT={self.title}")
        if self.script:
            lines.append(f"EDEN_TEST_SCRIPT={self.script_name}")
        if self.record:
            lines.append("EDEN_TEST_RECORD=1")
        return "\n".join(lines) + "\n"


def slugify(text):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-.")[:48]


def plain_number(text, most):
    """The app's Number(): digits only, no sign, no exponent, at most `most`."""
    if not re.fullmatch(r"[0-9]+", text) or int(text) > most:
        raise ValueError
    return int(text)


def script_seconds(text):
    """The app's Seconds(): "12", "12.5", ".25", "7."."""
    found = SCRIPT_TIME.fullmatch(text)
    if not found or not (found[1] or found[2]) or int(found[1] or 0) > 10_000_000:
        raise ValueError
    return float(f"{found[1] or 0}.{found[2] or 0}")


def check_script(text):
    """(problems, time of the last event) for a pad script. The same rules as ParseLine in
    test_harness.h: one line the app cannot read loses the whole script, so it fails here instead."""
    problems, last = [], 0.0
    for number, raw in enumerate(text.split("\n"), 1):
        parts = raw.split("#", 1)[0].split()
        if not parts:
            continue
        try:
            stick = len(parts) > 1 and parts[1] in ("LSTICK", "RSTICK")
            if len(parts) != (5 if stick else 3):
                raise ValueError
            at = script_seconds(parts[0])
            hold = plain_number(parts[-1], 86_400_000)
            if hold == 0:
                raise ValueError
            if stick:
                plain_number(parts[2], 255), plain_number(parts[3], 255)
            elif parts[1] not in PAD_BUTTONS:
                raise ValueError
            last = max(last, at + hold / 1000)
        except ValueError:
            problems.append(f"line {number}: {raw.strip()!r}")
    return problems, last


# A test's "live": see the top of this file. live-switches.json is the list of what the app can change:
# {"switches": {NAME: {"kind": "one" | "mode" | "frames", "armed": bool, "needs_when_off": [env lines]}}}.
# kind is how the app reads the value ("one": only an exact 1 is on; "mode": unset or 0... is off;
# "frames": a number, 0 is off). armed: it only changes anything when it was on in env.txt at boot.

def live_list():
    try:
        return json.loads(LIVE_LIST.read_text())["switches"]
    except (OSError, ValueError, KeyError, TypeError):
        return None


def live_on(kind, value):
    """Whether the app takes `value` (None: not set) as on, for a switch of this kind."""
    if kind == "one":
        return value == "1"
    if kind == "mode":
        return value is not None and not value.startswith("0")
    found = re.match(r"[0-9]+", value or "")
    return bool(found and int(found[0]))


def live_problems(live, env):
    """(problems, the "live" value made whole) for a test's "live" and its env lines."""
    problems = []
    if not isinstance(live, dict):
        return ["live must be an object"], None
    for key in sorted(set(live) - LIVE_KEYS):
        problems.append(f"live: unknown key {key!r}")
    known = live_list()
    if known is None:
        problems.append(f"live: cannot read {LIVE_LIST.name}, the list of switches the app can change")
        known = {}
    set_at_boot = {}
    for line in env:
        name, _, value = line.partition("=")
        set_at_boot[name] = value
    phases = live.get("phases")
    if not isinstance(phases, dict) or not phases:
        return problems + ["live: needs phases, an object of name -> NAME=VALUE lines"], None
    if len(phases) > 16:
        problems.append("live: at most 16 phases")
    for name, lines in phases.items():
        if not LIVE_NAME.fullmatch(name) or name == "end":
            problems.append(f"live: phase name {name!r} (letters, digits, _ . -, at most 24)")
        if not isinstance(lines, list) or not all(isinstance(e, str) and ENV_LINE.fullmatch(e) for e in lines):
            problems.append(f"live: phase {name} must be a list of NAME=VALUE lines")
            continue
        for line in lines:
            switch, _, value = line.partition("=")
            entry = known.get(switch)
            if entry is None:
                if known:
                    problems.append(f"live: {switch} cannot change while the game runs "
                                    f"(the ones that can: {', '.join(sorted(known))})")
                continue
            if entry.get("armed") and not live_on(entry.get("kind"), set_at_boot.get(switch)):
                problems.append(f"live: {switch} must be on in env: it only changes when it was on at boot")
    # A switch is off in some phase when a phase says so, or leaves it at an env value that is off.
    named = {line.partition("=")[0] for lines in phases.values() if isinstance(lines, list)
             for line in lines if isinstance(line, str)}
    for switch in sorted(named & set(known)):
        entry = known[switch]
        off = False
        for lines in phases.values():
            values = [line.partition("=")[2] for line in lines if isinstance(line, str)
                      and line.partition("=")[0] == switch] if isinstance(lines, list) else []
            off = off or not live_on(entry.get("kind"), values[-1] if values else set_at_boot.get(switch))
        for need in entry.get("needs_when_off", []) if off else []:
            if need not in env:
                problems.append(f"live: {switch} is off in a phase, which needs {need} in env")
    order = live.get("order", list(phases))
    if isinstance(order, str):
        # "ABBA" with one-letter phases, as the app reads it
        order = (re.split(r"[ ,]+", order.strip()) if re.search(r"[ ,]", order) or order in phases
                 else list(order))
    if not isinstance(order, list) or not order or not all(isinstance(o, str) and o in phases for o in order):
        problems.append("live: order must name phases, e.g. \"ABBA\" or [\"on\", \"off\"]")
        order = list(phases)
    if len(order) > 256:
        problems.append("live: at most 256 phases in a round")
    numbers = {}
    for key, default, low, high in (("period", None, 5, 3600), ("settle", 2, 0, 600), ("start", 5, 0, 3600)):
        value = live.get(key, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
            problems.append(f"live: {key} must be a number of seconds from {low} to {high}")
            value = default or low
        numbers[key] = value
    rounds = live.get("rounds", 1)
    if isinstance(rounds, bool) or not isinstance(rounds, int) or not 1 <= rounds <= 10000:
        problems.append("live: rounds must be a whole number from 1")
        rounds = 1
    if numbers["settle"] >= numbers["period"]:
        problems.append("live: settle must be shorter than period, or no frame is counted")
    problems = list(dict.fromkeys(problems))  # a switch named in two phases is one problem
    return problems, {"phases": phases, "order": order, "rounds": rounds, **numbers}


def live_seconds(live):
    """From the test spot to the end of the schedule."""
    return live["start"] + len(live["order"]) * live["rounds"] * live["period"]


def live_text(live, ident):
    """The control file, as common/live_switch.h reads it. "end" last: the app ignores a file without it."""
    lines = [f"id={ident}", f"period_ms={round(live['period'] * 1000)}", f"settle_ms={round(live['settle'] * 1000)}",
             f"order={','.join(live['order'])}", f"repeat={live['rounds']}"]
    for name, switches in live["phases"].items():
        lines.append(f"[{name}]")
        lines += switches
    return "\n".join(lines + ["end"]) + "\n"


def live_gameplay_line(script):
    """The 1-based line of the WAIT that means "at the test spot": a WAIT line with LIVE in its comment
    (live-plan.py --spot last tags one), else the script's gameplay WAIT by postprocess.py's rule, None
    without one. A script's presses count from the WAIT before them, so presses timed to the phases
    need that same WAIT as the spot."""
    if script is None:
        return None
    with contextlib.suppress(OSError, UnicodeDecodeError):
        for number, raw in enumerate(script.read_text().split("\n"), 1):
            code, _, comment = raw.partition("#")
            parts = code.split()
            if len(parts) > 1 and parts[1] == "WAIT" and re.search(r"\bLIVE\b", comment):
                return number
    try:
        spec = importlib.util.spec_from_file_location("postprocess_for_live", code_file("postprocess.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.gameplay_wait_line(script.read_text())[0]
    except Exception:  # postprocess.py is another tool: a fault there must not stop a test
        return None


# A test's "config": settings for the app's eglantineps5.json, e.g. {"performance": {"unsafe_cpu": true}}.
# Objects merge key by key into the file as it was at the batch start; any other value replaces.

def config_problems(config):
    """What is wrong with a plan's config, [] if nothing. null and NaN would reach the app's parser."""
    if not isinstance(config, dict) or not config:
        return ["config must be an object with at least one setting"]
    problems = []

    def walk(value, name):
        if value is None:
            problems.append(f"config {name} is null")
        elif isinstance(value, float) and not math.isfinite(value):
            problems.append(f"config {name} is not a finite number")
        elif isinstance(value, dict):
            if not value:
                problems.append(f"config {name} is an empty object")
            for key, inner in value.items():
                walk(inner, f"{name}.{key}" if name else key)
        elif isinstance(value, list):
            for index, inner in enumerate(value):
                walk(inner, f"{name}[{index}]")

    walk(config, "")
    return problems


def config_settings(config, keys=()):
    """(keys, value) for every setting a config sets, objects opened up."""
    for key, value in config.items():
        if isinstance(value, dict):
            yield from config_settings(value, keys + (key,))
        else:
            yield keys + (key,), value


def show_setting(keys, value):
    return ".".join(keys) + "=" + json.dumps(value, ensure_ascii=False)


def merge_config(base, overrides):
    """A new document: base with overrides laid over it. Neither argument changes."""
    merged = copy.deepcopy(base)

    def lay(into, over):
        for key, value in over.items():
            if isinstance(value, dict) and isinstance(into.get(key), dict):
                lay(into[key], value)
            else:
                into[key] = copy.deepcopy(value)

    lay(merged, overrides)
    return merged


def config_bytes(document, like):
    """The file as the app writes it: two-space indent, UTF-8, the last newline as `like` has it.
    For every copy of the app's file kept so far this gives its exact bytes back."""
    text = json.dumps(document, indent=2, ensure_ascii=False)
    return (text + ("\n" if like.endswith(b"\n") else "")).encode()


def read_config(data):
    """(document, None), or (None, why it cannot be the base of a test's config)."""
    if data is None:
        return None, "it is not there"
    if not data.strip():
        return None, "it is empty"
    try:
        document = json.loads(data)
    except ValueError as error:
        return None, f"it is not JSON ({error})"
    if not isinstance(document, dict):
        return None, "it is not a JSON object"
    return document, None


def setting_at(document, keys):
    """(True, value) if the document has that setting, else (False, None)."""
    for key in keys:
        if not isinstance(document, dict) or key not in document:
            return False, None
        document = document[key]
    return True, document


def config_kind(value):
    if isinstance(value, bool):
        return "true/false"
    if value is None:
        return "null"
    return {int: "number", float: "number", str: "text", list: "list", dict: "object"}.get(type(value), "?")


def same_setting(one, other):
    """Equal as JSON values: true is not 1, but 1 is 1.0 (the app may write a number either way)."""
    if config_kind(one) == config_kind(other) == "number":
        return one == other
    return json.dumps(one, sort_keys=True) == json.dumps(other, sort_keys=True)


def config_surprises(base, overrides):
    """Settings the app's file does not have (a typo?) or where the value changes its kind."""
    found = []
    for keys, value in config_settings(overrides):
        there, old = setting_at(base, keys)
        if not there:
            # The deepest part that is there tells a new game or a new key from a typo'd section.
            for depth in range(len(keys) - 1, -1, -1):
                if setting_at(base, keys[:depth])[0]:
                    break
            found.append(f"{'.'.join(keys)} is not in the app's file" +
                         (f" (it has no {'.'.join(keys[:depth + 1])})" if depth < len(keys) - 1 else ""))
        elif config_kind(old) != config_kind(value):
            found.append(f"{'.'.join(keys)} is {config_kind(old)} in the app's file, the plan gives "
                         f"{config_kind(value)}")
    return found


def load_plan(path):
    """The plan's tests. Exits listing everything wrong with it, so one fix round is enough."""
    try:
        entries = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        sys.exit(f"Cannot read the plan: {error}")
    if not isinstance(entries, list) or not entries:
        sys.exit("The plan must be a JSON list with at least one test.")
    problems, tests = [], []
    for number, entry in enumerate(entries, 1):
        def bad(text):
            problems.append(f"test {number}: {text}")
        if not isinstance(entry, dict):
            bad("not an object")
            continue
        # A typo in may_hang would quietly drop the safety mark, so an unknown key is an error.
        for key in sorted(set(entry) - PLAN_KEYS):
            bad(f"unknown key {key!r}")
        name = entry.get("name")
        if not isinstance(name, str) or not slugify(name):
            bad("needs a name")
            name = f"test-{number}"
        env = entry.get("env", [])
        if not isinstance(env, list) or not all(isinstance(e, str) and ENV_LINE.fullmatch(e) for e in env):
            bad("env must be a list of NAME=VALUE lines")
            env = []
        title = entry.get("title")
        booted = [e.split("=", 1)[1] for e in env if e.startswith("EDEN_TEST_BOOT=")]
        if booted and title and booted != [title]:
            bad("title and EDEN_TEST_BOOT disagree")
        title = title or (booted[0] if booted else None)
        if not isinstance(title, str) or not TITLE.fullmatch(title):
            bad("needs a title of 16 hex digits (title, or EDEN_TEST_BOOT in env)")
            title = "F" * 16
        elif not int(title, 16):
            # The app's search takes a file it cannot read for title 0, so this would boot that file.
            bad("title 0 would boot the first unreadable file in roms/")
        for line in env:
            if line.startswith(("EDEN_TEST_SCRIPT=", "EDEN_TEST_RECORD=")):
                bad(f"{line.split('=')[0]} comes from the script and record keys, not from env")
        cold_lines = [line.split("=", 1)[1] for line in env if line.split("=", 1)[0] == cold_caches.COLD_LINE]
        if len(cold_lines) > 1 or any(value not in ("0", "1") for value in cold_lines):
            bad(f"{cold_caches.COLD_LINE} must be there once, as =1 (cold start) or =0 (not)")
        set_lines = [line.split("=", 1)[1] for line in env if line.split("=", 1)[0] == cold_caches.SET_LINE]
        if len(set_lines) > 1 or any(value not in ("0", "1") for value in set_lines):
            bad(f"{cold_caches.SET_LINE} must be there once, as =1 (the shader set aside too) or =0 (kept in place)")
        seconds = entry.get("seconds")
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not 0 < seconds < float("inf"):
            bad("needs seconds, a number above 0")
            seconds = 1
        script = entry.get("script")
        if script is not None:
            script = (path.parent / script).resolve()
            try:
                wrong, _ = check_script(script.read_text())
                if wrong:
                    bad(f"script {script.name}: bad lines: {'; '.join(wrong[:5])}")
            except (OSError, UnicodeDecodeError) as error:
                bad(f"cannot read the script: {error}")
                script = None
        flags = {}
        for key in ("may_hang", "record"):
            flags[key] = entry.get(key, False)
            if not isinstance(flags[key], bool):
                bad(f"{key} must be true or false")
                flags[key] = True
        if script is not None and flags["record"]:
            bad("script and record together: the app plays the script and records nothing")
        config = entry.get("config")  # absent or null: the app's file stays as it was at the batch start
        if config is not None:
            for problem in config_problems(config):
                bad(problem)
        live = entry.get("live")  # absent or null: no switch changes while the game runs
        if live is not None:
            wrong, live = live_problems(live, env)
            for problem in wrong:
                bad(problem)
            if flags["record"]:
                bad("live and record together: a recorded route is not a fixed spot")
        tests.append(Test(number, name, title, seconds, env, script, flags["may_hang"], flags["record"],
                          str(entry.get("note", "")), config, live, cold=cold_lines == ["1"],
                          cold_set=set_lines == ["1"]))
    slugs = [test.slug for test in tests]
    for slug in sorted({s for s in slugs if slugs.count(s) > 1}):
        problems.append(f"two tests share the name {slug}")
    if sum(test.may_hang for test in tests) > 1:
        problems.append("more than one may_hang test: at most one per console boot")
    if problems:
        sys.exit("The plan has problems, nothing was done:\n  " + "\n  ".join(problems))
    return tests


def newest_config_copy(root):
    """(path, document) of the newest config-before.json a batch here kept, (None, None) if none.
    Only for the plan print: a batch lays a test's config over the console's file as it is then."""
    copies = []
    with contextlib.suppress(OSError):
        copies = sorted(Path(root).glob("auto-*/config-before.json"), key=lambda p: p.stat().st_mtime)
    for path in reversed(copies):
        with contextlib.suppress(OSError):
            document, _ = read_config(path.read_bytes())
            if document is not None:
                return path, document
    return None, None


def config_print_lines(config, reference):
    lines = []
    for keys, value in config_settings(config):
        text = show_setting(keys, value)
        if reference is not None:
            there, old = setting_at(reference, keys)
            if not there:
                text += "  (not in the app's file)"
            else:
                text += f"  (now {json.dumps(old, ensure_ascii=False)}"
                text += ", another kind of value)" if config_kind(old) != config_kind(value) else ")"
        lines.append(text)
    return lines


def script_lint(script, tools):
    """What lint-scripts.py says about a script's timing: presses written as steps from the line
    before (a section's seconds count from its WAIT), presses dropped after END. Only ever a warning:
    [] when that tool is not there, fails or takes too long."""
    lint = tools / "lint-scripts.py"
    if not lint.exists():
        return []
    try:
        done = subprocess.run([sys.executable, str(lint), str(script)], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return []
    return [line.strip() for line in done.stdout.splitlines() if line.startswith("    ")]


def warm_copy_size(folder):
    """ " (<size>)" of a whole-cache copy by its manifest (no hashing; the check comes later), or ""."""
    try:
        manifest = json.loads((Path(folder) / "manifest.json").read_text())
        size = sum(sum(tree["files"].values()) for tree in manifest["trees"].values())
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return ""
    return f" ({warm_cache.human(size)})"


def print_plan(tests, args, blocks):
    total = sum(test.seconds for test in tests)
    configured = [test for test in tests if test.config is not None]
    reference_path, reference = newest_config_copy(args.out_root) if configured else (None, None)
    print(f"Plan {args.plan.name}: {len(tests)} test(s), up to {total / 60:.0f} min of play, console {args.host}")
    for test in tests:
        marks = [mark for mark, on in (("MAY HANG", test.may_hang), ("records the pad", test.record)) if on]
        print(f"\n{test.number}. {test.name}  ({test.seconds:g} s)" + (f"  [{', '.join(marks)}]" if marks else ""))
        if test.note:
            print(f"   {test.note}")
        print("   env.txt: " + test.env_text.strip().replace("\n", "\n            "))
        if test.cold:
            print("   COLD START: before the start the shader store and the driver cache are renamed aside "
                  "(" + ", ".join(path for _, path in cold_caches.targets(DATA, test.title)) + "); after the test "
                  "what the start built is kept as *.cold-built-<time> and the old ones go back, checked by a listing")
            # (the plan print names no EDEN_TEST_ line outside env.txt: the desk test checks that)
            print("   the shader set (*.nx2recipe, shader_set_index.txt) " +
                  ("goes aside too" if test.cold_set else "stays in place (the README says how to move it too)"))
        if test.script:
            _, last = check_script(test.script.read_text())
            print(f"   script {test.script.name}: last event {last:g} s after the guest starts")
            if last >= test.seconds:
                print("   WARNING: the time limit ends before the script does")
            else:
                print("   The time limit counts from /launch, the script from the guest starting, "
                      "which comes later: leave room for the boot.")
            for problem in script_lint(test.script, args.tools):
                print(f"   WARNING, script timing (lint-scripts.py): {problem}")
        if test.config is not None:
            print("   config: " + "\n           ".join(config_print_lines(test.config, reference)))
        if test.live is not None:
            live = test.live
            print(f"   live: {len(live['order']) * live['rounds']} phases of {live['period']:g} s "
                  f"({','.join(live['order'])} x {live['rounds']}), the first {live['settle']:g} s of each not "
                  f"counted; starts {live['start']:g} s after the test spot and takes {live_seconds(live):.0f} s "
                  "from there")
            for name, switches in live["phases"].items():
                print(f"         [{name}] " + (" ".join(switches) or "(env values)"))
            if live_seconds(live) + 30 > test.seconds:
                print("   WARNING: the time limit leaves under 30 s for the boot and the way to the test spot")
    if getattr(args, "warm_copy", None) is not None:
        print(f"\nWHOLE-CACHE RESTORE from the copy {args.warm_copy.name}: at the start the owner's {DATA}/user/cache and "
              f"{DATA}/cache are renamed to *{warm_cache.ASIDE} (never deleted); before every start the copy is checked "
              "against its SHA-256 list, the two live folders are renamed aside to *.old-<time> (nothing is deleted) "
              "and the copy uploaded whole, listed and partly read back; at the end the test folders are renamed aside "
              "the same way and the owner's folders go back, checked by a listing.")
        print(f"   ROOM ON THE CONSOLE: every start leaves its whole test cache behind as *.old-<time> (renamed aside "
              f"before the next start, or at the end): {len(tests)} set(s) for this plan, each about as big as the copy"
              + warm_copy_size(args.warm_copy) + ". The runner never deletes them: remove them by hand when you "
              "no longer need them (summary.md lists them).")
    if getattr(args, "launcher", "websrv") != "websrv":
        print(f"\nLAUNCHER: {launchers.describe(args)}. Files, logs and listings are still read through websrv's /fs.")
    hang = [test for test in tests if test.may_hang]
    if hang:
        print(f"\nWARNING: '{hang[0].name}' can hang the GPU, and a GPU hang has frozen the whole console. "
              "Plan a reboot and re-jailbreak after it.")
        if hang[0] is not tests[-1]:
            print("It is not the last test: if it hangs, the tests after it do not run.")
    print("\nEvery test runs with exactly these env lines, env.txt is replaced for the test and put back after.")
    if configured:
        print(f"{len(configured)} test(s) with config: those settings go over {posixpath.basename(CONFIG)} as it is at "
              "the batch start, the other tests run with that file as it was, and it is put back after.")
        print(f"'now' is from {reference_path.parent.name}/config-before.json, the newest copy here."
              if reference_path else "No batch here kept a config-before.json, so the settings are not checked "
              "against the app's file yet.")
    for block in blocks:
        print(f"BLOCKED: {block}")


# ---------------------------------------------------------------- the console

def writable(path):
    """The only console paths this tool may write, rename to or delete."""
    if path == CONFIG:  # a test's config, and the batch-start file put back (put stages it under .new)
        return True
    folder, name = posixpath.split(path)
    if folder in ENV_FOLDERS:
        return name in ("env.txt", "env.txt.new")
    if folder == DATA:
        return (path in (TEST_QUIT, BOOT_ONCE, LIVE_FILE, LIVE_FILE + ".new")
                or bool(re.fullmatch(r"auto-run-[A-Za-z0-9._-]+\.txt(\.new)?", name)))
    return False


class Console:
    """Everything that talks to the PS5. Only --go ever makes one."""

    def __init__(self, args):
        self.host, self.ftp_port, self.timeout = args.host, args.ftp_port, args.timeout
        self.web = f"http://{args.host}:{args.web_port}"

    def _get(self, url, headers=None, timeout=None, tries=2):
        """A second try, so one Wi-Fi hiccup between two tests does not stop a whole batch."""
        request = urllib.request.Request(url, headers=headers or {})
        for attempt in range(tries):
            try:
                with urllib.request.urlopen(request, timeout=timeout or self.timeout) as response:
                    return response.status, response.read()
            except urllib.error.HTTPError as error:
                return error.code, b""
            except (OSError, http.client.HTTPException) as error:
                failure = error
                time.sleep(min(1, self.timeout))
        raise NoAnswer(str(failure)) from failure

    def read(self, path, offset=0, length=None):
        """A file's bytes from offset, None if it is not there. Only the new part of a log travels."""
        headers = {}
        if offset or length:
            last = "" if length is None else offset + length - 1
            headers["Range"] = f"bytes={offset}-{last}"
        status, data = self._get(f"{self.web}/fs{urllib.parse.quote(path)}", headers)
        if status == 404:
            return None
        if status == 416:
            return b""
        if status == 200:  # an older websrv ignores Range and sends the whole file
            return data[offset:None if length is None else offset + length]
        if status == 206:
            return data
        raise NoAnswer(f"HTTP {status} for {path}")

    def list(self, path):
        """{name: entry} of a folder, None if it is not there."""
        status, data = self._get(f"{self.web}/fs{urllib.parse.quote(path)}?fmt=json")
        if status == 404:
            return None
        if status != 200:
            raise NoAnswer(f"HTTP {status} for {path}")
        try:
            return {entry["name"]: entry for entry in json.loads(data)}
        except (ValueError, KeyError, TypeError) as error:
            raise NoAnswer(f"bad listing of {path}") from error

    def launch(self):
        """Start EglantinePS5, and nothing else. Returns the HTTP status.

        websrv's /launch first kills whatever big app is open, so callers make sure it is closed."""
        return self._get(f"{self.web}/launch?titleId={APP}", timeout=3 * self.timeout, tries=1)[0]

    @contextlib.contextmanager
    def _ftp(self):
        client = ftplib.FTP()
        try:
            try:
                client.connect(self.host, self.ftp_port, timeout=self.timeout)
            except OSError:
                time.sleep(min(1, self.timeout))
                client.connect(self.host, self.ftp_port, timeout=self.timeout)
            client.login()
            client.encoding = "utf-8"
            client.voidcmd("TYPE I")
            yield client
            client.quit()
        except (OSError, EOFError, ftplib.Error) as error:
            raise NoAnswer(f"FTP: {error}") from error
        finally:
            client.close()

    def check_ftp(self):
        with self._ftp():
            pass

    @staticmethod
    def _retrieve(client, path):
        data = io.BytesIO()
        try:
            client.retrbinary(f"RETR {path}", data.write)
        except ftplib.error_perm:
            return None
        return data.getvalue()

    def read_ftp(self, path):
        with self._ftp() as client:
            return self._retrieve(client, path)

    def put(self, path, data):
        """set-env.py's write: stage under .new, read it back, rename into place, read that back.
        All over FTP, so env.txt can still go back when websrv is gone, as it can be after a boot."""
        if not writable(path):
            raise Refused(path)
        with self._ftp() as client:
            client.storbinary(f"STOR {path}.new", io.BytesIO(data))
            if self._retrieve(client, path + ".new") != data:
                raise NoAnswer(f"staged copy of {path} does not match, nothing replaced")
            client.rename(path + ".new", path)
            if self._retrieve(client, path) != data:
                raise NoAnswer(f"{path} does not match after the rename")

    def touch(self, path):
        if not writable(path):
            raise Refused(path)
        with self._ftp() as client:
            client.storbinary(f"STOR {path}", io.BytesIO(b""))

    def remove(self, path):
        if not writable(path):
            raise Refused(path)
        with self._ftp() as client:
            # Not client.delete(): ftpsrv answers DELE with 226, which ftplib calls an error.
            client.sendcmd(f"DELE {path}")

    def rename_cold(self, source, target):
        """A cold start's rename: a cache folder inside its own folder, or a shader-set file between the title
        folder and its .cold-aside- folder (cold_caches.py allowed_pair). ColdCaches.rename and move_file list
        right before (target not there: the console's RNTO would replace it) and right after."""
        if not cold_caches.allowed_pair(source, target, DATA):
            raise Refused(f"{source} -> {target}")
        with self._ftp() as client:
            client.rename(source, target)

    def mkdir_cold(self, path):
        """The cold start's one other write: the empty live title folder, so the shader set can stay in place
        (cold_caches.py allowed_folder; ColdCaches.make_folder lists right before and right after)."""
        if not cold_caches.allowed_folder(path, DATA):
            raise Refused(path)
        with self._ftp() as client:
            # sendcmd, not client.mkd(): any 2xx answer will do; the listing after it is the proof.
            client.sendcmd(f"MKD {path}")

    def download(self, path, dest):
        """A console file streamed to dest over the web server (a whole-cache copy): (bytes, sha256). The file
        is written under .part and only renamed to dest once the read is complete. NoAnswer on any failure."""
        found, size = hashlib.sha256(), 0
        part = dest.with_name(dest.name + ".part")
        request = urllib.request.Request(f"{self.web}/fs{urllib.parse.quote(path)}")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response, open(part, "wb") as out:
                if response.status != 200:
                    raise NoAnswer(f"HTTP {response.status} for {path}")
                for chunk in iter(lambda: response.read(4 << 20), b""):
                    out.write(chunk)
                    found.update(chunk)
                    size += len(chunk)
        except urllib.error.HTTPError as error:
            raise NoAnswer(f"HTTP {error.code} for {path}") from error
        except (OSError, http.client.HTTPException) as error:
            raise NoAnswer(f"the read of {path} broke off ({error})") from error
        os.replace(part, dest)
        return size, found.hexdigest()

    @contextlib.contextmanager
    def warm_writer(self):
        """One FTP session for the whole-cache restore's writes (thousands of files: one session, not one each)."""
        with self._ftp() as client:
            yield WarmWriter(client)

    def sandboxes(self):
        entries = self.list("/mnt/sandbox")
        if entries is None:
            raise NoAnswer("/mnt/sandbox is not there")
        return entries

    def mounted_sandboxes(self):
        """The app's sandboxes with their mounts, as "name@mtime".

        A running app's sandbox holds data, mnt and preinst (never app0, seen from outside). When it
        closes, ShadowMount unmounts them and an empty entry stays. It only does that for a process
        it started: one that came back after a crash keeps its mounts after closing, until the next
        launch. So mounted means the app may be open, and not mounted means it is closed."""
        return {f"{name}@{entry.get('mtime')}" for name, entry in self.sandboxes().items()
                if name.startswith(APP) and "data" in (self.list(f"/mnt/sandbox/{name}") or {})}

    def other_games(self):
        """Other titles that look open. /launch would kill them."""
        return [name for name in self.sandboxes() if OTHER_GAME.fullmatch(name) and not name.startswith(APP)
                and len(self.list(f"/mnt/sandbox/{name}") or {}) > 1]


class WarmWriter:
    """The whole-cache restore's writes on one FTP session. Each is checked here against warm_cache.py's rules
    (write_ok, rename_ok) before it is sent: MKD and STOR only inside <data>/user/cache and <data>/cache, never
    under a .warm-owner-aside or .old- name; renames only live <-> live.warm-owner-aside and live ->
    live.old-<time>. warm_cache.py lists right before and after."""

    def __init__(self, client):
        self.client = client

    @staticmethod
    def _check(ok, what, *paths):
        if not ok:
            raise Refused(f"{what} {' -> '.join(paths)}")

    def mkd(self, path):
        self._check(warm_cache.write_ok(path, DATA), "MKD", path)
        self.client.sendcmd(f"MKD {path}")  # any 2xx; the listing after is the proof

    def stor(self, local, path):
        self._check(warm_cache.write_ok(path, DATA), "STOR", path)
        with open(local, "rb") as handle:
            self.client.storbinary(f"STOR {path}", handle)

    # No dele and no rmd: the whole-cache restore deletes nothing (23 Nov 2026). websrv's and its FTP server's
    # listings follow links, so a delete that walks them could go through a link; a live folder is renamed aside
    # to <folder>.old-<time> instead, one RNTO on its top name (warm_cache.py).

    def rename(self, source, target):
        self._check(warm_cache.rename_ok(source, target, DATA), "RENAME", source, target)
        self.client.rename(source, target)


# ---------------------------------------------------------------- frames (obs/grab.py, obs/loop.py)

class Obs:
    def __init__(self, host, port):
        self.socket = socket.create_connection((host, port), timeout=5)
        key = base64.b64encode(os.urandom(16)).decode()
        self.socket.sendall(f"GET / HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
                            "Sec-WebSocket-Protocol: obswebsocket.json\r\n\r\n".encode())
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = self.socket.recv(4096)
            if not chunk:
                raise EOFError("OBS closed the connection")
            data += chunk
        self.buffer = data.split(b"\r\n\r\n", 1)[1]
        if "authentication" in self.receive()["d"]:
            raise OSError("OBS asks for a password, turn it off in Tools > WebSocket Server Settings")
        self.send({"op": 1, "d": {"rpcVersion": 1}})
        self.receive()
        self.scene = self.request("GetCurrentProgramScene")["responseData"]["currentProgramSceneName"]

    def _take(self, count):
        while len(self.buffer) < count:
            chunk = self.socket.recv(1 << 20)
            if not chunk:
                raise EOFError("OBS closed the connection")
            self.buffer += chunk
        taken, self.buffer = self.buffer[:count], self.buffer[count:]
        return taken

    def receive(self):
        head = self._take(2)
        length = head[1] & 127
        if length == 126:
            length = struct.unpack(">H", self._take(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", self._take(8))[0]
        return json.loads(self._take(length))

    def send(self, message):
        payload, mask = json.dumps(message).encode(), os.urandom(4)
        size = len(payload)
        head = bytes([0x81]) + (bytes([0x80 | size]) if size < 126 else bytes([0x80 | 126]) + struct.pack(">H", size))
        self.socket.sendall(head + mask + bytes(c ^ mask[i % 4] for i, c in enumerate(payload)))

    def request(self, kind, data=None):
        self.send({"op": 6, "d": {"requestType": kind, "requestId": kind, "requestData": data or {}}})
        while True:
            answer = self.receive()
            if answer.get("op") == 7:
                return answer["d"]

    def frame(self):
        answer = self.request("GetSourceScreenshot", {"sourceName": self.scene, "imageFormat": "jpg",
                                                      "imageWidth": 640, "imageCompressionQuality": 70})
        return base64.b64decode(answer["responseData"]["imageData"].split(",", 1)[1])

    def close(self):
        self.socket.close()


CAPTURE_SOURCE = SETTINGS["capture"]["source"]  # the capture card's source in OBS (obs-fit.py sets its fit)


def capture_fills(transform, width, height):
    """obs-fit.py's test: the source is shown over the canvas's whole width or whole height."""
    return abs(transform["width"] - width) < 2 or abs(transform["height"] - height) < 2


def capture_fit(args):
    """(fills, what OBS shows). fills is None when OBS does not answer or has no such source: then
    nothing is known, and nothing is refused."""
    try:
        obs = Obs(args.obs_host, args.obs_port)
    except (OSError, EOFError, ValueError, KeyError, TypeError) as error:
        return None, f"OBS did not answer ({error})"
    try:
        video = obs.request("GetVideoSettings")["responseData"]
        width, height = video["baseWidth"], video["baseHeight"]
        items = obs.request("GetSceneItemList", {"sceneName": obs.scene})["responseData"]["sceneItems"]
        item = next((i for i in items if i.get("sourceName") == CAPTURE_SOURCE), None)
        if item is None:
            return None, f"no source named {CAPTURE_SOURCE!r} in OBS's scene"
        shown = obs.request("GetSceneItemTransform", {"sceneName": obs.scene, "sceneItemId": item["sceneItemId"]})[
            "responseData"]["sceneItemTransform"]
        return capture_fills(shown, width, height), (
            f"the capture source is {shown['sourceWidth']:.0f}x{shown['sourceHeight']:.0f}, shown "
            f"{shown['width']:.0f}x{shown['height']:.0f} on a {width}x{height} canvas")
    except (OSError, EOFError, ValueError, KeyError, TypeError) as error:
        return None, f"OBS gave no answer to use ({error!r})"
    finally:
        with contextlib.suppress(OSError):
            obs.close()


class FrameSaver(threading.Thread):
    """Saves a frame every few seconds. A run never depends on OBS: errors only end up in a note."""

    def __init__(self, host, port, folder, every):
        super().__init__(daemon=True)
        self.host, self.port, self.folder, self.every = host, port, folder, every
        self.done = threading.Event()
        self.client = None
        self.count = 0
        self.error = None

    def grab(self):
        try:
            if self.client is None:
                self.client = Obs(self.host, self.port)
            data = self.client.frame()
            self.folder.mkdir(exist_ok=True)
            self.count += 1
            (self.folder / f"f{self.count:04d}-{time.strftime('%H%M%S')}.jpg").write_bytes(data)
        except (OSError, EOFError, ValueError, KeyError, IndexError, TypeError) as error:
            self.error = str(error) or type(error).__name__
            if self.client:
                self.client.close()
            self.client = None

    def run(self):
        while True:
            self.grab()
            if self.done.wait(self.every):
                return

    def finish(self):
        """Stop, after one last frame: it is the one that shows an error on screen."""
        self.done.set()
        self.join(timeout=15)
        self.grab()
        if self.client:
            self.client.close()


class VideoRecorder:
    """Records the whole test through OBS, then runs video-check.py on it. A run never depends on
    this: errors only end up in a note. Stops short of filling the disk."""

    MIN_FREE = 8 << 30

    def __init__(self, host, port, folder):
        self.host, self.port, self.folder = host, port, folder
        self.client, self.error, self.saved = None, None, None

    def start(self):
        try:
            if shutil.disk_usage(self.folder).free < self.MIN_FREE:
                self.error = "under 8 GB free, no video"
                return
            self.client = Obs(self.host, self.port)
            if self.client.request("GetRecordStatus")["responseData"].get("outputActive"):
                self.error = "OBS was already recording, no video"
                self.client.close()
                self.client = None
                return
            self.client.request("StartRecord")
        except (OSError, EOFError, ValueError, KeyError, TypeError) as error:
            self.error = str(error) or type(error).__name__
            self.client = None

    def finish(self):
        if not self.client:
            return
        try:
            path = pathlib.Path(self.client.request("StopRecord")["responseData"]["outputPath"])
            size = -1
            for _ in range(40):  # OBS finishes the file after it answers
                time.sleep(0.5)
                now = path.stat().st_size if path.exists() else -1
                if now == size and now > 0:
                    break
                size = now
            self.saved = self.folder / f"video{path.suffix}"
            shutil.move(str(path), str(self.saved))
            subprocess.run([sys.executable, str(code_file("video-check.py")), str(self.saved),
                            "--out", str(self.folder)], capture_output=True, timeout=600)
        except (OSError, EOFError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
            self.error = str(error) or type(error).__name__
        finally:
            self.client.close()


def trash_old_videos(out_root, keep):
    """Old test videos are moved to the folder named in the settings (folders.video_trash): the reports and
    sheets stay. With no such folder the videos stay where they are."""
    trash = runner_config.folder("video_trash")
    if trash is None:
        return
    for video in pathlib.Path(out_root).glob("auto-*/run*/video.*"):
        if keep in video.parents:
            continue
        with contextlib.suppress(OSError):
            trash.mkdir(parents=True, exist_ok=True)
            shutil.move(str(video), str(trash / f"{video.parent.name}{video.suffix}"))


# ---------------------------------------------------------------- logs

class Follower:
    """A local copy of one console log, fetched as it grows. It only ever appends, so a new process
    rewriting the log on the console cannot wipe the run's copy."""

    def __init__(self, remote, local, limit):
        self.remote, self.local, self.limit, self.have, self.tail = remote, local, limit, 0, b""
        self.cut = False

    def update(self, console, size):
        """New bytes, with the end of the last ones in front so a split marker is still found.
        With some switches heap.log has reached 500 MB, so a copy stops at the limit. The looking
        goes on past it, at the end of the log: a freeze must be seen however long the log is."""
        if size is None or size <= self.have:
            return b""
        keep = self.have < self.limit
        if not keep:
            self.cut = True
            self.have = max(self.have, size - CHUNK)
        data = console.read(self.remote, offset=self.have,
                            length=min(CHUNK, self.limit - self.have) if keep else CHUNK)
        if not data:
            return b""
        if keep:
            with open(self.local, "ab") as out:
                out.write(data)
        self.have += len(data)
        scan, self.tail = self.tail + data, data[-200:]
        return scan


def differs(one, other):
    """Do two file starts prove two files? A start that is still short proves nothing yet."""
    shortest = min(len(one), len(other))
    return shortest > 0 and one[:shortest] != other[:shortest]


def find_stop(data):
    """(kind, the log line) if these log bytes hold a freeze or a device-lost."""
    def line_at(position):
        start = data.rfind(b"\n", 0, position) + 1
        end = data.find(b"\n", position)
        return data[start:None if end < 0 else end].decode(errors="replace").strip()[:200]

    position = data.find(b"DEVICE_LOST")
    if position >= 0:
        return "device_lost", line_at(position)
    for match in WAITED.finditer(data):
        if int(match[1]) >= 30:
            return "freeze", line_at(match.start())
    return None


def read_crash(folder):
    """Fields of the newest crash report in a run folder, None if it has none."""
    reports = sorted(p for p in folder.glob("crash-*.txt") if CRASH_REPORT.fullmatch(p.name))
    if not reports:
        return None
    text = reports[-1].read_text(errors="replace")
    fields = dict(re.findall(r"^(what|reason|where|thread|time|memory|then): (.*)$", text, re.M))
    fields["report"] = reports[-1].name
    return fields


def crash_closes(fields):
    """The report says no new process comes: a crash right after a restart, or a GPU hang."""
    return "closes" in (fields or {}).get("then", "")


def crash_text(fields):
    thread = re.sub(r"\s*\(0x[0-9a-f]+\)$", "", fields.get("thread", "?"))
    return f"{fields.get('reason') or fields.get('what', '?')} on {thread} at {fields.get('where', '?')}"


def fps_numbers(folder):
    """(median, last) frame rate from the crash set's heap log if there is one, else heap.log."""
    logs = sorted(folder.glob("crash-*-heap.log")) or [folder / "heap.log"]
    if not logs[-1].exists():
        return None
    values = [float(v) for v in FRAME_LINE.findall(logs[-1].read_text(errors="replace"))]
    return (statistics.median(values), values[-1]) if values else None


# ---------------------------------------------------------------- what outlives this process

def load_state(root):
    """{} only when there is no file. A file that cannot be read may hold a stop or the way back to
    env.txt, so nothing goes on until someone has looked at it."""
    path = root / "auto-run-state.json"
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as error:
        sys.exit(f"Cannot read {path}: {error}\nIt may hold a stop or the saved env.txt, so nothing was done.")


def save_state(root, state):
    temporary = root / "auto-run-state.json.new"
    temporary.write_text(json.dumps(state, indent=2))
    os.replace(temporary, root / "auto-run-state.json")


def blocked(state, tests, args):
    """Why a --go may not start. Reads only the state file on the Mac."""
    reasons = []
    pending = state.get("pending_restore")
    if pending:
        files = "env.txt and eglantineps5.json" if pending.get("config") is not None else "env.txt"
        reasons.append(f"{files} from {pending['batch']} was never put back: run --restore-env first")
    cold = state.get("cold_pending")
    if cold and cold.get("host") != args.host:
        reasons.append(f"a cold start in {cold.get('batch')} left caches aside on another console: run "
                       "--restore-env --go with that console's --host first")
    warm = state.get("warm_pending")
    if warm and warm.get("host") != args.host:
        reasons.append(f"a whole-cache restore in {warm.get('batch')} left the owner's caches aside on another "
                       "console: run --restore-env --go with that console's --host first")
    stopped = state.get("stopped")
    if stopped and not (args.clear_stop or args.new_boot):
        reasons.append(f"the last batch stopped on {stopped['kind']} ({stopped['test']}, {stopped['when']}). "
                       "Look at the console first, then add --clear-stop, or --new-boot if it was rebooted")
    hang = state.get("hang_test")
    if hang and any(test.may_hang for test in tests) and not args.new_boot:
        reasons.append(f"'{hang['test']}' already used this console boot's may_hang test ({hang['when']}). "
                       "Reboot the console, then add --new-boot")
    return reasons


@contextlib.contextmanager
def only_one_run(root):
    with open(root / ".auto-run.lock", "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            sys.exit("Another auto-run is running.")
        yield


def ignore_signals():
    """A second Ctrl-C must not cut off the way back to the old env.txt."""
    for number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(number, signal.SIG_IGN)


def notify(args, title, text):
    """A notification (settings: notify.command). It must never be what takes a stop down, so it
    swallows its own errors."""
    if args.notify_file:
        with open(args.notify_file, "a") as out:
            out.write(f"{title}: {text}\n")
        return
    runner_config.notify(title, text)


def put_env_back(console, before, config=None):
    """Return each env.txt to what it was. Where there was none, remove ours: set-env.py --off would
    rename it over any env.txt.off the owner keeps. Raises NoAnswer if a folder cannot be checked.
    config: the batch-start eglantineps5.json, put back after env.txt when a test changed it."""
    if console.read_ftp(BOOT_ONCE) is not None:  # asked for a start that never came: it must not come now
        console.remove(BOOT_ONCE)
    for folder, text in before.items():
        path = f"{folder}/env.txt"
        data = None if text is None else base64.b64decode(text)
        if data is not None:
            console.put(path, data)
        elif console.read_ftp(path) is not None:
            console.remove(path)
        if console.read_ftp(path) != data:
            raise NoAnswer(f"{path} is not back")
    if config is not None:
        console.put(CONFIG, config)
        if console.read_ftp(CONFIG) != config:
            raise NoAnswer(f"{CONFIG} is not back")


def cold_keeper(state, root, batch, run, host, note_file):
    """keep(note) for cold_caches: the note into note_file (a run or batch folder), and while anything may be
    aside, into the state file too (cold_pending), so the next --go or --restore-env --go finds the way back.
    The note holds console paths, counts and sizes only: no address, no folder of this computer."""
    def keep(note):
        note_file.write_text(json.dumps(note, indent=2) + "\n")
        current = state.get("cold_pending")
        if note["status"] in cold_caches.OPEN:
            state["cold_pending"] = {"batch": batch, "run": run, "host": host, "note": note}
        elif current and current.get("batch") == batch and current.get("run") == run:
            state.pop("cold_pending")
        save_state(root, state)
    return keep


def warm_keeper(state, root, batch, host, note_file):
    """keep(note) for warm_cache: the note into note_file, and while the owner's folders may be aside, into the
    state file too (warm_pending), so the next --go or --restore-env --go puts them back first. The note holds
    console paths, counts, sizes and the copy's folder name only: no address, no folder of this computer."""
    def keep(note):
        note_file.write_text(json.dumps(note, indent=2) + "\n")
        current = state.get("warm_pending")
        if note["status"] in warm_cache.OPEN:
            state["warm_pending"] = {"batch": batch, "host": host, "note": note}
        elif current and current.get("batch") == batch:
            state.pop("warm_pending")
        save_state(root, state)
    return keep


def console_log_sizes(console):
    """The sizes of the app's three logs, eden_log.txt first (as Batch.log_sizes)."""
    eden, logs = console.list(EDEN_DIR) or {}, console.list(LOG_DIR) or {}
    return tuple((folder.get(name) or {}).get("size")
                 for folder, name in ((eden, "eden_log.txt"), (logs, "stderr.log"), (logs, "heap.log")))


def warm_for(console, state, say):
    return warm_cache.WarmCache(
        console, DATA, say=say, app_open=lambda: bool(console.mounted_sandboxes() - set(state.get("stale_sandboxes", []))),
        log_sizes=lambda: console_log_sizes(console), errors=(NoAnswer,))


def warm_copy_command(args):
    """--check-warm-copy (this computer only) and --make-warm-copy (reads the console; only with --go)."""
    if args.check_warm_copy:
        try:
            _, info, total = warm_cache.check_copy(args.check_warm_copy, DATA)
        except warm_cache.WarmRefused as error:
            print(f"COPY NOT GOOD: {error}")
            return 2
        print(f"Copy good: {total['files']} files, {warm_cache.human(total['bytes'])}, made {info.get('made')}; every "
              "file matches its SHA-256 and the manifest")
        return 0
    folder = args.make_warm_copy
    if not args.go:
        print(f"Would copy {DATA}/user/cache and {DATA}/cache from the console, whole, into {folder.name}, with a "
              "SHA-256 list. Reads only; the app must be closed. Nothing was sent to the console. Add --go to do it.")
        return 0
    with only_one_run(args.out_root):
        state = load_state(args.out_root)
        if state.get("warm_pending"):
            sys.exit("The owner's caches are set aside by an earlier whole-cache restore: run --restore-env --go "
                     "first. Nothing was read.")
        console = Console(args)
        cache = warm_for(console, state, say=lambda text: print(f"{time.strftime('%H:%M:%S')} {text}", flush=True))
        try:
            info = warm_cache.make_copy(cache, folder, {"from": "the console's live cache folders"})
        except warm_cache.WarmRefused as error:
            sys.exit(f"No copy made: {error}")
    print(f"Copy made: {folder.name}, {info['files']} files, {warm_cache.human(info['bytes'])} in {info['seconds']:.0f} s")
    return 0


def launcher_check_command(args):
    """--check-launcher: reads only. Which title runs now, and for ProsperoMgr its temperatures. Starts nothing."""
    print(f"Launcher: {launchers.describe(args)}")
    if args.launcher == "websrv":
        print("websrv's /launch has no call that only reads, so there is nothing to ask it. Nothing was sent.")
        return 0
    if not args.go:
        print("Would ask GET /api/titles/running and GET /api/thermal. Nothing was sent; add --go.")
        return 0
    launcher = launchers.make(args, NoAnswer)
    try:
        running = launcher.running()
        thermal = launcher.thermal()
    except (NoAnswer, launchers.LaunchRefused) as error:
        print(f"No clear answer: {error}")
        return 1
    print(f"Running title: {running or 'none'}" + (" (this runner's app)" if running == APP else ""))
    if thermal and thermal.get("ok"):
        print("Temperatures: " + ", ".join(f"{k} {thermal[k]} C" for k in ("cpu_c", "soc_c", "m2_c", "hottest_c")
                                          if isinstance(thermal.get(k), int)))
    else:
        print(f"Temperatures: none given ({thermal!r}); ProsperoMgr reads them only with its supporting payloads")
    return 0


def restore_command(args):
    """--restore-env: finish the job of a run that could not put env.txt back. With --go it also puts back
    any shader store or driver cache a cold start left aside (the note in the state file, and any .cold-aside-
    folder on the console)."""
    state = load_state(args.out_root)
    pending = state.get("pending_restore")
    cold = state.get("cold_pending")
    warm = state.get("warm_pending")
    config = None
    if not pending:
        print("Nothing to restore: no run left env.txt changed.")
    else:
        if pending["host"] != args.host:
            sys.exit(f"The saved env.txt belongs to {pending['host']}, not {args.host}.")
        print(f"env.txt saved by {pending['batch']}:")
        for folder, text in pending["before"].items():
            print(f"  {folder}: " + ("no env.txt" if text is None else
                                     repr(base64.b64decode(text).decode(errors="replace"))))
        config = pending.get("config")
        config = None if config is None else base64.b64decode(config)
        if config is not None:
            print(f"and {CONFIG} as it was at that batch's start, {len(config)} bytes (its config-before.json)")
    if cold:
        if cold.get("host") != args.host:
            sys.exit(f"The cold-start caches left aside belong to {cold.get('host')}, not {args.host}.")
        print(f"Cold start in {cold.get('batch') or 'an earlier run'} left aside: " + ", ".join(
            item["aside"] for item in cold["note"]["items"] if item.get("state") in ("maybe", "aside")))
    if warm:
        if warm.get("host") != args.host:
            sys.exit(f"The owner's caches set aside belong to {warm.get('host')}, not {args.host}.")
        print(f"A whole-cache restore in {warm.get('batch') or 'an earlier run'} left the owner's caches aside: " +
              ", ".join(tree["aside"] for tree in warm["note"]["trees"].values() if tree.get("before")))
    if not args.go:
        print("Nothing was sent to the console. Add --go to put these back (with --go the console's cache folders "
              "are also checked for any .cold-aside- or .warm-owner-aside folder left behind).")
        return 0
    with only_one_run(args.out_root):
        console = Console(args)
        if pending:
            try:
                put_env_back(console, pending["before"], config)
            except NoAnswer as error:
                sys.exit(f"Could not put {'env.txt' if config is None else 'env.txt and eglantineps5.json'} "
                         f"back: {error}")
            state.pop("pending_restore")
            save_state(args.out_root, state)
            print("env.txt is back and checked in both folders.")
            if config is not None:
                print("eglantineps5.json is back and checked.")

        def log_sizes():
            eden, logs = console.list(EDEN_DIR) or {}, console.list(LOG_DIR) or {}
            return tuple((folder.get(name) or {}).get("size")
                         for folder, name in ((eden, "eden_log.txt"), (logs, "stderr.log"), (logs, "heap.log")))
        caches = cold_caches.ColdCaches(
            console, DATA, ENV_FOLDERS, say=lambda text: print(f"{time.strftime('%H:%M:%S')} {text}", flush=True),
            app_open=lambda: bool(console.mounted_sandboxes() - set(state.get("stale_sandboxes", []))),
            log_sizes=log_sizes, errors=(NoAnswer,))
        note_file = args.out_root / f"cold-recovery-{time.strftime('%Y%m%d-%H%M%S')}.json"
        keep = cold_keeper(state, args.out_root, cold and cold["batch"], cold and cold["run"], args.host, note_file)
        ok, how = caches.recover(cold and cold["note"], keep)
        if not ok:
            sys.exit(f"Cold-start caches NOT back: {how}. Nothing more was moved; {note_file.name} says what is where.")
        print(f"Cold-start caches: {how}.")
        warm_file = args.out_root / f"warm-recovery-{time.strftime('%Y%m%d-%H%M%S')}.json"
        caches = warm_for(console, state, say=lambda text: print(f"{time.strftime('%H:%M:%S')} {text}", flush=True))
        ok, how = caches.recover(warm and warm["note"],
                                 warm_keeper(state, args.out_root, warm and warm["batch"], args.host, warm_file))
        if not ok:
            sys.exit(f"The owner's caches NOT back: {how}. Nothing more was moved.")
        print(f"Whole-cache restore: {how}.")
    return 0


# ---------------------------------------------------------------- one test

class Run:
    def __init__(self, batch, test):
        self.test = test
        self.folder = new_run_folder(batch.folder, batch.args.out_root, test.slug)
        limit = int(batch.args.max_log_mib * (1 << 20))
        self.eden = Follower(EDEN_LOG, self.folder / "eden_log.txt", limit)
        self.others = [Follower(f"{LOG_DIR}/{name}", self.folder / name, limit) for name in ("heap.log", "stderr.log")]
        self.frames = None
        self.launched = None
        self.boot_head = b""
        self.eden_before = b""
        self.eden_fresh = False
        self.crashes_before = set()
        self.recording_before = None
        self.sizes = None
        self.grew = None
        self.sandbox_seen = False
        self.gone_polls = 0
        self.game_seen = None
        self.last_wait = None
        self.config_sent = None  # the eglantineps5.json this run's config put on the console
        # A live test: the script line whose WAIT means "at the test spot", when that was seen, when
        # the schedule went to the console.
        self.live_line = None
        self.live_from = None
        self.live_written = None
        self.result = {"number": test.number, "name": test.name, "folder": self.folder.name, "ending": None,
                       "detail": "", "seconds": None, "game_after": None, "frames": 0, "notes": []}

    def end(self, ending, detail=""):
        if self.result["ending"] is None:
            self.result.update(ending=ending, detail=detail)
            if self.launched is not None:
                self.result["seconds"] = round(time.monotonic() - self.launched)

    def note(self, text):
        self.result["notes"].append(text)


def launch_origin_shift(poll, seen_open):
    """next/ (12 Nov 2026): how far after "now" a start's time origin lies when --launch-fast-check saw the app
    open `seen_open` s after the first 503, so that it is where the old full --poll pause put it."""
    return max(0.0, float(poll) - float(seen_open))


def new_batch_folder(root, plan):
    stamp, number = time.strftime("%Y%m%d-%H%M%S"), 1
    while True:
        folder = root / (f"auto-{stamp}-{slugify(plan)}" + ("" if number == 1 else f"-{number}"))
        try:
            folder.mkdir()
            return folder
        except FileExistsError:
            number += 1


def new_run_folder(batch, root, slug):
    """runNN-<test>, carrying on the owner's numbering. mkdir fails on a taken name, so a folder is
    never reused, whatever else runs at the same time."""
    names = [p.name for p in root.iterdir()] + [p.name for p in root.glob("auto-*/run*")]
    numbers = [int(m[1]) for m in map(re.compile(r"run(\d+)").match, names) if m]
    number = max(numbers, default=0) + 1
    while True:
        folder = batch / f"run{number}-{slug}"
        try:
            folder.mkdir()
            return folder
        except FileExistsError:
            number += 1


class Batch:
    def __init__(self, args, tests, state):
        self.args, self.tests, self.state = args, tests, state
        self.console = Console(args)
        self.launcher = launchers.make(args, NoAnswer)  # None: websrv's /launch
        self.folder = new_batch_folder(args.out_root, args.plan.stem)
        self.log = open(self.folder / "batch.log", "a")
        self.results = []
        self.stop = None
        self.interrupted = False
        self.launched_any = False
        self.env_before = None
        self.env_back = None
        # Only a plan with config uses these: the app's file as read at the start (its exact bytes and
        # the document), and whether any test has written the file since.
        self.config_before = None
        self.config_base = None
        self.config_touched = False
        self.told_owner = False
        self.build = None
        self.started = time.time()
        self.closed_at = None  # when quit_app last saw the app closed, since the last /launch
        self.save_clean = False  # local to this batch, proved only from finished run logs
        self.save_job = None  # the restore-save.py that runs now, if one does (start_save)
        # next/ (12 Nov 2026): early stop rules from <plan>.stop.json, starts they skipped, network drops resumed.
        self.rules, self.rules_message = None, None
        module = None if getattr(args, "no_stop_rules", False) else stop_rules_module()
        if module is not None:
            self.rules, self.rules_message = module.StopRules.load(args.plan, [t.name for t in tests])
        self.skipped = []
        self.net_drops = []
        self.cold = cold_caches.ColdCaches(self.console, DATA, ENV_FOLDERS, say=self.say, app_open=self.app_open,
                                           log_sizes=self.log_sizes, errors=(NoAnswer,))
        self.cold_recovered = None  # what the start-up check put back, for the summary
        # --warm-copy: the whole cache put back from one copy before every start (warm_cache.py)
        self.warm = warm_cache.WarmCache(self.console, DATA, say=self.say, app_open=self.app_open,
                                         log_sizes=self.log_sizes, errors=(NoAnswer,))
        self.warm_note = None  # this batch's note: the owner's folders, where they are, the restores
        self.warm_recovered = None  # what the start-up check put back, for the summary
        self.warm_left = None  # why the owner's folders are not back at the end, if they are not
        self.warm_old_now = None  # the .old- folders on the console at the batch end (all batches), if listed

    @property
    def put_back(self):
        """What goes back at the end, for the messages."""
        return "env.txt and eglantineps5.json" if self.config_touched else "env.txt"

    def say(self, text):
        line = f"{time.strftime('%H:%M:%S')} {text}"
        print(line, flush=True)
        self.log.write(line + "\n")
        self.log.flush()

    def save_state(self):
        save_state(self.args.out_root, self.state)

    def app_open(self):
        return bool(self.console.mounted_sandboxes() - set(self.state.get("stale_sandboxes", [])))

    def forget_sandboxes(self):
        """The mounts there are now are known leftovers, not a running app."""
        self.state["stale_sandboxes"] = sorted(self.console.mounted_sandboxes())
        self.save_state()

    # The whole batch.

    def run(self):
        (self.folder / "plan.json").write_bytes(self.args.plan.read_bytes())
        try:
            if self.rules_message:
                self.say(self.rules_message)
            self.prepare()
            for test in self.tests:
                reason = self.rules.skip_reason(test.name) if self.rules else None
                if reason:  # recorded as skipped, never as valid or invalid; no run folder, nothing sent
                    self.skipped.append({"number": test.number, "name": test.name, "reason": reason})
                    self.say(f"Test {test.number} of {len(self.tests)}: {test.name} SKIPPED by a stop rule: {reason}")
                    continue
                self.run_test(test)
                if self.stop or self.interrupted:
                    break
                self.judge_rules(test)
        except Stop as stop:
            self.stop = stop
        except KeyboardInterrupt:
            self.interrupted = True
        except Exception as error:
            self.stop = Stop("tool_error", repr(error))
            raise
        finally:
            ignore_signals()
            try:
                self.end_save_job()
            finally:  # whatever the wait for the save does, env.txt goes back and the page is written
                try:
                    self.warm_back()  # --warm-copy: the owner's caches back, once the app is closed
                finally:
                    self.restore_env()
                    self.finish()
        return 2 if self.stop else 130 if self.interrupted else 0

    def prepare(self):
        """Checks before the first write. Whatever fails here has changed nothing on the console."""
        console = self.console
        if not self.args.no_frames:
            # A game shown in a corner of the recording (8 Nov: 1280x720 unscaled on the 1920x1080
            # canvas, for 11 hours) halves what the flash meter sees. Stop before a batch of such videos.
            fills, shown = capture_fit(self.args)
            if fills is False and not self.args.capture_any:
                raise Stop("not_started", f"the game does not fill the recording: {shown}. Run obs-fit.py "
                                          "(it sets the source to fit the canvas), or add --capture-any to "
                                          "record it as it is")
            if fills is False:
                self.say(f"WARNING: the game does not fill the recording ({shown}); --capture-any, so it runs")
            elif fills:
                self.say(f"OBS: {shown}")
        self.say(f"Checking the console at {self.args.host}")
        try:
            if console.list(DATA) is None:
                raise Stop("not_started", f"{DATA} is not there")
            console.check_ftp()
            for folder in ENV_FOLDERS:
                if console.list(folder) is None:
                    raise Stop("not_started", f"{folder} is not there")
            if self.args.confirmed_closed:
                self.forget_sandboxes()
            else:
                others = console.other_games()
                if others:
                    raise Stop("not_started", f"{', '.join(others)} looks open and /launch would kill it. "
                                              "Close it, or add --confirmed-closed if it is closed")
            if self.app_open():
                if not self.args.close_open_app:
                    raise Stop("not_started", "the app looks open: its sandbox has its mounts, and someone may be "
                                              "using it. A crash restart leaves them behind after closing too. "
                                              "If it is closed add --confirmed-closed, "
                                              "or add --close-open-app to close it with test-quit")
                self.say("The app looks open, closing it with test-quit")
                self.quit_app()
            self.clear_test_quit()
            self.cold_recover()
            self.warm_recover()
            before = {}
            copies = self.folder / "env-before"
            copies.mkdir()
            for folder in ENV_FOLDERS:
                data = console.read(f"{folder}/env.txt")
                before[folder] = None if data is None else base64.b64encode(data).decode()
                name = folder.strip("/").replace("/", "_")
                (copies / (name + (".absent" if data is None else ".env.txt"))).write_bytes(data or b"")
                if data and b"EDEN_TEST_" in data:
                    self.say(f"WARNING: env.txt in {folder} already has EDEN_TEST_ lines, it goes back like that")
            config = console.read(CONFIG)
            if config:
                (self.folder / "config-before.json").write_bytes(config)
        except NoAnswer as error:
            raise Stop("no_answer", f"the console does not answer: {error}") from error
        configured = [test.name for test in self.tests if test.config is not None]
        if configured:
            # A test's config only ever goes over this copy. With no copy there is nothing to lay it
            # over, and a file built from nothing would lose every other setting.
            self.config_base, why = read_config(config)
            if self.config_base is None:
                raise Stop("not_started", f"{', '.join(configured)} set config, but {CONFIG} could not be read "
                                          f"at the start: {why}. Nothing was written, no test ran")
            self.config_before = config
            self.say(f"{posixpath.basename(CONFIG)} read ({len(config)} bytes), kept as config-before.json")
        # Written before env.txt changes: even a killed process leaves the way back on the Mac.
        self.env_before = before
        self.state["pending_restore"] = {"batch": self.folder.name, "host": self.args.host, "before": before}
        self.save_state()
        self.warm_aside()  # --warm-copy only: last, so a refusal here has changed nothing else

    def restore_save(self, early=None, again=False):
        """Every test starts from one save: a walk goes through doorways and the game saves there.
        early: (returncode, output) of the restore-save.py save_ahead started, if one ran. again: an app
        was open before this start and check_closed closed it, so the save goes back (once more) now."""
        if self.args.save is None:
            return
        if self.args.discard_save_reuse:
            if again:
                self.save_clean = False
            if self.save_clean and early is None and not again:
                self.say("SAVE restore skipped: finished run confirmed session copy (copied)")
                return
            self.say("SAVE restore required: " + ("app was open" if again else
                     "first install or no finished-run copy proof"))
        if early is not None and not again:
            if early[0]:
                raise Stop("not_started", f"the save could not be put back: {early[1].strip()[-200:]}")
            self.say(f"Save {self.args.save.name} put back")
            return
        if early is not None:
            self.say("An app was open before this start: the save goes back again, now that it is closed")
        # The same start as save_ahead's. A Ctrl-C while this waits leaves the job in save_job, and the
        # way out (end_save_job) waits for it to the end.
        self.start_save()
        code, output = self.wait_save_job()
        if code:
            raise Stop("not_started", f"the save could not be put back: {output.strip()[-200:]}")
        self.say(f"Save {self.args.save.name} put back")

    def discard_save_confirmed(self, run):
        """The env is a request; only this finished run's complete copy warning proves isolation."""
        if (self.closed_at is None or run.result["ending"] not in ("script_end", "time_limit")
                or run.result.get("notes")
                or any(CRASH_STEM.match(p.name) for p in run.folder.glob("crash-*"))
                or dict(line.split("=", 1) for line in run.test.env)
                   .get("EDEN_TEST_DISCARD_SAVE") != "1"):
            return False
        followers = [run.eden] + run.others
        if any(f.cut or not f.local.exists() for f in followers):
            return False
        warning = re.compile(rb"(?:^|[ \t])EDEN_TEST_DISCARD_SAVE: this session's save is the copy "
                             rb"/test-discard/user/save/[^ \t\r\n]+ \(copied\); the save at "
                             rb"/user/save/[^ \t\r\n]+ is not written to[ \t]*\r?\n$")
        try:
            for follower in followers:
                with follower.local.open("rb") as handle:
                    if any(warning.search(line) for line in handle):
                        return True
        except OSError:
            return False
        return False

    def start_save(self):
        """Start restore-save.py, in a session of its own: a Ctrl-C at the terminal reaches this tool
        and not the save, and this tool then waits for it (wait_save_job, end_save_job). subprocess.run
        would kill it halfway. Every put-back starts here: the early one, the one before the first
        test, --save-late, and the second one after an app was found open. errors="replace": what it
        prints is only ever shown, and bytes that are no text must not make the wait fail."""
        self.save_job = subprocess.Popen(
            [sys.executable, str(code_file("restore-save.py")), str(self.args.save)],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            errors="replace", start_new_session=True)

    def save_ahead(self, test):
        """Start putting the save back for the next test now, while this Mac finishes this run (video
        check, reports) and the console has nothing else to do. Only right after quit_app saw the app
        closed, never after the last test, never for a live test (its wrap-up removes a file over FTP),
        never with --save-late. restore-save.py makes its own closed check as always. Until it has
        ended this tool writes nothing to the console and starts nothing there: run_test waits for it
        first. One read does go out meanwhile, close_run's copy of crash-index.txt over HTTP; that
        changes nothing on the console."""
        if self.args.discard_save_reuse and self.save_clean:
            return  # next restore_save logs this decision
        if (self.args.save is None or self.args.save_late or test is self.tests[-1] or test.live is not None
                or self.closed_at is None):
            return
        try:
            if self.app_open():
                return  # run_test closes it first and puts the save back after, as before
        except NoAnswer:
            return
        self.say(f"Putting save {self.args.save.name} back while this Mac finishes the run")
        self.start_save()

    def wait_save_job(self):
        """(returncode, output) of the restore-save.py that start_save started, once it has ended.
        None if none runs. Never cut short: a save goes back whole. A Ctrl-C in here leaves save_job
        as it is, so the next call waits on."""
        job = self.save_job
        if job is None:
            return None
        out, err = job.communicate()
        self.save_job = None
        return job.returncode, (out or "") + (err or "")

    def end_save_job(self):
        """On the way out of a test or the batch: no write goes to the console while the save does."""
        ended = self.wait_save_job()
        if ended is not None:
            self.say(f"Save {self.args.save.name} put back" if not ended[0]
                     else f"The save could not be put back: {ended[1].strip()[-200:]}")

    def judge_rules(self, test):
        """The stop rules on the start(s) of this test that just ended (a network rerun adds a second one)."""
        if not self.rules:
            return
        plan_entry = None
        with contextlib.suppress(OSError, ValueError, TypeError, IndexError):
            plan_entry = json.loads(self.args.plan.read_text())[test.number - 1]
        for result in [r for r in self.results if r["name"] == test.name]:
            try:
                lines = self.rules.after_start(self.folder, result, plan_entry)
            except Exception as error:  # noqa: BLE001 - a rule fault decides nothing and stops nothing
                lines = [f"stop rules: {type(error).__name__}: {error}; nothing decided"]
            for line in lines:
                self.say(line)

    def network_drop(self, stop):
        """True for a no-answer stop that a network drop explains, while --net-resume may still resume one."""
        return (not getattr(self.args, "no_net_resume", True) and stop.kind == "no_answer" and not self.net_drops
                and bool(NETWORK_ERROR.search(str(stop.detail))))

    def wait_for_console(self):
        """True once the console answers three looks in a row within --net-resume-minutes. Reads only."""
        deadline = time.monotonic() + self.args.net_resume_minutes * 60
        good = 0
        while good < 3:
            if time.monotonic() > deadline:
                return False
            try:
                if self.console.list(DATA) is None:
                    raise NoAnswer(f"{DATA} is not there")
                good += 1
                time.sleep(min(self.args.poll, 5))
            except NoAnswer as error:
                if good or not hasattr(self, "_told_drop"):
                    self.say(f"Network drop: no answer yet ({error})")
                    self._told_drop = True
                good = 0
                time.sleep(min(10.0, max(self.args.poll, 0.2)))
        return True

    def resume_after_drop(self, run):
        """After a network drop: (True, how) when the app is closed again and nothing hides a crash or a hang,
        so the same start may run once more; (False, why) when the console needs a look (stop as before).
        Same tests as overnight/recover-net.py: the game must be alive (its log grows, frames counted) before
        test-quit goes to it; an app that is gone, frozen or has a new crash file is never touched."""
        if not self.wait_for_console():
            return False, f"the console did not answer again within {self.args.net_resume_minutes:g} min"
        self.say("Network drop: the console answers again")
        try:
            logs = self.console.list(LOG_DIR) or {}
            if run.launched is not None and self.new_crash_files(run, logs):
                return False, "a crash file appeared during the drop: look first"
            if not self.app_open():
                if run.launched is None:
                    return True, "the start had not launched yet and the app is closed"
                return False, "the app is gone after the drop and there is no crash file: look for a CE error first"
            first = self.log_sizes()[0]
            time.sleep(self.args.net_alive_wait)
            second = self.log_sizes()[0]
            if first is None or second is None or second <= first:
                return False, f"the game's log does not grow ({first} -> {second} bytes): frozen or hung, look first"
            tail = self.console.read(EDEN_LOG, offset=max(0, second - 12000)) or b""
            frames = re.findall(rb"(\d+) frames, ([\d.]+) fps", tail) + re.findall(rb"EDEN_VULKAN_FRAME frames=(\d+) "
                                                                                  rb"seconds=[\d.]+ fps=([\d.]+)", tail)
            if not frames or int(frames[-1][0]) == 0:
                return False, "the game's log grows but counts no frames: looks hung, look first"
            self.say(f"Network drop: the game is alive ({frames[-1][0].decode()} frames, {frames[-1][1].decode()} fps "
                     "in its last report): closing it with test-quit")
            self.quit_app()
            with contextlib.suppress(Stop, NoAnswer):  # the last of the dropped start's logs, for its folder
                self.follow(run, self.console.list(LOG_DIR) or {})
            if self.new_crash_files(run, self.console.list(LOG_DIR) or {}):
                return False, "the app crashed while closing after the drop: look first"
        except Stop as stop:
            return False, f"closing after the drop: {ENDINGS[stop.kind]}: {stop.detail}"
        except NoAnswer as error:
            return False, f"the console stopped answering again: {error}"
        return True, "the app is closed again"

    def run_test(self, test, rerun_of=None):
        run = Run(self, test)
        if rerun_of:
            run.result["rerun_of"] = rerun_of
            run.note(f"the same start again after a network drop in {rerun_of} (same build, env and save)")
        self.say(f"Test {test.number} of {len(self.tests)}: {test.name}, folder {run.folder.name}"
                 + (f" (again, after the network drop in {rerun_of})" if rerun_of else ""))
        again = False
        try:
            if test is not self.tests[0] or rerun_of:
                # The system finishes with the last app in its own time: --settle from when it closed.
                # With --save-late the whole pause from here, as it was before the early save.
                late = self.args.save_late or self.closed_at is None
                since = 0.0 if late else time.monotonic() - self.closed_at
                time.sleep(max(0.0, self.args.settle - since))
            early = self.wait_save_job()  # first: no write and no start goes to the console meanwhile
            opened = self.check_closed()
            self.restore_save(early, again=opened)
            if self.args.discard_save_reuse:
                self.save_clean = False  # a failed launch/finish must never carry old proof forward
            self.warm_restore(run)  # --warm-copy only: the whole cache from the copy; refuses while the app runs
            self.cold_aside(run)  # EDEN_TEST_COLD=1 / --cold only; refuses (nothing moved) while the app runs
            self.start(run)
            self.finish_run(run, self.watch(run))
            if self.args.discard_save_reuse:
                self.save_clean = self.discard_save_confirmed(run)
            if not self.cold_back(run):  # before save_ahead: no rename while the save goes back
                return
            self.save_ahead(test)
        except (Stop, NoAnswer) as caught:
            stop = caught if isinstance(caught, Stop) else Stop("no_answer", str(caught))
            if self.network_drop(stop):
                again = self.dropped(run, stop)
            else:
                self.stopped(run, stop)
        except KeyboardInterrupt:
            self.interrupted = True
            run.end("interrupted")
            self.say("Stopped by hand, closing the app")
            ignore_signals()
            self.end_save_job()
            self.salvage(run)
            with contextlib.suppress(Stop, NoAnswer):
                self.quit_app()
        finally:
            try:
                self.cold_back(run, late=True)  # a stop, a crash of this tool, Ctrl-C: once the app is closed
            finally:
                self.close_run(run)
        if again and not self.stop and not self.interrupted:
            self.run_test(test, rerun_of=run.folder.name)

    def dropped(self, run, stop):
        """--net-resume: the first network drop of a batch. The stop is latched first (the Mac may not get to
        the end of this), then lifted once the app is closed again; the start counts as not valid ("network
        drop") and runs once more. Returns True for the rerun; False after a normal stop."""
        if self.launched_any:
            self.latch(stop, run.test.name)
        self.net_drops.append({"test": run.test.name, "folder": run.folder.name, "detail": str(stop.detail)[:300],
                               "when": time.strftime("%Y-%m-%d %H:%M:%S")})
        self.say(f"NETWORK DROP in {run.test.name}: {stop.detail}. Waiting up to {self.args.net_resume_minutes:g} min "
                 "for the console; this start is not counted and runs once more (--no-net-resume: stop as before)")
        self.end_save_job()
        ok, how = self.resume_after_drop(run)
        if run.result["ending"]:  # it may have got to its time limit and then not closed
            run.note(f"{ENDINGS[run.result['ending']]} first")
            run.result["ending"] = None
        self.net_drops[-1]["resumed"] = ok
        self.net_drops[-1]["how"] = how
        if not ok:
            self.stopped(run, Stop("no_answer", f"{stop.detail}; network drop not resumed: {how}"))
            return False
        run.end("no_answer", f"network drop: {stop.detail}; not counted, the same start runs again ({how})")
        run.result["network_drop"] = True
        self.state.pop("stopped", None)
        self.save_state()
        self.save_clean = False  # the dropped start played: its save goes back before the rerun
        self.say(f"Network drop resumed ({how}): {run.test.name} runs again")
        return True

    def latch(self, stop, name):
        """From here the next --go refuses until the owner says they looked."""
        self.state["stopped"] = {"kind": stop.kind, "test": name, "when": time.strftime("%Y-%m-%d %H:%M"),
                                 "folder": self.folder.name}
        self.save_state()

    def stopped(self, run, stop):
        self.stop = stop
        if self.launched_any:  # first: the Mac may not get to the end of this, and the next --go must know
            self.latch(stop, run.test.name)
        if run.result["ending"]:  # it may have got to its time limit and then not closed
            run.note(f"{ENDINGS[run.result['ending']]} first")
            run.result["ending"] = None
        run.end(stop.kind, stop.detail)
        self.say(f"STOP: {ENDINGS[stop.kind]}: {stop.detail}")
        # In this order: the console may not last, as a GPU hang has frozen it within minutes.
        notify(self.args, "EglantinePS5 tests stopped", f"{ENDINGS[stop.kind]} in {run.test.name}. "
                                                        "Next steps are yours.")
        self.told_owner = True
        self.end_save_job()  # env.txt goes back after the save, not while it is being written
        self.restore_env()
        self.salvage(run)

    # Before a test.

    def check_closed(self):
        """Closes an app that is open before a start. True if there was one."""
        opened = self.app_open()
        if opened:
            self.say("The app is still open, closing it first")
            self.quit_app()
        self.clear_test_quit()
        return opened

    def clear_test_quit(self):
        """A test-quit left lying around would close the next start at once."""
        if "test-quit" in (self.console.list(DATA) or {}):
            self.say("Removing a test-quit left behind")
            self.console.remove(TEST_QUIT)

    # Cold starts (cold_caches.py): EDEN_TEST_COLD=1 in a test's env, or --cold for every test.

    def cold_say(self, folder, text):
        """A cold-start line: in batch.log and on screen as every line, and in that folder's cold.log."""
        self.say(text)
        with open(folder / cold_caches.LOG_NAME, "a") as out:
            out.write(f"{time.strftime('%H:%M:%S')} {text}\n")

    def cold_recover(self):
        """The start-up check, on every --go: a shader store or driver cache an earlier, cut-off run left aside
        goes back before anything else is written. Refuses the batch when it cannot."""
        pending = self.state.get("cold_pending") or {}
        keep = cold_keeper(self.state, self.args.out_root, pending.get("batch"), pending.get("run"), self.args.host,
                           self.folder / "cold-recovery.json")
        self.cold.say = lambda text: self.cold_say(self.folder, text)
        try:
            ok, how = self.cold.recover(pending.get("note"), keep)
        finally:
            self.cold.say = self.say
        if not ok:
            raise Stop("not_started", f"start-up check: a shader store or driver cache an earlier cold start left "
                                      f"aside could not be put back: {how}. Nothing else was sent; "
                                      "cold-recovery.json says what is where")
        if how == cold_caches.NOTHING_LEFT:
            self.say(f"Start-up check: {how}")
        else:
            self.cold_recovered = how

    def cold_aside(self, run):
        if not run.test.cold:
            return
        run.result["cold"] = {"status": "checking"}
        keep = cold_keeper(self.state, self.args.out_root, self.folder.name, run.folder.name, self.args.host,
                           run.folder / cold_caches.NOTE_NAME)
        self.cold.say = lambda text: self.cold_say(run.folder, text)
        self.cold.last_note = None
        try:
            run.cold_note = self.cold.set_aside(run.test.title, keep, move_set=run.test.cold_set)
        except cold_caches.ColdRefused as error:
            run.result["cold"]["status"] = "refused"
            raise Stop("not_started", f"cold start refused, nothing was moved: {error}") from error
        except cold_caches.ColdNotBack as error:
            run.cold_note, run.cold_done = self.cold.last_note, True  # the start-up check takes it from here
            run.result["cold"]["status"] = "not_back"
            raise Stop("cold_not_back", f"{error}. The next --go or --restore-env --go puts them back") from error
        finally:
            self.cold.say = self.say
            if getattr(run, "cold_note", None) is None and self.cold.last_note is not None:
                # Cut off inside set_aside (Ctrl-C, a tool error): run_test's finally puts back what moved.
                run.cold_note = self.cold.last_note
        note = run.cold_note
        run.result["cold"] = {"status": note["status"],
                              "set_aside": [{"what": i["what"], "path": i["path"], "files": i["before"]["files"],
                                             "bytes": i["before"]["bytes"]} for i in note["items"]],
                              "set_kept": [k["name"] for i in note["items"] for k in i.get("keep", [])]}

    def cold_back(self, run, late=False):
        """After the test: the old caches back, once the app is closed. False when they are not back (the batch
        stops; the state file keeps the way back for the next --go or --restore-env --go). Runs once a run."""
        note = getattr(run, "cold_note", None)
        if note is None or getattr(run, "cold_done", False) or note["status"] not in cold_caches.OPEN:
            return True
        run.cold_done = True
        if late:
            self.end_save_job()  # no rename while a save goes back
        keep = cold_keeper(self.state, self.args.out_root, self.folder.name, run.folder.name, self.args.host,
                           run.folder / cold_caches.NOTE_NAME)
        handlers = {number: signal.signal(number, signal.SIG_IGN)  # a Ctrl-C must not cut a put-back in half
                    for number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
        self.cold.say = lambda text: self.cold_say(run.folder, text)
        try:
            ok, why = self.cold.put_back(note, keep)
        finally:
            self.cold.say = self.say
            for number, handler in handlers.items():
                signal.signal(number, handler)
        cold = run.result.setdefault("cold", {})
        cold.update(status=note["status"], back=ok,
                    built=[posixpath.basename(i["built"]) for i in note["items"] if i.get("built")])
        if ok:
            self.say("Cold start: the old shader store and driver cache are back, checked by a listing")
            return True
        left = ", ".join(i["aside"] for i in note["items"] if i["state"] in ("maybe", "aside"))
        text = (f"the old caches are NOT back ({why}). They stay renamed on the console ({left}); the next --go, "
                "or --restore-env --go, puts them back once the app is closed")
        run.note("cold start: " + text)
        self.say("COLD START: " + text)
        if not self.stop and not self.interrupted:
            self.stop = Stop("cold_not_back", text)
            if self.launched_any:
                self.latch(self.stop, run.test.name)
        notify(self.args, "EglantinePS5 tests stopped", f"cold start in {run.test.name}: the old caches are NOT "
                                                        "back. Next steps are yours.")
        self.told_owner = True
        return False

    # The whole-cache restore (warm_cache.py): --warm-copy <copy folder>, GrowingBlackBeans' warm-run-steps.md step 0.

    def warm_say(self, text):
        """A whole-cache line: in batch.log and on screen as every line, and in the batch folder's warm.log."""
        self.say(text)
        with open(self.folder / warm_cache.LOG_NAME, "a") as out:
            out.write(f"{time.strftime('%H:%M:%S')} {text}\n")

    def warm_keep(self, note_file=None):
        return warm_keeper(self.state, self.args.out_root, self.folder.name, self.args.host,
                           note_file or self.folder / warm_cache.NOTE_NAME)

    def warm_recover(self):
        """The start-up check, on every --go: the owner's caches an earlier, cut-off run left aside go back before
        anything else is written. Refuses the batch when it cannot."""
        pending = self.state.get("warm_pending") or {}
        keep = warm_keeper(self.state, self.args.out_root, pending.get("batch"), self.args.host,
                           self.folder / "warm-recovery.json")
        self.warm.say = self.warm_say
        try:
            ok, how = self.warm.recover(pending.get("note"), keep)
        finally:
            self.warm.say = self.say
        if not ok:
            raise Stop("not_started", f"start-up check: the owner's cache folders an earlier whole-cache restore left "
                                      f"aside could not be put back: {how}. Nothing else was sent")
        if how == warm_cache.NOTHING_LEFT:
            self.say(f"Start-up check: {how}")
        else:
            self.warm_recovered = how

    def warm_aside(self):
        """--warm-copy: the copy checked, then the owner's two cache folders renamed aside for the batch."""
        if self.args.warm_copy is None:
            return
        self.warm.say = self.warm_say
        self.warm.last_note = None
        try:
            _, info, total = warm_cache.check_copy(self.args.warm_copy, DATA)
            self.warm_say(f"Whole-cache restore: copy {self.args.warm_copy.name}, {total['files']} files, "
                          f"{warm_cache.human(total['bytes'])}, made {info.get('made')}: matches its SHA-256 list")
            self.warm_note = self.warm.set_aside(self.args.warm_copy.name, self.warm_keep())
        except warm_cache.WarmRefused as error:
            raise Stop("not_started", f"whole-cache restore refused, nothing was moved: {error}") from error
        except warm_cache.WarmNotBack as error:
            self.warm_note = self.warm.last_note
            raise Stop("warm_not_back", f"{error}. The next --go or --restore-env --go puts them back") from error
        finally:
            self.warm.say = self.say
            if self.warm_note is None and self.warm.last_note is not None and \
                    self.warm.last_note.get("status") in warm_cache.OPEN:
                self.warm_note = self.warm.last_note  # cut off inside set_aside: the batch end puts back what moved

    def warm_restore(self, run):
        """Before a start: the live cache folders renamed aside to .old-<time> and the copy uploaded whole
        (warm_cache.WarmCache.restore). Nothing is deleted."""
        if self.warm_note is None or self.args.warm_copy is None:
            return
        self.warm.say = self.warm_say
        try:
            record = self.warm.restore(self.args.warm_copy, self.warm_note, self.warm_keep())
        except warm_cache.WarmRefused as error:
            run.result["warm_restore"] = {"ok": False, "why": str(error)}
            raise Stop("not_started", f"whole-cache restore refused, nothing written: {error}") from error
        except warm_cache.WarmFailed as error:
            run.result["warm_restore"] = {"ok": False, "why": str(error)}
            raise Stop("warm_failed", f"{error}. The owner's caches stay aside until the batch end puts them "
                                      "back") from error
        finally:
            self.warm.say = self.say
        run.result["warm_restore"] = record
        self.warm_say(f"Whole-cache restore before {run.test.name}: done ({run.folder.name})")

    def warm_back(self):
        """At the batch end: the test caches renamed aside to .old-<time> and the owner's caches renamed back, once
        the app is closed.
        When they cannot go back the batch stops; the state file keeps the way back for the next --go."""
        note = self.warm_note
        if note is None or note.get("status") not in warm_cache.OPEN:
            return
        self.warm.say = self.warm_say
        try:
            ok, why = self.warm.back(note, self.warm_keep())
        finally:
            self.warm.say = self.say
        if ok:
            try:  # every .old- folder on the console now, this batch's and earlier ones, for summary.md (reads only)
                self.warm_old_now = self.warm.old_folders()
            except (NoAnswer, warm_cache.Unclear):
                self.warm_old_now = None
            return
        self.warm_left = why
        text = (f"the owner's caches are NOT back ({why}). They stay renamed on the console ("
                + ", ".join(t["aside"] for t in note["trees"].values() if t.get("before")) +
                "); the next --go, or --restore-env --go, puts them back once the app is closed")
        self.say("WHOLE-CACHE RESTORE: " + text)
        if not self.stop and not self.interrupted:
            self.stop = Stop("warm_not_back", text)
            if self.launched_any:
                self.latch(self.stop, self.results[-1]["name"] if self.results else "?")
        notify(self.args, "EglantinePS5 tests stopped", "the owner's caches are NOT back. Next steps are yours.")
        self.told_owner = True

    def start(self, run):
        test, console = run.test, self.console
        (run.folder / "env.txt").write_text(test.env_text)
        if test.script:
            data = test.script.read_bytes()
            (run.folder / "script.txt").write_bytes(data)
            console.put(f"{DATA}/{test.script_name}", data)
        for folder in ENV_FOLDERS:
            console.put(f"{folder}/env.txt", test.env_text.encode())
        self.put_config(run)
        if test.live is not None:
            # A schedule left from another run would start with the app, during the boot.
            if posixpath.basename(LIVE_FILE) in (console.list(DATA) or {}):
                self.say("Removing a live-switches.txt left behind")
                console.remove(LIVE_FILE)
            run.live_line = live_gameplay_line(test.script)

        self.spend_crash_note()
        logs = console.list(LOG_DIR) or {}
        run.crashes_before = {found[0] for found in map(CRASH_STEM.match, logs) if found}
        run.recording_before = logs.get(posixpath.basename(RECORDED))
        before = console.read(BOOT_TRACE, length=HEAD) or b""
        run.eden_before = console.read(EDEN_LOG, length=2000) or b""

        if test.may_hang:
            self.state["hang_test"] = {"test": test.name, "when": time.strftime("%Y-%m-%d %H:%M"),
                                       "folder": run.folder.name}
            self.save_state()
            notify(self.args, "EglantinePS5 test", f"'{test.name}' may hang the GPU and is starting now")

        # The app boots the title only if this file is there, and takes it away: this start, no other.
        console.touch(BOOT_ONCE)
        self.say("Starting the app through " + ("ProsperoMgr's launch call" if self.launcher is not None else "/launch"))
        self.launch_seen_open = None
        self.launch()
        run.launched = time.monotonic()
        if self.launch_seen_open is not None:
            # Reviewed 12 Nov: every time in a start (the "seconds" limit, --game-wait, result "seconds",
            # game_after, the live schedule) counts from run.launched. Before --launch-fast-check that moment was
            # the full --poll pause after the 503. Keep it there, so a start still gets all its game time and its
            # numbers match older cards and borrowed controls; only the frames and video start sooner (by
            # launch_origin_shift, which postprocess.py takes off its recording-lag guess).
            shift = launch_origin_shift(self.args.poll, self.launch_seen_open)
            run.launched += shift
            run.result["launch_open_after"] = self.launch_seen_open
            run.result["launch_origin_shift"] = round(shift, 2)
        if not self.args.no_frames:
            run.frames = FrameSaver(self.args.obs_host, self.args.obs_port, run.folder / "frames",
                                    self.args.frame_every)
            run.frames.start()
            run.video = VideoRecorder(self.args.obs_host, self.args.obs_port, run.folder)
            run.video.start()
            trash_old_videos(self.args.out_root, run.folder.parent)
        run.boot_head = self.wait_boot(before)
        run.grew = time.monotonic()
        self.say("The app started")

    def put_config(self, run):
        """eglantineps5.json for this test, by the same staged write as env.txt: the batch-start file
        with the test's config laid over it, or, once a test has changed it, the batch-start file
        itself. Never built on what an earlier test left. A plan without config does nothing here."""
        test = run.test
        if test.config is None and self.config_before is None:
            return
        if self.config_base is None or self.config_before is None:
            raise Refused(f"{CONFIG} with no batch-start copy to build on")  # prepare stops before this
        if test.config is None:
            data = self.config_before
        else:
            data = config_bytes(merge_config(self.config_base, test.config), self.config_before)
            run.result["config"] = test.config
            self.say("Config for this test: " + ", ".join(show_setting(keys, value)
                                                          for keys, value in config_settings(test.config)))
            for surprise in config_surprises(self.config_base, test.config):
                self.say(f"WARNING: config {surprise}")
                run.note(f"config: {surprise}")
        (run.folder / "config.json").write_bytes(data)
        if test.config is None and not self.config_touched:
            return  # the console still has the batch-start file
        if not self.config_touched:
            # Written before the file changes: even a killed process leaves the way back on the Mac.
            self.config_touched = True
            self.state["pending_restore"]["config"] = base64.b64encode(self.config_before).decode()
            self.save_state()
        self.console.put(CONFIG, data)
        run.config_sent = data
        if test.config is None:
            self.say(f"{posixpath.basename(CONFIG)} is the batch-start file again for this test")

    def check_config_kept(self, run):
        """The app writes its settings file itself when it saves. A setting of this test's config that
        is not in the file after the run may not have been in force either. Reads only, and a console
        that does not answer here stops nothing: the next look at the logs would see that."""
        if run.config_sent is None or run.test.config is None:
            return
        try:
            data = self.console.read(CONFIG)
        except NoAnswer:
            return
        if data is None or data == run.config_sent:
            return
        (run.folder / "config-after.json").write_bytes(data)
        after, why = read_config(data)
        if after is None:
            run.note(f"{posixpath.basename(CONFIG)} after the run: {why}, see config-after.json")
            return
        changed = []
        for keys, value in config_settings(run.test.config):
            there, now = setting_at(after, keys)
            if not there or not same_setting(now, value):
                changed.append(show_setting(keys, value) + (f" is now {json.dumps(now, ensure_ascii=False)}"
                                                            if there else " is gone"))
        if changed:
            run.note("the app changed this test's config during the run: " + "; ".join(changed))
            self.say(run.result["notes"][-1])

    def launch(self):
        self.launched_any = True
        self.closed_at = None  # from here a close seen before this start says nothing
        if self.launcher is not None:
            # --launcher prosperomgr: one call, no retry. websrv's 503 retries below rest on /launch killing a
            # starting app; ProsperoMgr's launch does not, and what a second launch does there is not known.
            try:
                self.launcher.launch(APP)
            except launchers.LaunchRefused as error:
                raise Stop("not_started", f"ProsperoMgr did not start the app: {error}") from error
            self.say("ProsperoMgr: launch answered ok")
            return
        for attempt in range(3):
            status = self.console.launch()
            if status == 200:
                return
            self.say(f"/launch answered {status}")
            if attempt == 0 and getattr(self.args, "launch_fast_check", False):
                # next/ (12 Nov 2026): 588 of 588 starts in overnight/queue-*.run.log got one 503 and were open at
                # the first look --poll s later; none needed a second /launch. Look every --launch-check-every s
                # instead, up to the same --poll s. A second /launch is never sent sooner than before (it would
                # kill a starting app); from the second retry on the old pause is all there is.
                deadline = time.monotonic() + self.args.poll
                while True:
                    time.sleep(min(self.args.launch_check_every, max(0.0, deadline - time.monotonic())))
                    if self.app_open():
                        self.launch_seen_open = round(self.args.poll - max(0.0, deadline - time.monotonic()), 1)
                        self.say(f"The app is open {self.launch_seen_open:g} s after the 503 (--launch-fast-check)")
                        return
                    if time.monotonic() >= deadline:
                        break
                continue
            time.sleep(self.args.poll)
            if self.app_open():  # started after all: another /launch would kill it
                return
        raise Stop("no_answer", f"/launch answered {status} three times")

    def wait_boot(self, before):
        """The new boot trace's head, once the file differs from `before`."""
        deadline = time.monotonic() + self.args.boot_wait
        while time.monotonic() < deadline:
            time.sleep(min(self.args.poll, 1))
            trace = self.console.read(BOOT_TRACE, length=HEAD) or b""
            if trace and (not before or differs(trace, before)):
                return trace
        raise Stop("no_answer", f"no fresh boot trace {self.args.boot_wait:g} s after the launch")

    def spend_crash_note(self):
        """A crash that closed the app left crash-note.txt: the next start opens the launcher whatever
        env.txt says, and moves that crash's logs beside its report. Spent here, so it is no test's."""
        if "crash-note.txt" not in (self.console.list(LOG_DIR) or {}):
            return
        self.say("The last crash closed the app, so its next start is only the launcher: using that up")
        before = self.console.read(BOOT_TRACE, length=HEAD) or b""
        self.launch()
        self.wait_boot(before)
        self.quit_app()

    # During a test.

    def watch(self, run):
        """Until something ends the test. Returns an ending, or raises Stop."""
        args = self.args
        last_answer = time.monotonic()
        while True:
            time.sleep(args.poll)
            now = time.monotonic()
            try:
                ending = self.look(run, now)
                last_answer = now
            except NoAnswer as error:
                if now - last_answer >= args.no_answer:
                    raise Stop("no_answer", f"no reply for {now - last_answer:.0f} s: {error}") from error
                continue
            if ending:
                return ending

    def look(self, run, now):
        args, console = self.args, self.console
        logs = console.list(LOG_DIR) or {}
        if self.new_crash_files(run, logs):
            return "crash"
        trace = console.read(BOOT_TRACE) or b""
        if differs(trace, run.boot_head):
            return "restart"
        if len(trace) > len(run.boot_head):
            run.boot_head = trace[:HEAD]
        if trace:
            (run.folder / "boot-trace.txt").write_bytes(trace)
            self.note_build(trace)
        eden_size = self.follow(run, logs)
        if any(mark in trace for mark in TRACE_GAME):
            self.game_seen(run)

        sizes = (eden_size, len(trace)) + tuple((logs.get(posixpath.basename(f.remote)) or {}).get("size")
                                                for f in run.others)
        if sizes != run.sizes:
            run.sizes, run.grew = sizes, now
        live = self.app_open()
        run.sandbox_seen = run.sandbox_seen or live
        run.gone_polls = 0 if live or not run.sandbox_seen else run.gone_polls + 1
        if run.gone_polls >= 2:
            self.no_crash_file(run, "the app is gone")
        # The launcher logs nothing, so silence only means something once the game runs.
        if run.game_seen is not None and now - run.grew >= args.silence:
            self.no_crash_file(run, f"no log has grown for {now - run.grew:.0f} s")
        self.live_step(run, now)
        if now - run.launched >= run.test.seconds:
            # A guest thread waiting for the GPU may be a freeze on its way to 30 s, and test-quit
            # would then force the exit of a stuck app. The wait logs every 5 s while it lasts. A
            # freeze has shown itself well within four graces; short waits that keep coming must
            # not hold a test open for ever.
            if (run.last_wait is not None and now - run.last_wait < args.stall_grace
                    and now - run.launched < run.test.seconds + 4 * args.stall_grace):
                return None
            return "time_limit" if run.game_seen is not None else "no_game"
        if run.game_seen is None and now - run.launched >= args.game_wait:
            return "no_game"
        return None

    def live_step(self, run, now):
        """A live test: once the test spot is reached, write the schedule. The app does the rest."""
        test = run.test
        if test.live is None or run.game_seen is None or run.live_written is not None:
            return
        if run.live_from is None:
            if run.live_line is None:
                run.live_from = run.game_seen  # no WAIT line to go by: from the game starting
            else:
                marks = b""
                with contextlib.suppress(OSError):
                    marks = (run.folder / "stderr.log").read_bytes()
                if re.search(rb"EDEN_TEST wait_met line=%d " % run.live_line, marks):
                    run.live_from = now
                    self.say(f"The test spot is reached (the WAIT on script line {run.live_line})")
        if run.live_from is None or now - run.live_from < test.live["start"]:
            return
        text = live_text(test.live, run.folder.name)
        self.console.put(LIVE_FILE, text.encode())
        (run.folder / "live-switches.txt").write_text(text)
        run.live_written = now
        run.result["live"] = {"written_after": round(now - run.launched), "seconds": live_seconds(test.live),
                              "order": test.live["order"], "rounds": test.live["rounds"],
                              "period": test.live["period"]}
        self.say(f"Live schedule written: {len(test.live['order']) * test.live['rounds']} phases of "
                 f"{test.live['period']:g} s, done in about {live_seconds(test.live) - test.live['start']:.0f} s")

    def new_crash_files(self, run, logs):
        """By the report's stamp: a set the app finishes later, an earlier crash's, is not a new crash."""
        return [name for name in logs if (found := CRASH_STEM.match(name)) and found[0] not in run.crashes_before]

    def no_crash_file(self, run, what):
        """A dying app writes its crash file first and may be starting again, so look once more."""
        time.sleep(self.args.settle)
        logs = self.console.list(LOG_DIR) or {}
        trace = self.console.read(BOOT_TRACE, length=HEAD) or b""
        if not self.new_crash_files(run, logs) and not differs(trace, run.boot_head):
            raise Stop("system_error", f"{what}, and there is no crash file. "
                                       "Look for a CE error on screen, it needs someone to press OK")

    def follow(self, run, logs):
        """Bring the local logs up to date and look for a freeze. Returns the eden log's size."""
        console = self.console
        # heap.log and stderr.log are new before the boot trace is (main.cpp), so they count at once.
        found = None
        for follower in run.others:
            entry = logs.get(posixpath.basename(follower.remote)) or {}
            found = found or find_stop(follower.update(console, entry.get("size")))
        folder = console.list(EDEN_DIR) or {}
        size = (folder.get("eden_log.txt") or {}).get("size")
        if not run.eden_fresh:
            # The boot trace turns new before this log does, and the old log may hold a marker
            # from an earlier run. Nothing from it counts until the log has been rewritten.
            head = console.read(EDEN_LOG, length=2000) or b""
            run.eden_fresh = differs(head, run.eden_before) or (head != b"" and not run.eden_before)
        if run.eden_fresh:
            new = run.eden.update(console, size)
            if any(mark in new for mark in GAME_STARTED):
                self.game_seen(run)
            if WAITED.search(new):
                run.last_wait = time.monotonic()
            found = found or find_stop(new)
        if found:
            raise Stop(*found)
        return size

    def game_seen(self, run):
        if run.game_seen is None:
            run.game_seen = time.monotonic()
            run.result["game_after"] = round(run.game_seen - run.launched)
            self.say(f"The game started, {run.result['game_after']} s after /launch")

    def note_build(self, trace):
        found = BUILD.search(trace.decode(errors="replace"))
        if found and not self.build:
            self.build = re.sub(r"\s+", " ", found[1])

    # After a test.

    def copy_crashes(self, run):
        logs = self.console.list(LOG_DIR) or {}
        names = self.new_crash_files(run, logs)
        for name in names:
            local = run.folder / name
            if not local.exists() or local.stat().st_size != logs[name].get("size"):
                data = self.console.read(f"{LOG_DIR}/{name}")
                if data is not None:
                    local.write_bytes(data)
        return names

    def settle_crashes(self, run):
        """Copy the crash set until it stops changing. The app writes its files one by one."""
        seen = None
        for _ in range(4):
            time.sleep(self.args.settle)
            self.copy_crashes(run)
            now = sorted((p.name, p.stat().st_size) for p in run.folder.glob("crash-*"))
            if now == seen and read_crash(run.folder):
                return
            seen = now

    def finish_run(self, run, ending):
        if ending == "restart":
            time.sleep(self.args.settle)
            if self.new_crash_files(run, self.console.list(LOG_DIR) or {}):
                ending = "crash"
        closed = False
        if ending == "crash":
            self.settle_crashes(run)
            self.check_crash_files(run)
            fields = read_crash(run.folder)
            run.end("crash", crash_text(fields) if fields else "crash files without a report")
            lived = re.search(r"(\d+) s after the app started", (fields or {}).get("time", ""))
            if lived:
                run.result["seconds"] = int(lived[1])
            self.say(f"Crash: {run.result['detail']}")
            closed = crash_closes(fields)
            if closed:
                self.say("The crash closed the app")
            else:
                # Only the report is there yet: the next process moves the run's logs beside it.
                self.wait_restart(run)
                self.settle_crashes(run)
                self.check_crash_files(run)
        elif ending == "restart":
            # Nothing says why, so nothing says the console is fine. salvage takes the moved logs.
            raise Stop("restart", "the app started again with no crash file. Look at the console first")
        elif ending == "no_game":
            waited = round(time.monotonic() - run.launched)
            run.end("no_game", f"no game {waited} s after /launch: {self.why_no_game(run)}")
            self.say(f"No game: {run.result['detail']}")
        else:
            run.end(ending)
            self.say(f"Time limit reached after {run.result['seconds']} s")
        if not closed:
            self.quit_app()
        self.after_close(run, restarted=ending == "crash" and not closed)

    def why_no_game(self, run):
        text = b"".join(path.read_bytes() for path in (run.folder / "stderr.log", run.folder / "boot-trace.txt")
                        if path.exists())
        found = re.search(rb"EDEN_TEST (?:boot_skipped|bad_boot) \S+|development game \S+ not found", text)
        return found[0].decode(errors="replace") if found else "does this build have EDEN_TEST_BOOT?"

    def take_moved_logs(self, run):
        """The app started again with no crash file, so the end of this run's logs moved aside at that
        start (main.cpp, and Eden's own log rotation). Adds to the run's copies what they lack."""
        console = self.console
        logs, eden = console.list(LOG_DIR) or {}, console.list(EDEN_DIR) or {}
        found = None
        for follower, folder, name in ((run.eden, EDEN_DIR, "eden_log.txt.old.txt"),
                                       (run.others[0], LOG_DIR, "heap.prev.log"),
                                       (run.others[1], LOG_DIR, "stderr.prev.log")):
            entry = (eden if folder == EDEN_DIR else logs).get(name)
            if entry:
                follower.remote = f"{folder}/{name}"
                found = found or find_stop(follower.update(console, entry.get("size")))
        if found:
            raise Stop(*found)

    def check_crash_files(self, run):
        """A device-lost can end in a normal crash report. It stops the batch all the same."""
        for path in sorted(run.folder.glob("crash-*")):
            found = find_stop(path.read_bytes())
            if found:
                raise Stop(*found)

    def wait_restart(self, run):
        """After a crash the app comes back in its launcher. Close it only once it is there."""
        deadline = time.monotonic() + self.args.restart_wait
        while time.monotonic() < deadline:
            if differs(self.console.read(BOOT_TRACE, length=HEAD) or b"", run.boot_head):
                return
            time.sleep(min(self.args.poll, 1))
        # crash_report.cpp hands over to the system then, and that is the CE error needing an OK.
        raise Stop("system_error", f"the crash report said the app starts again, and {self.args.restart_wait:g} s "
                                   "later it has not. Look for a CE error on screen, it needs someone to press OK")

    def quit_app(self):
        """Close the app with test-quit. The app taking the file away is its answer. Its watcher thread
        gives that even with the game stuck, and then forces the exit 3 s later, so this must never go
        to a frozen app. Raises Stop if an app is there and does not answer.

        Closed: ShadowMount took the sandbox mounts away, so the process is gone. A process it does not
        track keeps them (a crash restart, or a start its log calls "runtime preparation timed out"):
        that one is closed once it took the file at least --close-floor s ago and none of its logs has
        grown for --close-quiet s, never earlier. One whose eden_log.txt still grows when --quit-wait is
        over stops the batch, unless the boot trace, read once more, shows a new process: the app then
        crashed on its way out and came back, and the new process is asked to close, once. Only
        eden_log.txt counts for that stop: a new process rewrites heap.log and stderr.log before its
        boot trace is new, and eden_log.txt after, so those two growing can be a restart that the boot
        trace does not show yet. With --close-quiet 0 it counts as closed after --quit-wait, as before."""
        console, args = self.console, self.args
        trace = console.read(BOOT_TRACE, length=HEAD) or b""
        self.ask_to_quit()
        deadline = time.monotonic() + args.quit_wait
        answered = sizes = still = grew = None
        asked_again = False
        while True:
            while time.monotonic() < deadline:
                time.sleep(min(args.poll, 0.5))
                with contextlib.suppress(NoAnswer):
                    if "test-quit" in (console.list(DATA) or {}):
                        continue
                    now = time.monotonic()
                    if answered is None:
                        answered = now
                        deadline = now + args.quit_wait  # the file went at once, the process goes later
                    if not self.app_open():
                        self.say("The app closed")
                        self.closed_at = time.monotonic()
                        return
                    newer = console.read(BOOT_TRACE, length=HEAD) or b""
                    if differs(newer, trace):  # crashed on its way out and came back: ask the new process
                        trace, answered, sizes, still, grew = newer, None, None, None, None
                        self.ask_to_quit()
                        continue
                    if args.close_quiet > 0:
                        seen, now = self.log_sizes(), time.monotonic()
                        if seen != sizes:
                            if sizes is not None and seen[0] != sizes[0]:
                                grew = now  # eden_log.txt, the one log the stop below goes by
                            sizes, still = seen, now  # still counts from the first look at these sizes
                        elif now - answered >= args.close_floor and now - still >= args.close_quiet:
                            self.say(f"The app answered test-quit and no log of it has grown for {now - still:.0f} s: "
                                     "closed, its sandbox keeps its mounts as after a crash restart")
                            self.forget_sandboxes()
                            self.closed_at = time.monotonic()
                            return
            if (answered is None or args.close_quiet <= 0 or args.quit_wait < args.close_floor + args.close_quiet
                    or grew is None or time.monotonic() - grew >= args.close_quiet + 1):
                break
            # Its watcher forces the exit 3 s after it takes the file, and eden_log.txt still grows. A
            # process that came back wrote it too: the boot trace is new before that log is, so one
            # more look at the trace tells the two apart. No answer here is no proof of a new process.
            newer = b""
            with contextlib.suppress(NoAnswer):
                newer = console.read(BOOT_TRACE, length=HEAD) or b""
            if asked_again or not differs(newer, trace):
                raise Stop("no_answer", f"the app took test-quit {args.quit_wait:g} s ago and its logs still "
                                        "grow: it may still be running. Look at the console first")
            asked_again = True  # once: an app that comes back every time must not keep this going
            self.say("A new process is there, the app came back while it closed: asking that one to close")
            trace, answered, sizes, still, grew = newer, None, None, None, None
            self.ask_to_quit()
            deadline = time.monotonic() + args.quit_wait
        if answered is not None:
            self.say("The app answered test-quit, its sandbox keeps its mounts as after a crash restart")
            self.forget_sandboxes()
            self.closed_at = time.monotonic()
            return
        # Left lying around, the file would close the next start at once.
        if "test-quit" in (console.list(DATA) or {}):
            console.remove(TEST_QUIT)
        if self.app_open():
            raise Stop("no_answer", f"the app did not close within {args.quit_wait:g} s of test-quit. "
                                    "If it was already closed, this was a leftover sandbox: use --confirmed-closed")
        self.say("Nothing answered test-quit, and the app is not there")
        self.closed_at = time.monotonic()

    def log_sizes(self):
        """The sizes of the app's three logs, eden_log.txt first. Its game and its shutdown write to
        them, a gone process does not. A process that started again rewrites them: heap.log and
        stderr.log before its boot trace is new (main.cpp), eden_log.txt after."""
        eden, logs = self.console.list(EDEN_DIR) or {}, self.console.list(LOG_DIR) or {}
        return tuple((folder.get(name) or {}).get("size")
                     for folder, name in ((eden, "eden_log.txt"), (logs, "stderr.log"), (logs, "heap.log")))

    def ask_to_quit(self):
        """test-quit, once the running process watches for it. A process that has only just started
        takes a test-quit away unread (TestHarness::Start), which would look just like a clean close,
        and the next /launch would then kill it. It logs EDEN_TEST on right before that. An app that
        never logs it was started with no EDEN_TEST_ setting, and nothing there reads test-quit."""
        console = self.console
        deadline = time.monotonic() + self.args.quit_wait
        while b"EDEN_TEST on" not in (console.read(STDERR_LOG, length=1 << 16) or b""):
            if time.monotonic() >= deadline:
                raise Stop("no_answer", "this app does not read test-quit: it logged no EDEN_TEST on, so it was "
                                        "opened by hand or is an older build. Close it by hand. If it is "
                                        "already closed, this was a leftover sandbox: use --confirmed-closed")
            time.sleep(min(self.args.poll, 0.5))
        console.touch(TEST_QUIT)

    def after_close(self, run, restarted):
        """The app is closed, so nothing rewrites the logs: take the last of them."""
        console = self.console
        logs = console.list(LOG_DIR) or {}
        exit_crash = self.new_crash_files(run, logs) if run.result["ending"] != "crash" else []
        if not restarted and not exit_crash:
            self.follow(run, logs)
            trace = console.read(BOOT_TRACE)
            if trace and not differs(trace, run.boot_head):  # a stop-limit restart wrote a new one
                (run.folder / "boot-trace.txt").write_bytes(trace)
        if exit_crash:
            self.settle_crashes(run)
            fields = read_crash(run.folder)
            run.note("crashed while closing: " + (crash_text(fields) if fields else "see the crash files"))
            self.say(run.result["notes"][-1])
            self.check_crash_files(run)
            if not crash_closes(fields):
                self.wait_restart(run)
                self.settle_crashes(run)
                self.quit_app()
        if run.test.record:
            entry = (console.list(LOG_DIR) or {}).get(posixpath.basename(RECORDED))
            if entry is None or entry == run.recording_before:
                run.note("the app wrote no new recorded-input.txt")
            else:
                data = console.read(RECORDED) or b""
                (run.folder / "recorded-input.txt").write_bytes(data)
                self.say(f"Saved the recording, {len(data.splitlines())} lines")
        self.check_config_kept(run)

    def salvage(self, run):
        """Keep what can still be read after a stop. Reads only: the console is left alone."""
        with contextlib.suppress(NoAnswer):
            time.sleep(self.args.settle)
            self.copy_crashes(run)
            mounts = self.console.read(SHADOWMOUNT_LOG)  # when the system saw the app stop
            if mounts:
                (run.folder / "shadowmount-debug.log").write_bytes(mounts)
            trace = self.console.read(BOOT_TRACE) or b""
            if run.boot_head and not differs(trace, run.boot_head):
                (run.folder / "boot-trace.txt").write_bytes(trace)
                with contextlib.suppress(Stop):
                    self.follow(run, self.console.list(LOG_DIR) or {})
            elif run.boot_head and not self.new_crash_files(run, self.console.list(LOG_DIR) or {}):
                with contextlib.suppress(Stop):
                    self.take_moved_logs(run)

    def close_run(self, run):
        run.end("tool_error", "see the traceback")
        for follower in [run.eden] + run.others:
            if follower.cut:
                run.note(f"{follower.local.name} cut at {self.args.max_log_mib:g} MiB")
        if getattr(run, "video", None):
            run.video.finish()
            if run.video.error:
                run.note(f"no video: {run.video.error}")
        if run.frames:
            run.frames.finish()
            run.result["frames"] = run.frames.count
            if run.frames.count == 0:
                run.note(f"no frames: {run.frames.error or 'OBS gave none'}")
        with contextlib.suppress(NoAnswer):
            index = self.console.read(f"{LOG_DIR}/crash-index.txt")
            if index is not None:
                (run.folder / "crash-index.txt").write_bytes(index)
        if run.test.live is not None:
            if run.live_written is None:
                run.note("live: the schedule was never written (the test spot was not reached)")
            elif not self.stop:  # after a stop nothing more goes to the console
                with contextlib.suppress(NoAnswer, ftplib.Error, OSError):
                    self.console.remove(LIVE_FILE)
        run.result["fps"] = fps_numbers(run.folder)
        if run.test.cold and run.launched is not None:
            # cold-proof.v2.py's log rules: no pipeline records read at boot, an empty prepared store.
            proof = cold_caches.cold_proof(run.folder / "eden_log.txt")
            run.result.setdefault("cold", {})["proof"] = proof
            if proof.get("cold") is False:
                run.note("cold start: the boot still read stored pipelines: " + ", ".join(
                    f"{key} {value}" for key, value in proof.items() if key != "cold"))
            elif proof.get("cold") is None:
                run.note("cold start: the log does not show all three boot lines that prove a cold start (unknown)")
        if run.launched is not None:
            try:
                self.cache_report(run)
            except Exception as error:  # a reader of the log must never cost a start its result.json
                run.note(f"caches: the caches line could not be made ({error!r})")
        fields = read_crash(run.folder)
        if fields:
            run.result["crash"] = fields
        self.check_env_seen(run)
        self.check_test_marks(run)
        (run.folder / "result.json").write_text(json.dumps(run.result, indent=2))
        self.reports(run)
        self.results.append(run.result)

    def cache_report(self, run):
        """The caches line of every start that was launched, warm or cold: which caches the runner set aside and
        put back (a cold start only), and what the boot log says the start reused. Reads the run folder's own
        copy of eden_log.txt; nothing is asked of the console. It changes no verdict: a start whose boot log
        does not read as it was asked gets a note."""
        cold = run.result.get("cold") if run.test.cold else None
        use = cold_caches.boot_caches(run.folder)
        restored = run.result.get("warm_restore")
        restored = restored if restored and restored.get("ok") else None
        if restored:
            line = warm_cache.cache_line(use, restored, cold_caches.boot_text)
            short = warm_cache.cache_short(use, restored, cold_caches.boot_text)
        else:
            line, short = cold_caches.cache_line(use, cold), cold_caches.cache_short(use, cold)
        run.result["caches"] = dict(use, asked="cold" if run.test.cold else "whole cache restored" if restored
                                    else "not cold", line=line, short=short)
        if run.test.cold:
            self.cold_say(run.folder, line)
        elif restored:
            self.warm_say(line)
        else:
            self.say(line)
        reads = use["reads_as"]
        if restored and reads in ("cold", "half"):
            run.note(f"caches: the whole cache was put back from the copy, but the boot log reads as {reads}: "
                     "not a warm control")
        elif run.test.cold and reads in ("warm", "half"):
            run.note(f"caches: asked for a cold start, but the boot log reads as {reads} ({cold_caches.boot_text(use)})")
        elif not run.test.cold and reads in ("cold", "half"):
            run.note(f"caches: not asked to be a cold start, but the boot log reads as {reads}: the store was new "
                     "(a first start on this console, or the caches were not in place)")

    def check_env_seen(self, run):
        """The app prints every env.txt line it took. A missing one means the run tested something else."""
        logs = sorted(run.folder.glob("crash-*-heap.log")) or [run.folder / "heap.log"]
        if not logs[-1].exists():
            return
        with open(logs[-1], "rb") as log:
            text = log.read(1 << 20).decode(errors="replace")  # they come first
        missing = [line for line in run.test.env_text.splitlines() if f"EDEN_ENV {line}" not in text]
        if missing:
            run.note("env.txt lines the app did not report: " + " ".join(missing))

    def check_test_marks(self, run):
        """What the app said about the test. A script it could not read leaves the game running with
        no presses, and that must not pass for a run of the route."""
        logs = sorted(run.folder.glob("crash-*-stderr.log")) or [run.folder / "stderr.log"]
        if not logs[-1].exists():
            return
        marks = re.findall(r"EDEN_TEST (\S.*)", logs[-1].read_text(errors="replace"))
        run.result["test_marks"] = marks
        for mark in marks:
            if mark.split()[0] in ("script_error", "bad_boot", "bad_script", "boot_skipped", "session_skipped",
                                   "record_error", "no_quit_watcher"):
                run.note(f"the app said: {mark}")
        if run.test.script and run.game_seen is not None and not any(m.startswith("script_start") for m in marks):
            run.note("the script did not play: the app never logged script_start")

    def reports(self, run):
        """The tools track's reports, where they exist."""
        jobs = [("run-report.py", [str(run.folder)], "report.txt")]
        if (run.folder / "frames").is_dir():
            jobs.append(("fog-score.py", [str(run.folder / "frames")], "fog-score.txt"))
        for tool, arguments, output in jobs:
            path = self.args.tools / tool
            if not path.exists():
                continue
            try:
                done = subprocess.run([sys.executable, str(path), *arguments], capture_output=True, timeout=180)
                (run.folder / output).write_bytes(done.stdout + done.stderr)
                if done.returncode:
                    run.note(f"{tool} failed, see {output}")
            except (OSError, subprocess.SubprocessError) as error:
                run.note(f"{tool} failed: {error}")

    # The end of the batch.

    def restore_env(self):
        if self.env_before is None or self.env_back:
            return
        config = self.config_before if self.config_touched else None
        error = None
        for attempt in range(3):
            try:
                put_env_back(self.console, self.env_before, config)
                self.env_back = True
                self.state.pop("pending_restore", None)
                self.save_state()
                self.say("env.txt is back and checked in both folders" +
                         ("" if config is None else ", eglantineps5.json too (config-before.json)"))
                return
            except NoAnswer as caught:
                error = caught
                time.sleep(self.args.settle)
        self.env_back = False
        self.say(f"{self.put_back} could NOT be put back: {error}")

    def finish(self):
        stop = self.stop
        if stop and self.launched_any and "stopped" not in self.state:
            self.latch(stop, self.results[-1]["name"] if self.results else "?")
        page = self.summary()
        (self.folder / "summary.md").write_text(page)
        (self.folder / "summary.json").write_text(json.dumps(
            {"stopped": stop and stop.kind, "detail": stop and stop.detail, "interrupted": self.interrupted,
             "env_back": self.env_back, "build": self.build, "tests": self.results,
             # next/: starts a stop rule skipped (no folder: never in "tests"), the rules' decisions, network drops
             "skipped": self.skipped, "stop_rules": self.rules.report() if self.rules else (
                 {"not_used": self.rules_message} if self.rules_message else None),
             "net_drops": self.net_drops}, indent=2))
        print("\n" + page, flush=True)
        self.say(f"Everything is in {self.folder}")
        back = "" if self.env_back is not False else f" {self.put_back} is NOT back: run --restore-env."
        if stop:
            if not self.told_owner:
                notify(self.args, "EglantinePS5 tests stopped", f"{ENDINGS[stop.kind]}.{back}")
            elif back:
                notify(self.args, "EglantinePS5 tests stopped", back.strip())
        else:
            counts = {}
            for result in self.results:
                ending = ENDINGS[result["ending"]]
                counts[ending] = counts.get(ending, 0) + 1
            text = ", ".join(f"{count}x {ending}" for ending, count in counts.items())
            notify(self.args, "EglantinePS5 tests done", f"{len(self.results)} of {len(self.tests)} ran: {text}.{back}")

    def summary(self):
        stop, results = self.stop, self.results
        minutes = (time.time() - self.started) / 60
        lines = [f"# {self.folder.name}", "",
                 f"Plan {self.args.plan.name}, console {self.args.host}, build {self.build or 'not seen'}, "
                 f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(self.started))}, {minutes:.0f} min.", ""]
        if stop:
            lines.append(f"**STOPPED: {ENDINGS[stop.kind]}.** {stop.detail}")
            if self.launched_any:
                lines.append(f"Nothing more was sent to the console except {self.put_back}"
                             + (" and a cold start's caches put back, only with the app closed (below)"
                                if any(r.get("cold") for r in results) else "")
                             + (" and the owner's caches put back, only with the app closed (below)"
                                if self.warm_note else "")
                             + ". The next steps are the owner's.")
        elif self.interrupted:
            lines.append("**Stopped by hand.**")
        elif self.skipped:
            ended = self.rules.ended_by if self.rules and self.rules.ended_by else "stop rules"
            lines.append(f"{len(results)} start(s) ran; {len(self.skipped)} skipped by {ended} (see below).")
        else:
            lines.append(f"All {len(results)} test(s) ran.")
        if self.env_back is True:
            lines.append("env.txt: back as it was, checked in both folders.")
        elif self.env_back is False:
            lines.append("env.txt: **NOT back.** When the console answers: `auto-run.py --restore-env --host <console> --go`.")
        else:
            lines.append("env.txt: never touched.")
        if self.config_touched:
            lines.append("eglantineps5.json: " + ("back as it was (config-before.json), checked." if self.env_back
                                                  else "**NOT back**, `--restore-env` puts it back with env.txt."))
        configured = [test for test in self.tests if test.config is not None]
        if configured:
            lines += ["", "Config (laid over config-before.json; each run's file is its config.json):"]
            lines += [f"- {test.name}: " + ", ".join(show_setting(keys, value) for keys, value in
                                                     config_settings(test.config)) for test in configured]
        colds = [result for result in results if result.get("cold")]
        pending = self.state.get("cold_pending")
        if colds or self.cold_recovered or pending:
            lines += ["", "Cold starts (shader store and driver cache renamed aside for the start and back after; "
                          "each run folder's cold.log and cold-note.json say what moved where):"]
            if self.cold_recovered:
                lines.append(f"- start-up check, before the first test: {self.cold_recovered}")
            shown = {"already_cold": "the console had neither: nothing moved", "back": "back, checked by a listing",
                     "refused": "refused, nothing moved", "not_back": "**NOT back**", "checking": "not started",
                     "not_moved": "cut off before anything moved",
                     "aside": "**still aside**", "moving": "**still aside**"}
            for result in colds:
                cold = result["cold"]
                text = shown.get(cold.get("status"), cold.get("status"))
                if cold.get("set_kept"):
                    text += "; shader set kept in place: " + ", ".join(cold["set_kept"])
                if cold.get("built"):
                    text += "; what the start built is kept as " + ", ".join(cold["built"])
                proof = (cold.get("proof") or {}).get("cold")
                if "proof" in cold:
                    text += "; boot log: " + {True: "cold (no stored pipelines read)", False: "NOT cold",
                                              None: "cannot tell"}[proof]
                lines.append(f"- {result['name']}: {text}")
            if pending:
                lines.append("- **NOT BACK on the console:** " + ", ".join(
                    item["aside"] for item in pending["note"]["items"] if item.get("state") in ("maybe", "aside")) +
                    ". The next `--go`, or `--restore-env --go`, puts them back once the app is closed.")
        warm_note, warm_pending = self.warm_note, self.state.get("warm_pending")
        if warm_note or self.warm_recovered or warm_pending:
            lines += ["", "Whole-cache restore (GrowingBlackBeans' warm-run-steps.md step 0; warm.log and warm-note.json "
                          "in this folder say what moved where):"]
            if self.warm_recovered:
                lines.append(f"- start-up check, before the first test: {self.warm_recovered}")
            if warm_note:
                lines.append(f"- copy: {warm_note.get('copy')}, checked against its SHA-256 list before every start")
                owner = [f"{t['path']} ({t['before']['files']} files, {cold_caches.human(t['before']['bytes'])})"
                         for t in warm_note["trees"].values() if t.get("before")]
                lines.append("- the owner's caches set aside for the batch: " + (", ".join(owner) or "none there") +
                             "; " + ("back at the end, each listing the same as before"
                                     if warm_note.get("status") == "back" else "**NOT BACK**"))
                olds = warm_note.get("old") or []
                if olds:
                    lines.append(f"- {len(olds)} test cache folder(s) renamed aside and KEPT on the console (the runner "
                                 "deletes nothing; remove them by hand when you no longer need them): " +
                                 ", ".join(f"`{e['to']}`" + ("" if e.get("state") == "kept" else
                                                             " (the rename did not show; look by hand)")
                                           for e in olds))
                if self.warm_old_now:
                    lines.append(f"- all .old- test cache folders on the console at the end, from this batch and "
                                 f"earlier ones: {len(self.warm_old_now)}")
            for result in results:
                restored = result.get("warm_restore")
                if restored and restored.get("ok"):
                    lines.append(f"- {result['name']}: the copy put back ({restored['files']} files, "
                                 f"{cold_caches.human(restored['bytes'])}, {restored['seconds']:.0f} s), listing the "
                                 "same as the copy, " + str(sum(t["read_back"] for t in restored["trees"].values())) +
                                 " files read back")
                elif restored:
                    lines.append(f"- {result['name']}: **not put back**: {restored.get('why')}")
            counts = sorted({r["caches"].get("store_pipelines") for r in results
                             if (r.get("warm_restore") or {}).get("ok") and r.get("caches")}, key=str)
            if len(counts) > 1:
                lines.append("- **the store's pipeline count differs between restored starts** "
                             f"({', '.join(map(str, counts))}): the starts did not begin alike")
            if warm_pending:
                lines.append("- **NOT BACK on the console:** " + ", ".join(
                    t["aside"] for t in warm_pending["note"]["trees"].values() if t.get("before")) +
                    f". {self.warm_left or ''} The next `--go`, or `--restore-env --go`, puts them back once the app "
                    "is closed.")
        used = [result for result in results if result.get("caches")]
        if used:
            lines += ["", "Caches per start (what the runner set aside, and what each boot log says the start reused; "
                          "a start that is not cold restores nothing; the full line is in result.json, \"caches\"):"]
            lines += [f"- {result['name']}: {result['caches']['short']}" for result in used]
        if results:
            lines += ["", "| # | Test | Ended | After | Game at | FPS med/last | Frames | Folder |",
                      "|---|---|---|---|---|---|---|---|"]
        for result in results:
            ended = ENDINGS[result["ending"]]
            if result["ending"] == "crash":
                ended = f"crash: {result['detail']}"
            fps = result.get("fps")
            lines.append("| {} | {} | {} | {} | {} | {} | {} | {} |".format(
                result["number"], result["name"], ended,
                "-" if result["seconds"] is None else f"{result['seconds']} s",
                "-" if result["game_after"] is None else f"{result['game_after']} s",
                "-" if not fps else f"{fps[0]:.0f}/{fps[1]:.0f}", result["frames"], result["folder"]))
        notes = [f"- {result['name']}: {note}" for result in results for note in result["notes"]]
        notes += [f"- {result['name']}: {result['detail']}" for result in results
                  if result["ending"] not in ("crash", "time_limit") and result["detail"]
                  and not (stop and result["detail"] == stop.detail)]
        if notes:
            lines += ["", "Notes:"] + notes
        if self.net_drops:
            lines += ["", "Network drops:"] + [
                f"- {d['test']} ({d['folder']}): {d['detail'][:160]}; "
                + (f"resumed ({d.get('how')}), not counted, run again" if d.get("resumed") else
                   f"not resumed: {d.get('how', 'stopped')}") for d in self.net_drops]
        if self.rules_message:
            lines += ["", self.rules_message[0].upper() + self.rules_message[1:] + "."]
        if self.rules and self.rules.decisions:
            lines += ["Stop rule decisions:"] + [f"- rule {d['number']} ({d['rule']}) after {d['start']}: {d['text']}"
                                                 for d in self.rules.decisions]
        if self.skipped:
            lines += ["", "Skipped by a stop rule (not run, neither valid nor invalid):"]
            lines += [f"- {s['name']}: {s['reason']}" for s in self.skipped]
        ran = {result["number"] for result in results} | {s["number"] for s in self.skipped}
        left = [test.name for test in self.tests if test.number not in ran]
        if left:
            lines += ["", "Not run: " + ", ".join(left)]
        return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- start

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plan", nargs="?", type=Path, help="JSON list of tests")
    parser.add_argument("--host", default=runner_config.host(required=False) or None,
                        help="the console's address (default: console.host in runner-config.json; the code itself "
                             "has no address, on purpose)")
    parser.add_argument("--go", action="store_true", help="really do it; without this nothing reaches the console")
    parser.add_argument("--restore-env", action="store_true",
                        help="put back env.txt after a run that could not; with --go also any shader store or driver "
                             "cache a cold start left aside (it looks for .cold-aside- folders on the console)")
    parser.add_argument("--close-open-app", action="store_true", help="close the app with test-quit if it is open")
    parser.add_argument("--confirmed-closed", action="store_true",
                        help="the owner has seen the app is closed: what the sandbox shows is a leftover")
    parser.add_argument("--clear-stop", action="store_true", help="the owner has looked at the last stop, run again")
    parser.add_argument("--new-boot", action="store_true",
                        help="the console has been rebooted since the last stop or may_hang test")
    parser.add_argument("--save", type=Path, help="save backup folder to put back before every test")
    parser.add_argument("--cold", action="store_true",
                        help="every test a cold start, as EDEN_TEST_COLD=1 in its env: the shader store and the "
                             "driver cache renamed aside before the start and put back after (cold_caches.py)")
    parser.add_argument("--warm-copy", type=Path,
                        help="whole-cache restore (GrowingBlackBeans' warm-run-steps.md step 0): the owner's two cache "
                             "folders renamed aside for the batch, and before every start the live ones replaced by "
                             "this copy, checked; the owner's back at the end (warm_cache.py). Not with a cold start")
    parser.add_argument("--make-warm-copy", type=Path,
                        help="copy the console's two cache folders whole into this new folder, with a SHA-256 list "
                             "(reads only; the app must be closed; with --go)")
    parser.add_argument("--check-warm-copy", type=Path,
                        help="check a whole-cache copy against its SHA-256 list and manifest (this computer only)")
    parser.add_argument("--launcher", choices=launchers.KINDS, default=SETTINGS["launcher"]["kind"],
                        help="how the app is started: websrv (its /launch, the default) or prosperomgr (ProsperoMgr's "
                             "POST /api/titles/launch; launchers.py). Files and logs are read through websrv either way")
    parser.add_argument("--launcher-host", default=SETTINGS["launcher"]["host"] or None,
                        help="ProsperoMgr's address (default: the console's)")
    parser.add_argument("--launcher-port", type=int, default=SETTINGS["launcher"]["port"],
                        help=f"ProsperoMgr's port (default {launchers.PROSPEROMGR_PORT})")
    parser.add_argument("--check-launcher", action="store_true",
                        help="with --go: ask the launcher which title runs (and ProsperoMgr its temperatures); starts "
                             "nothing, writes nothing")
    parser.add_argument("--web-port", type=int, default=SETTINGS["console"]["web_port"])
    parser.add_argument("--ftp-port", type=int, default=SETTINGS["console"]["ftp_port"])
    parser.add_argument("--obs-host", default=SETTINGS["capture"]["obs_host"])
    parser.add_argument("--obs-port", type=int, default=SETTINGS["capture"]["obs_port"])
    parser.add_argument("--no-frames", action="store_true", default=not SETTINGS["capture"]["enabled"],
                        help="no frames and no video (the default when capture.enabled is false in the settings)")
    parser.add_argument("--capture-any", action="store_true",
                        help="run even when OBS does not show the capture over the whole canvas")
    parser.add_argument("--frame-every", type=float, default=5, help="seconds between frames")
    parser.add_argument("--poll", type=float, default=5, help="seconds between looks at the logs")
    parser.add_argument("--silence", type=float, default=75,
                        help="seconds without any log growth that mean the app is gone (the game logs every 15)")
    parser.add_argument("--stall-grace", type=float, default=12,
                        help="a GPU wait logged this recently holds the time limit back (the wait logs every 5)")
    parser.add_argument("--no-answer", type=float, default=60, help="seconds of no reply that stop the batch")
    parser.add_argument("--timeout", type=float, default=10, help="seconds for one request")
    parser.add_argument("--boot-wait", type=float, default=60, help="seconds for the app to start after /launch")
    parser.add_argument("--game-wait", type=float, default=120, help="seconds for the game to start after /launch")
    parser.add_argument("--restart-wait", type=float, default=60, help="seconds for the app to come back after a crash")
    parser.add_argument("--quit-wait", type=float, default=20, help="seconds for the app to close after test-quit")
    parser.add_argument("--close-quiet", type=float, default=4,
                        help="an app that took test-quit but keeps its sandbox mounts is closed once no log of it "
                             "has grown for this long (0: only after all of --quit-wait, as before)")
    parser.add_argument("--close-floor", type=float, default=6,
                        help="and never sooner than this after it took the file (its watcher forces the exit "
                             "3 s after, test_harness.h kQuitLimit)")
    parser.add_argument("--discard-save-reuse", action="store_true",
                        help="reuse only after a closed run's session-copy (copied) warning; otherwise restore")
    parser.add_argument("--save-late", action="store_true",
                        help="put the save back right before each start, after the whole --settle pause, as "
                             "before, not while this Mac finishes the test before")
    parser.add_argument("--settle", type=float, default=4, help="seconds for files to finish after an ending")
    parser.add_argument("--max-log-mib", type=float, default=256, help="most of one log to copy while a test runs")
    parser.add_argument("--out-root", type=Path, default=OUT_ROOT)
    parser.add_argument("--tools", type=Path, default=TOOLS, help="where run-report.py and fog-score.py are")
    parser.add_argument("--notify-file", type=Path, help="write notifications here instead of showing them (tests)")
    # added 12 Nov 2026
    parser.add_argument("--no-stop-rules", action="store_true",
                        help="ignore <plan>.stop.json: every start runs, as before")
    parser.add_argument("--no-net-resume", action="store_true",
                        help="a network drop stops the batch, as before (default: wait, close the app, run that "
                             "start once more; a second drop in the batch stops it)")
    parser.add_argument("--net-resume-minutes", type=float, default=15,
                        help="minutes to wait for the console after a network drop (default 15)")
    parser.add_argument("--net-alive-wait", type=float, default=10,
                        help="seconds between the two looks at the game's log after a drop (default 10)")
    parser.add_argument("--launch-fast-check", action="store_true",
                        help="after the first 503 from /launch, look for the open app every --launch-check-every s "
                             "(up to --poll s) instead of one look after --poll s. Every start time still counts from "
                             "the moment the old full pause would have ended (default off; saves no game time)")
    parser.add_argument("--launch-check-every", type=float, default=0.5)
    args = parser.parse_args()
    if not args.host:
        parser.error("no console address: give --host or set console.host in runner-config.json")
    if args.launcher not in launchers.KINDS:
        parser.error(f"launcher.kind {args.launcher!r} in runner-config.json: use one of {', '.join(launchers.KINDS)}")
    runner_config.use_console(args.host, args.web_port, args.ftp_port)  # the save tools started from here use the same console
    if not args.restore_env and args.plan is None and not (args.make_warm_copy or args.check_warm_copy
                                                           or args.check_launcher):
        parser.error("name a plan file")
    if sum(bool(x) for x in (args.restore_env, args.make_warm_copy, args.check_warm_copy, args.plan,
                             args.check_launcher)) > 1:
        parser.error("one at a time: a plan, --restore-env, --make-warm-copy, --check-warm-copy or --check-launcher")
    return args


def main():
    args = parse_args()
    args.out_root.mkdir(parents=True, exist_ok=True)
    if args.restore_env:
        return restore_command(args)
    if args.make_warm_copy or args.check_warm_copy:
        return warm_copy_command(args)
    if args.check_launcher:
        return launcher_check_command(args)
    tests = load_plan(args.plan)
    if args.cold:
        for test in tests:
            test.cold = True
    if args.warm_copy is not None and any(test.cold for test in tests):
        sys.exit("--warm-copy and a cold start in one batch: the whole-cache restore would put the caches back "
                 "under the cold start. Run them as two batches. Nothing was done.")
    if args.warm_copy is not None and args.go:
        try:
            warm_cache.check_copy(args.warm_copy, DATA)
        except warm_cache.WarmRefused as error:
            sys.exit(f"The whole-cache copy is not good: {error}. Nothing was sent to the console.")
    lone = [test.name for test in tests if test.cold_set and not test.cold]
    if lone:
        sys.exit(f"{cold_caches.SET_LINE}=1 needs a cold start ({cold_caches.COLD_LINE}=1 or --cold): " +
                 ", ".join(lone))
    if not args.go:
        print_plan(tests, args, blocked(load_state(args.out_root), tests, args))
        print("\nNothing was sent to the console. Add --go to run this.")
        return 0
    signal.signal(signal.SIGTERM, signal.default_int_handler)
    signal.signal(signal.SIGHUP, signal.default_int_handler)
    runner_config.keep_awake(os.getpid())  # a sleeping computer would lose the run, and stop nothing
    with only_one_run(args.out_root):
        state = load_state(args.out_root)
        blocks = blocked(state, tests, args)
        print_plan(tests, args, blocks)
        if blocks:
            sys.exit("\nNot started, nothing was sent to the console.")
        print()
        if args.new_boot:
            state.pop("hang_test", None)
        if args.new_boot or args.clear_stop:
            state.pop("stopped", None)
        save_state(args.out_root, state)
        return Batch(args, tests, state).run()


if __name__ == "__main__":
    sys.exit(main())
