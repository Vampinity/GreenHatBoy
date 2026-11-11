import json,re,statistics as st,collections,os
def corr(a,b):
    ma,mb=st.mean(a),st.mean(b); sa=sum((x-ma)**2 for x in a)**.5; sb=sum((y-mb)**2 for y in b)**.5
    return sum((x-ma)*(y-mb) for x,y in zip(a,b))/(sa*sb) if sa and sb else 0
D=json.load(open(os.environ['CLAUDE_JOB_DIR']+"/tmp/topsight/data.json"))
G=re.compile(r'EDEN_GPU_TIME wall_ms=([\d.]+) busy_ms=([\d.]+) submissions=(\d+) max_ms=([\d.]+)')
res=collections.defaultdict(list); used=[]
for run,r in D.items():
    f=r['dir']+'logs/stderr.log'
    if not os.path.exists(f) or not r['win']: continue
    g=[(float(m[1]),float(m[2]),int(m[3]),float(m[4])) for m in G.finditer(open(f,errors='ignore').read())]
    if len(g)<10: continue
    W=r['win']; best=(1.0,len(W)-len(g))
    used.append((run,round(best[0],2),best[1])); off=best[1]
    for k in range(len(g)):
        j=k+off
        if not 0<=j<len(W): continue
        w=W[j]
        if w['fps']>=45 or w['frames']<40: continue
        reg='L' if w['fence']<1 else ('M' if w['fence']<5 else 'H')
        res[reg].append((w['fps'],g[k][1]/g[k][0]*100,g[k][1]/w['frames'],g[k][2]/w['frames'],g[k][3],run))
json.dump({k:v for k,v in res.items()},open(os.environ['CLAUDE_JOB_DIR']+"/tmp/topsight/gpu.json","w"))
print("runs aligned:",len(used), used[:5])
for reg in "LMH":
    v=res[reg]
    if v: print(f"{reg}: n={len(v)} runs={len(set(x[5] for x in v))} fps {st.mean(x[0] for x in v):.1f} | GPU busy {st.mean(x[1] for x in v):.0f}% | GPU ms/frame {st.mean(x[2] for x in v):.1f} (p90 {sorted(x[2] for x in v)[int(len(v)*.9)]:.1f}) | submissions/frame {st.mean(x[3] for x in v):.1f} | longest submission med {st.median(x[4] for x in v):.1f} ms")
