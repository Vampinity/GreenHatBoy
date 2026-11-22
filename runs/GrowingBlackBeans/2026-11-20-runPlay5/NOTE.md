# runPlay5: what the logs are, and what the toolkit read (20 Nov 2026)

**The play session:** `eden_log.txt.old.txt` with `logs/*.prev.*`. 6,122 s (1 h 42 min), alpha T186, handheld,
LP1 on, warm store reused. The user closed it by hand (no test-stop), so the log has no shutdown lines and stops
mid-play. That is not a crash.

**The un-suffixed files** (`eden_log.txt`, `logs/stderr.log`, `heap.log`, `boot-trace.txt`, 08:30) are a later
launch of about 45 s that never got past building driver shaders. They aren't part of the play session.

**Read with the STK** (checkrun OK; runreport; eglog windows; census t_s for timing):
- 0-55 min: 30-47 fps per 5 min, all heavy (GPU-paced). 259 shaders built in play, all in the first 15 min.
- The largest free block wore down steadily: 770 MiB → ~300 (15 min) → ~60 (40 min) → 3 (55 min). Guest grew
  5.5 → 6.7 GiB.
- 60-80 min, the memory wall without a crash:
  - images refused (587 in the whole session; corrected 22 Nov from 880), ~7,900 pack-on-refusal calls, swap reclaim for graphics;
  - 10-19 fps, with single frames of 2-10 s.
- 80-90 min: a pause in a menu, then play at 27-36 fps with no refusals, but free memory stayed near 0.
- Play, not a measured start: one session, places unknown. It proves nothing about LP1 or any switch. It does show
  a slow wear-down that a 6-minute field start can't see (a case for one long-session check in M1 later; not
  planned).

**Where (the user, 20 Nov):** started from the same save as `kokiri_four_stops`. Sword, shield, Mido, the Deku
Tree, the whole first dungeon, out to the field, then to a later area. **The wall hit exactly on entering that
area** (~55-60 min), and free memory never really came back after it. So the slow wear-down covers the
forest, the dungeon and the field, and that area's load is where it ran out.

**The driver's samples** (`RADV_PS5_MEMORY available_mib`, one every ~5 s; the source waveydude's chart uses, 20 Nov)
agree with the census: the lowest per 5 min was 770 at the start, ~300-450 by 15-35 min, 59 at 40 min, 9 at 55 min,
then 0 from 60-75 min. The lowest of all was 0 at 3,845 s. waveydude's run in another later area (9.40, W-39 play build) kept 890 MiB
at 38-41 min. Same source, so the lows compare. Console, firmware, build and route all differ, though, so the
comparison says where the wall came, not why.
