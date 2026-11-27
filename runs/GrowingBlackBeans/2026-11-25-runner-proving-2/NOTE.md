# runner-proving-2, the runner's shakedown start 2 of 2: control (25 Nov 2026, 07:33), not read

- Alpha T186 01.219.028, base PS5 13.60, handheld 1x, warm field route c4fada64155f, the control env. One control start on the runner (Vampinity's PR 38 at 31ace18), run before batch B to prove the runner on our console. Not part of any batch and not read; kept and posted so every start of the day is in GHB.
- Boot warm: 80,770 known, 3 records read (3 own), Total Pipeline Count 4; completed, script done.
- Log cut after the quit (`end_kind log_cut`): the close was not captured, so the scorer marks it not eligible as a control. Not read anyway.
- Whole-cache restore before this start: copy ws2 (made 2026-11-25 06:57:21), 27 files, 2.1 GiB, 217 s, at 2026-11-25 07:38:36; read back 26 + 13 files; user-cache digest 07472daf4d3a, cache digest 48d0fe46e312 (the same in every start).
- VMA dumps left on the console: 0.
- Graphics refusals to script_end 5; largest block at the black 1,149 MiB; 16 s under 16 MiB; worst frame after the black 1,253 ms; load 19.2 s; field walk 18.97 fps; distinct failed shapes 1.

## The close, for Vampinity's question on #50 (added 27 Nov)

**The command line.** The runner doesn't record it. The one written for this start (our setup notes, step 6), from the
runner's folder on the Pi, with the plan and the route beside it:

    python3 auto-run-wait.py proving-one-control.json --warm-copy ~/ghb-runs/warm-copies/ws2 --go

So the close settings were the defaults: `--quit-wait 20`, `--close-quiet 4`, `--close-floor 6`.

**`batch.log`, from the quit on** (the whole file names the console's address and a home folder on the Pi, so it
stays local; these lines are copied as they are, with nothing private in them):

    07:46:16 Script done, the test ends in 10 s
    07:46:27 Script done after 465 s
    07:46:30 The app closed

**Which close case fired: mounts gone.** "The app closed" is the line of the mounts-gone case alone (ShadowMount took
the sandbox's mounts away: the process is gone). The 4 s-quiet case prints its own line ("no log of it has grown for
...") and can't fire sooner than `--close-floor`, 6 s after the app took test-quit; this one closed 3 s after it.
Start 1 closed the same way, 4 s after its quit, with its stderr going on to `kernel.CloseServices()` (+419 ms).

**So it's a stuck close, not an early copy.** The logs were copied only after the process was gone. Start 2's stderr
stops after `kernel.SuspendEmulation(true)`, and the last line of its `eden_log.txt` is
`WaitForFrame: nx2:vi2 present #9110 fence (1, 65998) not reached in 4 s (now 65993)`: a present that never
finished. 3 s is the app's own watcher forcing the exit after test-quit (`test_harness.h` kQuitLimit), which fits a
close that was stuck at that frame.
