# Phase 4, batch L7: amendment 2, starts in the FAST state

FROZEN: 2026-11-27, 15:20 UTC. Drafted 27 Nov (desk), frozen before the night run of 27 Nov started,
before any L7 start was read, and before batch CR was read. Points 1, 4, 5 and 6 apply to batch CR too. Amends BATCH-L7-RULES.md (sha1 f79d40a9ebd4) and amendment 1
(sha1 2e82c4f1c87f), which stay unchanged. Decided by the user; reported with the batch's result in its D2 line.

Public copy: the frozen text, with six references to local files replaced by plain descriptions (local sha1 8c97ae6c8b93).

## Why
1. **The redo ran in two states.** In the second sitting's redo (27 Nov), starts 1-14 (00:17-02:14)
   ran the field at 81-83k ring words a frame and ~28 fps. Starts 15-22 (02:25-03:46) ran at 135-140k and ~18 fps. That
   is the same as every one of the 87 runner starts before. 7 of the 14 fast starts missed the field gate (line 92);
   none of the others did. Findings: the redo-split note (on request; it holds the runner's local folder names).
2. **It isn't an arm's effect.** The 14 hold controls (C3, C4, C5, C7, C8, C9) and every arm, and they run in one block
   of time. Env, build, boot, caches, save, launch mode and runner patch were the same in both groups. The cause is not
   known, and a reboot alone didn't bring it back (a reboot test, 3 control starts straight after a reboot: 0 of 3).
3. **The rules don't cover it.** A fast start completes, and a fast control is `control_eligible`. Left as it is, the
   read would set fast and slow starts side by side, and the field's figures would move by about half for a reason
   that has nothing to do with the arms.

## What changes
1. **The state rule.** A start is in the FAST state when the median ring k words a frame over its 5 s windows from 90
   to 140 s is under 110k (`state-check.py`, the same rule in the runner's `fast_state` stop and in both
   imports). A FAST start doesn't count, whatever its arm. It's rerun at the end, in frozen order, with its first files
   kept aside, like any start that doesn't count (rules, "A start that doesn't count"). Its figures aren't read.
2. **The redo's 14 FAST starts** (entries 7-13 and 15-21) are rerun by this rule, tonight. Their files stay in the
   redo's result folder and are packed under their own ids (`runM1L7-NN-..-fast1`), not read. Reported beside the read:
   how many, when, and the gate misses.
3. **The redo's 8 normal starts count** (C10, Y4, Z4, C11, W4, X4, C12, Z1). They pass every check a start has, and
   their state reads like the 87 before.
4. **If an arm looks FAST and the controls don't.** If every FAST start of a sitting is in one arm, and controls run
   just before and after it read normal, that's no longer "doesn't count": it may be what the arm does. The batch
   stops there (the runner stops at the first one anyway), and the user decides before anything is rerun or read.
5. **The runner stop.** At the first FAST start the runner ends the batch (`fast_state`). The rest is planned from the
   next number, as for a hang, after a reboot.

6. **A control cut at the close counts.** A warm control whose only fault is the close (`end_kind log_cut`, the log
   running past script_done + 10 s, run under the whole-cache restore) is eligible, as an arm start already keeps its
   count after a bad quit. Why and the check: docs/GrowingBlackBeans/batch-cr-rules/CLOSE-CUTS.md. L7's C2 keeps its rerun (the first
   files stay aside, as the rules say for a start rerun before this).

Checked before the draft: all 15 L7 starts counted now read normal (134-140k), and so do all 12 CR starts (135-139k).
Everything else in the rules and amendment 1 applies unchanged.

## The choices, and why
- **Where the line sits (110k).** The two groups don't overlap: the fast starts lie at 76-94k and every other start at
  124-154k. Any line in that gap sorts all 124 runner starts so far the same way (87 before, the redo's 22, the reboot test's 3, CR's 12). 110k was set before the reboot test, CR and
  tonight's run. Not chosen: a line on fps or the gate. Those are outcomes an arm could move, while the field's work
  per frame is what the game was asked to draw.
- **Counting the redo's 8 normal starts (point 3), the user's call.** Not chosen: void all 22 redo starts. That would
  rerun 8 more (about 1.6 h) for starts that show no sign of the fast state. Against counting them: they come from the
  same sitting as the fast ones, after a flip nobody can explain.
- **Batch CR.** CR's rules (BATCH-CR-RULES.md, sha1 9088f44c6340) have the same gap. Proposed: this amendment's points
  1, 4, 5 and 6 apply to CR too, frozen at the same time. With 6, CR's C1, C7 and C8 count: 8 eligible controls, the
  read can go ahead without a rerun. 0 of 12 CR starts were FAST.
