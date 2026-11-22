# Grouped screening: testing several switches in one start

How we screen switches in groups instead of one at a time, written for phase 4 of GrowingBlackBeans' plan ("explain the control", section 5 of [review-2026-11-15-post-alpha-audit](../GrowingBlackBeans/review-2026-11-15-post-alpha-audit.md)). It comes from our desk notes of 19 Nov: a group design, a reach check, and a critic's pass over both that corrected several of their figures. The corrected figures are the ones used here. Figures marked **model** come from a simulation, not from starts.

The rule at the heart of it is GrowingBlackBeans': **a batch that does not move is recorded as "screened as a group", never as "each of these was tested".** Everything below is there to keep that rule honest and to say what to do when a group does move.

The lines to screen, with what we already know about each, are in [control-switch-ledger-2026-11-19.md](control-switch-ledger-2026-11-19.md).

## Answer first

1. **Put 3 or 4 switches that share no code and no memory pool into one arm.** Each group gets 3 starts against shared controls. The aim is fewer starts that could never show anything, not faster starts.
2. **Every speed switch goes into two different groups**, with new partners the second time. That second group is what catches a gain hidden by a partner's slowdown.
3. **A switch is "cleared" only with its own count line** (a line that counts work it did, printed only where the switch is on) in at least 2 of its 3 starts. A line that only says it is on is "set, work not counted"; no line at all is "set, never fired". Neither is cleared.
4. **A group that moves is split by a fixed table, not by guessing**: 8 starts for 3 or 4 members, each member in 4 and out of 4.
5. **Before any start, a desk reach check** asks whether the code a switch changes runs at all on our route. A switch that cannot act gets no start.
6. **For phase 4 everything turns around:** the control's switches are switched **off** in groups. The arm is the control minus the group. The rest of the method stays the same; the differences are in "Phase 4: switching off instead of on".

## Words, once

- **Control:** a start with the control settings and nothing changed. **Arm:** a start that changes something.
- **Group:** one arm that changes 2 to 4 switches at once (its members).
- **Mix:** one way of dealing the switches into groups. The **second mix** deals the same switches again with new partners.
- **Proof line:** a log line that shows a member acted. Only a **count line** (a count of work done, printed only in starts where the switch is on) clears a member. An **on-line** (it is set) or a line printed once when first reached shows it is set, not that it did anything. Some switches print nothing. A thin count (a handful of items in a whole start) is reported as thin.
- **Reach:** the code a switch changes runs in a control start. Reached does not mean it helps.
- **Flag:** a group whose field speed sits outside the controls by more than chance allows (see "Statistics").
- **Harm signal:** a crash, a freeze to the end, a lost device, a new picture fault in a clip, or a guard's fire line.

## How to form a group

A switch may join a group only when all of these hold. They should be checked by a script in the batch generator, not by eye.

1. **It can act on this control and route** (the reach check below). A switch that cannot act would be "cleared" falsely.
2. **It has a proof line,** named before the batch runs. A switch with no line can only ride for harm, and its line in the ledger then says "set in N starts, no harm seen; not tested".
3. **No shared code with another member:** not the same function or nearby lines of one file (from the patch hunks), and not read in the same function or within about 150 lines (from the source).
4. **No shared scarce resource:** at most one member per family, even with different code. Families we use: the memory pool (anything that uses or frees pool memory), the texture collector, the command list path, the pipeline cache, JIT code, fences and queries, page protection, crash guards. Two memory switches can fight over the one pool without sharing a line of code.
5. **A pair that only works together goes in as one member** (for example a switch and the line it needs).
6. **Likely slowdowns and crash suspects go alone or in a small risk group, last in each pass.** This keeps the commonest masking pair (a gain next to a slowdown) out of the groups.
7. **Shader store names:** a switch that changes the shader store's name needs its own store (about 2 h to prepare). Such switches go only with other store names, 2 or 3 to a store, and the group's store is prepared with exactly that set. Before reading speed, check that the fresh store's pipeline count and first-sight build stalls match the control's.
8. **Switches that can change while the game runs** are better read in a live on/off plan inside one start. Groups are for boot-only switches and for load and crash questions.

Why 3 or 4 (**model**, 42 switches): larger groups do not save starts. They flag more often, their follow-up is bigger, and they find fewer gains because more partners add more noise. 4 is the cheapest size that keeps the find rate, and the 8-start split table exists only for 3 or 4 members. A fifth member is fine when it is a harm-only passenger, such as a crash guard.

