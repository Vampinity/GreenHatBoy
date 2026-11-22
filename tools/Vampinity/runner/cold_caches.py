"""Cold starts for the runner: set the shader store and the driver cache aside before a start, put them back after.

A cold start is a start with no shader store and no driver cache, like a new player's very first start. The runner
uses this file when a test's env has EDEN_TEST_COLD=1, or when it was started with --cold.

  shader store   <app.data_dir>/user/cache/shader/<title in small letters>   (the game's whole shader folder: the
                 pipeline cache, the prepared stores and their lists, the shader set, every variant folder)
  driver cache   <app.data_dir>/cache/radv                                    (the Mesa/RADV disk shader cache,
                 shared by every game)

Before the start each one that is there and not empty is RENAMED, in its own folder, to
<name>.cold-aside-<date>-<time>. Nothing is copied and nothing is deleted. After the test the app has built new
ones in their place: those are renamed to <name>.cold-built-<date>-<time> (kept, never deleted), and then the
.cold-aside- folder is renamed back. Then a listing of every file under it must show the same files and sizes as
before. The console's rename replaces an existing target, so before every rename a listing taken right then must
show the source there and the target not there.

The shader set stays in place by default. Its two input files sit at the top of the title folder: the recipe (any
*.nx2recipe, the app reads every one there) and shader_set_index.txt beside it. A store build needs them, and they
are not a cache (the app never writes them). So after the folder is renamed aside, a new, empty title folder is
made and those files are renamed into it from the .cold-aside- folder. After the test they are renamed back into the
.cold-aside- folder first, then the rest goes as above, so the listing check covers them too. What the set BUILDS
(prep_shader_set.* in the variant folder, shader_set_prepass.skip) is cache and goes aside with the rest.
EDEN_TEST_COLD_SET=1 in the test's env moves the set aside too (the whole folder, nothing made, as before).

The way back is written down before the first rename: cold-note.json in the run folder and "cold_pending" in the
runner's state file. If the runner is cut off, the next --go (or --restore-env --go) finds the leftover folder,
by that note or by its name on the console, and puts it back first.

Rules:
  - The app must be closed: the runner's own closed check, then eden_log.txt the same size over QUIET seconds and
    no test-quit file lying in the data folder. If it is not, nothing is moved (before) or nothing is put back
    (after: the folders stay aside and the next start-up check puts them back).
  - A listing that does not answer is "unknown", never "not there": the step stops.
  - A radv-shader-cache file in an app folder refuses the cold start: with cache/radv gone the app would move that
    file in as its driver cache, so the start would not be cold and the file would leave the app folder.
  - Only these renames exist: <live> -> <live>.cold-aside-<stamp>, <live>.cold-aside-<stamp> -> <live>,
    <live> -> <live>.cold-built-<stamp>, in the same folder; and, for a shader-set file only, <title
    folder>.cold-aside-<stamp>/<file> <-> <title folder>/<file> (allowed_pair). The one other write is making the
    empty live title folder when it is not there (allowed_folder). Nothing here writes a file on the console or
    removes one.

Also here, for every start, cold or not: boot_caches() reads the run folder's copy of the boot log for what the
start reused (the store, new or reused, its pipeline count, the driver pipeline cache), and cache_line() makes
the one line the runner logs from it. That part only reads local files.

Standard library only.
"""
import hashlib
import json
import posixpath
import re
import time

COLD_LINE = "EDEN_TEST_COLD"
SET_LINE = "EDEN_TEST_COLD_SET"  # =1: the shader set goes aside too
SET_SUFFIX = ".nx2recipe"  # the recipe: the app reads every *.nx2recipe at the top of the title folder
SET_INDEX = "shader_set_index.txt"  # beside the recipe: which game files hold its programs
ASIDE = ".cold-aside-"
BUILT = ".cold-built-"
STAMP = r"\d{8}-\d{6}(?:-\d{1,3})?"
QUIET = 20.0  # seconds; the game logs a heartbeat about every 15 s, so a shorter look can miss a frozen app
NOTE_NAME = "cold-note.json"
LOG_NAME = "cold.log"
TRAPS = {"radv-shader-cache": "with cache/radv aside the app moves this file in as its driver cache "
                              "(the start would not be cold, and the file would leave the app folder)"}
