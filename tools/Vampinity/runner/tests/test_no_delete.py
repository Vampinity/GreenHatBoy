#!/usr/bin/env python3
"""Offline tests for two changes asked for on PR 38 (GrowingBlackBeans, 23 Nov 2026):

  1. Nothing on the console is deleted by walking a listing. websrv's fs?fmt=json listing (src/fs.c) stats every
     entry THROUGH links, so a link to a folder lists as "d". The whole-cache restore now renames a live folder aside
     to <folder>.old-<time> with one rename, and the save restore renames an extra slot aside the same way. These
     cases plant links where the old code would have walked into them and check that what the links point at is
     untouched, that no DELE or RMD is sent, and that the links themselves are kept as links.
  2. A launcher option: --launcher prosperomgr (ProsperoMgr's POST /api/titles/launch). Tested against a stand-in for
     ProsperoMgr's answers as its public source gives them (launchers.py says where each one comes from).

Run: python3 tests/test_no_delete.py   (or python3 -m unittest discover tests)
It uses test_cold_start.py's stand-in console (a local folder that lists like websrv, links followed) and its
offline guard: no socket connects and no program starts. Standard library only.
"""
import contextlib
import hashlib
import io
import json
import os
import runpy
import shutil
import sys
import tempfile
import traceback
import types
import unittest
import urllib.error
import urllib.parse
import urllib.request
import warnings
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_cold_start as H  # noqa: E402  the stand-in console, the stubs, the shared checks (installs the guard)
import offline_guard  # noqa: E402

tool, warm_cache, launchers = H.tool, H.warm_cache, H.tool.launchers
DATA, RADV = H.DATA, H.RADV
USER_CACHE, DRIVER_CACHE = H.USER_CACHE, H.DRIVER_CACHE
SCRATCH = Path(tempfile.mkdtemp(prefix="no-delete-desk-"))
SAVE_SCRIPT = H.HERE / ("restore" + "-save.py")
PRECIOUS = f"{DATA}/user/precious"  # a folder outside both caches that a link points at
RESULTS, RUN = [], []
VERBOSE = False


def case(name):
    """As test_cold_start.case, in this file's own scratch folder: the shared checks run after every case
    (nothing the console had is lost, no delete sent, no private value written, nothing left this process)."""
    def wrap(function):
        def run():
            H.SCENARIO.clear()
            H.FAKE.clear()
            folder = SCRATCH / name.split(" ")[0]
            folder.mkdir()
            root, out = folder / "console", folder / "out"
            root.mkdir()
            out.mkdir()
            offline_guard.install()
            del offline_guard.ATTEMPTS[:]
            try:
                problems = function(root, out, folder) or []
                if "console" in H.FAKE:
                    problems += [p for p in H.nothing_deleted(H.FAKE["before"], H.FAKE["console"]) if p not in problems]
                problems += [p for p in H.private_values(out) if p not in problems]
            except Exception:  # noqa: BLE001
                problems = ["the case itself failed: " + traceback.format_exc()]
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


def plant_precious(root):
    """The folder a link will point at, with two files, one in a subfolder. {console path: sha256}."""
    H.put_file(root, f"{PRECIOUS}/a.bin", os.urandom(700))
    H.put_file(root, f"{PRECIOUS}/sub/b.bin", os.urandom(300))
    return {p: d for p, d in H.hashes(root).items() if p.startswith(PRECIOUS + "/")}


def precious_intact(root, before):
    now = {p: d for p, d in H.hashes(root).items() if p.startswith(PRECIOUS + "/")}
    return [] if now == before else [f"WHAT THE LINK POINTS AT CHANGED: {len(now)} files now, {len(before)} before "
                                     f"(missing {sorted(set(before) - set(now))[:3]})"]


def old_folders(root):
    return sorted(c for parent in (root / DATA.lstrip("/"), root / f"{DATA}/user".lstrip("/"))
                  for c in parent.iterdir() if warm_cache.OLD in c.name)


def quiet_cache(fake):
    return warm_cache.WarmCache(fake, DATA, say=lambda text: None, app_open=lambda: False,
                                log_sizes=lambda: [10, 1, 1], errors=(tool.NoAnswer,), quiet=0)


# ---------------------------------------------------------------- 1. links in the caches

@case("N1 a link to a folder and a link to a file inside a live test cache: renamed aside whole, never walked; "
      "what they point at stays byte for byte")
