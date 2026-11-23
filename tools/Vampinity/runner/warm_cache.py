"""The whole-cache restore for warm starts: step 0 of GrowingBlackBeans' warm-run-steps.md, in the runner.

GrowingBlackBeans' warm controls start every time on the same cache: before each start both cache folders are
deleted whole and uploaded again from one copy, taken once right after the store build. The whole cache is both
folders, as they are, nothing picked file by file:

  user-cache   <app.data_dir>/user/cache    (the shader stores, the app's and the driver's pipeline files,
                                             vulkan_pipelines.bin among them, the JIT list, everything in it)
  cache        <app.data_dir>/cache         (the driver's disk caches, cache/radv among them)

The runner does the same when it is started with --warm-copy <copy folder>, with two changes for a console that
someone also plays on: THE OWNER'S OWN TWO FOLDERS ARE NEVER DELETED, AND NOTHING ELSE IS EITHER. Where the steps
say "delete", the runner renames the folder aside instead, in its own folder, once, by its top name:

  <folder>.old-<YYYYMMDD-HHMMSS>   (a test cache that was live; kept on the console, never deleted by the runner)

  1. Once, at the start of the batch: the copy is checked against its SHA-256 list. With the app closed, each of
     the owner's two folders is listed (every path and size) and renamed, in its own folder, to
     <folder>.warm-owner-aside. Then they are listed again under that name: the same paths and sizes, or the batch
     stops (and they go back).
  2. Before every start: the copy is checked against its SHA-256 list again, the app must be closed, and the
     owner's folders are listed again and must still be the same as before they moved. Only then the two live
     folders (what the copy and the starts put there) are renamed aside to <folder>.old-<time>, and the copy is
     uploaded whole into new folders. The new live folders are listed: the same folders, files and sizes as the
     copy. Then a sample of the uploaded files is read back and compared byte for byte (read_back).
  3. At the end of the batch, also after a crash, a stop, a tool error or Ctrl-C, once the app is closed: the
     test folders are renamed aside to <folder>.old-<time>, the owner's folders renamed back, and their listing
     must be the one taken before they moved. If the app is still open (a freeze) or the console does not answer,
     nothing moves yet: the batch stops with NOT BACK and the next --go (any plan) or --restore-env --go puts them
     back first.

Every start leaves one whole test cache per folder on the console (as big as the copy). The batch summary and
warm-note.json list each <folder>.old-<time> folder; remove them by hand (any FTP client) once you no longer need
them. Nothing in this runner deletes them.

Why renames and no deletes (GrowingBlackBeans, PR 38, 23 Nov 2026): websrv's fs?fmt=json listing stats each entry
with fstatat() without AT_SYMLINK_NOFOLLOW (websrv src/fs.c), and its FTP server's LIST and MLSD use stat(), so a
link to a folder lists as an ordinary folder ("d"), and a dangling link is left out. No listing this runner reads
can tell a link from a folder. A delete that walks such a listing would go through a link and delete what it
points at. A rename does not: rename(2) moves the name it is given, and if that name is a link, only the link
moves. So the runner never walks a listing to write anything: the only writes on a folder that was already there
are the single renames of the top folders; every upload goes into folders this runner has just made itself (MKD
of a name that was not there). The walks that remain only read (listings to compare, read-backs), and a walk stops
on any entry that is not plainly "d" or "-", and below 40 folders (a link loop).

A copy is made once with --make-warm-copy <folder> --go (reads only, the app closed): both live folders are
copied to this computer, with manifest.json (every folder, file and size), SHA256SUMS and copy.json. The copy
holds the console's folder paths, file names, sizes and hashes. No address, no folder of this computer.

Rules, all enforced here:
  - A listing that does not answer, or answers with something unclear, is "unknown", never "not there": the
    step stops. Nothing is renamed on a guess.
  - Writes: MKD and STOR only in the two live folders and below; no DELE and no RMD at all; and three renames
    only: <live> -> <live>.warm-owner-aside and back, and <live> -> <live>.old-<time> (write_ok, rename_ok).
    Nothing under an aside or .old- name is ever written. The runner's console class checks the same rules again
    before it sends a write.
  - Before a rename a listing taken right then shows the source there and the target not there (the console's
    RNTO replaces an existing target); a listing right after shows it done. If a rename cannot be done, the step
    stops and says so; nothing else is tried in its place.
  - A live folder is renamed aside only after the owner's aside folders were listed again right then and found
    the same as before they moved, so what sits in the live place was put there by this tool or by a test start.
  - An .warm-owner-aside folder that this computer has no note of is never touched: look by hand.
  - The note (what is where, the listings before, every .old- folder) is written on this computer before every
    write on the console.
  - The app must be closed: the runner's own check (no sandbox mounts), the three logs the same size over QUIET
    seconds, and no test-quit lying in the data folder.

Ported from our own night kit's restore tool (22 Nov 2026), in this runner's style; deletes replaced by renames
(23 Nov 2026). Standard library only.
"""
import hashlib
import json
import os
import posixpath
import re
import shutil
import time
from pathlib import Path