OPEN = ("moving", "aside", "not_back")  # note states with something (maybe) still aside
NOTHING_LEFT = "no cold-start folder is left aside"


class ColdRefused(Exception):
    """The cold start cannot go ahead. Nothing was moved (or what was moved is back again)."""


class ColdNotBack(Exception):
    """Something was moved and could not be put back. The note says what is where."""


class MoveFailed(Exception):
    """A rename that was not proven safe, failed, or did not show afterwards."""


def targets(data, title):
    return [("shader store", f"{data}/user/cache/shader/{title.lower()}"), ("driver cache", f"{data}/cache/radv")]


def _parents(data):
    """Folder -> test for a live cache name in it."""
    return {f"{data}/cache": lambda n: n == "radv",
            f"{data}/user/cache/shader": lambda n: bool(re.fullmatch(r"[0-9a-f]{16}", n))}


def split_name(name):
    """(live name, ASIDE or BUILT, stamp) for a moved name, None for any other name."""
    found = re.fullmatch(r"(.+?)(\.cold-aside-|\.cold-built-)(" + STAMP + ")", name)
    return (found[1], found[2], found[3]) if found else None


def is_set_file(name):
    """A shader-set input file (kept in place by default): a recipe or its index. Never a moved name."""
    return (name == SET_INDEX or (name.endswith(SET_SUFFIX) and len(name) > len(SET_SUFFIX))) and not split_name(name)


def allowed_folder(path, data):
    """The one folder a cold start may make: a live title folder, to keep the shader set in place."""
    folder, name = posixpath.split(path)
    return folder == f"{data}/user/cache/shader" and bool(re.fullmatch(r"[0-9a-f]{16}", name))


def _set_folders(one, other, data):
    """True when one folder is a live title folder and the other is its .cold-aside- folder, side by side."""
    for live, aside in ((one, other), (other, one)):
        moved = split_name(posixpath.basename(aside))
        if (allowed_folder(live, data) and posixpath.dirname(aside) == posixpath.dirname(live) and moved
                and moved[1] == ASIDE and moved[0] == posixpath.basename(live)):
            return True
    return False


def allowed_pair(source, target, data):
    """The only renames a cold start may ask the console for (see the top of this file)."""
    source_folder, source_name = posixpath.split(source)
    target_folder, target_name = posixpath.split(target)
    if source_folder != target_folder:  # only a shader-set file, between a title folder and its .cold-aside- folder
        return source_name == target_name and is_set_file(source_name) and _set_folders(source_folder,
                                                                                         target_folder, data)
    is_live = _parents(data).get(source_folder)
    if is_live is None:
        return False
    if is_live(source_name):  # live -> aside or built
        moved = split_name(target_name)
        return bool(moved) and moved[0] == source_name
    moved = split_name(source_name)  # aside -> live
    return bool(moved) and moved[1] == ASIDE and moved[0] == target_name and is_live(target_name)


def digest(manifest):
    text = "\n".join(f"{name}\t{size}" for name, size in sorted(manifest.items()))
    return hashlib.sha256(text.encode()).hexdigest()


def counts(manifest):
    return {"files": len(manifest), "bytes": sum(manifest.values()), "digest": digest(manifest)}


def human(size):
    for unit in ("bytes", "KiB", "MiB", "GiB"):
        if size < 1024 or unit == "GiB":
            return f"{size:.0f} {unit}" if unit == "bytes" else f"{size:.1f} {unit}"
        size /= 1024


def cold_proof(eden_log):
    """The three boot lines that say a start found no stored pipelines (cold-proof.v2.py's rules 1 and 2).
    {} when the log is missing. cold: True only when all three are there and 0."""
    try:
        text = eden_log.read_text(errors="replace")
    except OSError:
        return {}
    out = {}
    for key, pattern in (("pipelines_read_at_boot", r"Total Pipeline Count: (\d+)"),
                         ("prepared_records_at_boot", r"Shader preparation: (\d+) pipelines known"),
                         ("records_read_for_preparation", r"Shader preparation stats: (\d+) records read")):
        found = re.search(pattern, text)
        out[key] = int(found[1]) if found else None
    values = list(out.values())
    out["cold"] = None if None in values else not any(values)
    return out


