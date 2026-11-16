# How we work (a proposal for all three of us)

> **Status: proposal, open for discussion.** If we agree, it moves to `docs/WORKFLOW.md` and `AGENTS.md` points at it. Until then, read "`docs/WORKFLOW.md`" below as this file.

`AGENTS.md` says what to do before and after a job: search, claim it in "Who is working on what", write
it down. This file covers everything in between, so that any of us, or any of our assistants, picking up
any of our work finds the same shape:
- how we keep a working folder;
- how a run, a build and a work session are set up and closed;
- how we measure.

It's plain markdown on purpose, so it works with any assistant. Claude Code users can also install the
two skills in `tools/GrowingBlackBeans/skills/`, which do the session steps below for you.

---

## 1. Your working folder (local, private)

Keep one folder for Green Hat Boy work, laid out the same way:

```
<work folder>/
  README.md        points at the next three
  OVERVIEW.md      the project, who does what, the goals, the jargon: written for a fresh assistant
  TECHNICAL.md     how YOUR builds, envs, runs and tools work on YOUR machine
  CURRENT.md       one line: where the newest session brief is
  BUILDS.md        every build you made: version, base, patches, commit, status
  SESSIONS.md      one line per work session: what it settled
  run<ID>/         one folder per run: prepared before, filled after
  <build>/         the build installed on your console now
  sessions/YYYY-MM-DD/
    BRIEF.md       the hand-off to your next session
    review.md      the closing review
    runs/ builds/ findings/ posts/ envs/
```

**Why:** an assistant that opens a new session knows nothing. It reads three files in this order:
1. **OVERVIEW** (what and why);
2. **TECHNICAL** (how);
3. **CURRENT → BRIEF** (where we are and what's next).

After that it's up to speed. Without them, it rebuilds the picture from an automatic summary that keeps
the facts but loses the decisions and the reasons behind them.

**The top level holds only what's in use:** runs not yet run, the installed build, and the living docs.
Everything else is filed under `sessions/<date>/` when a session closes.

## 2. A run

- **Name:** `run<Letters><n>`. The letters say what the experiment is (e.g. `KS1` = scripted start 1),
  and the number repeats it.
- **The folder is prepared before the run,** with its `env.txt`. The env's header says, in plain words:
  - which build it's for;
  - what changes from your everyday settings, and why;
  - what to do on the console (route, stops, what to watch for, what to press);
  - what to copy back afterwards.

  Whoever holds the controller follows the header, so it has to be complete.
- **After the run:** copy the log and the dumps back into the same folder. Then pack it into `runs/<you>/`
  with `tools/pack-run.py` (or your own packer). Before pushing, audit it:
  - no console user numbers (`EDEN_PAD_OPEN` / `EDEN_PAD_USERS` lines);
  - no save-profile ids;
  - no real names, emails, local paths or private repos.
- **Everyday settings:** keep your normal play env as one file with a comment on every line you adopted
  (when, and on what evidence). Every run's env is "everyday plus or minus", which makes runs comparable
  across people.

## 3. A build

- **Name:** `t<base>-<you><n>` (e.g. `t134-gbb9` = Vampinity's T134 plus GrowingBlackBeans' patches,
  build 9). Give it a version number of its own (`contentVersion`), so the boot log says which build
  made it.
- **New behaviour goes behind a switch that is off by default** (house rule). It writes one log line
  when it's first used. Unset, it changes nothing.
- **Record it:**
  - a row in your `BUILDS.md`;
  - the patch and its switch in `patches/<you>/README.md`;
  - a short note in `docs/<you>/build-*.md`: what it adds, what was tested, and what wasn't.

## 4. A work session

**Open:**
1. Read `OVERVIEW.md`, `TECHNICAL.md`, `CURRENT.md` and the brief.
2. Fetch this repo, and read what changed since the brief: new commits, new comments in "Who is working on
   what" and in the threads you're active in, replies included.
3. Check your folder for work in flight.
4. Then say what's next, and whether it needs the console.

**Close** (once a day, or when a plan finishes):
1. File the day's runs, builds, findings and posts into `sessions/<date>/`. Check every run is in `runs/`
   first.
2. Write a short review. What happened, one line per run: hypothesis → result → status. Then:
   - what we learned;
   - what we got wrong;
   - the plan with decision rules.
3. Write `BRIEF.md` for next time, in the template below. One to two pages, standing on its own.
4. Point `CURRENT.md` at it and add a line to `SESSIONS.md`.
5. If something lasting changed (a build, a tool, a rule, a lead), update `OVERVIEW`, `TECHNICAL` or `BUILDS`.
6. Post your line in "Who is working on what".

**Brief template:**
- **Goal and rules in force:** the goal and the constraints.
- **What's settled:** with numbers and run ids.
- **What's retracted:** earlier claims shown wrong, and where the correction is posted.
- **In flight, and with whom:** our asks, others' promises, runs and builds waiting.
- **The plan:** steps, each with what, why, the decision rule, console or desk, and which run folder.
- **Where things live.**
- **Decisions waiting on you:** each with a recommendation.

## 5. How we measure

The project has four **anatomy programmes**, one per way a session can fail. Each has a lead, and all
three of us feed all four:
- frame time;
- hitches;
- the memory wall;
- flashes and crashes.

The plan is in Discussion #5. The same habits apply to all of them:

- **Write the question, the unit, the budget and the decision rules before measuring,** so that a null
  result still counts.
- **Fixed places, scripted.** A scripted start repeats to about 2%; a hand-played stop drifts up to 12%.
  The places include transitions (doors, area loads, the pause menu), because hitches, memory peaks and
  crashes live there.
- **Judge every fix on four numbers:** fps, hitch ms per minute, the largest free memory block at the peak,
  and flashes per minute. Many fixes move a problem from one programme to another.
- **Noise.** Fps varies by about ±1 between runs of the same setup:
  - 4 runs a side for a verdict; 3 is a screen;
  - use live switches on a schedule where they exist;
  - look at runs one by one, not only the average.
- **Instruments cost time.** Counts survive instrumentation and times don't, so never compare fps from a
  profiled run with a clean one. Measured costs are in `tools/GrowingBlackBeans/eglog/LOGS.md`.
- **Check what's already measured** before building a counter. Most of our detours were unread logs, not
  missing ones.
- **Post corrections openly,** in the thread where the claim was made.

## 6. What stays private

**Stays private:**
- briefs, transcripts and `sessions/` folders;
- local paths;
- console user numbers, save-profile ids, IPs;
- real names, emails, chat handles, private repos.

**Goes in this repo:** packed runs, docs, patches, tools, and redacted reviews.

No story spoilers: call later places "a later area".

## 7. Setting your assistant up

Add one line to the standing instruction from `AGENTS.md` (in your `CLAUDE.md`, `AGENTS.md` or your
assistant's memory):

```
Also follow docs/WORKFLOW.md in Vampinity/GreenHatBoy: keep my work folder in its layout, and open and
close each work session as it says.
```

**Claude Code:** copy `tools/GrowingBlackBeans/skills/ghb-session/` and
`tools/GrowingBlackBeans/skills/review-regroup-replan/` into `~/.claude/skills/`. Then
`/ghb-session open` and `/ghb-session close` do section 4 for you.
