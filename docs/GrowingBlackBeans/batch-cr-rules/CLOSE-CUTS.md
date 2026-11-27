# Log cuts at the close cost us controls for nothing (27 Nov 2026, desk)

**What happens.** In 9 runner starts (B: Y1, C5, X3; L7: C2, plus C6 and Y4 in the void sitting; CR: C1, C7, C8)
`eden_log.txt` ends 15.8-20.2 s after `script_done`, each time just after the same three shutdown steps (gpu
NotifyShutdown, audio Shutdown), before `EDEN_AUDIO_PORT_CLOSED`, the scorer's close line. The app's shutdown runs
longer than the 3 s the watcher gives it after test-quit, and the exit is forced. Three different stalls in CR (a
guest abort in a socket poll, the stuck present fence, a thread dump), all after the script. About 1 start in 8.

**Why that made a control ineligible.** `control_eligible` (stk_score.py) needs `end_ok`, a clean close, because then
"its caches were saved and the next start's cache state is known". On the runner every start gets the whole cache put
back from the copy ws2 and checked file by file first, so the next start doesn't depend on this close. Arm starts
already keep their count after a bad quit (every batch's rules); only controls were thrown out.

**It changes no figure.** Four good controls (CR C2, C3, C4; L7 C10), their logs cut at script_done + 16 s and their
stderr at the same shutdown step, scored again: only `end_kind`, `end_ok`, the tail length and the session age differ.
Refusals, the black, seconds under 16 MiB, worst, load and the walk are the same.

**What changed.** The batch kit (`batch_kit.py`), batches L7 and CR only: a warm
control that fails only the close, with the log past script_done + 10 s and the runner's restore note in its folder,
counts. Batches B and C read byte-identical. Frozen with L7 amendment 2 (and CR's). CR goes from 5 to 8 eligible
controls; tonight's plan drops CR's three reruns.

**Not fixed:** the slow shutdown itself (the alpha's close path). It no longer costs a start, so it waits.
**Later, for GHB:** the same exception in `stk_score.py` for runs under the whole-cache restore (a PR to the STK).
