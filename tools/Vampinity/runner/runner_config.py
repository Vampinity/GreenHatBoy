#!/usr/bin/env python3
"""One place for everything that differs from person to person: the console's address, the folders on
this computer, where the game's save lives on the console, whether a capture card is used, how you want
to be told about a stop, and how the computer is kept awake.

Every tool in this folder reads its settings from here, so no tool carries an address, a home folder or
a save name of its own.

The settings file is JSON. It is looked for in this order:
  1. the path in the environment variable GHB_RUNNER_CONFIG
  2. runner-config.json next to this file
With no file the defaults below apply: no console address (every tool that talks to a console then
stops and says so), folders under ~/ghb-runs, capture on, notifications printed only.

  python3 runner_config.py          prints the settings in use and where they came from
  python3 runner_config.py --check  the same, and exit 1 if something a start needs is missing

Python standard library only. Works on macOS and Linux.
"""
import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

DEFAULTS = {
    # The console. "label" is what goes into shared run folders (the run contract: a label, never an address).
    "console": {"host": "", "web_port": 8080, "ftp_port": 2121, "label": "console-1"},
    # The app on the console. env_folders: every folder the app may read env.txt from (the installed app first;
    # add your own backup copy of the app folder here if you keep one).
    "app": {"id": "PPSA98515", "data_dir": "/data/eglantineps5", "env_folders": ["/data/homebrew/PPSA98515"],
            "shadowmount_log": "/data/shadowmount/debug.log"},
    # The game. save_dir is the game's save folder ON THE CONSOLE, which ends in <profile folder>/<title>.
    # The profile folder is personal: look it up on your own console and never post it.
    "game": {"title": "0400486024DEC000", "save_dir": ""},
    # Folders on this computer. video_trash: where old test videos are moved at the start of a test
    # ("" leaves them where they are). legacy_video_roots: extra folders to look in for old videos.
    "folders": {"out_root": "~/ghb-runs/logs", "save_backups": "~/ghb-runs/save-backups", "notes": "~/ghb-runs/notes",
                "video_trash": "", "legacy_video_roots": []},
    # Capture through OBS (WebSocket on, no password). enabled false: no frames, no video, nothing asked of OBS.
    # hwaccel: ffmpeg's decoder help for the flicker meter: "auto" (videotoolbox on macOS, none elsewhere),
    # "none", or any name ffmpeg -hwaccels lists.
    "capture": {"enabled": True, "obs_host": "127.0.0.1", "obs_port": 4455, "source": "Video Capture Device",
                "hwaccel": "auto"},
    # How to tell you about a stop. command: "" prints only; "macos" shows a macOS notification; or a list,
    # for example ["notify-send", "{title}", "{text}"], with {title} and {text} filled in.
    "notify": {"command": ""},
    # Keeping the computer awake while a batch runs: "auto" (caffeinate on macOS, systemd-inhibit on Linux
    # when it is there), "none", or a list such as ["caffeinate", "-i", "-w", "{pid}"].
    "keep_awake": {"command": "auto"},
    # Other programs the queue waits for before it starts an item (regular expressions on the command line).
    "wait_for": [r"auto-run(-wait)?\.py .*--go"],
}

_cache = None


def config_path():
    """The settings file in use, or None."""
    named = os.environ.get("GHB_RUNNER_CONFIG")
    if named:
        return Path(named).expanduser()
    beside = HERE / "runner-config.json"
    return beside if beside.exists() else None


def _merge(base, extra, where=""):
    for key, value in extra.items():
        if key.startswith("_"):  # "_comment" keys are notes for people
            continue
        if key not in base:
            raise SystemExit(f"runner config: unknown setting {where}{key}")
        if isinstance(base[key], dict):
            if not isinstance(value, dict):
                raise SystemExit(f"runner config: {where}{key} must be an object")
            _merge(base[key], value, f"{where}{key}.")
        else:
            base[key] = value
    return base


