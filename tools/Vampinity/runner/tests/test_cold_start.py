#!/usr/bin/env python3
"""Offline tests of the runner's cold-start option (EDEN_TEST_COLD=1 / --cold) and of its caches line.
They never talk to a console: offline_guard.py makes any network use or child process fail, and every case
checks that none was even tried.

  python3 -m unittest discover -s tools/Vampinity/runner/tests -v      from the top of the repo
  python3 tools/Vampinity/runner/tests/test_cold_start.py              the same cases, PASS/FAIL per case

A local scratch folder stands in for the console (FakeConsole: the same calls as the runner's Console, and a
rename that replaces an existing target the way the console's RNTO does, logged so a test can prove it never
happened). The runner itself is loaded through the wait wrapper and run with its real main(), Batch.run,
run_test, prepare and close_run. Stubbed are only the parts that start and close the game: Batch.start (writes
env.txt, "opens" the app, makes it build new caches and writes a boot log), Batch.watch (the scenario's ending),
Batch.finish_run and Batch.quit_app (the app closes). Settings come from a scratch runner-config.json and every
folder setting points into the scratch folder, so no real address, folder or save is read or written.
Standard library only.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import posixpath
import shutil
import sys
import tempfile
import time
import traceback
import types
import unittest
import warnings
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import offline_guard  # noqa: E402

offline_guard.install()  # before the runner is loaded: from here no socket connects and no program starts

HERE = Path(__file__).resolve().parent.parent  # the runner's folder
SCRATCH = Path(tempfile.mkdtemp(prefix="cold-desk-"))
HOST = "console.invalid"  # a name that can never resolve (RFC 6761); the guard refuses the lookup anyway
for _name in [name for name in os.environ if name.startswith("GHB_RUNNER_")]:
    del os.environ[_name]  # no setting of the person who runs the tests leaks in
SETTINGS = SCRATCH / "runner-config.json"
SETTINGS.write_text(json.dumps({
    "console": {"host": HOST},
    "app": {"env_folders": ["/data/homebrew/PPSA98515"]},
    "capture": {"enabled": False},
    "folders": {"out_root": str(SCRATCH / "default-out"), "save_backups": str(SCRATCH / "save-backups"),
                "notes": str(SCRATCH / "notes"), "video_trash": "", "legacy_video_roots": []},
    "notify": {"command": ""},
    "keep_awake": {"command": "none"},
}))
os.environ["GHB_RUNNER_CONFIG"] = str(SETTINGS)

_spec = importlib.util.spec_from_file_location("wait_wrapper", HERE / ("auto-run" + "-wait.py"))
wrapper = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wrapper)
tool = wrapper.tool
cold_caches = tool.cold_caches
tool.runner_config.keep_awake = lambda pid: None
RealConsole = tool.Console  # kept for the one case that proves the guard stops the real thing

DATA = tool.DATA
TITLE = "0400486024DEC000"
SHADER = f"{DATA}/user/cache/shader/{TITLE.lower()}"
RADV = f"{DATA}/cache/radv"
APP_FOLDER = "/data/homebrew/PPSA98515"
RECIPE_NAME = "example-set-v1.nx2recipe"  # a shader set's recipe: any *.nx2recipe at the top of the title folder
RECIPE = f"{SHADER}/{RECIPE_NAME}"
INDEX = f"{SHADER}/shader_set_index.txt"
STORE = "prep_0a1b2c3d"  # a made-up store name


def boot_log(pipelines, store_state, driver_cache):
    """The boot lines the app writes about its caches, in the wording of a real log (a public packed run of
    19 Nov 2026), with made-up ids. pipelines 0 and store_state "new": a first start."""
    known = 78735 if pipelines else 0
    lines = ["[   5.975301] Render.Vulkan <Info> LoadDiskResources: EDEN_UP_SHADER_PREP_SOURCE_STAMP: id "
             f"src00112233445566778899aabbccddeeff (files 418) dev0011223344556677, store {STORE} {store_state} "
             f"({known} pipelines), build 84805134.1795073122000000000"]
    if driver_cache:
        lines.append("[   7.209710] Render.Vulkan <Info> LoadVulkanPipelineCache: Loaded Vulkan driver pipeline cache: "
                     f"{SHADER}/up_v1_2/vulkan_pipelines.bin")
    lines += [f"[  10.927571] Render.Vulkan <Info> LoadDiskResources: Total Pipeline Count: {pipelines}",
              f"[  46.592914] Render.Vulkan <Info> PrepareKept: Shader preparation: {known} pipelines known, 0 left to "
              "prepare (0 of this console's own records, 0 predicted), 0 struck out",
              f"[  46.594317] Render.Vulkan <Info> PrepareKept: Shader preparation stats: {pipelines and 7816} records "
              f"read ({pipelines and 7816} own, 0 predicted): 0 left out"]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- the console stand-in

class FakeConsole:
    """A local folder as the console. Answers like the runner's Console: None for "not there", NoAnswer for
    trouble. Every call is logged."""

    def __init__(self, root):
        self.root = Path(root)
        self.calls, self.overwrites, self.removed, self.renamed, self.made = [], [], [], [], []
        self.fail_mkdir = False  # True: the folder is made but the answer is lost (the worst case)
        self.app_running = False
        self.log_grows = False
        self.log_reads = 0
        self.fail_rename_at = None  # the n-th rename (1-based) fails with no answer
        self.ctrl_c_at = None  # Ctrl-C comes right before the n-th rename
        self.down = False

    def local(self, path):
        assert path.startswith("/") and ".." not in path.split("/"), path
        return self.root / path.lstrip("/")

    def _up(self, what):
        if self.down:
            raise tool.NoAnswer(f"fake: no answer for {what}")

    def list(self, path):
        self.calls.append(("list", path))
        self._up(path)
        folder = self.local(path)
        if not folder.exists():
            return None
        if not folder.is_dir():
            raise tool.NoAnswer(f"fake: {path} is a file")
        out = {".": {"name": ".", "mode": "d"}, "..": {"name": "..", "mode": "d"}}  # websrv lists these too
        for child in sorted(folder.iterdir()):
            out[child.name] = {"name": child.name, "mode": "d" if child.is_dir() else "-",
                               "size": 0 if child.is_dir() else child.stat().st_size, "mtime": 1}
        if path == tool.EDEN_DIR and "eden_log.txt" in out:
            self.log_reads += 1
            if self.log_grows:
                out["eden_log.txt"]["size"] += self.log_reads
        return out

    def read(self, path, offset=0, length=None):
        self.calls.append(("read", path))
        self._up(path)
        file = self.local(path)
        if not file.is_file():
            return None
        data = file.read_bytes()[offset:]
        return data if length is None else data[:length]

    read_ftp = read

    def put(self, path, data):
        self.calls.append(("put", path))
        if not tool.writable(path):
            raise tool.Refused(path)
        self.local(path).parent.mkdir(parents=True, exist_ok=True)
        self.local(path).write_bytes(data)

    def touch(self, path):
        self.put(path, b"")

    def remove(self, path):
        self.calls.append(("remove", path))
        if not tool.writable(path):
            raise tool.Refused(path)
        self.removed.append(path)
        self.local(path).unlink()

    def check_ftp(self):
        self._up("ftp")

    def launch(self):
        return 200

    def rename_cold(self, source, target):
        self.calls.append(("rename", source, target))
        if not cold_caches.allowed_pair(source, target, DATA):
            raise tool.Refused(f"{source} -> {target}")
        self._up("ftp")
        if self.fail_rename_at is not None and len(self.renamed) + 1 == self.fail_rename_at:
            self.fail_rename_at = None
            raise tool.NoAnswer("fake: FTP: connection reset during RNTO")
        if self.ctrl_c_at is not None and len(self.renamed) + 1 == self.ctrl_c_at:
            self.ctrl_c_at = None
            raise KeyboardInterrupt  # Ctrl-C at the terminal right before this rename is sent
        s, t = self.local(source), self.local(target)
        if not s.exists():
            raise tool.NoAnswer(f"fake: 550 {source}")
        if t.exists():  # what RNTO does on the console: the old target is gone
            self.overwrites.append((source, target))
            shutil.rmtree(t) if t.is_dir() else t.unlink()
        os.rename(s, t)
        self.renamed.append((source, target))

    def mkdir_cold(self, path):
        self.calls.append(("mkdir", path))
        if not cold_caches.allowed_folder(path, DATA):
            raise tool.Refused(path)
        self._up("ftp")
        folder = self.local(path)
        if folder.exists():  # ftpsrv answers 550; the caller lists first, so this must never happen
            raise tool.NoAnswer(f"fake: 550 {path} exists")
        folder.mkdir()
        self.made.append(path)
        if self.fail_mkdir:
            self.fail_mkdir = False
            raise tool.NoAnswer("fake: FTP: connection reset after MKD")

    def sandboxes(self):
        return {f"{tool.APP}_000": {"mtime": 1}}

    def mounted_sandboxes(self):
        return {f"{tool.APP}_000@1"} if self.app_running else set()

    def other_games(self):
        return []


def put_file(root, path, data):
    file = Path(root) / path.lstrip("/")
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(data)


def console_layout(root, shader=True, radv=True, recipe=False):
    """A console with an app, its logs, and (by default) a full shader store and driver cache. recipe: the shader
    set's two input files at the top of the title folder too."""
    put_file(root, f"{APP_FOLDER}/env.txt", b"EDEN_UP_PLAY_SETTING=1\n")
    put_file(root, f"{APP_FOLDER}/eboot.bin", b"\x7fELF" + b"\0" * 64)
    put_file(root, f"{DATA}/user/log/eden_log.txt", b"old log\n" * 10)
    put_file(root, f"{DATA}/logs/stderr.log", b"old\n")
    put_file(root, f"{DATA}/logs/boot-trace.txt", b"old trace\n")
    (Path(root) / "mnt/sandbox").mkdir(parents=True, exist_ok=True)
    if shader:
        put_file(root, f"{SHADER}/up_v1_2/prep_5093ab9e.bin", os.urandom(3000))
        put_file(root, f"{SHADER}/up_v1_2/prep_stores.txt", b"prep_5093ab9e\n")
        put_file(root, f"{SHADER}/prep_stores.txt", b"prep_5093ab9e\n")
        put_file(root, f"{SHADER}/vulkan.bin", os.urandom(1200))
        put_file(root, f"{SHADER}/up_v1_2/prep_shader_set.bin", os.urandom(700))  # what the set built: cache
    if recipe:
        put_file(root, RECIPE, b"NX2RCP01" + os.urandom(500))
        put_file(root, INDEX, b"romfs/shader/a.bfsha\n" * 4)
    if radv:
        put_file(root, f"{RADV}/00/4f1c0de9", os.urandom(900))
        put_file(root, f"{RADV}/index", os.urandom(64))