# ---- which caches a start used (every start, warm or cold)
#
# waveydude asked for this on 18 Nov: for a cold start, log which caches were moved and that they went back; for
# a warm start, log what it actually reused. The first half is the cold start's own note; the second half is in
# the boot log. The store line is read with the same pattern as the shared scorer (STAMP_RE in
# tools/stk/stk_score.py), and "reads_as" follows the run contract's cache class (docs/RUN-CONTRACT.md):
#   warm  the store was reused
#   cold  a new store, Total Pipeline Count 0, no driver pipeline cache loaded
#   half  a new store, but pipelines or a driver pipeline cache came from an earlier start: never a control
STORE_LINE = re.compile(r"SOURCE_STAMP:\s*id\s+(\S+).*?store\s+(prep_\w+)\s+(reused|created|new)\s+"
                        r"\((\d+)\s+pipelines\)(?:,\s*build\s+(\d+))?")
KNOWN_LINE = re.compile(r"Shader preparation: (\d+) pipelines known, (\d+) left to prepare")
RECORDS_LINE = re.compile(r"Shader preparation stats: (\d+) records read \((\d+) own")
TOTAL_LINE = re.compile(r"Total Pipeline Count:\s*(\d+)")
DRIVER_LINE = re.compile(r"Loaded Vulkan driver pipeline cache")
BOOT_LINES = 5000  # the boot's cache lines sit in the first few thousand lines; the scorer looks as far


def boot_caches(folder):
    """What a start's own boot log says about its caches, from the copy of eden_log.txt in its run folder (a
    crash copy of the log, crash-*-eden_log.txt, when the plain one has no store line). Reads local files only.
    A value the log does not give is None, and "why_missing" then says why."""
    out = {"source": None, "store": None, "store_state": None, "store_pipelines": None, "store_build": None,
           "pipelines_known": None, "left_to_prepare": None, "records_read": None, "own_records": None,
           "total_pipeline_count": None, "driver_pipeline_cache_loaded": None, "reads_as": None, "why_missing": ""}
    logs = [folder / "eden_log.txt"] + sorted(folder.glob("crash-*-eden_log.txt"))
    seen = []
    for log in logs:
        try:
            with open(log, errors="replace") as handle:
                lines = [line for _, line in zip(range(BOOT_LINES), handle)]
        except OSError:
            continue
        seen.append((log.name, lines))
        if any(STORE_LINE.search(line) for line in lines):
            break
    if not seen:
        out["why_missing"] = "no eden_log.txt in the run folder"
        return out
    out["source"], lines = seen[-1] if any(STORE_LINE.search(line) for line in seen[-1][1]) else seen[0]
    for line in lines:
        if out["store"] is None and (found := STORE_LINE.search(line)):
            out["store"], state = found[2], found[3]
            out["store_state"] = "reused" if state == "reused" else "new"  # older builds wrote "created" for new
            out["store_pipelines"], out["store_build"] = int(found[4]), found[5]
        if out["pipelines_known"] is None and (found := KNOWN_LINE.search(line)):
            out["pipelines_known"], out["left_to_prepare"] = int(found[1]), int(found[2])
        if out["records_read"] is None and (found := RECORDS_LINE.search(line)):
            out["records_read"], out["own_records"] = int(found[1]), int(found[2])
        if out["total_pipeline_count"] is None and (found := TOTAL_LINE.search(line)):
            out["total_pipeline_count"] = int(found[1])
    out["driver_pipeline_cache_loaded"] = any(DRIVER_LINE.search(line) for line in lines)
    if out["store"] is None:
        out["why_missing"] = (f"no shader store line (SOURCE_STAMP ... store prep_...) in the first {BOOT_LINES} "
                              f"lines of {out['source']}: the game did not get that far, or the build words it otherwise")
    elif out["store_state"] == "reused":
        out["reads_as"] = "warm"
    elif not out["total_pipeline_count"] and not out["driver_pipeline_cache_loaded"]:
        out["reads_as"] = "cold"
    else:
        out["reads_as"] = "half"
    return out


