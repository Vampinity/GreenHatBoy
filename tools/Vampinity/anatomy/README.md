# Anatomy readers

These are the small readers behind my boxes on the four coverage maps:

- `docs/img/coverage-frame-vampinity.png`
- `docs/img/coverage-hitches-vampinity.png`
- `docs/img/coverage-memory-wall-vampinity.png`
- `docs/img/coverage-flashes-crashes-vampinity.png`

They use the same layout and colours as GrowingBlackBeans' maps. A box with a + moved up one step from my data.

Every reader takes the logs of one start: `eden_log.txt` and `stderr.log`, plain or `.gz`, the way they sit in `runs/`. You need Python 3 and nothing else. The one-line commands at the bottom need `zgrep` and `awk`, which come with macOS and Linux.

**What my numbers are.** Most come from builds T185 to T188, with frame ahead off and the load window on, on the scripted route from the field to the area after it. The exceptions: the transitions box (T122, T126) and Hitches: Other areas are from older builds, Other kinds counts crashes over all my builds, and Crash rate is hand play on T186. The T185 to T188 starts (run1548 and later) are not in `runs/`. The readers also run on the starts that are there, for example `2026-11-14-run1470` to `run1472`, so you can try them.

Some boxes without a + keep GrowingBlackBeans' colour but carry my label, because my data reads differently there: Area loads, Unexplained, Load seconds, Two ahead, Read sync, 40 ms cap and All writes. Two ahead stays grey: my only counts there are cloth blinks from 3 starts with frame ahead on (14 Nov, T179 and T184), which is another meter than the flash counter.

## The readers

| Reader | What it answers | Run it | Box it fills |
|---|---|---|---|
| `ht_split.py` | Splits the GPU thread's long frames (100 ms or more) into before the load, inside it and after it. Gives their ms, how much of that has a name, and the biggest named kinds. Needs `EDEN_UP_HITCH_TRACE=1`. | `python3 ht_split.py eden_log.txt 205.6 247.6` | Hitches: Inside a load. Also the numbers behind my notes on Area loads and Unexplained. |
| `memmap.py` | Finds the moment after the load when the largest free block is smallest, and shows who holds the memory then: guest, GPU blocks, heap, JIT, tables. Also gives the highest `target=` (render targets) after the load and the longest reclaim stretch. | `python3 memmap.py runs/Vampinity --glob '2026-11-14-run147*/stderr.log.gz'` | Memory: Holder table, Render targets. The stretch column helps with The 10 s block wait. |
| `frame_split.py` | Splits the frame of a window into the game's own part, the back thread's busy and idle time, the time the front waits for the back, and ring words a frame. | `python3 frame_split.py eden_log.txt 110 185 66` | Frame: Other areas (the field walk). |
| `crash_census.py` | Lists every crash report under a folder with its kind, thread, reason line, request size and time into the session. Writes `crashes.csv` and `crash-census.md`. | `python3 crash_census.py --runs runs --output-dir /tmp/census` | Crashes: Other kinds. |

GrowingBlackBeans' `tools/GrowingBlackBeans/eglog` (`eglog.py`, `anatomy.py`) reads the same "GPU split per second" and texture cache lines with more options. `frame_split.py` is here because it is the exact cut behind my Other areas numbers: the game's part is the frame minus the time blocked on present.

The two times for `ht_split.py` are app seconds, the stamp at the start of each `eden_log.txt` line: when the load starts and when it ends. The example times are from one of my starts (run1621). For `frame_split.py` the times are the window, and the last number leaves out rows with a mean frame over that many ms. `memmap.py` finds the load by the route's `wait_met line=92` mark: line 92 of `tools/Vampinity/routes/field-to-past-field.txt` is the wait for the field load to start. Use `--load-line` for another route.
Add `--json` to `ht_split.py`, `memmap.py` or `frame_split.py` to get the same numbers as one JSON object on stdout, for other scripts to read.

About `crash_census.py`:

- It was written for me by Codex. I checked it against 6 crash reports, and kind, thread, reason, place in the code and time matched in all 6. An earlier check of 18 reports and one freeze matched on kind in all 19.
- It reads only. It writes its two output files to `--output-dir`. Keep that outside `runs/`.
- `--self-test` makes and removes test files next to the script.
- Its "CPU JIT fault" kind means "SIGSEGV in a CPU core thread outside the game's code". In my 164 crashes, all 36 of those came with the largest free block at 0 to 2 MiB. So most are the memory wall, not a JIT bug.
- It knows the place only from the script name, not from where the game was.

## One-line counts

These boxes need no script. Each command reads one start: run it inside the start's folder. `stderr.log*` and `eden_log.txt*` match the plain file and the `.gz` one in `runs/`, and `zgrep` reads both.

**Memory waits** (Hitches): how many times game threads waited for memory, the longest wait, and the total per thread.

```sh
zgrep -h 'EDEN_UP_FAULT_WAIT end' stderr.log* | awk '{delete v; for(i=1;i<=NF;i++){split($i,a,"=");v[a[1]]=a[2]} n++; w=v["waited_ms"]+0; if(w>m)m=w; s[v["thread"]]+=w} END{printf "waits=%d longest_ms=%d by thread:",n,m; for(t in s)printf " %s=%.1fs",t,s[t]/1000; print ""}'
```

**Hitches by place** (Hitches): presents over 100 ms before the load starts and after it ends. Put in the same two times as for `ht_split.py`.

```sh
zgrep -h 'presents: frame' eden_log.txt* | awk -v ls=205.6 -v le=247.6 -F'[][]' '{t=$2+0; if (match($0,/, [0-9]+ over 100 ms/)) {n=substr($0,RSTART+2,RLENGTH-2)+0; if(t<=ls)b+=n; else if(t>le)a+=n}} END{print "before_load="b, "after_load="a}'
```

**Guest memory** (Memory): the most packed guest memory still held in the pool, in MiB. Census `guest=` counts these pages too, so `guest=` minus `held=` is the part that is not packed.

```sh
zgrep -ho 'EDEN_SWAP_PACK .*held=[0-9]*MiB' stderr.log* | sed -E 's/.*held=([0-9]+)MiB/\1/' | sort -n | tail -1
```

**The 10 s block wait** (Memory): reclaim stretches of 10 s or more with 0 passes and a waiter left unserved. Older starts in `runs/` may not have this line at all (run1470 has none).

```sh
zgrep -h 'EDEN_UP_WAIT_RECLAIM totals' stderr.log* | grep -E 'stretch_ms=[1-9][0-9]{4,} .*passes=0 .*unserved=1'
```

**Textures, uploads** (Frame): the texture cache's own lines, once every 600 frames. Divide by 600 for a frame.

```sh
zgrep -hE 'Texture cache last 600 frames: ([0-9]+ uploads|created)' eden_log.txt*
```

## Boxes with no reader here

Some boxes came from notes and hand counts, not from a reader:

- Hitches: Other areas, Load seconds.
- Memory: the transitions box.
- Crashes: Crash rate (3 crashes in about 2 hours of hand play on one build).
- Flashes: the Two ahead label. The cloth blinks were counted on screen recordings with frame ahead on, not logs, and that reader is not in this folder.