def hashes(root):
    """{console path: sha256} of every file under the stand-in."""
    out = {}
    for dirpath, _, files in os.walk(root):
        for name in files:
            p = Path(dirpath) / name
            out["/" + str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


# ---------------------------------------------------------------- the stubs (only what starts and closes the game)

SCENARIO = {}


def stub_start(self, run):
    fake = self.console
    test = run.test
    (run.folder / "env.txt").write_text(test.env_text)
    for folder in tool.ENV_FOLDERS:
        fake.put(f"{folder}/env.txt", test.env_text.encode())
    shader = fake.local(SHADER)
    # What the start finds in the live title folder: {console path: sha256}. Only shader-set files = still cold.
    found = {"/" + str(p.relative_to(fake.root)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in shader.rglob("*") if p.is_file()} if shader.exists() else {}
    SCENARIO.setdefault("at_start", []).append(found)
    was_cold = all(cold_caches.is_set_file(posixpath.basename(p)) and posixpath.dirname(p) == SHADER for p in found)
    fake.app_running = True
    self.launched_any = True
    self.closed_at = None
    run.launched = time.monotonic()
    run.game_seen = 1.0
    # The game builds caches where it finds none (or adds to the ones there).
    put_file(fake.root, f"{SHADER}/up_v1_2/prep_built.bin", b"built by this start " * 20)
    put_file(fake.root, f"{RADV}/ff/built", b"driver binary " * 10)
    # The boot log follows what the start found, unless the scenario says otherwise ("half": a new store, but a
    # driver pipeline cache and pipelines from an earlier start; "none": a log without any cache line).
    kind = SCENARIO.get("boot") or ("cold" if was_cold else "warm")
    (run.folder / "eden_log.txt").write_text({
        "cold": boot_log(0, "new", False), "warm": boot_log(4204, "reused", True),
        "half": boot_log(4204, "new", True), "none": "[   1.000000] Frontend <Info> nothing about caches here\n"}[kind])
    SCENARIO.setdefault("started", []).append(test.name)


def stub_watch(self, run):
    what = SCENARIO.get("ending", "script_end")
    if what == "script_end":
        return "script_end"
    if what == "crash_gone":  # the game crashed and the app is gone: the runner stops on a system error
        self.console.app_running = False
        raise tool.Stop("system_error", "fake: the app is gone with no crash file")
    if what == "freeze":  # frozen: the app stays open
        raise tool.Stop("freeze", "fake: no frame for 30 s")
    if what == "tool_bug":  # this tool fails; the app had already gone
        self.console.app_running = False
        raise RuntimeError("fake: a bug in the runner")
    if what == "ctrl_c":
        raise KeyboardInterrupt
    raise AssertionError(what)


def stub_finish_run(self, run, ending):
    run.end(ending)
    self.quit_app()


def stub_quit_app(self):
    if SCENARIO.get("ending") == "freeze":
        raise tool.Stop("no_answer", "fake: the frozen app does not take test-quit")
    self.console.app_running = False
    self.closed_at = time.monotonic()


tool.Batch.start = stub_start
tool.Batch.watch = stub_watch
tool.Batch.finish_run = stub_finish_run
tool.Batch.quit_app = stub_quit_app
cold_caches.QUIET = 0.01  # the closed check's eden_log.txt look: 20 s on a console, a moment here
FAKE = {}
tool.Console = lambda args: FAKE["console"]


def plan(folder, name, env, tests=1):
    path = Path(folder) / f"{name}.json"
    path.write_text(json.dumps([{"name": f"{name}-{k}", "title": TITLE, "seconds": 60, "env": env}
                                for k in range(1, tests + 1)]))
    return path


def run_main(plan_path, out_root, extra=()):
    """The runner's own main(), through the wait wrapper's argument parser. (exit code, printed text)."""
    sys.argv = ["runner", str(plan_path), "--go", "--settle", "0", "--out-root", str(out_root),
                "--notify-file", str(Path(out_root) / "notify.txt"), *extra]
    printed = io.StringIO()
    code = None
    with contextlib.redirect_stdout(printed):
        try:
            code = tool.main()
        except SystemExit as stop:
            code = stop.code
        except Exception:  # noqa: BLE001 - a case may make the runner fail on purpose
            code = "raised: " + traceback.format_exc().strip().splitlines()[-1]
    return code, printed.getvalue()


def batches(out_root):
    return sorted(p for p in Path(out_root).glob("auto-*") if p.is_dir())


def state_of(out_root):
    path = Path(out_root) / "auto-run-state.json"
    return json.loads(path.read_text()) if path.exists() else {}


def asides(root):
    found = []
    for folder in (f"{DATA}/cache", f"{DATA}/user/cache/shader"):
        p = Path(root) / folder.lstrip("/")
        if p.exists():
            found += sorted(f"{folder}/{c.name}" for c in p.iterdir() if ".cold-" in c.name)
    return found


# ---------------------------------------------------------------- the checks every case shares

def nothing_deleted(before, fake):
    """Every file the console had at the start is still there, byte for byte, at its own path (the old caches
    are back) or, for a case that stops with the caches aside, under a .cold-aside- name. No RNTO replaced a
    target, and nothing under a cache folder was ever removed."""
    after = hashes(fake.root)
    problems = []
    for path, digest in before.items():
        if after.get(path) == digest:
            continue
        moved = [p for p, d in after.items() if d == digest and ".cold-aside-" in p]
        if not moved:
            problems.append(f"{path} is gone or changed")
    if fake.overwrites:
        problems.append(f"a rename replaced a target: {fake.overwrites}")
    cache_removes = [p for p in fake.removed if "/cache/" in p]
    if cache_removes:
        problems.append(f"removed under a cache folder: {cache_removes}")
    return problems


def private_values(out_root):
    """The cold-start files and lines the runner wrote must not hold an address or a folder of this computer."""
    bad = []
    home = str(Path.home())
    needles = [HOST, home, str(SCRATCH), "/" + "Users/", "/" + "home/"]
    files = [p for p in Path(out_root).rglob("*") if p.is_file() and
             (p.name in (cold_caches.NOTE_NAME, cold_caches.LOG_NAME, "cold-recovery.json"))]
    texts = [(p.name, p.read_text(errors="replace")) for p in files]
    for log in Path(out_root).rglob("batch.log"):
        texts.append((log.name, "\n".join(line for line in log.read_text().splitlines()
                                         if any(m in line for m in ("Cold start", "COLD START", "Start-up check")))))
    for name, text in texts:
        for needle in needles:
            if needle and needle in text:
                bad.append(f"{name} holds {needle!r}")
    return bad


RESULTS = []
VERBOSE = False  # True when run as a script: PASS/FAIL per case on the screen


def case(name):
    def wrap(function):
        def run():
            SCENARIO.clear()
            FAKE.clear()
            folder = SCRATCH / name
            folder.mkdir()
            root, out = folder / "console", folder / "out"
            root.mkdir()
            out.mkdir()
            del offline_guard.ATTEMPTS[:]
            try:
                problems = function(root, out, folder) or []
                # Every case: nothing the console had at the start is lost, and the cold-start files and lines
                # hold no address and no folder of this computer.
                if "console" in FAKE:
                    problems += [p for p in nothing_deleted(FAKE["before"], FAKE["console"]) if p not in problems]
                problems += [p for p in private_values(out) if p not in problems]
            except Exception:  # noqa: BLE001
                problems = ["the case itself failed: " + traceback.format_exc()]
            # Every case: nothing reached for the network and no program was started. The runner swallows a
            # refused connection as "no answer", so the guard's own list is what counts.
            if not offline_guard.installed():
                problems.append("the offline guard is not in place")
            problems += [f"tried to leave this process: {attempt}" for attempt in offline_guard.ATTEMPTS]
            del offline_guard.ATTEMPTS[:]
            RESULTS.append((name, problems))
            if VERBOSE:
                print(("PASS " if not problems else "FAIL ") + name)
                for problem in problems:
                    print("     " + problem.replace("\n", "\n     "))
            return problems
        RUN.append((name, run))
        return function
    return wrap


RUN = []


def new_fake(root, **layout):
    console_layout(root, **layout)
    FAKE["console"] = FakeConsole(root)
    FAKE["before"] = hashes(root)  # what the shared "nothing deleted" check compares with at the end
    return FAKE["console"]


@case("1 move then restore (EDEN_TEST_COLD=1, two cold starts in one batch)")
def _(root, out, folder):
    fake = new_fake(root)
    before = hashes(root)
    code, text = run_main(plan(folder, "cold", ["EDEN_TEST_DISCARD_SAVE=1", "EDEN_TEST_COLD=1"], tests=2), out)
    p = []
    if code != 0:
        p.append(f"exit {code}: {text[-600:]}")
    p += nothing_deleted(before, fake)
    for path in before:
        if before[path] != hashes(root).get(path):
            p.append(f"{path} is not back byte for byte")
    built = [a for a in asides(root) if ".cold-built-" in a]
    if len(built) != 4:  # two starts x (shader store, driver cache)
        p.append(f"expected 4 kept built sets, found {built}")
    if [a for a in asides(root) if ".cold-aside-" in a]:
        p.append(f"a .cold-aside- folder is left: {asides(root)}")
    if len(fake.renamed) != 12:  # per start: 2 aside, 2 built, 2 back
        p.append(f"expected 12 renames, got {len(fake.renamed)}: {fake.renamed}")
    if "cold_pending" in state_of(out):
        p.append("the state file still has cold_pending")
    runs = sorted(batches(out)[0].glob("run*"))
    for run in runs:
        result = json.loads((run / "result.json").read_text())
        cold = result.get("cold", {})
        if cold.get("status") != "back" or not cold.get("back"):
            p.append(f"{run.name}: result cold = {cold}")
        if (cold.get("proof") or {}).get("cold") is not True:
            p.append(f"{run.name}: the boot log should read cold: {cold.get('proof')}")
        if "EDEN_TEST_COLD" in (run / "env.txt").read_text():
            p.append(f"{run.name}: EDEN_TEST_COLD reached env.txt")
        log = (run / cold_caches.LOG_NAME).read_text()
        for needle in ("-> 0400486024dec000.cold-aside-", "-> radv.cold-aside-", "kept as radv.cold-built-",
                       "checked by a listing: the same"):
            if needle not in log:
                p.append(f"{run.name}: cold.log lacks {needle!r}")
        note = json.loads((run / cold_caches.NOTE_NAME).read_text())
        if note["status"] != "back" or [i["state"] for i in note["items"]] != ["back", "back"]:
            p.append(f"{run.name}: note {note['status']} {[i['state'] for i in note['items']]}")
    if "EDEN_TEST_COLD" in (root / APP_FOLDER.lstrip("/") / "env.txt").read_text():
        p.append("EDEN_TEST_COLD is in the console's env.txt")
    summary = (batches(out)[0] / "summary.md").read_text()
    if "back, checked by a listing" not in summary:
        p.append("summary.md does not say the caches are back")
    p += private_values(out)
    return p


@case("2a restore after a game crash (app gone, the batch stops on a system error)")
def _(root, out, folder):
    fake = new_fake(root)
    before = hashes(root)
    SCENARIO["ending"] = "crash_gone"
    code, text = run_main(plan(folder, "crash", ["EDEN_TEST_COLD=1"]), out)
    p = [] if code == 2 else [f"exit {code}, expected 2 (stopped)"]
    p += nothing_deleted(before, fake)
    if [a for a in asides(root) if ".cold-aside-" in a]:
        p.append(f"not put back after the crash: {asides(root)}")
    if any(before[k] != hashes(root).get(k) for k in before):
        p.append("the old caches are not back byte for byte")
    if "cold_pending" in state_of(out):
        p.append("cold_pending left in the state file")
    p += private_values(out)
    return p


@case("2b restore after this tool itself crashes (an exception in the runner)")
def _(root, out, folder):
    fake = new_fake(root)
    before = hashes(root)
    SCENARIO["ending"] = "tool_bug"
    code, text = run_main(plan(folder, "bug", ["EDEN_TEST_COLD=1"]), out)
    p = [] if str(code).startswith("raised") else [f"expected the runner to raise, got {code}"]
    p += nothing_deleted(before, fake)
    if [a for a in asides(root) if ".cold-aside-" in a] or any(before[k] != hashes(root).get(k) for k in before):
        p.append(f"not put back after the tool error: {asides(root)}")
    return p


@case("2c restore after Ctrl-C")
def _(root, out, folder):
    fake = new_fake(root)
    before = hashes(root)
    SCENARIO["ending"] = "ctrl_c"
    code, text = run_main(plan(folder, "ctrlc", ["EDEN_TEST_COLD=1"]), out)
    p = [] if code == 130 else [f"exit {code}, expected 130"]
    p += nothing_deleted(before, fake)
    if [a for a in asides(root) if ".cold-aside-" in a] or any(before[k] != hashes(root).get(k) for k in before):
        p.append(f"not put back after Ctrl-C: {asides(root)}")
    return p


@case("3a refusal while the app runs (eden_log.txt grows), nothing moved")
def _(root, out, folder):
    fake = new_fake(root)
    before = hashes(root)
    fake.log_grows = True
    code, text = run_main(plan(folder, "busy", ["EDEN_TEST_COLD=1"]), out)
    p = [] if code == 2 else [f"exit {code}, expected 2"]
    if fake.renamed:
        p.append(f"renamed while the app ran: {fake.renamed}")
    if SCENARIO.get("started"):
        p.append("the test started after the refusal")
    if hashes(root) != before:
        p.append("the console changed")
    summary = (batches(out)[0] / "summary.md").read_text()
    if "cold start refused, nothing was moved" not in summary:
        p.append("summary.md does not name the refusal")
    return p


@case("3b refusal while the app runs (sandbox mounted), straight on ColdCaches")
def _(root, out, folder):
    fake = new_fake(root)
    before = hashes(root)
    fake.app_running = True
    caches = cold_caches.ColdCaches(fake, DATA, [APP_FOLDER], say=lambda t: None,
                                    app_open=lambda: bool(fake.mounted_sandboxes()),
                                    log_sizes=lambda: (1, 1, 1), errors=(tool.NoAnswer,), quiet=0)
    p = []
    try:
        caches.set_aside(TITLE, keep=lambda note: None)
        p.append("set_aside did not refuse")
    except cold_caches.ColdRefused as error:
        if "running" not in str(error):
            p.append(f"refused for another reason: {error}")
    note = {"items": [{"what": "driver cache", "path": RADV, "aside": RADV + ".cold-aside-20261118-000000",
                       "state": "aside", "before": None}], "status": "aside"}
    ok, why = caches.put_back(note, keep=lambda n: None)
    if ok or "running" not in why:
        p.append(f"put_back did not wait for the app: {ok} {why}")
    if fake.renamed or hashes(root) != before:
        p.append("something moved")
    return p


@case("4 frozen app: caches stay aside; the next --go (a plain warm plan) puts them back first")
def _(root, out, folder):
    fake = new_fake(root)
    before = hashes(root)
    SCENARIO["ending"] = "freeze"
    code, text = run_main(plan(folder, "freeze", ["EDEN_TEST_COLD=1"]), out)
    p = [] if code == 2 else [f"first batch: exit {code}, expected 2"]
    left = [a for a in asides(root) if ".cold-aside-" in a]
    if len(left) != 2:
        p.append(f"expected both caches still aside while the app is frozen, found {left}")
    state = state_of(out)
    if "cold_pending" not in state:
        p.append("no cold_pending in the state file after the freeze")
    summary = (batches(out)[0] / "summary.md").read_text()
    if "NOT BACK on the console" not in summary:
        p.append("summary.md does not say the caches are not back")
    # The owner closes the frozen app; the next batch is a warm one.
    fake.app_running = False
    SCENARIO["ending"] = "script_end"
    code, text = run_main(plan(folder, "warm", []), out, extra=("--clear-stop",))
    if code != 0:
        p.append(f"second batch: exit {code}: {text[-800:]}")
    if [a for a in asides(root) if ".cold-aside-" in a]:
        p.append(f"start-up check did not put back: {asides(root)}")
    if any(before[k] != hashes(root).get(k) for k in before):
        p.append("the old caches are not back byte for byte")
    if "cold_pending" in state_of(out):
        p.append("cold_pending still in the state file")
    second = batches(out)[-1]
    if not (second / "cold-recovery.json").exists():
        p.append("no cold-recovery.json in the second batch folder")
    elif json.loads((second / "cold-recovery.json").read_text())["status"] != "back":
        p.append("cold-recovery.json does not say back")
    if "start-up check, before the first test: all back and checked" not in (second / "summary.md").read_text():
        p.append("the second summary.md does not name the start-up check")
    p += nothing_deleted(before, fake)
    p += private_values(out)
    return p


@case("5 leftover .cold-aside- folder with no note on this computer (state file lost)")
def _(root, out, folder):
    fake = new_fake(root, radv=False)
    put_file(root, f"{RADV}.cold-aside-20261101-000000/00/old", b"the owner's driver cache " * 30)
    put_file(root, f"{RADV}/ff/new", b"a cache built since " * 5)
    before = hashes(root)
    code, text = run_main(plan(folder, "warm", []), out)
    p = [] if code == 0 else [f"exit {code}: {text[-600:]}"]
    now = hashes(root)
    if now.get(f"{RADV}/00/old") != before[f"{RADV}.cold-aside-20261101-000000/00/old"]:
        p.append("the leftover is not back in place")
    built = [a for a in asides(root) if ".cold-built-" in a]
    if len(built) != 1 or now.get(f"{built[0]}/ff/new") != before[f"{RADV}/ff/new"]:
        p.append(f"what was in the live place is not kept as a built set: {built}")
    if [a for a in asides(root) if ".cold-aside-" in a]:
        p.append("a .cold-aside- folder is left")
    if fake.overwrites or set(before.values()) - set(now.values()):
        p.append("something was lost")
    return p


@case("6 the console already has no store: say so, move nothing")
def _(root, out, folder):
    fake = new_fake(root, shader=False, radv=False)
    code, text = run_main(plan(folder, "empty", ["EDEN_TEST_COLD=1"]), out)
    p = [] if code == 0 else [f"exit {code}: {text[-600:]}"]
    if fake.renamed:
        p.append(f"renamed: {fake.renamed}")
    run = next(batches(out)[0].glob("run*"))
    if "already has no shader store and no driver cache" not in (run / cold_caches.LOG_NAME).read_text():
        p.append("cold.log does not say the console was already cold")
    if json.loads((run / cold_caches.NOTE_NAME).read_text())["status"] != "already_cold":
        p.append("note status is not already_cold")
    return p


@case("7 radv-shader-cache in the app folder refuses the cold start, nothing moved")
def _(root, out, folder):
    fake = new_fake(root)
    put_file(root, f"{APP_FOLDER}/radv-shader-cache", b"x" * 10)
    before = hashes(root)
    code, text = run_main(plan(folder, "trap", ["EDEN_TEST_COLD=1"]), out)
    p = [] if code == 2 else [f"exit {code}, expected 2"]
    if fake.renamed or hashes(root) != before or SCENARIO.get("started"):
        p.append("something moved or the test started")
    return p


@case("8 a rename fails half way: what moved goes back, the start is refused")
def _(root, out, folder):
    fake = new_fake(root)
    fake.fail_rename_at = 2  # the driver cache's rename
    before = hashes(root)
    code, text = run_main(plan(folder, "half", ["EDEN_TEST_COLD=1"]), out)
    p = [] if code == 2 else [f"exit {code}, expected 2"]
    if hashes(root) != before:
        p.append(f"the console is not as before: {asides(root)}")
    if SCENARIO.get("started"):
        p.append("the test started")
    if "cold_pending" in state_of(out):
        p.append("cold_pending left")
    return p


@case("9 two .cold-aside- folders for one cache: refuse, move nothing")
def _(root, out, folder):
    fake = new_fake(root, radv=False)
    put_file(root, f"{RADV}.cold-aside-20261101-000000/a", b"one")
    put_file(root, f"{RADV}.cold-aside-20261102-000000/a", b"two")
    before = hashes(root)
    code, text = run_main(plan(folder, "warm", []), out)
    p = [] if code == 2 else [f"exit {code}, expected 2"]
    if fake.renamed or hashes(root) != before:
        p.append("something moved")
    return p


@case("10 --cold on the command line; a bad EDEN_TEST_COLD value is a plan error")
def _(root, out, folder):
    fake = new_fake(root)
    before = hashes(root)
    code, text = run_main(plan(folder, "flag", []), out, extra=("--cold",))
    p = [] if code == 0 else [f"exit {code}: {text[-600:]}"]
    if len(fake.renamed) != 6:
        p.append(f"--cold did not make the start cold: {fake.renamed}")
    if any(before[k] != hashes(root).get(k) for k in before):
        p.append("not back")
    code, text = run_main(plan(folder, "bad", ["EDEN_TEST_COLD=yes"]), out)
    if code == 0 or "EDEN_TEST_COLD must be there once" not in str(code):
        p.append(f"EDEN_TEST_COLD=yes was not refused as a plan error: {code}")
    sys.argv = ["runner", str(plan(folder, "show", ["EDEN_TEST_COLD=1"])), "--out-root", str(out)]
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        tool.main()
    if "COLD START" not in printed.getvalue() or "EDEN_TEST_COLD" in printed.getvalue():
        p.append("the plan print does not show the cold start, or shows the line in env.txt")
    return p


@case("11 --restore-env --go puts back what a cut-off run left")
def _(root, out, folder):
    fake = new_fake(root)
    before = hashes(root)
    SCENARIO["ending"] = "freeze"
    run_main(plan(folder, "freeze", ["EDEN_TEST_COLD=1"]), out)
    fake.app_running = False
    sys.argv = ["runner", "--restore-env", "--go", "--out-root", str(out)]
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        try:
            code = tool.main()
        except SystemExit as stop:
            code = stop.code
    p = [] if code == 0 else [f"exit {code}: {printed.getvalue()[-600:]}"]
    if [a for a in asides(root) if ".cold-aside-" in a] or any(before[k] != hashes(root).get(k) for k in before):
        p.append(f"not back: {asides(root)}")
    if "cold_pending" in state_of(out):
        p.append("cold_pending left")
    p += nothing_deleted(before, fake)
    return p


@case("13 Ctrl-C in the middle of setting aside (one cache moved, the other not yet)")
def _(root, out, folder):
    fake = new_fake(root)
    before = hashes(root)
    fake.ctrl_c_at = 2  # the shader store is aside, the driver cache's rename is next
    code, text = run_main(plan(folder, "cut", ["EDEN_TEST_COLD=1"]), out)
    p = [] if code == 130 else [f"exit {code}, expected 130"]
    if hashes(root) != before:
        p.append(f"the console is not as before: {asides(root)}")
    if SCENARIO.get("started"):
        p.append("the test started")
    if "cold_pending" in state_of(out):
        p.append("cold_pending left in the state file")
    run = next(batches(out)[0].glob("run*"))
    states = [i["state"] for i in json.loads((run / cold_caches.NOTE_NAME).read_text())["items"]]
    if states != ["back", "not_moved"]:
        p.append(f"note item states {states}, expected back, not_moved")
    return p


@case("14 a note cut off before its first rename: closed, not a false NOT BACK")
def _(root, out, folder):
    fake = new_fake(root)
    stale = {"what": "cold start", "title": TITLE, "status": "moving",
             "items": [{"what": "shader store", "path": SHADER, "aside": SHADER + ".cold-aside-20261117-000000",
                        "state": "planned", "before": None}]}
    (out / "auto-run-state.json").write_text(json.dumps(
        {"cold_pending": {"batch": "auto-old", "run": "run1-old", "host": HOST, "note": stale}}))
    code, text = run_main(plan(folder, "warm", []), out)
    p = [] if code == 0 else [f"exit {code}: {text[-600:]}"]
    if "cold_pending" in state_of(out):
        p.append("cold_pending stays for good")
    if "NOT BACK" in (batches(out)[0] / "summary.md").read_text():
        p.append("summary.md says NOT BACK for a note that moved nothing")
    if fake.renamed:
        p.append(f"renamed: {fake.renamed}")
    return p


@case("12 the rename allow-list: only the three cold-start renames, in the same folder")
def _(root, out, folder):
    ok = [(RADV, RADV + ".cold-aside-20261118-101500"), (RADV + ".cold-aside-20261118-101500", RADV),
          (RADV, RADV + ".cold-built-20261118-101500-2"), (SHADER, SHADER + ".cold-aside-20261118-101500")]
    no = [(RADV + ".cold-built-20261118-101500", RADV), (RADV, f"{DATA}/cache/other"),
          (RADV, f"{DATA}/user/cache/shader/radv.cold-aside-20261118-101500"),
          (f"{DATA}/user/save", f"{DATA}/user/save.cold-aside-20261118-101500"),
          (SHADER + ".cold-aside-20261118-101500", RADV), (RADV, RADV + ".cold-aside-x"),
          (f"{APP_FOLDER}/env.txt", f"{APP_FOLDER}/env.txt.cold-aside-20261118-101500")]
    aside = SHADER + ".cold-aside-20261118-101500"
    other = f"{DATA}/user/cache/shader/0100000000000000.cold-aside-20261118-101500"
    ok += [(f"{aside}/{RECIPE_NAME}", RECIPE), (RECIPE, f"{aside}/{RECIPE_NAME}"),
           (f"{aside}/shader_set_index.txt", INDEX), (INDEX, f"{aside}/shader_set_index.txt")]
    no += [(f"{aside}/vulkan.bin", f"{SHADER}/vulkan.bin"), (f"{aside}/up_v1_2", f"{SHADER}/up_v1_2"),
           (f"{SHADER}.cold-built-20261118-101500/{RECIPE_NAME}", RECIPE),
           (f"{aside}/a.nx2recipe", f"{SHADER}/b.nx2recipe"), (f"{aside}/up_v1_2/{RECIPE_NAME}", RECIPE),
           (f"{other}/{RECIPE_NAME}", RECIPE), (f"{RADV}.cold-aside-20261118-101500/shader_set_index.txt",
                                                 f"{RADV}/shader_set_index.txt"),
           (f"{aside}/.nx2recipe", f"{SHADER}/.nx2recipe"), (RECIPE, f"{SHADER}/up_v1_2/{RECIPE_NAME}"),
           (RECIPE, RECIPE + ".cold-aside-20261118-101500")]
    p = [f"refused: {pair}" for pair in ok if not cold_caches.allowed_pair(*pair, DATA)]
    p += [f"allowed: {pair}" for pair in no if cold_caches.allowed_pair(*pair, DATA)]
    if not cold_caches.allowed_folder(SHADER, DATA):
        p.append("allowed_folder refuses the live title folder")
    for path in (RADV, f"{DATA}/cache", f"{SHADER}/up_v1_2", aside, f"{DATA}/user/save", f"{DATA}/user/cache/shader"):
        if cold_caches.allowed_folder(path, DATA):
            p.append(f"allowed_folder lets a cold start make {path}")
    for path in (RADV, SHADER, RADV + "/x", RECIPE):
        if tool.writable(path):
            p.append(f"writable() now lets put/remove reach {path}")
    return p


def set_files_in(root, folder):
    """Shader-set files anywhere under a folder of the stand-in."""
    base = Path(root) / folder.lstrip("/")
    return sorted(str(p.relative_to(base)) for p in base.rglob("*") if p.is_file() and cold_caches.is_set_file(p.name))


@case("15 the shader set stays in place by default; the put-back puts all of it back")
def _(root, out, folder):
    fake = new_fake(root, recipe=True)
    before = hashes(root)
    code, text = run_main(plan(folder, "keep", ["EDEN_TEST_DISCARD_SAVE=1", "EDEN_TEST_COLD=1"]), out)
    p = [] if code == 0 else [f"exit {code}: {text[-600:]}"]
    at = SCENARIO.get("at_start", [{}])[0]
    if at != {RECIPE: before[RECIPE], INDEX: before[INDEX]}:
        p.append(f"at the start the live title folder held {sorted(at)}, not just the recipe and its index "
                 "with their own bytes")
    if any(before[k] != hashes(root).get(k) for k in before):
        p.append("not everything is back byte for byte")
    built = [a for a in asides(root) if ".cold-built-" in a]
    store_built = [b for b in built if b.startswith(SHADER + ".cold-built-")]
    if len(built) != 2 or len(store_built) != 1:
        p.append(f"expected one built store and one built driver cache, found {built}")
    elif set_files_in(root, store_built[0]):
        p.append(f"the built store holds shader-set files: {set_files_in(root, store_built[0])}")
    if [a for a in asides(root) if ".cold-aside-" in a]:
        p.append(f"a .cold-aside- folder is left: {asides(root)}")
    if fake.made != [SHADER]:
        p.append(f"folders made: {fake.made}, expected only the live title folder")
    if len(fake.renamed) != 10:  # 2 aside, 2 set files in, 2 set files back, 2 built, 2 back
        p.append(f"expected 10 renames, got {len(fake.renamed)}: {fake.renamed}")
    run = next(batches(out)[0].glob("run*"))
    cold = json.loads((run / "result.json").read_text()).get("cold", {})
    if cold.get("status") != "back" or not cold.get("back"):
        p.append(f"result cold = {cold}")
    if (cold.get("proof") or {}).get("cold") is not True:
        p.append(f"with only the set in place the boot log should read cold: {cold.get('proof')}")
    if cold.get("set_kept") != [RECIPE_NAME, "shader_set_index.txt"]:
        p.append(f"result cold.set_kept = {cold.get('set_kept')}")
    log = (run / cold_caches.LOG_NAME).read_text()
    for needle in ("-> 0400486024dec000.cold-aside-", "-> radv.cold-aside-",
                   f"shader set kept in place in {SHADER}: {RECIPE_NAME} (",
                   "nothing of the old caches is in place now but the shader set",
                   f"shader set {RECIPE_NAME}, shader_set_index.txt renamed back into 0400486024dec000.cold-aside-",
                   f"shader store back at {SHADER}, checked by a listing: the same"):
        if needle not in log:
            p.append(f"cold.log lacks {needle!r}")
    note = json.loads((run / cold_caches.NOTE_NAME).read_text())
    kept = [k["state"] for i in note["items"] for k in i.get("keep", [])]
    if note["status"] != "back" or kept != ["back", "back"] or note.get("shader_set") != "kept in place":
        p.append(f"note {note['status']}, kept files {kept}, shader_set {note.get('shader_set')}")
    if "shader set kept in place: " + RECIPE_NAME not in (batches(out)[0] / "summary.md").read_text():
        p.append("summary.md does not say the shader set stayed in place")
    return p


@case("16 EDEN_TEST_COLD_SET=1 moves the set aside with the store (and never reaches env.txt)")
def _(root, out, folder):
    fake = new_fake(root, recipe=True)
    before = hashes(root)
    code, text = run_main(plan(folder, "withset", ["EDEN_TEST_COLD=1", "EDEN_TEST_COLD_SET=1"]), out)
    p = [] if code == 0 else [f"exit {code}: {text[-600:]}"]
    if SCENARIO.get("at_start", [None])[0] != {}:
        p.append(f"the live title folder was there at the start: {SCENARIO.get('at_start')}")
    if fake.made or len(fake.renamed) != 6:
        p.append(f"expected the old way (6 renames, no folder made): {fake.renamed}, made {fake.made}")
    if any(before[k] != hashes(root).get(k) for k in before):
        p.append("not everything is back byte for byte")
    run = next(batches(out)[0].glob("run*"))
    if cold_caches.SET_LINE in (run / "env.txt").read_text():
        p.append("EDEN_TEST_COLD_SET reached the run's env.txt")
    if cold_caches.SET_LINE in (root / APP_FOLDER.lstrip("/") / "env.txt").read_text():
        p.append("EDEN_TEST_COLD_SET is in the console's env.txt")
    cold = json.loads((run / "result.json").read_text()).get("cold", {})
    if cold.get("set_kept") or cold.get("status") != "back":
        p.append(f"result cold = {cold}")
    note = json.loads((run / cold_caches.NOTE_NAME).read_text())
    if note.get("shader_set") != "set aside with the store":
        p.append(f"note shader_set = {note.get('shader_set')}")
    code, text = run_main(plan(folder, "lone", ["EDEN_TEST_COLD_SET=1"]), out)
    if "needs a cold start" not in str(code):
        p.append(f"EDEN_TEST_COLD_SET=1 without a cold start was not refused: {code}")
    code, text = run_main(plan(folder, "badset", ["EDEN_TEST_COLD=1", "EDEN_TEST_COLD_SET=2"]), out)
    if "EDEN_TEST_COLD_SET must be there once" not in str(code):
        p.append(f"EDEN_TEST_COLD_SET=2 was not a plan error: {code}")
    renamed = len(fake.renamed)
    code, text = run_main(plan(folder, "flagset", ["EDEN_TEST_COLD_SET=1"]), out, extra=("--cold",))
    if code != 0 or len(fake.renamed) - renamed != 6 or fake.made:
        p.append(f"--cold with EDEN_TEST_COLD_SET=1: exit {code}, {len(fake.renamed) - renamed} renames")
    for env, want in ((["EDEN_TEST_COLD=1"], "stays in place"), (["EDEN_TEST_COLD=1", "EDEN_TEST_COLD_SET=1"],
                                                                 "goes aside too")):
        sys.argv = ["runner", str(plan(folder, "show", env)), "--out-root", str(out)]
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            tool.main()
        if want not in printed.getvalue() or cold_caches.SET_LINE + "=" in printed.getvalue().split("COLD START")[0]:
            p.append(f"the plan print for {env} does not say the set {want}, or shows the line in env.txt")
    return p


@case("17 the folder make or a set-file move fails: everything back, the start refused")
def _(root, out, folder):
    fake = new_fake(root, recipe=True)
    before = hashes(root)
    fake.fail_mkdir = True  # the folder is made, the answer is lost
    code, text = run_main(plan(folder, "mkfail", ["EDEN_TEST_COLD=1"]), out)
    p = [] if code == 2 else [f"folder make: exit {code}, expected 2"]
    if hashes(root) != before or SCENARIO.get("started"):
        p.append(f"folder make: the console is not as before, or the test started: {asides(root)}")
    left = [a for a in asides(root) if ".cold-built-" in a]
    if len(left) != 1 or any((root / left[0].lstrip("/")).iterdir()):
        p.append(f"folder make: the made folder should be parked, empty: {left}")
    fake.fail_rename_at = len(fake.renamed) + 4  # aside, aside, the recipe in, then the index fails
    code, text = run_main(plan(folder, "mvfail", ["EDEN_TEST_COLD=1"]), out)
    if code != 2:
        p.append(f"set move: exit {code}, expected 2")
    if hashes(root) != before or SCENARIO.get("started"):
        p.append(f"set move: the console is not as before, or the test started: {asides(root)}")
    if [a for a in asides(root) if ".cold-aside-" in a] or "cold_pending" in state_of(out):
        p.append("set move: something left aside, or cold_pending left")
    for built in (a for a in asides(root) if ".cold-built-" in a):
        if set_files_in(root, built):
            p.append(f"set move: shader-set files left in {built}")
    return p


@case("18 Ctrl-C while the set's files are renamed into the new folder")
def _(root, out, folder):
    fake = new_fake(root, recipe=True)
    before = hashes(root)
    fake.ctrl_c_at = 4  # both caches aside, the recipe in place, Ctrl-C right before the index
    code, text = run_main(plan(folder, "cutset", ["EDEN_TEST_COLD=1"]), out)
    p = [] if code == 130 else [f"exit {code}, expected 130"]
    if hashes(root) != before or SCENARIO.get("started"):
        p.append(f"the console is not as before, or the test started: {asides(root)}")
    if "cold_pending" in state_of(out):
        p.append("cold_pending left in the state file")
    run = next(batches(out)[0].glob("run*"))
    note = json.loads((run / cold_caches.NOTE_NAME).read_text())
    kept = [k["state"] for i in note["items"] for k in i.get("keep", [])]
    if kept != ["back", "not_moved"] or note["status"] != "back":
        p.append(f"note {note['status']}, kept files {kept}, expected back, not_moved")
    return p


@case("19 frozen app with the set kept: aside until the next --go, then all back")
def _(root, out, folder):
    fake = new_fake(root, recipe=True)
    before = hashes(root)
    SCENARIO["ending"] = "freeze"
    code, text = run_main(plan(folder, "freezeset", ["EDEN_TEST_COLD=1"]), out)
    p = [] if code == 2 else [f"first batch: exit {code}, expected 2"]
    if len([a for a in asides(root) if ".cold-aside-" in a]) != 2:
        p.append(f"expected both caches aside while the app is frozen: {asides(root)}")
    if hashes(root).get(RECIPE) != before[RECIPE]:
        p.append("the recipe is not in the live folder while the caches are aside")
    fake.app_running = False
    SCENARIO["ending"] = "script_end"
    code, text = run_main(plan(folder, "warm", []), out, extra=("--clear-stop",))
    if code != 0:
        p.append(f"second batch: exit {code}: {text[-800:]}")
    if any(before[k] != hashes(root).get(k) for k in before) or [a for a in asides(root) if ".cold-aside-" in a]:
        p.append(f"not back byte for byte after the start-up check: {asides(root)}")
    for built in (a for a in asides(root) if ".cold-built-" in a):
        if set_files_in(root, built):
            p.append(f"shader-set files left in {built}")
    if "cold_pending" in state_of(out):
        p.append("cold_pending still in the state file")
    return p


@case("20 a leftover with the set in the live folder and no note on this computer")
def _(root, out, folder):
    fake = new_fake(root, shader=False)
    old = f"{SHADER}.cold-aside-20261101-000000"
    put_file(root, f"{old}/vulkan.bin", b"the owner's store " * 40)
    put_file(root, f"{old}/up_v1_2/prep_5093ab9e.bin", b"prepared " * 50)
    put_file(root, RECIPE, b"NX2RCP01 the owner's recipe")
    put_file(root, INDEX, b"romfs index\n")
    put_file(root, f"{SHADER}/up_v1_2/prep_built.bin", b"built by the cut-off start " * 5)
    before = hashes(root)
    code, text = run_main(plan(folder, "warm", []), out)
    p = [] if code == 0 else [f"exit {code}: {text[-600:]}"]
    now = hashes(root)
    for path, was in ((f"{SHADER}/vulkan.bin", f"{old}/vulkan.bin"), (RECIPE, RECIPE), (INDEX, INDEX),
                      (f"{SHADER}/up_v1_2/prep_5093ab9e.bin", f"{old}/up_v1_2/prep_5093ab9e.bin")):
        if now.get(path) != before[was]:
            p.append(f"{path} is not the owner's file")
    built = [a for a in asides(root) if a.startswith(SHADER + ".cold-built-")]
    if len(built) != 1 or now.get(f"{built[0]}/up_v1_2/prep_built.bin") != before[f"{SHADER}/up_v1_2/prep_built.bin"]:
        p.append(f"what the cut-off start built is not kept as a built set: {built}")
    elif set_files_in(root, built[0]):
        p.append(f"the built set holds shader-set files: {set_files_in(root, built[0])}")
    if [a for a in asides(root) if ".cold-aside-" in a]:
        p.append("a .cold-aside- folder is left")
    if fake.overwrites or set(before.values()) - set(now.values()):
        p.append("something was lost")
    return p


@case("21 a recipe in both the live and the set-aside folder: never renamed over, the old one goes back")
def _(root, out, folder):
    fake = new_fake(root, shader=False)
    old = f"{SHADER}.cold-aside-20261101-000000"
    put_file(root, f"{old}/vulkan.bin", b"the owner's store " * 40)
    put_file(root, f"{old}/{RECIPE_NAME}", b"NX2RCP01 the owner's recipe")
    put_file(root, RECIPE, b"NX2RCP01 another recipe someone put in")
    before = hashes(root)
    caches = cold_caches.ColdCaches(fake, DATA, [APP_FOLDER], say=lambda t: None, app_open=lambda: False,
                                    log_sizes=lambda: (1, 1, 1), errors=(tool.NoAnswer,), quiet=0)
    p = []
    try:
        caches.move_file(RECIPE, f"{old}/{RECIPE_NAME}")
        p.append("move_file renamed onto a file that is there")
    except cold_caches.MoveFailed as error:
        if "already there" not in str(error):
            p.append(f"move_file refused for another reason: {error}")
    if fake.renamed:
        p.append(f"renamed: {fake.renamed}")
    code, text = run_main(plan(folder, "warm", []), out)
    if code != 0:
        p.append(f"exit {code}: {text[-600:]}")
    now = hashes(root)
    if now.get(RECIPE) != before[f"{old}/{RECIPE_NAME}"]:
        p.append("the live recipe is not the owner's one from the set-aside folder")
    built = [a for a in asides(root) if a.startswith(SHADER + ".cold-built-")]
    if len(built) != 1 or now.get(f"{built[0]}/{RECIPE_NAME}") != before[RECIPE]:
        p.append(f"the other recipe is not kept with the built set: {built}")
    if fake.overwrites or set(before.values()) - set(now.values()):
        p.append("something was lost or renamed over")
    return p


# ---------------------------------------------------------------- the caches line (every start, warm or cold)

def caches_of(out, batch=0):
    """(result.json "caches" of the first run, its batch.log, its summary.md) of a batch."""
    folder = batches(out)[batch]
    run = next(folder.glob("run*"))
    return (json.loads((run / "result.json").read_text()).get("caches") or {}, (folder / "batch.log").read_text(),
            (folder / "summary.md").read_text(), run)


@case("22 a warm start: the caches line names the store it reused, in batch.log, result.json and summary.md")
def _(root, out, folder):
    fake = new_fake(root)
    before = hashes(root)
    code, text = run_main(plan(folder, "warm", ["EDEN_TEST_DISCARD_SAVE=1"]), out)
    p = [] if code == 0 else [f"exit {code}: {text[-600:]}"]
    if fake.renamed or fake.made:
        p.append(f"a start that is not cold moved something: {fake.renamed} {fake.made}")
    if any(before[k] != hashes(root).get(k) for k in before):
        p.append("a start that is not cold changed a cache file")
    caches, log, summary, run = caches_of(out)
    want = {"store": STORE, "store_state": "reused", "store_pipelines": 78735, "store_build": "84805134",
            "pipelines_known": 78735, "left_to_prepare": 0, "records_read": 7816, "own_records": 7816,
            "total_pipeline_count": 4204, "driver_pipeline_cache_loaded": True, "reads_as": "warm",
            "source": "eden_log.txt", "why_missing": "", "asked": "not cold"}
    for key, value in want.items():
        if caches.get(key) != value:
            p.append(f"result.json caches.{key} = {caches.get(key)!r}, expected {value!r}")
    line = caches.get("line", "")
    for needle in ("Caches: none set aside by the runner", f"store {STORE} reused (78735 pipelines), build 84805134",
                   "78735 pipelines known, 0 left to prepare", "7816 records read (7816 own)",
                   "Total Pipeline Count 4204", "driver pipeline cache loaded", "Reads as warm"):
        if needle not in line:
            p.append(f"the caches line lacks {needle!r}: {line}")
    if line not in log:
        p.append("the caches line is not in batch.log")
    if f"- warm-1: nothing set aside; boot log: store {STORE} reused (78735 pipelines)" not in summary:
        p.append("summary.md does not list the store the warm start reused")
    if (run / cold_caches.LOG_NAME).exists():
        p.append("a start that is not cold wrote a cold.log")
    if any("caches:" in note for note in json.loads((run / "result.json").read_text())["notes"]):
        p.append("a warm start that read warm got a caches note")
    return p


@case("23 a cold start: the caches line lists both caches moved aside, the set kept, the put-back, and reads cold")
def _(root, out, folder):
    new_fake(root, recipe=True)
    code, text = run_main(plan(folder, "coldline", ["EDEN_TEST_COLD=1"]), out)
    p = [] if code == 0 else [f"exit {code}: {text[-600:]}"]
    caches, log, summary, run = caches_of(out)
    line = caches.get("line", "")
    for needle in (f"Caches: set aside for this start: shader store {SHADER} (", f"driver cache {RADV} (",
                   f"shader set kept in place: {RECIPE_NAME}, shader_set_index.txt",
                   "put back: yes, checked by a listing", f"store {STORE} new (0 pipelines)",
                   "Total Pipeline Count 0", "no driver pipeline cache loaded", "Reads as cold"):
        if needle not in line:
            p.append(f"the caches line lacks {needle!r}: {line}")
    if caches.get("reads_as") != "cold" or caches.get("asked") != "cold" or caches.get("store_state") != "new":
        p.append(f"result.json caches: {caches}")
    cold_log = (run / cold_caches.LOG_NAME).read_text()
    if line not in cold_log or not cold_log.rstrip().endswith("Reads as cold"):
        p.append("the caches line is not the last line of cold.log")
    if line not in log:
        p.append("the caches line is not in batch.log")
    if "- coldline-1: set aside: shader store and driver cache, back; boot log:" not in summary:
        p.append("summary.md does not list what the cold start set aside")
    result = json.loads((run / "result.json").read_text())
    if (result["cold"].get("proof") or {}).get("cold") is not True:
        p.append(f"the cold proof changed: {result['cold'].get('proof')}")
    if any("caches:" in note for note in result["notes"]):
        p.append(f"a cold start that read cold got a caches note: {result['notes']}")
    return p


@case("24 a boot log that does not read as asked gets a note, and the cold verdict is left as it was")
def _(root, out, folder):
    new_fake(root)
    p = []
    SCENARIO["boot"] = "half"  # a new store, but a driver pipeline cache and pipelines from an earlier start
    code, text = run_main(plan(folder, "halfcold", ["EDEN_TEST_COLD=1"]), out)
    if code != 0:
        p.append(f"cold batch: exit {code}: {text[-600:]}")
    caches, log, summary, run = caches_of(out)
    result = json.loads((run / "result.json").read_text())
    if caches.get("reads_as") != "half" or "Reads as half" not in caches.get("line", ""):
        p.append(f"a new store with a driver pipeline cache should read as half: {caches}")
    if not any(note.startswith("caches: asked for a cold start, but the boot log reads as half") for note in result["notes"]):
        p.append(f"no note for a cold start that reads as half: {result['notes']}")
    if (result["cold"].get("proof") or {}).get("cold") is not False or result["cold"].get("status") != "back":
        p.append(f"the cold start's own proof and status changed: {result['cold']}")
    code, text = run_main(plan(folder, "halfwarm", []), out)
    if code != 0:
        p.append(f"second batch: exit {code}: {text[-600:]}")
    caches, log, summary, run = caches_of(out, batch=-1)
    notes = json.loads((run / "result.json").read_text())["notes"]
    if not any(note.startswith("caches: not asked to be a cold start, but the boot log reads as half") for note in notes):
        p.append(f"no note for a start that is not cold and reads as half: {notes}")
    return p


@case("25 no store line in the log: every value null, with the reason, and the start still closes")
def _(root, out, folder):
    new_fake(root)
    SCENARIO["boot"] = "none"
    code, text = run_main(plan(folder, "noline", []), out)
    p = [] if code == 0 else [f"exit {code}: {text[-600:]}"]
    caches, log, summary, run = caches_of(out)
    for key in ("store", "store_state", "store_pipelines", "total_pipeline_count", "reads_as"):
        if caches.get(key, "missing") is not None:
            p.append(f"caches.{key} should be null: {caches.get(key, 'missing')!r}")
    if "no shader store line" not in caches.get("why_missing", "") or "no store line" not in caches.get("line", ""):
        p.append(f"no reason given: {caches}")
    missing = cold_caches.boot_caches(folder / "no-such-run-folder")
    if missing["why_missing"] != "no eden_log.txt in the run folder" or missing["store"] is not None:
        p.append(f"a run folder without a log: {missing}")
    # A crashed start: the plain log is the restarted launcher's, the crash copy holds the test's own boot.
    crashed = folder / "crashed-run"
    crashed.mkdir()
    (crashed / "eden_log.txt").write_text("[   1.000000] Frontend <Info> the launcher after a crash\n")
    (crashed / "crash-20261119-083548-eden_log.txt").write_text(boot_log(4204, "reused", True))
    found = cold_caches.boot_caches(crashed)
    if found["source"] != "crash-20261119-083548-eden_log.txt" or found["reads_as"] != "warm":
        p.append(f"the crash copy of the log was not read: {found}")
    older = cold_caches.STORE_LINE.search("SOURCE_STAMP: id srcabc (files 3) devabc, store prep_1 created (0 pipelines)")
    if not older or older[3] != "created":
        p.append("an older build's 'created' store line is not read")
    return p


@case("26 the guard stops the real Console, OBS client and a child process, and records each try")
def _(root, out, folder):
    p = []
    args = types.SimpleNamespace(host=HOST, web_port=8080, ftp_port=2121, timeout=0.01)
    real = RealConsole(args)
    for what, call in (("a web listing", lambda: real.list("/data")), ("a web read", lambda: real.read("/data/x")),
                       ("the FTP check", real.check_ftp), ("an FTP write", lambda: real.touch(tool.TEST_QUIT)),
                       ("a cold rename", lambda: real.rename_cold(RADV, RADV + ".cold-aside-20261121-000000")),
                       ("/launch", real.launch)):
        before = len(offline_guard.ATTEMPTS)
        try:
            call()
            p.append(f"{what} on the real Console did not fail")
        except tool.NoAnswer:
            pass
        if len(offline_guard.ATTEMPTS) == before:
            p.append(f"{what} on the real Console left no record in the guard")
    for what, call in (("the OBS client", lambda: tool.Obs("127.0.0.1", 4455)),
                       ("a child process", lambda: tool.subprocess.run([sys.executable, "-c", "pass"])),
                       ("a name lookup", lambda: tool.socket.getaddrinfo(HOST, 80))):
        before = len(offline_guard.ATTEMPTS)
        try:
            call()
            p.append(f"{what} did not fail")
        except offline_guard.Blocked:
            pass
        if len(offline_guard.ATTEMPTS) == before:
            p.append(f"{what} left no record in the guard")
    if not any(HOST in attempt for attempt in offline_guard.ATTEMPTS):
        p.append("no recorded attempt names the stand-in console address")
    del offline_guard.ATTEMPTS[:]  # these were made on purpose
    return p


@case("27 printing a plan (no --go) makes no console and tries nothing: the guide's first-run plan, and a cold one")
def _(root, out, folder):
    p = []
    made = []
    tool.Console = lambda args: made.append(args) or FAKE["console"]  # FAKE is empty: making one would also fail
    try:
        first = folder / "launcher-only.json"
        first.write_text('[{"name": "launcher-only", "title": "FFFFFFFFFFFFFFFF", "seconds": 30}]')
        for path, extra, want in ((first, (), "1. launcher-only  (30 s)"),
                                  (plan(folder, "print", ["EDEN_TEST_COLD=1"]), (), "COLD START"),
                                  (plan(folder, "printflag", []), ("--cold",), "COLD START")):
            sys.argv = ["runner", str(path), "--out-root", str(out), *extra]
            printed = io.StringIO()
            with contextlib.redirect_stdout(printed):
                code = tool.main()
            text = printed.getvalue()
            if code != 0 or want not in text or "Nothing was sent to the console. Add --go to run this." not in text:
                p.append(f"{path.name}: exit {code}, printed {text[-300:]!r}")
    finally:
        tool.Console = lambda args: FAKE["console"]
    if made:
        p.append("a plan print made a console object")
    if batches(out):
        p.append(f"a plan print made a batch folder: {batches(out)}")
    return p


@case("28 a fault in the caches reader costs a start nothing: it closes, result.json is written, a note says so")
def _(root, out, folder):
    new_fake(root, recipe=True)
    before = hashes(root)
    reader = cold_caches.boot_caches

    def broken(run_folder):
        raise RuntimeError("fake: the reader fails")
    cold_caches.boot_caches = broken
    try:
        code, text = run_main(plan(folder, "readerfault", ["EDEN_TEST_COLD=1"]), out)
    finally:
        cold_caches.boot_caches = reader
    p = [] if code == 0 else [f"exit {code}: {text[-600:]}"]
    run = next(batches(out)[0].glob("run*"))
    if not (run / "result.json").exists():
        return p + ["no result.json"]
    result = json.loads((run / "result.json").read_text())
    if "caches" in result or not any(note.startswith("caches: the caches line could not be made") for note in result["notes"]):
        p.append(f"no note about the failed reader: {result.get('caches')} {result['notes']}")
    if result["cold"].get("status") != "back" or any(before[k] != hashes(root).get(k) for k in before):
        p.append(f"the cold start's put-back suffered: {result['cold']}")
    if "- readerfault-1:" not in (batches(out)[0] / "summary.md").read_text():
        p.append("summary.md was not written as usual")
    return p


def clean_up():
    shutil.rmtree(SCRATCH, ignore_errors=True)
    offline_guard.remove()


class ColdStart(unittest.TestCase):
    """One unittest test per case above. A case passes when it returns no problem."""
    maxDiff = None


def _as_test(name, run):
    def test(self):
        problems = run()
        self.assertEqual(problems, [], f"{name}:\n" + "\n".join(problems))
    test.__doc__ = name
    return test


for _number, (_case_name, _run) in enumerate(RUN, 1):
    _slug = "".join(c if c.isalnum() else "_" for c in _case_name.split(":")[0].split("(")[0].strip().lower())[:60]
    setattr(ColdStart, f"test_{_number:02d}_{_slug}", _as_test(_case_name, _run))


def setUpModule():
    # The runner keeps each batch.log open until its process ends; a test process runs many batches.
    warnings.simplefilter("ignore", ResourceWarning)


def tearDownModule():
    clean_up()


def main():
    global VERBOSE
    VERBOSE = True
    for _, run in RUN:
        run()
    failed = [name for name, problems in RESULTS if problems]
    print(f"\n{len(RESULTS) - len(failed)} of {len(RESULTS)} cases pass")
    clean_up()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