def boot_text(use):
    """The boot log's part of the caches line."""
    if use["store"] is None:
        return f"no store line ({use['why_missing']})"
    parts = [f"store {use['store']} {use['store_state']} ({use['store_pipelines']} pipelines)" +
             (f", build {use['store_build']}" if use["store_build"] else "")]
    if use["pipelines_known"] is not None:
        parts.append(f"{use['pipelines_known']} pipelines known, {use['left_to_prepare']} left to prepare")
    if use["records_read"] is not None:
        parts.append(f"{use['records_read']} records read ({use['own_records']} own)")
    parts.append("Total Pipeline Count " + ("not logged" if use["total_pipeline_count"] is None
                                            else str(use["total_pipeline_count"])))
    parts.append("driver pipeline cache loaded" if use["driver_pipeline_cache_loaded"]
                 else "no driver pipeline cache loaded")
    reads = {"warm": "warm", "cold": "cold",
             "half": "half (a new store, but pipelines or a driver pipeline cache came from an earlier start)"}
    return "; ".join(parts) + ". Reads as " + reads[use["reads_as"]]


def cache_line(use, cold=None):
    """One line for the logs about a start's caches. cold: the start's "cold" entry of result.json, None for a
    start that was not asked to be cold (the runner then moves nothing and restores nothing)."""
    if cold is None:
        moved = "Caches: none set aside by the runner (not a cold start; it starts on what is on the console)"
    elif not cold.get("set_aside"):
        moved = ("Caches: nothing set aside" + (", the console had no shader store and no driver cache"
                                                if cold.get("status") == "already_cold" else f" ({cold.get('status')})"))
    else:
        moved = "Caches: set aside for this start: " + ", ".join(
            f"{item['what']} {item['path']} ({item['files']} files, {human(item['bytes'])})" for item in cold["set_aside"])
        if cold.get("set_kept"):
            moved += "; shader set kept in place: " + ", ".join(cold["set_kept"])
        moved += "; put back: " + ("yes, checked by a listing" if cold.get("back") else
                                   f"NOT yet ({cold.get('status')})")
    return f"{moved}. Boot log: {boot_text(use)}"


def cache_short(use, cold=None):
    """The same for summary.md, without the paths."""
    if cold is None:
        moved = "nothing set aside"
    elif not cold.get("set_aside"):
        moved = "nothing to set aside"
    else:
        moved = ("set aside: " + " and ".join(item["what"] for item in cold["set_aside"]) +
                 (", back" if cold.get("back") else ", NOT back"))
    return f"{moved}; boot log: {boot_text(use)}"


