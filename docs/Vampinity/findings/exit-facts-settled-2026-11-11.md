# Forest exit, 11 Nov: what is settled (checked several times)

> **Found:** There is no forest-exit crash on T120 in the evidence: the owner's hand sessions were closed by hand (seen on video), and the one proven crash was on T121 in a later area after a pause-menu visit.
>
> **So:** Quote no forest-exit crash; earlier notes that said otherwise are corrected in the list at the end.

Written 2026-11-11. Sources: three independent checks (logs, video, comment) with their scratch in
(working files, not kept)
(`logs/`, `video/`, `comment/`), plus my own look at the primary files listed below. READ = seen in a file or a video
frame (file, line or video time given). INFERRED = my reading. Place names are the neutral set (hill, ravine, tunnel,
village, passage, next area, overlook, field).

**Short answer to the disagreement.** The audit is right and the steer note is wrong: none of the owner's T120 hand
sessions crashed. Both "session 1" and "session 2" end with the PS5 control centre, the app's options menu with
"Close App", then "Closing…" on screen (READ: `video/h0537/win150/sheet_01.jpg` row 4-5 for try 1, video 159-162 s;
`video/h0537/win392/sheet_01.jpg` rows 5-6 for try 2, video ~403-406 s; I opened both sheets myself). The log check could not tell from logs alone (no crash file, no failure line, but also no orderly shutdown line, which no
hand session has, not even the agreed close at 06:07). The video closes that gap. The audit called the closes
"inferred"; they are READ on screen. Only the button press itself is not visible (PS-button presses are not recorded).

## 1. Sessions and runs

Build: version string is 01.219.028 in all; build date Nov 11 02:48:21 = T120, 05:23:12 = T121 (READ in stderr;
the T-name mapping is INFERRED from batch names and project log:507).

| Session / run | Build | How far it got | How it ended | Evidence | Confidence |
|---|---|---|---|---|---|
| hand-20261111-0537 try 1 (pid 389, "session 1") | T120 | hill → ravine → tunnel → village → passage (803.7,822.2 at video 135 s); saved; talk from ~148 s. Never west of x 801.8: **no area change** | **Closed by the owner** during the talk (control centre 159 s, Close App 161 s, "Closing…" 162 s) | READ: `video/h0537/win150/sheet_01.jpg`, `video/h0537/minimap.txt`; no crash file (crash-index jumps 004408 → 060219); RADV low 16 MiB at t_s 138, back to 212 MiB at t_s 151 (`stderr.prev.log` L1045, L1131-1132) | high |
| hand-0537 try 2 (pid 390, "session 2") | T120 | from the passage save: talk, into the passage 294-301 s, short black 302.5 s (forest minimap ends), long black with load icon 341.7-354.9 s, misty path in the next area to 403 s. **Crossed** | **Closed by the owner** (control centre ~403 s, Close App ~405 s, "Closing…" ~405.5 s) | READ: `video/h0537/win296`, `win336`, `win392` sheets; no crash file. Pool largest free 2 MiB at the end (`stderr.log` L1337), but no failure line | high |
| hand-0547 (pid 391) | T120 | village lap only; never at the passage (never west of x 812) | **Closed by the owner** (Close App ~248.5 s, "Closing…" ~249.5 s) | READ: `video/h0547/win238/sheet_01.jpg`; no eden_log exists | high |
| hand-0554 (pid 392) | T121 + 3 memory lines | passage, crossed (~108 s short black, 147-160.5 s long black), next area, overlook scene ~240-325 s, a pause-menu visit ~355-365 s, then on the **field** with the field minimap (949.6-950.2, 889-890.4 at video 369-389 s) | **CRASH**: glitches 378.5/380.5 s, frozen picture 381.4-389.7 s, black, then launcher "EglantinePS5 stopped because of an error … crash-20261111-060219.txt" from ~394.5 s | READ: `video/h0554/sheet5_05.jpg` (I opened it: field with minimap, then the launcher error), `detect.txt` freeze 381.38-389.72; `crash-20261111-060219.txt` std::bad_alloc, thread am:1, largest free 2 MiB, heap 1984 MiB; stderr "EDEN_HEAP_FAILURE requested=463328" | high |
| hand-0607 (pid 394) | T120 | passage, crossed (short black 108.75 s, long black 149.75-166 s), misty path, field title card 220-232 s, overlook scene starts 234 s | **Closed by the owner** (Close App, "Closing…" ~238 s) | READ: `video/h0607/win222`, `sheet5_03.jpg`; project log:512 agrees | high |
| run1067 exit-census (batch auto-20261111-074053-batch-exit-census-t120) | T120 | hill → ravine → tunnel → village; stands by a tree at 834.9,824.4 from ~175 s. Never west of x ~832. **No area change** | Orderly script end (script_done at 181.995, then "shutdown: Stopping the game … CloseServices") | READ: run1067 stderr L1934+, eden_log SetTerminateResult @224.66; minimap paths `comment/p1067.txt`, `video/r1067/` | high |
| run1068 field-census (batch auto-20261111-075937-batch-field-census-t120) | T120 | from the passage: crossed (short blacks 129.2/132.1 s, long black 167.1-181.25 s), next area, overlook edge 215-245 s, then against a rock; **never on the field** (no field title card, no field minimap) | Orderly time-limit stop (result "time_limit", script_done 401.964, full shutdown lines) | READ: run1068 stderr L4835+, `video/r1068/sheetlast_02.jpg`, `comment/p1068.txt` | high |

