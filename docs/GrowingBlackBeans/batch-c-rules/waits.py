"""The batch D decision, from batch C's run (Vampinity, 25 Nov: "D only if C's waits probe shows active waits").

    python3 -I waits.py PKG          reads runM1C-29-PROBE and batch C's controls at PKG's top level

Per wait (the four in batch D's box: guest-write, JIT commit, new-handler, block wait trim):
- guest-write (fault) waits need EDEN_UP_FAULT_LOG: counted in the probe only (EDEN_UP_FAULT_WAIT end lines, their ms);
- JIT commit and new-handler waits print without it: counted in the probe and in every C control;
- block wait trim has no line: it acts inside a guest-write wait, so it is active when the probe shows guest-write waits.
A wait seen at least once gets an arm in batch D; a wait never seen in the probe and the 12 controls gets none, and is
reported as "never acted on this route (handheld, field)". Counting as in split-check/waits.py (22 Nov).
"""
import pathlib, re, sys, collections
P = pathlib.Path(sys.argv[1]).expanduser()
def lines(d):
    L = []
    for n in ('stderr.log', 'eden_log.txt'):
        f = d / n
        if f.exists(): L += f.read_text(errors='replace').splitlines()
    return L
def count(L):
    W = [l for l in L if l.startswith('EDEN_UP_FAULT_WAIT end')]
    ms = [int(x) for l in W for x in re.findall(r'waited_ms=(\d+)', l)]
    th = collections.Counter(x for l in L if l.startswith('EDEN_UP_FAULT_WAIT start') for x in re.findall(r'thread=(\S+)', l))
    return dict(fault=len(W), fault_threads=dict(th), fault_max_ms=max(ms) if ms else 0, fault_over_2000=sum(x > 2000 for x in ms),
                jit=sum('JIT code cache: no memory for its next part' in l for l in L),
                new=sum(bool(re.search(r'EDEN_UP_NEW_WAIT_MS.*(waits|begun|gave)', l)) for l in L))
probe = P / 'runM1C-29-PROBE'
assert (probe / 'stderr.log').exists(), 'the probe has not come back yet'
pr = count(lines(probe)); print('probe', pr)
ctl = [count(lines(d)) for d in sorted(P.glob('runM1C-*-C*')) if (d / 'stderr.log').exists()]
print(f'{len(ctl)} controls: jit', [c['jit'] for c in ctl], 'new', [c['new'] for c in ctl])
seen = {'guest-write wait': pr['fault'] > 0, 'JIT commit wait': pr['jit'] + sum(c['jit'] for c in ctl) > 0,
        'new-handler wait': pr['new'] + sum(c['new'] for c in ctl) > 0, 'block wait trim': pr['fault'] > 0}   # it acts only inside a guest-write wait (guest_memory_service.inc:1851): no line of its own
for k, v in seen.items(): print(f'{k:18}', 'ACTIVE: an arm in batch D' if v else 'never seen: no arm ("never acted on this route")')
print('batch D:', sum(seen.values()), 'arms' if any(seen.values()) else '(not run)')