ASIDE = ".warm-owner-aside"
OLD = ".old-"  # <live>.old-<YYYYMMDD-HHMMSS>[-n]: a test cache renamed aside, never deleted by the runner
OLD_TAIL = re.compile(r"\.old-\d{8}-\d{6}(-[1-9])?")
NOTE_NAME = "warm-note.json"
LOG_NAME = "warm.log"
QUIET = 20.0  # seconds; the game logs a heartbeat about every 15 s
WHOLE = 4 << 20  # the app's folder: files up to 4 MiB are read back whole
EDGE = 64 << 10  # bigger files: their first and last 64 KiB
SMALL_EVERY = 16  # the driver's folder: one in 16 files under 128 KiB (by sorted path) read back whole
MAC_SPARE = 5 << 30  # a new copy leaves this much free on this computer
OPEN = ("moving", "aside", "returning")  # note states: the owner's folders may not be in their place
NOTHING_LEFT = "no owner cache folder is left aside"


class WarmRefused(Exception):
    """The step did not go ahead. Nothing was written on the console (and anything renamed is back)."""


class WarmFailed(Exception):
    """Something was written on the console and the step did not finish. The note says what is where."""


class WarmNotBack(Exception):
    """The owner's folders were moved and could not be put back. The note says what is where."""


class Unclear(Exception):
    """A listing or read that did not give a clear answer (never taken for "not there")."""


def trees(data):
    data = data.rstrip("/")
    return [("user-cache", f"{data}/user/cache"), ("cache", f"{data}/cache")]


def live_of(path, data):
    """The live cache folder a console path is in (that folder's own path), or None."""
    for _, tree in trees(data):
        if path == tree or path.startswith(tree + "/"):
            return tree
    return None


def write_ok(path, data):
    """MKD and STOR only in a live cache folder (or the folder itself), never under an aside or .old- name."""
    parts = path.split("/")
    return (live_of(path, data) is not None and ASIDE not in path and OLD not in path and ".." not in parts
            and "." not in parts and "" not in parts[1:])


def old_ok(source, target, data):
    """A live cache folder renamed aside to <live>.old-<YYYYMMDD-HHMMSS>[-n], in its own folder. One way only."""
    return (any(source == tree for _, tree in trees(data)) and target.startswith(source)
            and OLD_TAIL.fullmatch(target[len(source):]) is not None)


def rename_ok(source, target, data):
    """The only renames: a live cache folder to its aside name and back, and a live cache folder to an .old- name."""
    return (any((source, target) in ((tree, tree + ASIDE), (tree + ASIDE, tree)) for _, tree in trees(data))
            or old_ok(source, target, data))


def digest(files, dirs):
    text = "\n".join([f"F\t{k}\t{files[k]}" for k in sorted(files)] + [f"D\t{d}" for d in sorted(dirs)])
    return hashlib.sha256(text.encode()).hexdigest()


def counts(files, dirs):
    return {"files": len(files), "dirs": len(dirs), "bytes": sum(files.values()), "digest": digest(files, dirs)}


def human(size):
    for unit in ("bytes", "KiB", "MiB", "GiB"):
        if size < 1024 or unit == "GiB":
            return f"{size:.0f} {unit}" if unit == "bytes" else f"{size:.1f} {unit}"
        size /= 1024


def sha_file(path):
    found = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            found.update(chunk)
    return found.hexdigest()


def _safe_relative(rel):
    parts = rel.split("/")
    return bool(rel) and not rel.startswith("/") and all(p not in ("", ".", "..") for p in parts)


# ---- the copy on this computer