def load(refresh=False):
    """The settings as a dict (DEFAULTS with the file's values over them). Read once per process."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    settings = copy.deepcopy(DEFAULTS)
    path = config_path()
    if path is not None:
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as error:
            raise SystemExit(f"runner config {path}: {error}")
        if not isinstance(data, dict):
            raise SystemExit(f"runner config {path}: must be a JSON object")
        _merge(settings, data)
    settings["_file"] = str(path) if path else None
    _cache = settings
    return settings


def folder(name):
    """A folder from "folders" as a Path with ~ filled in ("" gives None)."""
    text = load()["folders"].get(name) or ""
    return Path(text).expanduser() if text else None


def host(required=True):
    """The console's address. There is no built-in default, on purpose.

    The runner and the queue put the address they were started with (--host, or "host" in a queue file) into
    the environment variable GHB_RUNNER_HOST, and that wins here. So the save tools they start always talk to
    the same console as the test itself, also when the address was given on the command line."""
    value = os.environ.get("GHB_RUNNER_HOST") or load()["console"]["host"]
    if not value and required:
        raise SystemExit("no console address: set console.host in runner-config.json (see runner-config.example.json)")
    return value


def web_port():
    return int(os.environ.get("GHB_RUNNER_WEB_PORT") or load()["console"]["web_port"])


def ftp_port():
    return int(os.environ.get("GHB_RUNNER_FTP_PORT") or load()["console"]["ftp_port"])


def use_console(address, web=None, ftp=None):
    """Called by the runner and the queue once they know which console this run is for: every tool they start
    from here on (save back-up, save put-back) inherits it."""
    os.environ["GHB_RUNNER_HOST"] = str(address)
    if web:
        os.environ["GHB_RUNNER_WEB_PORT"] = str(web)
    if ftp:
        os.environ["GHB_RUNNER_FTP_PORT"] = str(ftp)


def web(path=""):
    """http://<console>:<web port>/fs<path> (websrv's file view)."""
    return f"http://{host()}:{web_port()}/fs{path}"


def save_dir():
    """The game's save folder on the console. Personal, so it must come from the settings file."""
    value = load()["game"]["save_dir"]
    if not value:
        raise SystemExit("no save folder: set game.save_dir in runner-config.json to the game's save folder on "
                         "YOUR console (it ends in <your profile folder>/<title>)")
    return value.rstrip("/")


def hwaccel():
    """ffmpeg arguments for hardware decoding, [] for none."""
    value = load()["capture"].get("hwaccel", "auto")
    if value == "auto":
        value = "videotoolbox" if sys.platform == "darwin" else "none"
    return [] if value in ("", "none", None) else ["-hwaccel", str(value)]


def notify(title, text):
    """Tell the person at the computer. Never raises: a notification must not take a stop down."""
    command = load()["notify"].get("command", "")
    try:
        if command == "macos":
            script = ["on run argv",
                      'display notification (item 2 of argv) with title (item 1 of argv) sound name "Basso"', "end run"]
            command = ["osascript"] + [part for line in script for part in ("-e", line)] + [title, text]
        elif isinstance(command, list) and command:
            command = [str(part).replace("{title}", title).replace("{text}", text) for part in command]
        else:
            print(f"[notice] {title}: {text}", file=sys.stderr, flush=True)
            return
        subprocess.run(command, timeout=15, capture_output=True)
    except (OSError, subprocess.SubprocessError, ValueError):
        pass


def keep_awake(pid):
    """Start whatever keeps this computer awake while process `pid` lives. Never raises."""
    command = load()["keep_awake"].get("command", "auto")
    try:
        if command == "auto":
            if sys.platform == "darwin" and shutil.which("caffeinate"):
                command = ["caffeinate", "-i", "-w", "{pid}"]
            elif shutil.which("systemd-inhibit"):
                command = ["systemd-inhibit", "--what=sleep:idle", "--why=console test batch",
                           "tail", "--pid={pid}", "-f", "/dev/null"]
            else:
                return
        if not isinstance(command, list) or not command:
            return
        subprocess.Popen([str(part).replace("{pid}", str(pid)) for part in command],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, ValueError):
        pass


def process_list(pattern):
    """[(pid, command line)] of running programs whose command line matches the pattern (pgrep).
    macOS prints the full command line with -fl; Linux needs -a for that."""
    flags = "-fl" if sys.platform == "darwin" else "-af"
    try:
        done = subprocess.run(["pgrep", flags, pattern], capture_output=True, text=True)
    except OSError:
        return []
    found = []
    for line in done.stdout.splitlines():
        pid, _, command = line.partition(" ")
        if pid.isdigit():
            found.append((int(pid), command))
    return found


def problems():
    """What a scripted start still needs, as plain lines ([] when ready)."""
    settings, out = load(), []
    if settings["_file"] is None:
        out.append("no settings file: copy runner-config.example.json to runner-config.json and fill it in")
    if not settings["console"]["host"]:
        out.append("console.host is empty")
    if not settings["game"]["save_dir"]:
        out.append("game.save_dir is empty (only needed when a test puts a save back or backs one up)")
    for tool in ("ffmpeg", "ffprobe"):
        if settings["capture"]["enabled"] and not shutil.which(tool):
            out.append(f"{tool} is not installed (needed for the video check and the flicker meter)")
    return out


if __name__ == "__main__":
    shown = {key: value for key, value in load().items() if key != "_file"}
    if shown["console"]["host"]:
        shown["console"] = dict(shown["console"], host="<set>")  # never print an address into a shared log
    if shown["game"]["save_dir"]:
        shown["game"] = dict(shown["game"], save_dir="<set>")
    print("settings file:", load()["_file"] or "none (defaults)")
    print(json.dumps(shown, indent=2))
    missing = problems()
    for line in missing:
        print("MISSING:", line)
    sys.exit(1 if missing and "--check" in sys.argv else 0)