def _(root, out, folder):
    fake = H.new_fake(root)
    copy, code, text = H.make_warm_copy(folder, out)
    p = [] if code == 0 else [f"--make-warm-copy exit {code}: {text[-300:]}"]
    precious = plant_precious(root)
    H.FAKE["before"] = H.hashes(root)
    seen = {}

    def plant(console):  # during the first start: someone (or something) puts two links into the live caches
        if seen:
            return
        os.symlink(console.local(PRECIOUS), console.local(f"{RADV}/link-to-folder"))
        os.symlink(console.local(f"{PRECIOUS}/a.bin"), console.local(f"{USER_CACHE}/link-to-file"))
        seen["folder"] = console.list(RADV)["link-to-folder"]["mode"]
        seen["file"] = console.list(USER_CACHE)["link-to-file"]
    H.SCENARIO["after_start"] = plant
    code, text = H.run_main(H.plan(folder, "links", [], tests=2), out, ("--warm-copy", str(copy)))
    if code != 0:
        p.append(f"exit {code}: {text[-500:]}")
    if seen.get("folder") != "d" or (seen.get("file") or {}).get("mode") != "-":
        p.append(f"the stand-in does not list links as websrv does (folder link {seen.get('folder')}, file link "
                 f"{seen.get('file')})")
    p += precious_intact(root, precious)
    through = [w for w in fake.warm_writes if any("link-to-" in x for x in w[1:])]
    if through:
        p.append(f"a write went through or at a link: {through[:3]}")
    kept_links = [q for q in (c / "radv/link-to-folder" for c in old_folders(root)) if q.is_symlink()]
    kept_links += [q for q in (c / "link-to-file" for c in old_folders(root)) if q.is_symlink()]
    if len(kept_links) != 2 or any(Path(os.readlink(q)).resolve() not in (fake.local(PRECIOUS).resolve(),
                                                                         fake.local(f"{PRECIOUS}/a.bin").resolve())
                                   for q in kept_links):
        p.append(f"the two links are not kept as links in the .old- folders: {kept_links}")
    p += H.owner_back(H.FAKE["before"], root)
    if len(H.SCENARIO.get("started", [])) != 2:
        p.append(f"starts: {H.SCENARIO.get('started')}")
    return p


@case("N2 the live folder itself is a link: one rename moves the link, the upload goes into a new folder; the batch "
      "end moves it aside again; what it points at stays byte for byte")
def _(root, out, folder):
    fake = H.new_fake(root, radv=False)  # the owner has no driver cache folder: <data>/cache is free
    copy, code, text = H.make_warm_copy(folder, out)
    p = [] if code == 0 else [f"--make-warm-copy exit {code}: {text[-300:]}"]
    precious = plant_precious(root)
    H.FAKE["before"] = H.hashes(root)
    caches, notes = quiet_cache(fake), []
    keep = lambda note: notes.append(json.dumps(note))  # noqa: E731
    note = caches.set_aside(copy.name, keep)
    os.symlink(fake.local(PRECIOUS), fake.local(DRIVER_CACHE))  # a link where the live driver cache goes
    if fake.list(DATA)["cache"]["mode"] != "d":
        p.append("the stand-in does not list the link as a folder")
    record = caches.restore(copy, note, keep)
    p += precious_intact(root, precious)
    moved = [m["to"] for m in record["set_old"] if m["tree"] == "cache"]
    if len(moved) != 1 or not fake.local(moved[0]).is_symlink():
        p.append(f"the link was not moved aside as a link: {record['set_old']}")
    live = fake.local(DRIVER_CACHE)
    if live.is_symlink() or not (live / "radv/index").is_file():
        p.append("the copy did not land in a new, real folder")
    ok, why = caches.back(note, keep)
    if not ok:
        p.append(f"back: {why}")
    p += precious_intact(root, precious)
    if fake.local(DRIVER_CACHE).exists():
        p.append(f"{DRIVER_CACHE} is there at the end; the owner had none")
    if len(note.get("old", [])) != 3 or any(e["state"] != "kept" for e in note["old"]):
        p.append(f"the note does not list the three .old- folders as kept: {note.get('old')}")
    if not any('"old"' in n for n in notes):
        p.append("the note was not written before the renames aside")
    p += H.owner_back(H.FAKE["before"], root)
    return p