def check_copy(folder, data=None):
    """Every file of the copy there, with its size and SHA-256 as listed, no other file, every folder there.
    (manifest, copy info, {"files", "bytes"}). Raises WarmRefused when anything differs. data: the console's
    data folder; the copy must be of that console's two cache folders."""
    folder = Path(folder)
    try:
        manifest = json.loads((folder / "manifest.json").read_text())
        info = json.loads((folder / "copy.json").read_text())
        listed = (folder / "SHA256SUMS").read_text().splitlines()
    except (OSError, ValueError) as error:
        raise WarmRefused(f"{folder.name} is not a whole-cache copy ({error})") from error
    try:
        sums_file = {line[66:]: line[:64] for line in listed if line.strip()}
        total = {"files": 0, "bytes": 0}
        keys = [key for key, _ in trees(data or "/x")]
        if not set(manifest["trees"]) <= set(keys) or not manifest["trees"]:
            raise WarmRefused(f"{folder.name}: the copy names {sorted(manifest['trees'])}, not user-cache and cache")
        for key, path in (trees(data) if data else [(k, manifest["trees"][k]["path"]) for k in manifest["trees"]]):
            tree = manifest["trees"].get(key)
            if tree is None:
                continue
            if tree["path"] != path:
                raise WarmRefused(f"{folder.name}: the copy's {key} is of {tree['path']}, this console's is {path}")
            root, want, sums = folder / key, tree["files"], manifest["sha256"][key]
            if not all(_safe_relative(rel) for rel in list(want) + list(tree["dirs"])):
                raise WarmRefused(f"{folder.name}: the copy's {key} names a path outside its folder")
            seen = {}
            for dirpath, _, filenames in os.walk(root):
                for name in filenames:
                    full = Path(dirpath) / name
                    seen[full.relative_to(root).as_posix()] = full.stat().st_size
            if seen != want:
                extra, missing = sorted(set(seen) - set(want))[:3], sorted(set(want) - set(seen))[:3]
                sized = sorted(k for k in set(seen) & set(want) if seen[k] != want[k])[:3]
                raise WarmRefused(f"{folder.name}: the copy's {key} differs from its manifest: extra {extra}, "
                                  f"missing {missing}, other size {sized}")
            for d in tree["dirs"]:
                if not (root / d).is_dir():
                    raise WarmRefused(f"{folder.name}: the copy's {key} lacks the folder {d}")
            for rel in sorted(want):
                found = sha_file(root / rel)
                if found != sums.get(rel) or sums_file.get(f"{key}/{rel}") != found:
                    raise WarmRefused(f"{folder.name}: {key}/{rel} does not match its SHA-256")
            if digest(want, tree["dirs"]) != info["digest"][key]:
                raise WarmRefused(f"{folder.name}: the {key} manifest does not match copy.json")
            total["files"] += len(want)
            total["bytes"] += sum(want.values())
        if len(sums_file) != total["files"]:
            raise WarmRefused(f"{folder.name}: SHA256SUMS lists {len(sums_file)} files, the manifest {total['files']}")
    except (KeyError, TypeError, AttributeError) as error:
        raise WarmRefused(f"{folder.name}: the copy's lists are not readable ({error!r})") from error
    return manifest, info, total


