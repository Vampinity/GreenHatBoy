#!/usr/bin/env python3
"""Lint auto-run scripts for timing mistakes (9 Nov: two scripts were written with deltas).
Rules (test_harness.h): a section starts after each WAIT/MAYBE; its times are absolute seconds since that WAIT
was met; presses timed at or after END are dropped, presses not yet started when the next WAIT is met are dropped,
and ANY non-blank line after END in the file makes the app refuse the whole script (test_harness.h:485-503).
Flags: lines after END (fatal), presses at/after END (dropped), start times out of order within a section (the
parser re-sorts them: the clearest sign of deltas), and 3+ presses sharing one start time. Usage: lint-scripts.py [files...] (default: every
*.txt script with WAIT lines next to this file, and in its overnight/ and auto-run-tests/ subfolders if you keep such).
Reads files only: it never talks to a console."""
import sys, glob, os, collections
AFTER_END = {}
def sections(path):
    secs=[[]]; ended=None; AFTER_END[path]=[]
    for n,l in enumerate(open(path, errors='replace'),1):
        s=l.split('#',1)[0].strip()
        if not s: continue
        if ended is not None: AFTER_END[path].append(n); continue
        p=s.split()
        try: t=float(p[0])
        except ValueError: continue
        kind=p[1] if len(p)>1 else '?'
        secs[-1].append((t,kind,n))
        if kind=='END': ended=n
        if kind in ('WAIT','MAYBE','STEER'): secs.append([])  # STEER ends its section as a WAIT does
    return secs
def lint(path):
    probs=[]
    secs=sections(path)
    if AFTER_END[path]: probs.append('FATAL: line(s) %s come after END; the app refuses the whole script'%','.join(map(str,AFTER_END[path][:6])))
    for i,sec in enumerate(secs):
        presses=[(t,k,n) for t,k,n in sec if k not in ('WAIT','MAYBE','END','STEER')]
        ends=[t for t,k,n in sec if k=='END']
        if ends:
            e=min(ends); late=[n for t,k,n in presses if t>=e]
            if late: probs.append('section %d: %d press(es) at or after END %.1f s are dropped (lines %s)'%(i,len(late),e,','.join(map(str,late[:6]))))
        order=[t for t,k,n in sec if k not in ('WAIT','MAYBE','STEER')]
        if any(b<a for a,b in zip(order,order[1:])): probs.append('section %d: start times go backwards (the harness re-sorts them; written as deltas?)'%i)
        c=collections.Counter(t for t,k,n in presses if k!='MAYBE')
        dup=[(t,m) for t,m in c.items() if m>=3]
        if dup: probs.append('section %d: %s presses share one start time (written as deltas?)'%(i,', '.join('%d at %.1f s'%(m,t) for t,m in dup)))
    return probs
files=sys.argv[1:] or sorted(set(f for pat in [os.path.join(os.path.dirname(os.path.abspath(__file__)),p) for p in ('overnight/*.txt','auto-run-tests/*.txt','*.txt')] for f in glob.glob(pat)
        if 'WAIT' in open(f,errors='replace').read() and not f.endswith('.bad-deltas')))
bad=0
for f in files:
    pr=lint(f)
    if pr: bad+=1; print(f); [print('   ',x) for x in pr]
print('%d of %d scripts flagged'%(bad,len(files)))
sys.exit(1 if bad else 0)