@case("N3 a rename aside that cannot be done: the step stops and says so; nothing deleted, the test caches and the "
      "owner's caches stay where they are; --restore-env --go puts the owner's back later")
def _(root, out, folder):
    fake = H.new_fake(root)
    copy, code, text = H.make_warm_copy(folder, out)
    p = [] if code == 0 else [f"--make-warm-copy exit {code}: {text[-300:]}"]
    real_rename = H.FakeWarmWriter.rename

    def refused_old(self, source, target):
        if warm_cache.OLD in target:
            self.fake.calls.append(("warm-rename-refused", source, target))
            raise tool.NoAnswer("fake: 550 rename refused")
        return real_rename(self, source, target)
    H.FakeWarmWriter.rename = refused_old
    try:
        code, text = H.run_main(H.plan(folder, "norename", [], tests=2), out, ("--warm-copy", str(copy)))
    finally:
        H.FakeWarmWriter.rename = real_rename
    if code != 2:
        p.append(f"exit {code}, expected 2: {text[-300:]}")
    if H.SCENARIO.get("started") != ["norename-1"]:
        p.append(f"starts: {H.SCENARIO.get('started')} (the second must not start)")
    summary = (H.batches(out)[0] / "summary.md").read_text()
    if "COULD NOT RENAME" not in summary or "nothing deleted" not in summary:
        p.append("summary.md does not say the rename could not be done and nothing was deleted")
    live = [q for q in fake.local(USER_CACHE).rglob("*") if q.is_file()] if fake.local(USER_CACHE).is_dir() else []
    if not live:
        p.append("the first start's test cache is gone from the live place")
    if len(H.warm_asides(root)) != 2 or "warm_pending" not in H.state_of(out):
        p.append(f"the owner's folders should stay aside, noted: {H.warm_asides(root)}")
    code, text = H.run_argv(["--restore-env", "--go", "--out-root", str(out)])
    p += H.owner_back(H.FAKE["before"], root)
    if H.warm_asides(root) or "warm_pending" in H.state_of(out):
        p.append(f"--restore-env --go did not put the owner's back: {code!r}")
    if len(old_folders(root)) != 2:
        p.append(f"the test cache left in place should now be kept as two .old- folders: {old_folders(root)}")
    return p


@case("N4 the plan print says every start leaves a whole test cache behind, and that nothing deletes them")
def _(root, out, folder):
    fake = H.new_fake(root)
    copy, code, text = H.make_warm_copy(folder, out)
    fake.calls.clear()
    code, text = H.run_argv([str(H.plan(folder, "print", [], tests=3)), "--warm-copy", str(copy), "--out-root",
                             str(out)])
    p = [] if code == 0 else [f"exit {code}"]
    for needle in ("ROOM ON THE CONSOLE", "3 set(s) for this plan", "never deletes them", "renamed aside to *.old-<time>"):
        if needle not in text:
            p.append(f"the plan print lacks {needle!r}")
    if fake.calls:
        p.append(f"the plan print asked the console: {fake.calls[:3]}")
    return p


# ---------------------------------------------------------------- 1b. the save restore

class FakeFTP:
    """The console's FTP server on the stand-in, as the save restore uses it. DELE is remove() and RMD rmdir() on the
    path (the system resolves links in the middle of it), RNTO a plain rename (a link moves as the link)."""
    sent = []

    def __init__(self):
        self.root = H.FAKE["console"].root

    def local(self, path):
        return self.root / path.lstrip("/")

    def connect(self, *a, **k):
        pass

    def login(self, *a, **k):
        pass

    def voidcmd(self, command):
        FakeFTP.sent.append(command)

    def mkd(self, path):
        FakeFTP.sent.append(f"MKD {path}")
        if self.local(path).exists():
            raise H.tool.ftplib.error_perm("550 exists")
        self.local(path).mkdir()

    def storbinary(self, command, handle):
        FakeFTP.sent.append(command.split(" ", 1)[0] + " " + command.split(" ", 1)[1])
        self.local(command.split(" ", 1)[1]).write_bytes(handle.read())

    def sendcmd(self, command):
        FakeFTP.sent.append(command)
        what, path = command.split(" ", 1)
        local = self.local(path)
        try:
            if what == "MKD":
                local.mkdir()
            elif what == "DELE":
                os.rmdir(local) if local.is_dir() and not local.is_symlink() else os.unlink(local)
            elif what == "RMD":
                os.rmdir(local)
        except OSError as error:  # the server answers 550 with the system's words
            raise H.tool.ftplib.error_perm(f"550 {error.strerror}") from error
        return "226 ok"

    def rename(self, source, target):
        FakeFTP.sent.append(f"RNFR {source} -> RNTO {target}")
        if self.local(target).exists() or self.local(target).is_symlink():
            raise H.tool.ftplib.error_perm("550 target there")
        os.rename(self.local(source), self.local(target))

    def quit(self):
        pass


