import re,os,json,sys,glob,collections
pkg=os.path.expanduser("~/Desktop/work/EglantinePS5-package")
dirs=[l.strip() for l in open(sys.argv[1])]
TS=re.compile(r'^\[\s*([\d.]+)\]')
FPS=re.compile(r'nx2:vi2 5 s: (\d+) frames, ([\d.]+) fps, mean ([\d.]+) ms, 1% low ([\d.]+) ms, worst ([\d.]+) ms, fence ([\d.]+) ms')
SPLIT=re.compile(r'GPU split per second: back idle ([\d.]+) ms, (\d+) ring words, front waited ([\d.]+) ms(.*)')
FIELD=re.compile(r'([a-z][a-z \-]+?) ([\d.]+) ms \((\d+)/s, longest ([\d.]+) ms\)')
out={}
for d in dirs:
    run=os.path.basename(d.rstrip('/'))
    env={}
    if os.path.exists(d+'env.txt'):
        for l in open(d+'env.txt',errors='ignore'):
            l=l.strip()
            if l and not l.startswith('#') and '=' in l:
                k,v=l.split('=',1); env[k.strip()]=v.strip()
    win=[]; split=[]; events=collections.defaultdict(list); build=None
    for l in open(d+'eden_log.txt',errors='ignore'):
        m=TS.match(l)
        if not m: continue
        t=float(m[1])
        f=FPS.search(l)
        if f:
            win.append(dict(t=t,frames=int(f[1]),fps=float(f[2]),mean=float(f[3]),low=float(f[4]),worst=float(f[5]),fence=float(f[6]))); continue
        s=SPLIT.search(l)
        if s:
            rec=dict(t=t,back_idle=float(s[1]),ring=int(s[2]),front_waited=float(s[3]))
            for fm in FIELD.finditer(s[4]):
                rec[fm[1].strip()]=float(fm[2]); rec[fm[1].strip()+'#']=int(fm[3])
            split.append(rec); continue
        if 'pipeline built on the GPU thread' in l:
            ms=re.search(r'in ([\d.]+) ms',l); events['pipe'].append((t,float(ms[1]) if ms else 0))
        elif 'OoT resource poll backoff' in l:
            w=re.search(r'avg walk (\d+) us',l); n=re.search(r'(\d+) walks in',l)
            events['poll'].append((t,int(n[1])*int(w[1])/1000/10 if w and n else 0))
        elif 'Native zstd:' in l:
            mm=re.search(r'(\d+) calls .*?(\d+) MiB decompressed on the host in (\d+) ms',l)
            if mm: events['zstd'].append((t,int(mm[1]),int(mm[2]),int(mm[3])))
        elif 'ASTC GPU decodes' in l:
            mm=re.search(r'(\d+) in',l); events['astc'].append((t,int(mm[1]) if mm else 0))
        elif 'VMA heap 1: usage' in l:
            mm=re.search(r'usage (\d+) MiB of budget (\d+) MiB',l); events['vma'].append((t,int(mm[1]),int(mm[2])))
        elif 'Buffer cache:' in l and 'buffers' in l:
            mm=re.search(r'(\d+) buffers (\d+) MiB',l); events['bufcache'].append((t,int(mm[1]),int(mm[2])))
        elif 'diagnostic build' in l and build is None:
            pass
    bt=d+'logs/boot-trace.txt'
    if os.path.exists(bt):
        mm=re.search(r'diagnostic build ([\d.]+)',open(bt,errors='ignore').read()); build=mm[1] if mm else None
    out[run]=dict(dir=d,env=env,build=build,win=win,split=split,events=dict(events))
json.dump(out,open(sys.argv[2],'w'))
print(len(out),"runs;", sum(1 for r in out.values() if r['win']),"with windows;", sum(1 for r in out.values() if r['split']),"with split stats")