Two blacks per crossing (READ, timing): a ~1 s black right after the passage, where the forest minimap ends, and a
13-16 s black with a load icon about 40 s later. Anything labelled "at the area change" should say which one.

## 2. Real crashes on 11 Nov that we can prove

1. **06:02:19, hand-0554, T121 + EDEN_NX2_RT_EVICT_PRESSURE=1, EDEN_NX2_GRAPHICS_PIPELINE_OOM_RETRY=1,
   RADV_PS5_SCRATCH_WAVES_PER_CU=4 (memory lines per project log:512).** Place: the field, about 170 s after the
   field title card and shortly after a pause-menu visit (READ, video). What died: std::bad_alloc on thread am:1 at
   eboot+0xb7f15, a 452 KiB (463328 B) request, largest free block 2 MiB, heap 1984 MiB (READ, crash txt + stderr).
   Present fence "not reached in 4 s" at 386.87 and 390.88 before it (READ, eden_log). The code site
   "nvhost_gpu SubmitGPFIFO" is NOT verified: no symbolised stack exists in any note (a local note only repeats it).
   The link to the pause menu (L17 of the comment: 901 images rebuilt in 7 frames, burst at app 377.8) is consistent
   with the timing but INFERRED.
2. Four earlier crashes, 00:08:35, 00:16:09, 00:23:42, 00:44:08 (READ: crash-index.txt; reports copied into
   `auto-20261111-051009-batch-stand-tracker/run1055-control3-stand-tracker/` and
   `auto-20261111-000542-batch-t114-b/run984-l2-walk-fast-hog896-large8/`). All SIGSEGV on a CPUCore thread "outside
   the app's code", 110-113 s after start, largest free block 0-1 MiB. They come from batch t114-b, deliberate
   896/1024 MiB memory-hog walks (READ: folder names; run-to-crash mapping 978/981/984/992 INFERRED from order).
   **Not on the forest-exit route and not T120**; they say nothing about the exit.

No T120 run or session crashed on 11 Nov at or after the forest exit (READ for the four hand sessions and 1067/1068).

## 3. The posted comment (6791926516, text `census-2026-11-11/post-body-waveydude-v2.md`), sentence by sentence

