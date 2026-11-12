# Read this first

Three of us work on this project, each with an AI assistant. Twice now two of us built the same fix without knowing. So before you start a job that takes more than an hour:

## 1. Search

Look here first:

- `docs/Vampinity/BUILDS.md`, `docs/Vampinity/SWITCHES.md` and `docs/Vampinity/findings/`
- `docs/GrowingBlackBeans/`
- `patches/*/README.md` (each patch and its switch)
- `runs/` and `index.csv` (every test run)
- `CHANGELOG.md`
- open branches on the forks `Vampinity/Eglantine-PS5-` and `waveydude/Eglantine-PS5-`

Search by switch name (`EDEN_UP_AHEAD_GUARD`), by patch number (`0924`) and by plain words (`stamp`, `two frames`). If someone did it already, build on that.

## 2. Claim

Add one line to the pinned "Who is working on what" thread in Discussions: what, on which build, since when.

## 3. Write it down

When you're done: the result goes in your own `docs/<name>/` folder, the switch in your `patches/<name>/README.md`, and one line in the thread: done, parked or dropped, and why.

## Set this up once

If you work in your own fork or folder, your assistant will not see this file by itself. Give it this standing instruction once (for Claude Code: the `CLAUDE.md` of the folder you work in; for Codex and others: its `AGENTS.md` or memory):

```
Standing rule for Green Hat Boy work. Before any build, patch or job that takes more than an hour:
1. Fetch the newest Vampinity/GreenHatBoy and read its AGENTS.md.
2. Search docs/Vampinity (BUILDS.md, SWITCHES.md, findings/), docs/GrowingBlackBeans, patches/*/README.md,
   CHANGELOG.md and the open branches on Vampinity/Eglantine-PS5- and waveydude/Eglantine-PS5- for overlap.
3. Tell me what already exists, in which build, and how it tested, before you write code.
When the job is done, remind me to add one line to the "Who is working on what" thread and to put the result
in my docs folder.
```

## House rules

- New behaviour goes behind a switch that is off by default.
- Never commit game files, keys, firmware, or a log that still holds a console user number. `tools/pack-run.py` removes it.
- No story spoilers in any text. Some of us are playing for the first time; call later places "a later area".
- Credit people by name for work you port or build on.
