# Helping out

Thank you for wanting to help. Here are the ways, easiest first.

There is no download for newcomers yet. Until the first alpha is out, the ways below are mostly for people who already test.

## 1. Send a run log

Runs from other consoles and firmwares help us most. No crash is needed. Open an [issue](https://github.com/Vampinity/GreenHatBoy/issues/new/choose) and pick **Send a run log**.

## 2. Report a crash or a glitch

Open an [issue](https://github.com/Vampinity/GreenHatBoy/issues/new/choose) and pick **Crash or glitch**. One crash per issue, please.

## 3. Answer questions

People often ask the same things about install and the first start. If you know the answer, reply in [Q&A](https://github.com/Vampinity/GreenHatBoy/discussions/categories/q-a). Discussions is the forum tab of this page.

## 4. Share a fix

A pull request is a way to send us a change to the files here. Never made one? That is fine. Post your patch in [General](https://github.com/Vampinity/GreenHatBoy/discussions/categories/general) and we will take it from there.

If you do open a pull request:

- Send one change per pull request, against `main`.
- Say what you tested, on which console and which firmware.
- Put your change behind a switch that is off by default.

The switch keeps test builds comparable. A change goes in as a numbered patch in `patches/<your name>/`. It should do nothing until its switch is set, for example `EDEN_GBB_GUARD_EARLY=1`. A settings file in `envs/<your name>/` turns the switch on for a test. Add a line for your patch and its switch to the README in your patches folder.

## Before a big job

Planning something that takes more than an hour? Check first that nobody did it already.

1. **Search** the `docs/` folders, the patches READMEs, `index.csv` and `CHANGELOG.md`, by switch name, patch number or a plain word. [AGENTS.md](AGENTS.md) lists every place.
2. **Claim** it with one line in the pinned "Who is working on what" thread.
3. **Write it down** when done: result in your docs folder, one line in the thread.

Working with an AI assistant? It reads AGENTS.md on its own, or tell it: "read AGENTS.md first".

## What we cannot take

- Game files, keys or firmware, or links to them. Not in issues, not in Discussions, not in a pull request.
- Logs that still hold your console's user number. Our tool removes it, and your own folder names too: `python3 tools/pack-run.py <your run folder> --out . --author <your GitHub name>`. The folder needs the `eden_log.txt` and `env.txt` of that run.

## Spoilers

Some of us are playing the game for the first time. Please keep story details and later places vague.

Thanks again. Every log and every report helps.