| Line | Sentence (short) | Verdict |
|---|---|---|
| 1 | thanks / blue-balling | not a fact claim |
| 3 | "It gets the forest exit, the pause-menu route … and the field overlook with both censuses on" | a promise, still owed: t125-exit 1099-1101 stayed in the ravine (READ, min x 896.2-896.9) |
| 5 | "the pool is at single digits and whichever allocation comes next dies" | stands as a general reading; true for the T121 crash, not shown to kill anything on T120 at the exit |
| 5 | "RADV asking for 1.4 to 15 MiB at the forest exit" | numbers stand (stderr.prev L1032-1062, 1408-15652 KiB); place is wrong: at the passage, before the area change. Same refusals also appear in 1067 in the village, so not exit-specific (READ) |
| 5 | "(silent death, 16 MiB free)" | 16 MiB stands; **"death" is false**: the owner closed the app (READ, video) |
| 5 | "452 KiB command-list copy in nvhost_gpu's SubmitGPFIFO in the field (bad_alloc, 2 MiB free)" | stands for size, place, bad_alloc and 2 MiB (READ); the SubmitGPFIFO site cannot be checked |
| 5 | "I'm drafting a fix …" | a plan, not checked here |
| 7 | "Plain T120, EDEN_UP_MEM_CENSUS=1, base PS5, 1x, fast mode" | stands for 1067/1068 (build date READ) |
| 7 | "Leaving Kokiri Forest, two runs, same picture both times" | **false**: 1067 never left the forest; the two runs also look different (1068 dropped the old targets first) |
| 9-13 | the table (7 s before / at the change / 4 s later) | numbers stand (1067 n=20/24/26), **labels false**: all in the village, between the tunnel mouth and the save menu; "at the change" is not even the census's own area line |
| 15 | "In the second run the largest free block hit 0 with the pool at 12342 of 12352 out" | stands (1068 n=47, after the real crossing); "second run" implies a first crossing that did not happen |
| 15 | "for about two seconds both areas' render targets are alive at once" | **false**: from 1067 (one area); in 1068 the old set fell (815 → 164) before the new grew (414 → 1073) |
| 15 | "430 to 840 sits as slack" | 840 stands (1068 n=50, 837); 430 is from the village run |
| 15 | "heap is 1400 with about 320 fragmented from early on" | stands (1067 1400 / frag 271-322; 1068 heap 1432) |
| 15 | "Into a later area: images 1702 (843), largest free 16" | numbers stand (1068 n=76 t_s 191); place is the next area before the overlook, not the field |
| 15 | "pool is short by slack and fragmentation first, not by live images" | literal reading of TOP lines stands; misleading at the one 0 MiB line (n=47: "rest" +1179, slack 31) |
| 17-19 | AREA_EVICT / pause menu / BURST=300 | not checked by this check |

## 4. Our own notes that must be corrected

