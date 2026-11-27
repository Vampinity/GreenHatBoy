"""Turn EglantinePS5 core switches on or off through env.txt in both app folders.

Usage: set-env.py NAME=VALUE [NAME=VALUE ...]   writes env.txt
       set-env.py --off                         renames env.txt to env.txt.off
The app reads env.txt once, when its process starts (headless/main.cpp), so it takes effect at the
next start of the app. Nothing here touches the app's own files.
"""
import ftplib, io, json, os, sys, urllib.request

sys.path.insert(0, str(os.path.dirname(os.path.abspath(__file__))))
import runner_config  # noqa: E402  every per-person setting comes from runner-config.json

CFG = runner_config.load()
HOST, PORT = runner_config.host(), runner_config.ftp_port()
WEB = runner_config.web()
TARGETS = list(CFG["app"]["env_folders"])  # settings: app.env_folders


def names(folder):
    with urllib.request.urlopen(f"{WEB}{folder}?fmt=json", timeout=30) as r:
        return {e["name"] for e in json.load(r)}


def read(path):
    with urllib.request.urlopen(WEB + path, timeout=30) as r:
        return r.read()


entries = sys.argv[1:]
if not entries:
    sys.exit(__doc__)
off = entries == ["--off"]
if not off and any("=" not in e or e.startswith("=") for e in entries):
    sys.exit("each switch must be NAME=VALUE")

f = ftplib.FTP()
f.connect(HOST, PORT, timeout=60)
f.login()
f.encoding = "utf-8"
f.voidcmd("TYPE I")
text = ("\n".join(entries) + "\n").encode()
for folder in TARGETS:
    if off:
        if "env.txt" in names(folder):
            f.rename(f"{folder}/env.txt", f"{folder}/env.txt.off")
        print(folder, "env.txt present:", "env.txt" in names(folder))
        continue
    f.storbinary(f"STOR {folder}/env.txt.new", io.BytesIO(text))
    if read(f"{folder}/env.txt.new") != text:
        sys.exit(f"staged env.txt does not match in {folder}, nothing replaced there")
    f.rename(f"{folder}/env.txt.new", f"{folder}/env.txt")
    print(folder, "env.txt:", read(f"{folder}/env.txt").decode().split())
f.quit()