class ColdCaches:
    def __init__(self, console, data, app_folders, say, app_open, log_sizes, errors=(), quiet=None,
                 sleep=time.sleep, clock=lambda: time.strftime("%Y%m%d-%H%M%S")):
        self.console, self.data, self.app_folders = console, data.rstrip("/"), list(app_folders)
        self.say, self.app_open, self.log_sizes = say, app_open, log_sizes
        self.errors = tuple(errors) + (MoveFailed,)
        self.quiet = QUIET if quiet is None else quiet
        self.sleep, self.clock = sleep, clock
        self.last_note = None

    # ---- reading (strict: an error is never "not there")

    def entries(self, folder):
        found = self.console.list(folder)
        if found is None:
            return None
        return {name: entry for name, entry in found.items() if name not in (".", "..")}

    def entry(self, path):
        folder, name = posixpath.split(path)
        found = self.entries(folder)
        return None if found is None else found.get(name)

    def manifest(self, path, depth=32):
        """{relative file path: size} of every file under path. A folder that vanishes while it is read stops."""
        found = self.entries(path)
        if found is None:
            raise MoveFailed(f"{path} vanished while it was listed")
        out = {}
        for name, entry in found.items():
            if entry.get("mode") == "d":
                if depth <= 0:
                    raise MoveFailed(f"{path}/{name}: deeper than 32 folders")
                out.update({f"{name}/{k}": v for k, v in self.manifest(f"{path}/{name}", depth - 1).items()})
            else:
                size = entry.get("size")
                if not isinstance(size, int):
                    raise MoveFailed(f"{path}/{name} has no size in the listing")
                out[name] = size
        return out

    def closed(self):
        """(True, "") only when the runner sees no open app, eden_log.txt keeps its size for QUIET s and no
        test-quit is lying in the data folder. Anything unclear counts as open."""
        try:
            if self.app_open():
                return False, "the app is running (its sandbox has its mounts)"
            first = self.log_sizes()[0]
            self.sleep(self.quiet)
            second = self.log_sizes()[0]
            if self.app_open():
                return False, "the app is running (its sandbox has its mounts)"
            if first != second:
                return False, f"eden_log.txt grew from {first} to {second} bytes in {self.quiet:g} s: the app is running"
            top = self.entries(self.data)
            if top is None:
                return False, f"{self.data} is not there"
            if "test-quit" in top:
                return False, "a test-quit file is lying in the data folder: the app may be closing right now"
        except self.errors as error:
            return False, f"the app's state is unknown ({error})"
        return True, ""

    def traps(self):
        found = []
        for folder in self.app_folders:
            for name in self.entries(folder) or {}:
                why = TRAPS.get(name.lower())
                if why:
                    found.append(f"{folder}/{name}: {why}")
        return found

    def leftovers(self):
        """[(live path, aside path)] of every .cold-aside- folder on the console, whoever left it."""
        found = []
        for folder, is_live in _parents(self.data).items():
            for name in self.entries(folder) or {}:
                moved = split_name(name)
                if moved and moved[1] == ASIDE and is_live(moved[0]):
                    found.append((f"{folder}/{moved[0]}", f"{folder}/{name}"))
        return sorted(found)

    def free_name(self, path, kind):
        """path + kind + a stamp no entry in that folder has yet."""
        folder = posixpath.dirname(path)
        taken = set(self.entries(folder) or {})
        stamp = self.clock()
        name, number = posixpath.basename(path) + kind + stamp, 1
        while name in taken:
            number += 1
            name = posixpath.basename(path) + kind + f"{stamp}-{number}"
        return f"{folder}/{name}"

    # ---- the one write

    def rename(self, source, target):
        """One rename, proven safe by a listing taken right before, and proven done by one right after."""
        if not allowed_pair(source, target, self.data):
            raise MoveFailed(f"{source} -> {target} is not a cold-start rename")
        folder, source_name = posixpath.split(source)
        target_name = posixpath.basename(target)
        found = self.entries(folder)
        if found is None or source_name not in found:
            raise MoveFailed(f"{source} is not there")
        if target_name in found:
            raise MoveFailed(f"{target} is already there: not renaming over it")
        self.console.rename_cold(source, target)
        found = self.entries(folder)
        if found is None or target_name not in found or source_name in found:
            raise MoveFailed(f"the rename {source} -> {target} does not show in the listing")

    def move_file(self, source, target):
        """A shader-set file renamed between a title folder and its .cold-aside- folder: source there as a file
        and target not there by listings taken right before, both shown right after (same size)."""
        if not allowed_pair(source, target, self.data) or posixpath.dirname(source) == posixpath.dirname(target):
            raise MoveFailed(f"{source} -> {target} is not a shader-set move")
        source_folder, source_name = posixpath.split(source)
        target_folder, target_name = posixpath.split(target)
        there, place = self.entries(source_folder), self.entries(target_folder)
        if there is None or source_name not in there or there[source_name].get("mode") == "d":
            raise MoveFailed(f"{source} is not there as a file")
        if place is None:
            raise MoveFailed(f"{target_folder} is not there")
        if target_name in place:
            raise MoveFailed(f"{target} is already there: not renaming over it")
        size = there[source_name].get("size")
        self.console.rename_cold(source, target)
        there, place = self.entries(source_folder), self.entries(target_folder)
        if (there is None or place is None or source_name in there or target_name not in place
                or place[target_name].get("size") != size):
            raise MoveFailed(f"the rename {source} -> {target} does not show in the listings")

    def make_folder(self, path):
        """The empty live title folder, made only when a listing right before shows it is not there."""
        if not allowed_folder(path, self.data):
            raise MoveFailed(f"{path} is not a folder a cold start may make")
        folder, name = posixpath.split(path)
        found = self.entries(folder)
        if found is None:
            raise MoveFailed(f"{folder} cannot be listed")
        if name in found:
            raise MoveFailed(f"{path} is already there")
        self.console.mkdir_cold(path)
        found, inside = self.entries(folder), self.entries(path)
        if found is None or found.get(name, {}).get("mode") != "d" or inside != {}:
            raise MoveFailed(f"{path} does not show as a new, empty folder")

    # ---- the shader set (kept in place unless EDEN_TEST_COLD_SET=1)

    def keep_set(self, item, keep, note):
        """After the store went aside: a new, empty title folder, and the set's files renamed into it."""
        path, aside = item["path"], item["aside"]
        item["live_made"] = "maybe"  # written before the folder is made: a cut-off run still knows to look
        keep(note)
        self.make_folder(path)
        item["live_made"] = True
        keep(note)
        for kept in item["keep"]:
            kept["state"] = "maybe"
            keep(note)
            self.move_file(f"{aside}/{kept['name']}", f"{path}/{kept['name']}")
            kept["state"] = "in_place"
            keep(note)
        found = self.entries(path)
        want = {kept["name"]: kept["size"] for kept in item["keep"]}
        if found is None or {name: entry.get("size") for name, entry in found.items()} != want:
            raise MoveFailed(f"{path} does not list exactly the shader set's files")
        self.say(f"Cold start: shader set kept in place in {path}: " +
                 ", ".join(f"{name} ({size} bytes)" for name, size in sorted(want.items())) +
                 " (renamed back from the set-aside folder; EDEN_TEST_COLD_SET=1 moves it aside too)")

    def return_set(self, item, keep, note):
        """Before the live title folder is parked: every shader-set file in it that the .cold-aside- folder lacks
        goes back there (by the note, or found by its name when the note is gone). One that is in both stays in
        the live folder, so it is kept with what the start built; nothing is renamed over."""
        path, aside = item["path"], item["aside"]
        live, moved = self.entries(path), self.entries(aside)
        if live is None or moved is None:
            raise MoveFailed(f"{path} or {aside} cannot be listed")
        notes = {kept["name"]: kept for kept in item.get("keep", [])}
        back = []
        for name in sorted(n for n, entry in live.items() if is_set_file(n) and entry.get("mode") != "d"):
            if name in moved:
                self.say(f"Cold start: {name} is in {path} and in {posixpath.basename(aside)}: the set-aside one "
                         "is the old one; the live one stays with what the start built")
                continue
            self.move_file(f"{path}/{name}", f"{aside}/{name}")
            if name in notes:
                notes[name]["state"] = "back"
                keep(note)
            back.append(name)
        for kept in notes.values():
            if kept["state"] in ("maybe", "in_place"):
                if self.entry(f"{aside}/{kept['name']}") is None:
                    raise MoveFailed(f"the shader set's {kept['name']} is in neither {path} nor {aside}")
                kept["state"] = "back" if kept["state"] == "in_place" else "not_moved"
                keep(note)
        if back:
            self.say(f"Cold start: shader set {', '.join(back)} renamed back into {posixpath.basename(aside)}")

    # ---- before the start

    def set_aside(self, title, keep, move_set=False):
        """Rename the caches aside, and keep the shader set in place unless move_set (EDEN_TEST_COLD_SET=1).
        Returns the note. keep(note) is called before every write, so the way back is on the Mac before anything
        moves. Raises ColdRefused (nothing moved, or all of it back again) or ColdNotBack (moved, and the undo
        failed)."""
        note = {"what": "cold start: the shader store and the driver cache set aside for this start",
                "title": title, "status": "checking", "items": [],
                "shader_set": "set aside with the store" if move_set else "kept in place"}
        self.last_note = note
        try:
            left = self.leftovers()
            if left:
                raise ColdRefused("a .cold-aside- folder from an earlier run is still there (" +
                                  ", ".join(aside for _, aside in left) + "); the start-up check puts it back")
            traps = self.traps()
            if traps:
                raise ColdRefused("; ".join(traps))
        except self.errors as error:
            raise ColdRefused(f"cannot tell what is on the console ({error})") from error
        ok, why = self.closed()
        if not ok:
            raise ColdRefused(why)
        self.say("Cold start: the app is closed (no mounts, eden_log.txt still for "
                 f"{self.quiet:g} s, no test-quit)")
        try:
            for what, path in targets(self.data, title):
                entry = self.entry(path)
                if entry is None:
                    self.say(f"Cold start: {what} {path}: not there")
                    continue
                files = self.manifest(path) if entry.get("mode") == "d" else None
                if files is None:
                    raise ColdRefused(f"{path} is a file, not a folder: not touching it")
                if not files:
                    self.say(f"Cold start: {what} {path}: an empty folder, left as it is")
                    continue
                item = {"what": what, "path": path, "aside": self.free_name(path, ASIDE),
                        "state": "planned", "before": counts(files)}
                if what == "shader store" and not move_set:
                    top = self.entries(path)
                    if top is None:
                        raise MoveFailed(f"{path} vanished while it was listed")
                    kept = sorted(name for name, found in top.items()
                                  if is_set_file(name) and found.get("mode") != "d" and name in files)
                    if kept:
                        item["keep"] = [{"name": name, "size": files[name], "state": "planned"} for name in kept]
                    if len(kept) == len(files):
                        self.say(f"Cold start: {what} {path}: only the shader set ({', '.join(kept)}), left as it is")
                        continue
                note["items"].append(item)
        except self.errors as error:
            raise ColdRefused(f"cannot read the caches ({error})") from error
        if not note["items"]:
            note["status"] = "already_cold"
            keep(note)
            self.say("Cold start: the console already has no shader store and no driver cache for this game: "
                     "nothing to set aside, nothing moved")
            return note
        note["status"] = "moving"
        keep(note)
        try:
            for item in note["items"]:
                item["state"] = "maybe"  # written before the rename: a cut-off run still knows to look
                keep(note)
                self.rename(item["path"], item["aside"])
                item["state"] = "aside"
                keep(note)
                self.say(f"Cold start: {item['what']} {item['path']} -> {posixpath.basename(item['aside'])} "
                         f"({item['before']['files']} files, {human(item['before']['bytes'])})")
            for item in note["items"]:
                if self.entry(item["path"]) is not None:
                    raise MoveFailed(f"{item['path']} is still there after the rename")
            for item in note["items"]:
                if item.get("keep"):
                    self.keep_set(item, keep, note)
        except self.errors as error:
            self.say(f"Cold start: setting aside failed ({error}); putting back what moved")
            ok, why = self.put_back(note, keep, check_closed=False)
            if not ok:
                raise ColdNotBack(f"setting aside failed ({error}) and the undo failed: {why}") from error
            note["status"] = "refused"
            keep(note)
            raise ColdRefused(f"setting aside failed ({error}); everything is back") from error
        note["status"] = "aside"
        note["aside_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        keep(note)
        if any(item.get("keep") for item in note["items"]):
            self.say("Cold start: nothing of the old caches is in place now but the shader set; "
                     "the next start is a first start")
        else:
            self.say("Cold start: nothing of the old caches is in place now; the next start is a first start")
        return note

    # ---- after the test

    def put_back(self, note, keep, check_closed=True):
        """Put back every item of the note that may be aside. (True, "") when all are back and the listing of
        each shows the same files and sizes as before. Moves nothing while the app may be open."""
        todo = [item for item in note["items"] if item["state"] in ("maybe", "aside")]
        if not todo:
            if note.get("status") in OPEN:  # cut off before the first rename: nothing moved, close the note
                note["status"] = "not_moved"
                keep(note)
            return True, ""
        if check_closed:
            ok, why = self.closed()
            if not ok:
                note["status"] = "not_back"
                note["why"] = f"not put back yet: {why}"
                keep(note)
                return False, note["why"]
        bad = []
        for item in reversed(todo):
            try:
                self.back_one(item, keep, note)
            except self.errors as error:
                bad.append(f"{item['what']}: {error}")
                self.say(f"Cold start: {item['what']} NOT back: {error}")
        note["status"] = "not_back" if bad else "back"
        note["why"] = "; ".join(bad)
        if not bad:
            note["back_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        keep(note)
        return not bad, note["why"]

    def back_one(self, item, keep, note):
        path, aside = item["path"], item["aside"]
        live, moved = self.entry(path), self.entry(aside)
        if moved is None:
            if live is None:
                raise MoveFailed(f"neither {path} nor {aside} is there: nothing says where the old {item['what']} is")
            # The rename never happened (a run cut off right before it), or someone put it back by hand: what is
            # in place must then be the old folder itself, file for file.
            self.check_same(item, self.manifest(path), "in place (never moved, or already back)")
            item["state"] = "back" if item["state"] == "aside" else "not_moved"
            keep(note)
            return
        if live is not None and live.get("mode") == "d" and allowed_folder(path, self.data):
            self.return_set(item, keep, note)  # the shader set back into the old folder before live is parked
        if live is not None:  # what this start built: kept beside it, never renamed over
            built = self.free_name(path, BUILT)
            files = self.manifest(path) if live.get("mode") == "d" else {}
            item["built"] = built
            keep(note)
            self.rename(path, built)
            item["built_size"] = {"files": len(files), "bytes": sum(files.values())}
            keep(note)
            self.say(f"Cold start: what the start built, {path}, kept as {posixpath.basename(built)} "
                     f"({len(files)} files, {human(sum(files.values()))})")
        self.rename(aside, path)
        if self.entry(aside) is not None:
            raise MoveFailed(f"{aside} is still there after the rename")
        self.check_same(item, self.manifest(path), "back")
        item["state"] = "back"
        keep(note)

    def check_same(self, item, files, how):
        now = counts(files)
        item["after"] = now
        before = item.get("before")
        if before is None:
            self.say(f"Cold start: {item['what']} {how} at {item['path']} ({now['files']} files, "
                     f"{human(now['bytes'])}); no note of its size before, so only its name was checked")
            return
        if now["digest"] != before["digest"]:
            raise MoveFailed(f"{item['path']} is back but its listing differs from before: {now['files']} files, "
                             f"{now['bytes']} bytes now; {before['files']} files, {before['bytes']} bytes before")
        self.say(f"Cold start: {item['what']} {how} at {item['path']}, checked by a listing: the same "
                 f"{now['files']} files and {human(now['bytes'])} as before")

    # ---- the start-up check

    def recover(self, pending_note, keep):
        """Put back every .cold-aside- folder an earlier, cut-off run left: the ones its note names, and any other
        such name on the console. (True, text) when there was nothing, or all is back. Moves nothing while the app
        may be open."""
        try:
            found = self.leftovers()
        except self.errors as error:
            return False, f"cannot list the cache folders ({error})"
        items = []
        if pending_note:
            items = [item for item in pending_note.get("items", []) if item.get("state") in ("maybe", "aside")]
        named = {item["aside"] for item in items}
        for live, aside in found:
            if aside not in named:
                items.append({"what": "leftover " + ("driver cache" if live.endswith("/radv") else "shader store"),
                              "path": live, "aside": aside, "state": "aside"})
        if not items:
            if pending_note and pending_note.get("status") in OPEN:  # its run was cut off before anything moved
                pending_note["status"] = "not_moved"
                keep(pending_note)
            return True, NOTHING_LEFT
        lives = [item["path"] for item in items if item["state"] == "aside"]
        twice = sorted({p for p in lives if lives.count(p) > 1})
        if twice:
            return False, ("more than one .cold-aside- folder for " + ", ".join(twice) +
                           ": which one is the old cache is not clear. Rename them back by hand")
        note = {"what": "start-up check: cold-start folders left aside by an earlier run, put back",
                "status": "aside", "items": items}
        self.say("Start-up check: " + ", ".join(posixpath.basename(item["aside"]) for item in items) +
                 " left aside by an earlier run; putting back")
        ok, why = self.put_back(note, keep)
        return ok, ("all back and checked" if ok else why)
