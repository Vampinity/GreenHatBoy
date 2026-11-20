# runL1C: not counted (quit before END)

The log has no `script_done`: the start was quit before END (about 300 s after the black at the gate). The window after
the field has 36 of its 44 samples. The boot was right (80,770 reused/known, 3 own, total 4), both switches acted
(11 superseded lines, 32 drains) and the close finished (the shutdown driver-cache write is there).
Replaced by runL1E.

Kept for the store check: `store-after/` holds the five small store files copied after this clean close. All five
match `warm-restore/` byte for byte, so a warm start that closes cleanly leaves the store unchanged.