## Controls

- **At least 10 controls a batch,** shared by all groups in it. About one control for every 3 group starts.
- **Never more than 4 group starts in a row without a control.** A control goes first after any gap in the queue.
- **The control's place rotates** through the chunks, and the second pass runs in reverse order.
- **So does every group's.** A group's starts spread over places 1, 2 and 3 of a chunk, never all in one place, and the reader compares a group with the controls at the same places. In batch C (19 Nov, 42 starts) four of the night's five longest memory waits were in starts that ran first in their chunk, and the lead of a group that ran first in all three chunks cannot be told apart from its place.
- **Every start, arm or control, begins from the same restored cache.** Five control lines write the caches during play or at exit: `RADV_PS5_DISK_CACHE_PUT_NEW`, `RADV_PS5_DISK_CACHE_DRAIN_EXIT`, `EDEN_UP_FIRST_START_LIST_WRITE`, `EDEN_GBB_PIPELINE_SAVE_20S` and `EDEN_UP_DRIVER_CACHE_EVERY`. Without a whole-cache restore each start leaves the next one a different cache: in GrowingBlackBeans' warm starts of 18 Nov one start built 6 shaders in play where the start before built 199, and cold against warm moved the field walk from 13.4 to 18.9 fps, far more than the 3 % a group can see. Check each start's boot lines before reading it (pipelines known, own records, total count, the driver cache's boot write); a start that differs from the batch's controls is not read. This holds for own-store groups too, not only the pipeline count check.
- **One control set holds for one build, one mode, one route, one save and at most one night.** The level moved by about 1 fps with the hour on 11 Nov.
- **Drift check:** a trend fit over all the batch's controls (not first half against second half, which is too weak with few controls). If drift is over 1.5 % on the field, each group is judged against its two neighbouring controls.
- **One throwaway control after every install,** not counted.
- **For rare events** (a hang report, a blip), pool the controls of earlier batches on the same build, settings and route before tying an event to a group.

## Statistics: what a group can see

- **Flags use the two-sided 5 % t value for the batch's own control count,** not the known-noise shortcut, because a group can move either way and both a gain flag and a slow flag lead somewhere. With 7 controls that is about 2.45, with 10 about 2.26, with 14 about 2.16 (batch C's reader used 2.16). The power figures below are two-sided too, so flags and power match. (A first version said one-sided, 1.94 with 7 controls, against two-sided power figures; GrowingBlackBeans caught it.) The reader should print the degrees of freedom it used.
- **Smallest field change seen 4 times in 5** (80 % power, two-sided 5 %, handheld spread about 1.4 % a start, t on the batch's own controls):
  - a group, 3 starts against 7 controls: about 3.2 %
  - a group, 3 starts against 10 controls: about 2.9 %
  - one switch alone, 2 starts against 19 controls: about 3.1 %
  So a group with 10 controls sees as small a change as single arms, with far fewer starts.
- **GBB's noise figure (upstream issue 21, comment 88):** up to 3.6 fps between identical runs. Any gate starts there.
- **Load measures need more starts:** a light-load effect of about 20 to 30 % on the black at a load needs 6 or more starts with the change. No 3-start design places it.
- **Time under 2 fps cannot place any switch** at these sizes.
- **Measures read from the 5 s lines have blind spots.** Time under 1 fps misses a stall followed by a line that averages above 1 fps (batch C: one start read 0.0 s under 1 fps with a 13.3 s gap between lines and a 9.4 s frame). Read the longest gap between lines and the worst frame beside it.
- **Long-tail measures overstate.** The longest memory wait has a long tail (a control with no switch reached 6.6 s in batch C). A t from the controls' spread alone makes one bad start look like a group effect; check it with the group's own spread before calling it a lead.
- **Crashes:** a switch that crashes 1 start in 7 shows at least once in 3 starts 37 % of the time; 1 in 20 only 14 %. Grouping gives each switch more starts, so more chances to catch it, but up to 4 suspects.
- **Screen handheld.** Handheld controls are calm on the route (0 of 118 crashed before the script end by 19 Nov). That count was not made for the quit, and we have not read quits on their own yet: GrowingBlackBeans saw the game abort during shutdown in 10 of 55 handheld quits since 16 Nov, and in some others the log stops before the final driver cache write. Quit crashes are read on their own, against the same batch's controls, never folded into the route count; the removal of a close-path line such as `RADV_PS5_DISK_CACHE_DRAIN_EXIT` is judged on quits. Docked controls since 17 Nov ended in a crash 7 times in 17: 4 game-side (3 of them the first start after an install) and 3 the test's own screenshot. So a docked group, which has 3 starts, would meet a crash that is not its own in roughly 1 start of every 3 or 4 on a bad night and far fewer on a settled one; read the harm rule against the controls of the same batch. Memory-family members that clear get a docked read afterwards, on memory waits, the memory low point, refused images and freezes, never on a crash count under 10 starts.

## Decisions

1. **Quiet:** no flag and no harm in 3 starts, and each member shows its own count line in at least 2 of 3 (members with only an on-line or no line are "set", see Decision 5). Each member's ledger line then names its partners, the starts, the build, mode and route, the number of mixes, and "never tested alone". It goes into the second mix.
2. **Gain flag:** the group gets its split table (below). A member that wins there goes alone (4 starts), then the play route, then docked, before any settings file.
3. **Slow flag:** not split into singles. Its members go into the second mix with new partners. A member slow in both mixes is tested alone (3 starts) or written down as "kept, slower here". Nothing is retired on a slow flag.
4. **Harm:**
   - Stop the group's remaining starts on a lost device, a freeze to the end, or a crash whose thread runs a member's code (from the symbolised stack). The member it names is tested alone first. With no name, the group is split in halves, 3 starts each.
   - No stop on a known base crash with no member on its path; one extra start, and the crash stays on the group's line.
   - **A guard's fire line counts as the crash it prevented.** A guard can make a group look crash-free by turning a crash into a dropped frame.
5. **Did not act, or not counted:** a member with no line in 2 of 3 starts gets "set, never fired on this route"; one with only an on-line gets "set, work not counted". The group's verdict leaves both out. In batch C 9 of the 15 members that ran ended here (5 with an on-line only, 4 with no line), so a group's "quiet" covered fewer switches than it held.
6. **No early "no gain":** a quiet group always gets all 3 starts. An early stop is only for harm, or for a clear gain in 2 starts.

## Splitting a group that moved

- **3 members:** all 8 on/off mixes. **4 members:** an 8-start half table; each member is in 4 starts and out of 4, and one start has all on, one all off. **5 members:** a 12-start table, each member in 6.
- **The run order is fixed by script** so a steady drift cancels out of every member's effect. Table of 4: `++++ ---- --++ ++-- -+-+ +-+- -++- +--+`. Table of 3: `+++ --+ -+- +-- --- ++- +-+ -++`.
- **The all-on start runs first as a smoke start:** it must show every member's proof line and no harm.
- **A group that wins while no member wins alone** is a pair effect. The table shows it; the pair is then confirmed together, 4 starts against 4.
- **Own-store groups are split by halves,** because every split needs a new store.
- A split table costs 8 starts against 4 for a flagged single arm. That is the price of grouping, and it is paid only for groups that move.

## Two mixes against masking

One mix finds a gain cancelled by a partner's slowdown only about 1 time in 5 (**model**). With the second mix, each cleared speed member gets new partners, and the same model finds it about 3 times in 4. So every speed member gets 3 + 2 starts in two different groups. Guards and harm-only passengers skip the second mix, since masking does not apply to them. If a batch runs one mix only, every ledger line it writes says "one mix only, masking not checked".

After a round, all cleared members go together against the control (4 starts against 4). This catches pairs the rules kept apart, which are the likeliest to interact. A set below the control is split by group.

## The reach check (desk, before any start)

A desk read of the source and of the control starts' own logs asks, for each switch: does the code it changes run on this route? Verdicts: **none** (the value is already the default, or nothing reads it for this game, or it is read before the settings file), **not** (the case it handles never happens on this route), **needs** (it acts only with another switch the control lacks), **reached**, **likely**, **unknown**. On 19 Nov it settled 20 of 112 candidate switches with no start at all, and found 5 wrong "needs" entries in our ledger.

What can make a reach verdict wrong, and the check for it:
- **A reader we did not find** (in the driver, in a build script, added by a later port), or **a later build that changes a default.** Run the reach read again on each new tree; defaults live in the source.
- **Paths the route does not take:** docked, the village, the town, sessions longer than the route, a fresh shader store (many new pipelines), crash-only paths, or a value that creates its own case. A "not" holds only for the build, mode, route and store it was read on, and the ledger line says so.
- **The control changes.** Compare the next batch's control with the one the reach read used before reusing its verdicts.
- **A "none" or "not" is never written as "no gain".** It is "not reached on <build>, <route>, <mode>".

A later build could carry a read counter that rides in the control starts and counts every switch read by call site, at no extra start. It must then be in every start of a batch, arms and controls, or in none.

## What a group can and cannot show

Can show:
- a change in the group's sum of about 3 % or more on the field (with 10 controls)
- every harm signal, including harm that needs two members together
- that each member acted, from its own count line

Cannot show:
- a number for each member on its own (only the split table gives that)
- a gain hidden by a partner, without the second mix
- small load effects, crash rates, or anything docked from a handheld batch
- anything about a member that did not act, that prints no count line, or that the route never reaches
- anything about the quit, from the route's crash count

## Phase 4: switching off instead of on

For phase 4 the arm is **the control minus a group of its own lines**. The same rules apply, turned around:

- **What a result means.**
  - Quiet: "removed as a group, no change seen" = **screened as a group**. The lines may still matter elsewhere (docked, other areas, long play).
  - Faster or lighter without them: the lines cost something. Split the group; a member that wins alone is a candidate to take out.
  - Harm without them: one of them is needed. Split to find which, and write down what it is needed for.
- **Proof it acted, turned around:** the member's count line is present in the controls and absent in the arm. A member with only an on-line or no line in the controls cannot be shown to have acted, so its removal can only say "removed, no harm seen".
- **`=0` lines:** removing `EDEN_X=0` returns the feature to the build's default. For `EDEN_NX2_OOT_VISUAL_WORKAROUND` that is on (source comment); for the other three `=0` lines in the control the default was not checked. Treat such a removal as possibly switching something on: it may need its own reach check.
- **A parent goes off with its tuning lines, as one member** (for example a wait and its time limit, a drain and its threshold). Taking a parent away leaves its tuning lines with nothing to tune; taking a tuning line away only returns it to its default.
- **Needs-pairs go together:** a line that another line needs comes out with it, as one member.
- **Lines that repeat the default** change nothing when removed (on T197M, where the default was read). The ledger marks the ones we found; they need no start.
- **Guards and lines that never fired** (they act only in a rare failure) get a reach check first. On a route where they never act, removing them shows nothing.
- **Removals of big lines go in the risk group, last in each pass:** frame wait, guest swap, the load window, anything whose removal crashed or froze a start before.
- **Store names:** 27 of the lines to screen change the shader store's name. They go in own-store groups of 2 or 3.
- **Logs:** taking all log and count lines out in one group answers whether the logging itself costs speed. It needs its own readers, because the readers use those lines.

**Rough cost (estimate, our sums, 7.5 min a handheld start):** the 87 lines to screen and the 11 for a reach check first, 98 in all. 71 of them are not store names. In groups of 4 that is about 18 groups: 54 group starts and about 18 controls, near 72 starts or 9 h, fewer if the reach check settles some, plus 2 starts a speed member for the second mix. The 27 store names in groups of 3 need about 9 stores (about 18 h of preparation) and their own starts. Your own estimate on 15 Nov was nine batches and one control arm, about 40 starts and five hours; the difference is the second mix, 10 or more controls, and the store names.

## What the batch kit needs

- **A group generator** that asserts the rules in "How to form a group" (reach, proof line, shared code, one member per family, store names together), writes each member's proof pattern into the batch's notes, and writes the run order with the control count.
- **A skip list** the batch driver reads before each chunk, for a harm stop or an early table. The desk writes it between chunks; an unattended runner cannot stop a group by itself.
- **A reader** that treats a group as an arm, reads each member's proof line, prints the degrees of freedom behind each flag, and fits the split tables.

## Credits

The "screened as a group" rule and phase 4 itself are GrowingBlackBeans' (review of 15 Nov). The split tables are standard two-level designs (the 12-start one is a Plackett-Burman design). The second mix, the reach check and the corrected figures are from our desk notes of 19 Nov.