def fake_urlopen(fake):
    """websrv's /fs on the stand-in: ?fmt=json gives its listing (links followed), otherwise the file."""
    def urlopen(url, timeout=None):
        url = url.full_url if hasattr(url, "full_url") else url
        parts = urllib.parse.urlsplit(url)
        path = urllib.parse.unquote(parts.path)
        assert path.startswith("/fs"), url
        path = path[3:] or "/"
        if parts.query == "fmt=json":
            listing = fake.list(path)
            if listing is None:
                raise urllib.error.HTTPError(url, 404, "not found", {}, io.BytesIO(b""))
            body = json.dumps(list(listing.values())).encode()
        else:
            data = fake.read(path)
            if data is None:
                raise urllib.error.HTTPError(url, 404, "not found", {}, io.BytesIO(b""))
            body = data
        return contextlib.closing(types.SimpleNamespace(read=lambda *a: body, close=lambda: None))
    return urlopen


def run_save_restore(fake, backup, save_dir, script=SAVE_SCRIPT):
    """The save restore script, run in this process against the stand-in. (exit code or None, printed text)."""
    settings = tool.runner_config.load()
    old_dir, old_open, old_ftp = settings["game"]["save_dir"], urllib.request.urlopen, H.tool.ftplib.FTP
    settings["game"]["save_dir"] = save_dir
    urllib.request.urlopen = fake_urlopen(fake)
    H.tool.ftplib.FTP = FakeFTP
    FakeFTP.sent = []
    printed, code = io.StringIO(), None
    saved_argv = sys.argv
    sys.argv = [str(script), str(backup)]
    try:
        with contextlib.redirect_stdout(printed):
            runpy.run_path(str(script), run_name="__main__")
    except SystemExit as stop:
        code = stop.code
    except Exception:  # noqa: BLE001 - an FTP error ends the script with a traceback on a console too
        code = "raised: " + traceback.format_exc().strip().splitlines()[-1]
    finally:
        sys.argv = saved_argv
        settings["game"]["save_dir"] = old_dir
        urllib.request.urlopen, H.tool.ftplib.FTP = old_open, old_ftp
    return code, printed.getvalue()


@case("N5 the save restore: a slot that is a link to a folder is renamed aside as the link; nothing in it is deleted")
def _(root, out, folder):
    fake = H.new_fake(root)
    profile = f"{DATA}/user/nand/user/save/0000000000000000/PROFILE"
    save = f"{profile}/{H.TITLE}"
    H.put_file(root, f"{save}/slot_1/save.bin", b"old slot 1" * 10)
    H.put_file(root, f"{save}/slot_2/save.bin", b"a test's autosave" * 10)
    precious = plant_precious(root)
    os.symlink(fake.local(PRECIOUS), fake.local(f"{save}/slot_3"))  # a slot that is a link to another folder
    H.FAKE["before"] = H.hashes(root)
    backup = folder / "backup"
    H.put_file(backup, "slot_1/save.bin", b"the owner's slot 1" * 10)
    code, text = run_save_restore(fake, backup, save)
    p = [] if code is None else [f"exit {code}: {text[-300:]}"]
    p += precious_intact(root, precious)
    deletes = [c for c in FakeFTP.sent if c.startswith(("DELE", "RMD"))]
    if deletes:
        p.append(f"the save restore sent deletes: {deletes}")
    kept = fake.local(f"{DATA}/old-save-slots")
    aside = sorted(c.name for c in kept.iterdir()) if kept.is_dir() else []
    if len(aside) != 2 or not all(n.startswith(f"{H.TITLE}-") for n in aside):
        p.append(f"expected slot_2 and slot_3 in <data_dir>/old-save-slots as <title>-<time>-<slot>: {aside}")
    if not any(n.endswith("-slot_3") and (kept / n).is_symlink() for n in aside):
        p.append("the slot that is a link was not moved as the link")
    if any(n.endswith("-slot_2") and not (kept / n / "save.bin").is_file() for n in aside):
        p.append("the moved autosave slot is not kept whole")
    if sorted(c.name for c in fake.local(profile).iterdir()) != [H.TITLE]:
        p.append(f"something was put beside the save folder: {sorted(c.name for c in fake.local(profile).iterdir())}")
    if sorted(c.name for c in fake.local(save).iterdir()) != ["slot_1"] or \
            fake.local(f"{save}/slot_1/save.bin").read_bytes() != b"the owner's slot 1" * 10:
        p.append(f"the save folder is not the backup: {sorted(c.name for c in fake.local(save).iterdir())}")
    if "moved aside (kept on the console, remove by hand)" not in text:
        p.append(f"the last line does not name what was moved aside: {text[-200:]!r}")
    # The changed save files are the restore's job: the shared check must not count them as lost.
    H.FAKE["before"] = {k: v for k, v in H.FAKE["before"].items() if not k.startswith(save + "/")}
    return p