class WarmCache:
    def __init__(self, console, data, say, app_open, log_sizes, errors=(), quiet=None, sleep=time.sleep):
        self.console, self.data = console, data.rstrip("/")
        self.say, self.app_open, self.log_sizes = say, app_open, log_sizes
        self.errors = tuple(errors) + (Unclear,)
        self.quiet = QUIET if quiet is None else quiet
        self.sleep = sleep
        self.writes = 0
        self.last_note = None

    @property
    def trees(self):
        return trees(self.data)

    # ---- reading (strict: an error is never "not there")

    def entries(self, folder):
        found = self.console.list(folder)
        if found is None:
            return None
        if not isinstance(found, dict):
            raise Unclear(f"bad listing of {folder}")
        return {name: entry for name, entry in found.items() if name not in (".", "..")}

    def present(self, path):
        folder, name = posixpath.split(path)
        found = self.entries(folder)
        if found is None:
            raise Unclear(f"{folder} cannot be listed")
        return name in found

    def walk(self, path, depth=40):
        """({relative file path: size}, [relative folder paths]) of everything under path."""
        found = self.entries(path)
        if found is None:
            raise Unclear(f"{path} vanished while it was listed")
        files, dirs = {}, []
        for name, entry in sorted(found.items()):
            if "/" in name or name in ("", ".", ".."):
                raise Unclear(f"{path}: a listed name {name!r} is not a plain name")
            mode = entry.get("mode")
            if mode == "d":
                if depth <= 0:
                    raise Unclear(f"{path}/{name}: deeper than 40 folders")
                dirs.append(name)
                sub_files, sub_dirs = self.walk(f"{path}/{name}", depth - 1)
                files.update({f"{name}/{k}": v for k, v in sub_files.items()})
                dirs += [f"{name}/{d}" for d in sub_dirs]
            elif mode == "-":
                size = entry.get("size")
                if not isinstance(size, int) or isinstance(size, bool):
                    raise Unclear(f"{path}/{name} has no size in the listing")
                files[name] = size
            else:
                raise Unclear(f"{path}/{name} has no clear mode in the listing")
        return files, dirs

    def closed(self):
        """(True, "") only when the runner sees no open app, the app's logs keep their size for QUIET s and no
        test-quit is lying in the data folder. Anything unclear counts as open."""
        try:
            if self.app_open():
                return False, "the app is running (its sandbox has its mounts)"
            first = self.log_sizes()
            if not first or not isinstance(first[0], int) or isinstance(first[0], bool):
                return False, "eden_log.txt cannot be read in its folder listing: the app's state is unknown"
            self.sleep(self.quiet)
            second = self.log_sizes()
            if self.app_open():
                return False, "the app is running (its sandbox has its mounts)"
            if first != second:
                return False, f"the app's logs grew ({first} -> {second}) in {self.quiet:g} s: the app is running"
            top = self.entries(self.data)
            if top is None:
                return False, f"{self.data} is not there"
            if "test-quit" in top:
                return False, "a test-quit file is lying in the data folder: the app may be closing right now"
        except self.errors as error:
            return False, f"the app's state is unknown ({error})"
        return True, ""

    def leftovers(self):
        """The .warm-owner-aside folders on the console now."""
        return [tree + ASIDE for _, tree in self.trees if self.present(tree + ASIDE)]

    # ---- writes (every one counted, every one inside the guard)

    def _write(self, writer, what, *paths):
        self.writes += 1
        getattr(writer, what)(*paths)

    def rename(self, writer, source, target):
        if not rename_ok(source, target, self.data):
            raise WarmFailed(f"{source} -> {target} is not a whole-cache rename")
        folder = posixpath.dirname(source)
        found = self.entries(folder)
        if found is None:
            raise Unclear(f"{folder} cannot be listed")
        if posixpath.basename(source) not in found:
            raise WarmFailed(f"{source} is not there")
        if posixpath.basename(target) in found:
            raise WarmFailed(f"{target} is already there: not renaming over it")
        self._write(writer, "rename", source, target)
        found = self.entries(folder)
        if found is None or posixpath.basename(target) not in found or posixpath.basename(source) in found:
            raise WarmFailed(f"the rename {source} -> {target} does not show in the listing")

    def set_old(self, writer, path, note, keep, why):
        """A live cache folder renamed aside whole to <path>.old-<time>, in its own folder: one RNTO on the top name,
        nothing walked, nothing deleted (if the name is a link, only the link moves). The new name goes into the note
        before the rename. Returns the new name, or None when there is no such folder. Raises WarmFailed when the
        rename cannot be done (nothing else is tried in its place)."""
        if path not in [tree for _, tree in self.trees]:
            raise WarmFailed(f"{path} is not a live cache folder: not renaming it")
        folder = posixpath.dirname(path)
        found = self.entries(folder)
        if found is None:
            raise Unclear(f"{folder} cannot be listed")
        name = posixpath.basename(path)
        if name not in found:
            return None
        stamp = time.strftime("%Y%m%d-%H%M%S")
        free = [f"{path}{OLD}{stamp}{tail}" for tail in [""] + [f"-{n}" for n in range(1, 10)]
                if f"{name}{OLD}{stamp}{tail}" not in found]
        if not free:
            raise WarmFailed(f"no free {OLD}{stamp} name for {path}: not renaming it")
        target = free[0]
        entry = {"from": path, "to": target, "why": why, "state": "maybe"}
        note.setdefault("old", []).append(entry)
        keep(note)
        try:
            self.rename(writer, path, target)
        except (WarmFailed,) + self.errors as error:
            raise WarmFailed(f"COULD NOT RENAME {path} ASIDE to {posixpath.basename(target)} ({error}): stopped "
                             "there, nothing deleted") from error
        entry["state"] = "kept"
        keep(note)
        self.say(f"Whole-cache restore: the test cache {path} renamed aside to {posixpath.basename(target)} (kept on "
                 "the console; remove it by hand when you no longer need it)")
        return target

    def old_folders(self):
        """The <live>.old-<time> folders on the console now (reads only), for the summary."""
        found = []
        for _, tree in self.trees:
            folder, name = posixpath.split(tree)
            for entry in sorted(self.entries(folder) or {}):
                if entry.startswith(name + OLD) and OLD_TAIL.fullmatch(entry[len(name):]):
                    found.append(f"{folder}/{entry}")
        return found

    def upload_tree(self, writer, local_root, path, files, dirs, sums):
        """The copy's folder uploaded. Each file is hashed again right before it goes, so a copy that changed on
        this computer after its check is not sent."""
        if self.present(path):
            raise WarmFailed(f"{path} is there before the upload")
        self._write(writer, "mkd", path)
        for d in sorted(dirs, key=lambda x: (x.count("/"), x)):
            self._write(writer, "mkd", f"{path}/{d}")
        for rel in sorted(files):
            if sha_file(local_root / rel) != sums[rel]:
                raise WarmFailed(f"the copy's {rel} changed on this computer after it was checked: not sent")
            self._write(writer, "stor", str(local_root / rel), f"{path}/{rel}")

    def read_back(self, local_root, path, files, app_tree, sums):
        """Byte checks after an upload. The app's folder (a few dozen files): every file up to 4 MiB whole, every
        bigger one its first and last 64 KiB. The driver's folder (thousands of small files): every file from
        128 KiB its first and last 64 KiB, one in 16 of the smaller ones whole. A changed byte in the middle of a
        big file is not seen here; its size is, by the listing."""
        checked = 0
        small = {r: i for i, r in enumerate(r for r in sorted(files) if files[r] < EDGE * 2)}
        for rel in sorted(files):
            size = files[rel]
            spans = []
            if app_tree and size <= WHOLE:
                spans = [(0, size)] if size else []
            elif size >= EDGE * 2:
                spans = [(0, EDGE), (size - EDGE, EDGE)]
            elif size and small[rel] % SMALL_EVERY == 0:
                spans = [(0, size)]
            for offset, length in spans:
                got = self.console.read(f"{path}/{rel}", offset, length)
                if (offset, length) == (0, size):  # a whole file: against the SHA-256 the copy was checked with
                    same = got is not None and hashlib.sha256(got).hexdigest() == sums[rel]
                else:
                    with open(local_root / rel, "rb") as handle:
                        handle.seek(offset)
                        same = got == handle.read(length)
                if not same:
                    raise WarmFailed(f"{path}/{rel}: the bytes at {offset} (+{length}) read back differ from the copy")
                checked += 1
        return checked

    # ---- the owner's folders

    def owner_intact(self, note):
        """(True, "") when each of the owner's aside folders, listed now, is the same as before it moved."""
        if note.get("status") != "aside":
            return False, f"the owner's folders are not noted as aside (status {note.get('status')})"
        for key, tree in note["trees"].items():
            if tree.get("before") is None:
                continue  # the owner had no such folder: nothing to protect
            if tree.get("state") != "aside":
                return False, f"the owner's {key} is noted as {tree.get('state')}, not aside"
            try:
                if not self.present(tree["aside"]):
                    return False, f"{tree['aside']} is not there"
                now = counts(*self.walk(tree["aside"]))
            except self.errors as error:
                return False, f"the owner's {key} cannot be listed ({error})"
            if now["digest"] != tree["before"]["digest"]:
                return False, (f"THE OWNER'S {tree['aside']} DIFFERS FROM BEFORE: {now['files']} files, "
                               f"{now['bytes']} bytes now; {tree['before']['files']} files, "
                               f"{tree['before']['bytes']} bytes before")
        return True, ""

    def set_aside(self, copy_name, keep):
        """Once a batch: the owner's two folders renamed aside, proven unchanged. Returns the note. keep(note) is
        called before every write. Raises WarmRefused (nothing moved, or all of it back again) or WarmNotBack."""
        note = {"what": "whole-cache restore: the owner's cache folders set aside for this batch",
                "copy": copy_name, "status": "checking", "live": "owner", "trees": {}, "restores": []}
        self.last_note = note
        try:
            left = self.leftovers()
        except self.errors as error:
            raise WarmRefused(f"cannot tell what is on the console ({error})") from error
        if left:
            raise WarmRefused(", ".join(left) + " is already there (an earlier run?): the start-up check puts it "
                              "back when this computer has its note; otherwise look by hand")
        ok, why = self.closed()
        if not ok:
            raise WarmRefused(why)
        self.say(f"Whole-cache restore: the app is closed (no mounts, logs still for {self.quiet:g} s, no test-quit)")
        try:
            for key, path in self.trees:
                if self.present(path):
                    before = counts(*self.walk(path))
                    self.say(f"Whole-cache restore: the owner's {path}: {before['files']} files, {before['dirs']} "
                             f"folders, {human(before['bytes'])}")
                else:
                    before = None
                    self.say(f"Whole-cache restore: the owner has no {path}: nothing to set aside there")
                note["trees"][key] = {"path": path, "aside": path + ASIDE, "before": before,
                                      "state": "live" if before else "none"}
        except self.errors as error:
            raise WarmRefused(f"cannot list the owner's caches ({error})") from error
        note["status"] = "moving"
        keep(note)
        try:
            with self.console.warm_writer() as writer:
                for key, tree in note["trees"].items():
                    if tree["before"] is None:
                        continue
                    tree["state"] = "maybe"  # written before the rename: a cut-off run still knows to look
                    keep(note)
                    self.rename(writer, tree["path"], tree["aside"])
                    tree["state"] = "aside"
                    keep(note)
                    self.say(f"Whole-cache restore: the owner's {tree['path']} renamed to "
                             f"{posixpath.basename(tree['aside'])}")
            for tree in note["trees"].values():
                if tree["state"] == "none":
                    tree["state"] = "aside"  # nothing to protect, nothing to move back
            note["status"] = "aside"
            note["live"] = "none"
            note["aside_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            keep(note)
            ok, why = self.owner_intact(note)
            if not ok:
                raise WarmFailed("after the renames: " + why)
        except self.errors + (WarmFailed,) as error:
            self.say(f"Whole-cache restore: setting aside failed ({error}); putting back what moved")
            note["status"] = "aside" if note["status"] == "moving" else note["status"]
            ok, why = self.back(note, keep, check_closed=False)
            if not ok:
                raise WarmNotBack(f"setting aside failed ({error}) and the way back failed: {why}") from error
            raise WarmRefused(f"setting aside failed ({error}); the owner's folders are back") from error
        self.say("Whole-cache restore: the owner's folders are aside, listed again under their aside names: the same "
                 "as before they moved")
        return note

    # ---- before every start

    def restore(self, copy_folder, note, keep):
        """The copy put in place of the live folders (those are renamed aside to .old-<time>, never deleted).
        Returns the record of this restore. Raises WarmRefused
        (nothing written) or WarmFailed (written; the owner's folders are still aside, the note says so)."""
        started = time.monotonic()
        manifest, info, total = check_copy(copy_folder, self.data)
        copy_folder = Path(copy_folder)
        self.say(f"Whole-cache restore: the copy {copy_folder.name} checked against its SHA-256 list: "
                 f"{total['files']} files, {human(total['bytes'])} (made {info.get('made')})")
        ok, why = self.closed()
        if not ok:
            raise WarmRefused(why)
        ok, why = self.owner_intact(note)
        if not ok:
            raise WarmRefused("NOTHING DELETED: " + why)
        self.say("Whole-cache restore: the owner's folders listed again under their aside names: the same as before")
        note["live"] = "partial"
        keep(note)
        moved, uploaded_at = [], None
        writes_before = self.writes
        try:
            with self.console.warm_writer() as writer:
                for key, path in self.trees:
                    target = self.set_old(writer, path, note, keep, "live before a restore")
                    if target:
                        moved.append({"tree": key, "to": target})
                uploaded_at = time.monotonic()
                for key, path in self.trees:
                    tree = manifest["trees"].get(key)
                    if tree is not None:
                        self.upload_tree(writer, copy_folder / key, path, tree["files"], tree["dirs"],
                                         manifest["sha256"][key])
            upload_seconds = time.monotonic() - uploaded_at
            record = {"copy": copy_folder.name, "copy_made": info.get("made"), "set_old": moved, "trees": {}}
            for key, path in self.trees:
                tree = manifest["trees"].get(key)
                if tree is None:
                    if self.present(path):
                        raise WarmFailed(f"{path} is there, the copy has none")
                    continue
                now = counts(*self.walk(path))
                want = counts(tree["files"], tree["dirs"])
                if now["digest"] != want["digest"]:
                    raise WarmFailed(f"{path} after the upload: {now['files']} files, {now['dirs']} folders, "
                                     f"{now['bytes']} bytes; the copy has {want['files']}, {want['dirs']}, "
                                     f"{want['bytes']}")
                now["read_back"] = self.read_back(copy_folder / key, path, tree["files"], key == "user-cache",
                                                  manifest["sha256"][key])
                record["trees"][key] = now
        except self.errors + (WarmFailed, OSError) as error:
            if self.writes == writes_before:
                note["live"] = "test" if note.get("restores") else "none"
                keep(note)
                raise WarmRefused(f"nothing deleted: {error}") from error
            note["why"] = f"a restore stopped after {self.writes - writes_before} writes: {error}"
            keep(note)
            raise WarmFailed(f"the restore stopped after {self.writes - writes_before} writes on the console "
                             f"({error}); the live cache folders are not the copy now") from error
        seconds = time.monotonic() - started
        record.update(ok=True, files=total["files"], bytes=total["bytes"], seconds=round(seconds, 1),
                      upload_seconds=round(upload_seconds, 1),
                      mb_per_s=round(total["bytes"] / 1e6 / max(upload_seconds, 1e-3), 1),
                      at=time.strftime("%Y-%m-%d %H:%M:%S"))
        note["live"] = "test"
        note.pop("why", None)
        note["restores"].append({k: record[k] for k in ("at", "seconds", "files", "bytes")})
        keep(note)
        parts = [f"{k} {v['files']} files, {v['dirs']} folders, {human(v['bytes'])}, {v['read_back']} read back"
                 for k, v in record["trees"].items()]
        self.say(f"Whole-cache restore: the copy {copy_folder.name} is in place: {'; '.join(parts)}; each listing "
                 f"the same as the copy; {seconds:.0f} s")
        return record

    # ---- at the end (and the start-up check)

    def back(self, note, keep, check_closed=True):
        """The owner's folders back in their place, the test folders renamed aside to .old-<time>. (True, "") when
        each owner folder is back and its listing is the one taken before it moved. Moves nothing while the app may be open, and
        nothing when an owner folder is not where the note says, or not as it was."""
        if note.get("status") not in OPEN:
            return True, ""
        if check_closed:
            ok, why = self.closed()
            if not ok:
                note["why"] = f"not put back yet: {why}"
                keep(note)
                return False, note["why"]
        plan = []
        try:
            for key, tree in note["trees"].items():
                before = tree.get("before")
                aside_there, live_there = self.present(tree["aside"]), self.present(tree["path"])
                if before is None:
                    if aside_there:
                        raise WarmFailed(f"{tree['aside']} is there, but the owner had no {tree['path']}: LOOK BY HAND")
                    plan.append((key, "drop_live" if live_there else "none"))
                    continue
                if aside_there:
                    now = counts(*self.walk(tree["aside"]))
                    if now["digest"] != before["digest"]:
                        raise WarmFailed(f"THE OWNER'S {tree['aside']} DIFFERS FROM BEFORE ({now['files']} files, "
                                         f"{now['bytes']} bytes; before {before['files']}, {before['bytes']}): "
                                         "NOTHING MOVED, LOOK BY HAND")
                    plan.append((key, "swap"))
                elif live_there:
                    now = counts(*self.walk(tree["path"]))
                    if now["digest"] != before["digest"]:
                        raise WarmFailed(f"THE OWNER'S {key} IS NOT ASIDE AND {tree['path']} IS NOT HIS "
                                         f"({now['files']} files, {now['bytes']} bytes; his {before['files']}, "
                                         f"{before['bytes']}): NOTHING MOVED, LOOK BY HAND")
                    plan.append((key, "already"))
                else:
                    raise WarmFailed(f"THE OWNER'S {key} IS IN NEITHER PLACE ({tree['path']} nor {tree['aside']}): "
                                     "LOOK BY HAND")
        except self.errors + (WarmFailed,) as error:
            note["why"] = f"nothing moved: {error}"
            keep(note)
            return False, note["why"]
        note["status"] = "returning"
        keep(note)
        try:
            with self.console.warm_writer() as writer:
                for key, what in plan:
                    tree = note["trees"][key]
                    if what in ("swap", "drop_live"):
                        self.set_old(writer, tree["path"], note, keep, "live at the batch end")
                    if what == "swap":
                        tree["state"] = "maybe_back"
                        keep(note)
                        self.rename(writer, tree["aside"], tree["path"])
                    tree["state"] = "back"
                    keep(note)
            lines = []
            for key, tree in note["trees"].items():
                if tree.get("before") is None:
                    if self.present(tree["path"]):
                        raise WarmFailed(f"{tree['path']} is there; the owner had none")
                    lines.append(f"{tree['path']}: none, as before")
                    continue
                now = counts(*self.walk(tree["path"]))
                if now["digest"] != tree["before"]["digest"]:
                    raise WarmFailed(f"{tree['path']} IS BACK BUT ITS LISTING DIFFERS FROM BEFORE: LOOK BY HAND")
                tree["after"] = now
                lines.append(f"{tree['path']} {now['files']} files, {human(now['bytes'])}")
        except self.errors + (WarmFailed, OSError) as error:
            note["why"] = f"stopped on the way back: {error}"
            keep(note)
            return False, note["why"]
        note["status"] = "back"
        note["live"] = "owner"
        note["back_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        note.pop("why", None)
        keep(note)
        self.say("Whole-cache restore: the owner's caches are back: " + "; ".join(lines) +
                 "; each listing the same as before they moved")
        return True, ""

    def recover(self, pending_note, keep):
        """The start-up check of every --go: the owner's folders an earlier, cut-off run left aside go back
        first. (True, text) when there was nothing, or all is back."""
        try:
            left = self.leftovers()
        except self.errors as error:
            return False, f"cannot list the cache folders ({error})"
        if pending_note and pending_note.get("status") in OPEN:
            self.say("Start-up check: the owner's cache folders were left aside by an earlier run; putting back")
            ok, why = self.back(pending_note, keep)
            return ok, ("the owner's caches are back and checked" if ok else why)
        if left:
            return False, (", ".join(left) + " is on the console, and this computer has no note of it: nothing "
                           "says which listing it must have. Nothing was moved. Look by hand: the folder in its "
                           "place is a test cache")
        return True, NOTHING_LEFT


# ---- making a copy (reads only)

def make_copy(cache, folder, extra=None):
    """Both live cache folders downloaded whole into folder/<key>, with manifest.json, SHA256SUMS and copy.json.
    A listing before and one after each must be the same (else the app ran meanwhile). Refuses a folder that is
    there and not empty, and too little room on this computer. cache: a WarmCache (its console needs download)."""
    folder = Path(folder)
    if folder.exists() and any(folder.iterdir()):
        raise WarmRefused(f"{folder.name} is there and not empty: never written over")
    ok, why = cache.closed()
    if not ok:
        raise WarmRefused(why)
    plans = []
    try:
        left = cache.leftovers()
        if left:
            raise WarmRefused(", ".join(left) + " is on the console: the live folders are a test cache, not the "
                              "owner's. Put the owner's back first (--restore-env --go)")
        for key, path in cache.trees:
            if not cache.present(path):
                cache.say(f"Whole-cache copy: {path} is not there: the copy holds no {key}")
                continue
            plans.append((key, path) + cache.walk(path))
    except cache.errors as error:
        raise WarmRefused(f"cannot list the caches ({error})") from error
    if not plans:
        raise WarmRefused("neither cache folder is on the console: nothing to copy")
    need = sum(sum(files.values()) for _, _, files, _ in plans)
    folder.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(folder).free
    if free < need + MAC_SPARE:
        raise WarmRefused(f"this computer has {human(free)} free; the copy needs {human(need)} + {human(MAC_SPARE)}")
    started = time.monotonic()
    trees_out, sums, digests = {}, {}, {}
    try:
        for key, path, files, dirs in plans:
            root = folder / key
            root.mkdir()
            for d in sorted(dirs, key=lambda x: x.count("/")):
                (root / d).mkdir()
            sums[key] = {}
            for rel in sorted(files):
                size, sums[key][rel] = cache.console.download(f"{path}/{rel}", root / rel)
                if size != files[rel]:
                    raise WarmRefused(f"{path}/{rel}: {size} bytes read, the listing says {files[rel]}")
            if digest(*cache.walk(path)) != digest(files, dirs):
                raise WarmRefused(f"{path} changed while it was copied (the app ran?)")
            trees_out[key] = {"path": path, "files": files, "dirs": dirs}
            digests[key] = digest(files, dirs)
            cache.say(f"Whole-cache copy: {path}: {len(files)} files, {len(dirs)} folders, "
                      f"{human(sum(files.values()))}")
    except cache.errors as error:
        raise WarmRefused(f"the copy broke off ({error}); {folder.name} is not a copy") from error
    (folder / "manifest.json").write_text(json.dumps({"trees": trees_out, "sha256": sums}, indent=0))
    lines = [f"{sums[k][r]}  {k}/{r}" for k in sorted(sums) for r in sorted(sums[k])]
    (folder / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    info = dict(extra or {}, made=time.strftime("%Y-%m-%d %H:%M:%S"), digest=digests,
                seconds=round(time.monotonic() - started, 1),
                files=sum(len(t["files"]) for t in trees_out.values()),
                bytes=sum(sum(t["files"].values()) for t in trees_out.values()))
    (folder / "copy.json").write_text(json.dumps(info, indent=1))
    return info


def cache_line(use, record, boot_text):
    """The caches line of a start that had the whole cache put back first."""
    moved = (f"Caches: the whole cache put back before this start from the copy {record['copy']} "
             f"({record['files']} files, {human(record['bytes'])}; each folder's listing the same as the copy, "
             f"{sum(t['read_back'] for t in record['trees'].values())} files read back)")
    return f"{moved}. Boot log: {boot_text(use)}"


def cache_short(use, record, boot_text):
    return f"whole cache put back from {record['copy']}; boot log: {boot_text(use)}"