- `steer-forest-exit-2026-11-11.md (local note):20` "**the app crashed during the talk** (~158 s)" → closed by the owner at ~159-162 s.
- same file :23-24 "play there until a crash at ~400 s" → closed by the owner at ~405 s.
- same file :70-75 "never seen to its end (crash)" and "Session 1 crashed during it" → no crash; the talk was cut by the close.
- `the the project log` "Try 1 (05:37): the app died without a closing line at 164 s … right at the area change" → closed by the owner during the talk at the passage, before any area change; and "So with the memory wait on the exit is a coin toss on T120" → falls: T120 crossed 2 of 2 by video, never crashed.
- `project log:512` "(1) T120 … died at the area change, pool 16 MiB free" → closed at the passage; 16 MiB was at the passage. The rest of 512 stands, with the T121 crash placed on the field after a pause-menu visit.
- `project log:540` "the replay went through the village into the dark exit path … (his own tries: 16 and 14 MiB at the same place)" → 1067 stopped in the village by a tree.
- `project log:541` "The forest-exit crash, seen in the census (exit-census, run1067): render targets double for two seconds at the area change" and "(… one died)" → no area change, no exit crash; reads as "render targets grow by ~625 MiB in the village".
- `project log:551` "the forest exit a second time, same pattern as exit-census" → first and only census crossing; "(2) the change into the field at t=191" → the next area before the overlook.
- `project log:609` "session 1 … crashed during the talk there; session 2 … crashed about 100 s later in the next area" → both closed by the owner.
- `project log:616` "Open: Vampinity's second session crashed about 100 s after the area change" → it did not; the longer route variant is still useful but not to chase a crash there.
- `project log:619` "T120 died about half the time at the forest exit" (as the audit quotes it) → confirmed false.
- `a local note` "forest-exit crash = two sets of render targets for about 2 s plus allocator slack and fragmentation" → no forest-exit crash; "render targets of both areas alive at once for two seconds" is from a run with one area.
- `a local note` "three out-of-memory deaths, three sites (… RADV asks of 1.4-15 MiB at our forest exit …)" → two deaths (waveydude's 424 s one, our T121 field one); the RADV asks were refusals at the passage, not a death.
- `a local note` "does the exit survive more often than T120's about half" → T120 never died at the exit.
- `a local note` and `the day log (not public):53` release bar "forest exit and field entry 5 of 5" → the bar can stay, but its crash list is: no exit crash known; the one proven crash is on the field after a pause-menu visit, on T121. The steered route stands 35 s in the next area and never reaches the field, so it cannot test the field part; the bar needs a route onto the field with a pause-menu visit.
- `night-board-2026-11-11/results.json:20` "T120 died once at the area change and got through twice" → T120 never crashed; T121 crashed on the field. Line 33 ("reached the same memory dip as his own tries and got through") → village only. Line 34 ("twice now … 16 at the field's entry") → once; 16 MiB was in the next area.
- `exit-replay-audit-2026-11-11.md (local note):167` "(0 MiB given back)" → one ask (15652 KiB) got 64 MiB back (stderr.prev L1056). Section 4's "inferred" closes → READ on screen. Line 170 "Video ~388-390 s: Link in the field, then the launcher" → picture frozen from 381.4 s, error screen from ~394.5 s.
- The audit and census notes cite "eden_log" in the hand-* folders: there is none there; copies are in `run-logs/owner-session1-20261111/`, `owner-t120-repeat-20261111/`, `owner-t121-try-20261111/`; hand-0547 has none anywhere.

## 5. Still unknown

- The SubmitGPFIFO site of the T121 crash (needs symbolising eboot+0xb7f15 against the T121 eboot).
- Whether the pause-menu rebuild caused the T121 field crash (timing fits; one run).
- Whether T120 crashes on the field: no T120 session or run reached the field with a pause-menu visit; 0607 was closed at the overlook, 1068 never stepped onto the field.
- Whether T120 crashes later in the next area: 0537 try 2 ended at the owner's close with the largest free block at 2 MiB, so it may have been close; no evidence either way.
- The exact clock between census t_s and video time (both readings give the same conclusions).
- The steered route run1110 crossing is taken from project log:616 (frame check); this check did not re-check its video.

## 6. Draft follow-up comment (not posted; needs the owner's yes on this exact text)

```
Correction to my comment above. The census table under "Leaving Kokiri Forest, two runs" came from a test run that never left the forest; the replayed walk stopped in the village. So that table, "both areas' render targets are alive at once" and the 430 end of the slack range are withdrawn. The RADV asks with 16 MiB free also came before the exit, and that session didn't crash: I closed the app myself. What stands: the 452 KiB bad_alloc with 2 MiB free in a later area, and the one run that did cross (largest free block 0 with 12342 of 12352 out, 840 slack). Its "into a later area" line (1702, 16 free) was taken just before the field. I'm redoing the forest-exit runs with your settings on a steered route that crossed on its first run today.
```