# ---------------------------------------------------------------- 2. the launcher

class FakeProsperoMgr:
    """ProsperoMgr's answers as its source gives them (launchers.py names the files): /api/titles/running
    {"title_id"}, /api/titles/launch {"ok", "via_notification"} or {"error"} with a 4xx/5xx, /api/thermal."""

    def __init__(self, running="", launch=(200, {"ok": True, "via_notification": False}), down=False):
        self.running, self.launch, self.down, self.requests = running, launch, down, []

    def __call__(self, request, timeout=None):
        self.requests.append((request.get_method(), request.full_url, request.data,
                              request.get_header("Content-type"), timeout))
        if self.down:
            raise ConnectionRefusedError("fake: refused")
        path = urllib.parse.urlsplit(request.full_url).path
        if path == "/api/titles/running":
            status, body = 200, {"title_id": self.running}
        elif path == "/api/titles/launch" and request.get_method() == "POST":
            status, body = self.launch
        elif path == "/api/thermal":
            status, body = 200, {"ok": True, "cpu_c": 61, "soc_c": 58, "m2_c": 44, "hottest_c": 61}
        else:
            status, body = 404, {"error": "not found"}
        raw = json.dumps(body).encode()
        if status >= 400:
            raise urllib.error.HTTPError(request.full_url, status, "error", {}, io.BytesIO(raw))
        return contextlib.closing(types.SimpleNamespace(status=status, read=lambda *a: raw, close=lambda: None))


@case("N6 --launcher prosperomgr: the calls as ProsperoMgr's source has them; a notification, an error, an open app "
      "or no answer start nothing")
def _(root, out, folder):
    p = []
    good = FakeProsperoMgr()
    launcher = launchers.ProsperoMgr("console.invalid", 7070, 10, tool.NoAnswer, opener=good)
    launcher.launch(tool.APP)
    if [r[:2] for r in good.requests] != [("GET", "http://console.invalid:7070/api/titles/running"),
                                          ("POST", "http://console.invalid:7070/api/titles/launch")]:
        p.append(f"requests: {good.requests}")
    elif json.loads(good.requests[1][2]) != {"title_id": tool.APP} or good.requests[1][3] != "application/json":
        p.append(f"the launch body: {good.requests[1]}")
    for name, fake, needle in (
            ("notification", FakeProsperoMgr(launch=(200, {"ok": True, "via_notification": True})), "notification"),
            ("error", FakeProsperoMgr(launch=(500, {"error": "sceSystemServiceLaunchApp failed (0x80020002)"})),
             "sceSystemServiceLaunchApp failed (0x80020002)"),
            ("no user", FakeProsperoMgr(launch=(500, {"error": "no foreground user"})), "no foreground user"),
            ("open app", FakeProsperoMgr(running="PPSA01234"), "PPSA01234 is running")):
        try:
            launchers.ProsperoMgr("h", 7070, 10, tool.NoAnswer, opener=fake).launch(tool.APP)
            p.append(f"{name}: launch did not refuse")
        except launchers.LaunchRefused as error:
            if needle not in str(error):
                p.append(f"{name}: {error}")
        if name == "open app" and any(r[0] == "POST" for r in fake.requests):
            p.append("a launch was sent while another app runs")
    try:
        launchers.ProsperoMgr("h", 7070, 10, tool.NoAnswer, opener=FakeProsperoMgr(down=True)).launch(tool.APP)
        p.append("no answer: launch did not fail")
    except tool.NoAnswer:
        pass
    # Batch.launch: one call, a refusal is a "did not start" stop, never a websrv retry.
    said = []
    batch = types.SimpleNamespace(launcher=launchers.ProsperoMgr("h", 7070, 10, tool.NoAnswer,
                                                                  opener=FakeProsperoMgr(running="PPSA01234")),
                                  say=said.append, launched_any=False, closed_at=1.0,
                                  console=types.SimpleNamespace(launch=lambda: p.append("websrv /launch was used")))
    try:
        tool.Batch.launch(batch)
        p.append("Batch.launch did not stop on a refusal")
    except tool.Stop as stop:
        if stop.kind != "not_started":
            p.append(f"Batch.launch stopped as {stop.kind}")
    ok = FakeProsperoMgr()
    batch.launcher = launchers.ProsperoMgr("h", 7070, 10, tool.NoAnswer, opener=ok)
    tool.Batch.launch(batch)
    if sum(r[0] == "POST" for r in ok.requests) != 1:
        p.append(f"Batch.launch sent {sum(r[0] == 'POST' for r in ok.requests)} launches")
    return p


