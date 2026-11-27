# Phase 4, batch L7: amendment 1, z's proof line, and the freeze

FROZEN: 2026-11-27, 03:58 UTC. Drafted 26 Nov after the first sitting (starts 1-6), and frozen after the second
sitting had run (starts 7-28 and Z1 again, result folder auto-20261126-100237) but before any of its files were opened,
imported or read, and before any start of either sitting was read. Amends BATCH-L7-RULES.md (sha1 f79d40a9ebd4), which
stays unchanged. Decided by the user; reported with the batch's result in its D2 line.

## Why
1. **z's proof line is another switch's line.** The rules prove a z start by the `EDEN_UP_IR_FREE: ... freed before
   its driver compile` lines in `eden_log.txt` ("6 in each of batch A's 12 controls, present except in a z start").
   All six starts of the first sitting have the same 6 lines, Z1 included: the same six compute shaders, same sizes,
   at 77-79 s. Each line says "(GPU thread)". In T186's source (`vk_pipeline_cache.cpp:526-531`, `IrFreeMode`), a
   build made on the GPU thread during play is freed by **EDEN_UP_IR_FREE_RUNTIME**, which stays on in z by these rules.
   EDEN_UP_IR_FREE acts only on builds made by the builders at boot. So the 6 lines are no proof of z either way.
   Left as it is, the kit would mark every z start "wrong settings ran" (`batch_kit.py`, the MARK check).
2. **What z really acts on here.** On the warm store the boot does a small amount of building, on the builders,
   at about 3-4 s: the disk cache's pipelines (Total Pipeline Count 4) and the store check's probes ("probes 3, fresh
   translation"). These are what EDEN_UP_IR_FREE frees early. None of them holds 32 MiB of IR, and a builder's job
   under 32 MiB prints no line whether it frees or keeps (`FreeIr`, the log gate). So z acts, silently, on a few small
   builds in the first seconds. No log line can show it.
3. **The rules' expectation for z was wrong for the same reason.** "Up to ~50 MiB more at the peak of the boot builds
   near 78 s": the builds near 78 s are play builds (the runtime switch's), not boot builds. The expectation is
   corrected below, before any z start is read.
4. **Start 6 (Z1) froze.** At about 159 s the back thread stopped inside "present: submitting the copy to the
   swapchain", with the GPU idle and nothing queued. Frames stopped, the gate's STEER timed out at 182 s, the runner's
   30 s freeze rule stopped the batch at 197 s, and the console stopped answering. No crash file. The free block was
   1,293 MiB at 151 s. The rules already say what a hang does to the run order (plan from the next number, the hung
   start rerun at the end). They don't say whether a freeze counts in the calls, which are written for crashes.

## What changes
1. **z's proof is None** (as w and x): the env that ran is checked against the folder's by the runner import
   (EDEN_UP_IR_FREE absent, EDEN_UP_IR_FREE_RUNTIME=1 present). The `EDEN_UP_IR_FREE` lines are not used to say which
   env ran.
2. **z's best quiet verdict is "removed, no harm seen"**, at best. "No change seen" needs a line of its own, and z
   has none.
3. **Reported per start, not tested:** the IR free lines, labelled "play builds freed (IR_FREE_RUNTIME, on in every
   arm)", with their count and MiB, and any line that says "(builder)" (none expected).
4. **Expected for z, corrected:** at most a small change in the first seconds of the boot; nothing expected at the
   black or after it.
5. **The freeze.** Z1 is rerun at the end of the second sitting (the rules' hang rule). Its first files are kept and
   packed under their own id (`runM1L7-06-Z1-freeze1`), not read. **For the calls:** a freeze in an arm counts as a
   crash for "Moved" and "Stop" only if a second start of the same arm freezes or crashes. A single freeze is reported
   beside the read, with the arm and the place, and is not a call by itself. A freeze in a control makes it ineligible
   and is rerun, as any control that doesn't count.

Everything else in BATCH-L7-RULES.md applies unchanged. z stays in the batch, in the frozen order.

## The choices, and why
- **The freeze rule (point 5), the user's choice.** One freeze is weak evidence against z: z acts only at 3-4 s, and
  the freeze was at 159 s in the present path, which z doesn't touch. A freeze also isn't a crash (no crash file; the
  console itself hung). Not chosen: (a) a freeze counts from the first one, which would call z "moved" on one event;
  (b) a freeze never counts, which would miss a repeat.
- **z is kept.** It can only reach "no harm seen", but dropping it would change the frozen order.
