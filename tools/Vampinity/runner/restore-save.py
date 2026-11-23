"""Make the game's saves on the console match a backup. Stops if the app is open. Usage: restore-save.py <backup folder>

Slots that aren't in the backup are MOVED OUT of the game's save folder, because Continue loads the newest slot and
a test's autosave would otherwise decide where the next test starts. Back up your own save first (backup-save.py)
and put it back when the tests are done.

Moved out, not deleted (23 Nov 2026): each such slot folder is renamed, with one rename of the folder itself, to
<data_dir>/old-save-slots/<title>-<YYYYMMDD-HHMMSS>-<slot>: out of the emulator's save tree (user/nand/...), so
neither the emulator nor the game should look there (not yet tried on a console). The folder is made once if it is
not there. Nothing in a slot is walked or deleted. websrv's listings follow links (src/fs.c stats through them), so a
slot that is a link to a folder would list as a folder, and deleting what is listed inside it would delete what
the link points at. A rename moves only the link. The old slots stay on the console: remove them by hand when you
no longer need them (the last line names them)."""
import ftplib, hashlib, json, os, posixpath, sys, time, urllib.parse, urllib.request
sys.path.insert(0, str(os.path.dirname(os.path.abspath(__file__))))
import runner_config  # noqa: E402  every per-person setting comes from runner-config.json
CFG = runner_config.load()
HOST, PORT = runner_config.host(), runner_config.ftp_port()
WEB = runner_config.web()
DEST = runner_config.save_dir()  # settings: game.save_dir (your own profile folder; never post it)
APP, DATA = CFG["app"]["id"], CFG["app"]["data_dir"].rstrip("/")
src = sys.argv[1]
def ls(p):
    with urllib.request.urlopen(f"{WEB}{p}?fmt=json", timeout=30) as r:
        return [e for e in json.load(r) if e["name"] not in (".", "..")]
# A running app's sandbox holds data, mnt and preinst; a closed one stays behind as an empty entry.
# After a crash restart ShadowMount stops tracking the app and every later sandbox keeps its mounts until a reboot,
# so a mounted entry alone can't tell. Then the app's own log decides: if eden_log.txt doesn't grow over 6 s, the
# app is idle or closed; if it grows, nothing is written.
def log_size():
    return [e["size"] for e in ls(f"{DATA}/user/log") if e["name"] == "eden_log.txt"]
if [e for e in ls("/mnt/sandbox") if e["name"].startswith(APP) and ls(f"/mnt/sandbox/{e['name']}")]:
    before = log_size(); time.sleep(6)
    if log_size() != before:
        sys.exit("EglantinePS5 is open, nothing written")
f = ftplib.FTP(); f.connect(HOST, PORT, timeout=60); f.login(); f.encoding = "utf-8"; f.voidcmd("TYPE I")
n = 0
for root, dirs, files in os.walk(src):
    rel = os.path.relpath(root, src)
    target = DEST if rel == "." else f"{DEST}/{rel}"
    if rel != ".":
        try: f.mkd(target)
        except ftplib.error_perm: pass
    for name in files:
        if name.startswith("."): continue
        path = os.path.join(root, name)
        with open(path, "rb") as h: f.storbinary(f"STOR {target}/{name}", h)
        with urllib.request.urlopen(WEB + urllib.parse.quote(f"{target}/{name}"), timeout=60) as r: back = r.read()
        if hashlib.sha256(back).digest() != hashlib.sha256(open(path, "rb").read()).digest():
            sys.exit(f"copy differs: {target}/{name}")
        n += 1
gone = []
TITLE = posixpath.basename(DEST.rstrip("/"))
ASIDE_DIR = f"{DATA}/old-save-slots"  # outside the emulator's save tree; made once, never emptied by this tool
STAMP = time.strftime("%Y%m%d-%H%M%S")
extra = [e["name"] for e in ls(DEST)
         if e["name"].startswith("slot_") and not os.path.isdir(os.path.join(src, e["name"]))]
if extra:
    top = {e["name"]: e for e in ls(DATA)}
    if "old-save-slots" not in top:
        f.sendcmd(f"MKD {ASIDE_DIR}")  # any 2xx; the listing right after is the proof
        top = {e["name"]: e for e in ls(DATA)}
    if top.get("old-save-slots", {}).get("mode") != "d":
        sys.exit(f"{ASIDE_DIR} is not a folder: nothing moved; {extra} left in place")
    there = {e["name"] for e in ls(ASIDE_DIR)}
    for name in extra:
        aside = f"{TITLE}-{STAMP}-{name}"
        if aside in there:
            sys.exit(f"{ASIDE_DIR}/{aside} is already there: nothing renamed over it; {name} is left in place")
        # One rename of the slot folder itself (RNFR/RNTO; ftpsrv answers 226): nothing inside is walked or
        # deleted, and a slot that is a link moves as the link.
        f.rename(f"{DEST}/{name}", f"{ASIDE_DIR}/{aside}")
        there.add(aside)
        gone.append(f"{ASIDE_DIR}/{aside}")
    if not {posixpath.basename(g) for g in gone} <= {e["name"] for e in ls(ASIDE_DIR)}:
        sys.exit(f"the slots moved aside do not show in {ASIDE_DIR}: {gone}")
left = sorted(e["name"] for e in ls(DEST) if e["name"].startswith("slot_"))
wanted = sorted(d for d in os.listdir(src) if d.startswith("slot_"))
if left != wanted:
    sys.exit(f"slots left {left}, wanted {wanted}")
f.quit(); print("restored and verified", n, "files from", os.path.basename(src), "slots now", left,
               "moved aside (kept on the console, remove by hand):", gone or "none")