@case("N7 --check-launcher: reads only; without --go nothing is sent; settings and defaults")
def _(root, out, folder):
    p = []
    code, text = H.run_argv(["--check-launcher", "--launcher", "prosperomgr", "--out-root", str(out)])
    if code != 0 or "Nothing was sent" not in text:
        p.append(f"without --go: exit {code}, {text[-200:]!r}")
    fake = FakeProsperoMgr(running=tool.APP)
    old = urllib.request.urlopen
    urllib.request.urlopen = fake
    try:
        code, text = H.run_argv(["--check-launcher", "--launcher", "prosperomgr", "--launcher-port", "7071", "--go",
                                 "--out-root", str(out)])
    finally:
        urllib.request.urlopen = old
    if code != 0 or "Running title: PPSA98515 (this runner's app)" not in text or "cpu_c 61 C" not in text:
        p.append(f"with --go: exit {code}, {text[-300:]!r}")
    if any(r[0] != "GET" for r in fake.requests) or not all(":7071/" in r[1] for r in fake.requests):
        p.append(f"--check-launcher sent: {fake.requests}")
    code, text = H.run_argv(["--check-launcher", "--go", "--out-root", str(out)])
    if code != 0 or "websrv" not in text:
        p.append(f"websrv --check-launcher: exit {code}, {text[-200:]!r}")
    defaults = tool.runner_config.DEFAULTS["launcher"]
    if defaults != {"kind": "websrv", "host": "", "port": 7070}:
        p.append(f"launcher defaults: {defaults}")
    example = json.loads((H.HERE / "runner-config.example.json").read_text())
    if example.get("launcher") != defaults:
        p.append(f"runner-config.example.json launcher: {example.get('launcher')}")
    return p


# ---------------------------------------------------------------- running

def clean_up():
    shutil.rmtree(SCRATCH, ignore_errors=True)


class NoDelete(unittest.TestCase):
    maxDiff = None


def _as_test(name, run):
    def test(self):
        problems = run()
        self.assertEqual(problems, [], f"{name}:\n" + "\n".join(problems))
    test.__doc__ = name
    return test


for _number, (_case_name, _run) in enumerate(RUN, 1):
    setattr(NoDelete, f"test_{_number:02d}_{_case_name.split(' ')[0].lower()}", _as_test(_case_name, _run))


def setUpModule():
    warnings.simplefilter("ignore", ResourceWarning)
    H.SCRATCH.mkdir(exist_ok=True)  # make_warm_copy's stand-in lives in the case folder; the harness's own is kept


def tearDownModule():
    clean_up()
    H.clean_up()


def main():
    global VERBOSE
    VERBOSE = True
    for _, run in RUN:
        run()
    failed = [name for name, problems in RESULTS if problems]
    print(f"\n{len(RESULTS) - len(failed)} of {len(RESULTS)} cases pass")
    clean_up()
    H.clean_up()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
