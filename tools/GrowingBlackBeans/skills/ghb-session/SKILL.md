---
name: ghb-session
description: Open or close a Green Hat Boy work session (Ocarina of Time on a PS5 through EglantinePS5) in your Green Hat Boy work folder, the way docs/WORKFLOW.md in Vampinity/GreenHatBoy describes. Use "open" at the start of a session, or whenever the user starts Green Hat Boy work, passes a brief, or says "pick up where we left off". Use "close" when the user says the session or plan is finished, asks to "close out", "wrap up the day" or "file today's work", or wants the hand-off brief for next time.
---

# Green Hat Boy session: open and close

**Setup:**
- **WORK** is the user's Green Hat Boy work folder. If you don't know where it is, ask once and remember it.
- **GHB** is a clone of https://github.com/Vampinity/GreenHatBoy (public).
- **ME** is the user's GitHub name (their folder under `runs/`, `docs/`, `patches/`).

The layout and the reasons for it are in GHB `docs/WORKFLOW.md` (while it's a proposal: `docs/GrowingBlackBeans/workflow-proposal.md`). Read it the first time.

A session's work is filed in `WORK/sessions/YYYY-MM-DD/`, and `WORK/CURRENT.md` always points at the newest
brief. The point: a new session starts from a brief written on purpose, not from an automatic summary. The
facts survive on disk anyway, but the decisions and their reasons don't.

Say what you're doing in plain words, and show breakdowns as tables or pictures where that helps.

## Rules that apply to both

- **The standing rule in GHB `AGENTS.md`:** before any build, patch or job over an hour, fetch GHB, read
  `AGENTS.md`, search for overlap, and tell the user what exists before writing code.
- **Commit to GHB as ME** with ME's GitHub noreply address (`git log --author=ME -1 --format=%ae`), not
  whatever identity the clone has.
- **Never push or post without the user's OK.**
- **Never publish:**
  - the user's real name or email, local paths;
  - console user numbers (`EDEN_PAD_OPEN`/`EDEN_PAD_USERS` lines), save-profile ids;
  - private repos, chat handles.

  No story spoilers: call later places "a later area".
- **`BRIEF.md`, transcripts and anything under `sessions/` stay local.** Public copies of reviews go to
  GHB `docs/ME/` only after redaction and the user's OK.

## Open

0. Read `WORK/OVERVIEW.md` (the project, the people, the goals, the jargon) and `WORK/TECHNICAL.md` (how
   this user's builds, envs, runs and tools work). If either is missing, offer to write it: a fresh
   session needs both.
1. Read `WORK/CURRENT.md`, then the brief it names. If the user passed a brief, read that one.
2. Read any notes or memory the brief links to.
3. Fetch GHB. Read what changed since the brief's date:
   - new commits (`git log --since`);
   - new comments in "Who is working on what" and in the discussions the brief names, replies included.

   If `AGENTS.md` or `docs/WORKFLOW.md` changed, read them.
4. Look at the top level of WORK for work in flight:
   - run folders not yet run (an `env.txt` and no log);
   - runs copied back since the brief;
   - the installed build.
5. Tell the user, briefly:
   - what the brief says is next;
   - what changed since it was written, and whether that changes the plan;
   - the first step, and whether it needs the console.

## Close

Close when the user says the session or plan is finished. One close per day. If a session ran past
midnight, file each date's work under its own date.

1. **Inventory.** List the day's work and show it to the user:
   - runs whose log dates from that day, plus any that never got a log and won't be rerun;
   - builds made that day that are no longer installed, with their notes;
   - findings, reviews and plans dated that day;
   - posts, with their URLs;
   - envs written for runs that were never run.

   **Don't file what's still in use:** runs not yet run, the installed build, and the living docs (`README`,
   `OVERVIEW`, `TECHNICAL`, `CURRENT`, `BUILDS`, `SESSIONS`, and any other doc in active use).
2. **Back up first.** Every run in the list must be in GHB `runs/ME/` before it moves.
   - Pack missing ones with `tools/pack-run.py` (or the user's packer).
   - Strip console user numbers and redact profile ids.
   - Audit, and push on the user's OK.
3. **File.** Create `sessions/YYYY-MM-DD/{runs,builds,findings,posts,envs}` and move items in with `mv`.
   - Before moving runs, replace byte-identical files with hard links to one copy. The console's old dumps
     repeat in every run folder and can fill a disk.
   - Never delete anything without the user's OK.
4. **Transcript.** If your assistant can export the session transcript, put it in
   `sessions/YYYY-MM-DD/`. Local only.
5. **Review.** Run the `review-regroup-replan` skill over the day. Save it as `sessions/YYYY-MM-DD/review.md`.
6. **Brief.** Write `sessions/YYYY-MM-DD/BRIEF.md` from the template below. One to two pages: the hand-off,
   not a recap. It must stand on its own for a session that has read nothing else.
7. **Index.** Add one line to `SESSIONS.md` and point `CURRENT.md` at the new brief.
8. **Standing docs.** If anything lasting changed, update the standing docs; they're not for the day's
   results:
   - a new build, base or install step: `TECHNICAL.md` and `BUILDS.md`;
   - a new tool, rule or workflow: `TECHNICAL.md`;
   - a change of goal, lead, programme or collaborator: `OVERVIEW.md`.

   Say in the brief which changed.
9. **Tell the user** what was filed and where, and what's still at the top level and why. Remind them to add
   one line to "Who is working on what" and put the results in `docs/ME/`. Offer the public copy of the review.

## BRIEF.md template

```
# Brief for the next Green Hat Boy session (written YYYY-MM-DD)

## Goal and rules in force
The goal (one line). Constraints the user set (what's parked, what comes first). The privacy and
posting rules that bit this session.

## What's settled (with numbers and run ids)
Results the next session can build on, each with its evidence.

## What's retracted
Earlier claims shown wrong, and where the correction is posted.

## In flight, and with whom
Our open asks, collaborators' promises, builds or runs waiting on someone.

## The plan
Numbered steps, each with: what, why, decision rule, console or desk, which run folder or env.

## Where things live
Run folders, builds, tools, docs: local paths and GHB paths. What's in sessions/ and what's still at
the top level.

## Waiting on the user
Decisions and questions, each with a recommendation.
```
