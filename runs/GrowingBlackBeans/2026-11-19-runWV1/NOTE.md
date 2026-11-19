# runWV1: not a control (the close never finished)

Boot state right (80770 reused, 80770 known, 3 own, Total Pipeline Count 4). Route complete: 2 of 2 STEER legs,
4 of 4 waits, script_done at 332.1 s; quit 82.7 s later. Numbers (cut at script_done + 10 s, so unaffected by the
end): village lap 18.88 fps, field stand 12.8, worst frame 3.86 s, smallest largest free block 49 MiB, 0 OOM lines.

The end: stderr shows the app's shutdown begin ("Stopping the game", NotifyShutdown, audio, SuspendEmulation),
then at 418.3 s the game itself panics (`svc_exception.cpp Break: Userspace PANIC`, backtrace through
`nn::diag::detail::Abort`). The close never reaches CloseServices, the audio port close or the cache write, so stk
reads `end_kind: log_cut`, `end_ok: false`, `control_eligible: false`. runWS2 ended with the same Abort after its
quit (Vampinity's PR #19 point 3).

Store-growth check (the store files copied off after this start, not packed): all eight store files byte-identical to the post-build copy after this start,
including both .bin files. A normal warm start does not change the store.

runWV5 replaces it as a later-area warm control.
