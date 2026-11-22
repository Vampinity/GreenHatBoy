"""Copy the game's save off the console. Reading only. Usage: backup-save.py <name>"""
import sys
import json,os,urllib.request,urllib.parse
sys.path.insert(0, str(os.path.dirname(os.path.abspath(__file__))))
import runner_config  # noqa: E402  every per-person setting comes from runner-config.json
WEB=runner_config.web()
SAVE=runner_config.save_dir()  # settings: game.save_dir, ends in <profile folder>/<title>
DEST=str(runner_config.folder("save_backups"))  # settings: folders.save_backups
def ls(p):
    with urllib.request.urlopen(f"{WEB}{p}?fmt=json",timeout=30) as r:
        return [e for e in json.load(r) if e['name'] not in ('.','..')]
def copy(src,dst):
    os.makedirs(dst,exist_ok=True)
    n=b=0
    for e in ls(src):
        s=src+'/'+e['name']; d=os.path.join(dst,e['name'])
        if e['mode']=='d':
            a,c=copy(s,d); n+=a; b+=c
        else:
            with urllib.request.urlopen(WEB+urllib.parse.quote(s),timeout=60) as r: data=r.read()
            if len(data)!=e.get('size',len(data)): raise SystemExit(f"short read {s}")
            open(d,'wb').write(data); n+=1; b+=len(data)
    return n,b
name=sys.argv[1]
print(name,copy(SAVE,os.path.join(DEST,name)))
