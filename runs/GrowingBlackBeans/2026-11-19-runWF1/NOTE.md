# runWF1: not a control (quit before END)

Boot state right: `store prep_5093ab9e reused (80770 pipelines)`, 80770 known, `3 records read (3 own`,
`Total Pipeline Count: 4`. Route ran: 3 of 3 STEER legs, 5 of 5 required waits; the black at the gate at
script clock 151.0 s (line 92), line 97 at 291.0 s.

Quit at about 427 s on the script clock; END was due at 451 s. No `script_done`, so stk reads
`stopped_early`, `end_ok: false`, `control_eligible: false`.

Cause: the header's quit rule ("4 minutes after the area past the field first shows") was written for cold starts,
whose load lasts about a minute and a half. A warm load is short, so that rule lands before END. WF2-4's headers now
say "6 minutes after the screen goes black". runWF5 replaces it as the fourth field warm control.

Kept as data: field walk 19.14 fps (13 lines), after the field 13.9 (36 lines).
