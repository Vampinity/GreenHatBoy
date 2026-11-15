---
name: review-regroup-replan
description: Run a full review → regroup → rethink → replan cycle on an emulator performance/correctness investigation (built for EglantinePS5 / Ocarina of Time, works for any log-driven tuning work). Use when the user asks to "review, regroup, rethink, replan", "take stock", "do a fresh cycle", "where are we", "what have we learned", reaches a stopping point, or after a batch of test runs, a new upstream release, or a surprising result. Produces an evidence-based status, a ranked problem map, explicit corrections to earlier claims, and a plan with decision rules.
---

# Review → Regroup → Rethink → Replan

A stop-and-think cycle for log-driven investigations. Its value comes from three things. It is grounded in data, not memory. It corrects earlier claims in the open. It chooses the next step by how certain and meaningful the result will be, not by how cheap it is.

Run the phases in order. Show your work in numbers. Keep the final write-up short: the user reads it, the data backs it.

## 0. Set the frame (1 minute)

- **The goal.** Example: "stable 30 fps on a base PS5 along the Kokiri route." Restate it, plus any constraints the user has set: what is out of scope, what to deprioritise, which route, which hardware.
- **The previous cycle.** Find its date and plan in the notes, the memory, or the last write-up. Everything since then is what you review.
- **Standing rules.** Privacy and redaction. Which repos and collaborators must never be named publicly. Post only with approval. The user copies files themselves. Restate the ones that apply.

## 1. Review: what happened since the last cycle

Collect, then read. Don't summarise from memory.

1. **Runs.** Every run since the last cycle: from `index.csv` in the shared runs repo (filter by date and author), plus local run folders not yet packed. For each one, give its id, build, env difference from the everyday env, route, the player's impressions, and the result.
   - Use the toolkit if present (`tools/GrowingBlackBeans/eglog/`):
     - `eglog.py summary` for every run;
     - `runreport.py` for the important ones;
     - `abcompare.py` for every claimed gain or loss.
   - Report speed **per regime**, never only as a single fps. Light means the present waits under 1 ms (the game's CPU sets the pace); heavy means it waits 5 ms or more (the GPU thread sets the pace). They respond to different fixes.
2. **Builds and patches** made or adopted. What each changed and which switch turns it on.
3. **Outside changes.** New upstream or collaborator releases, issue threads, other forks the user follows. Read their notes and logs if they shared them, not just the headlines.
4. **The user's own observations.** Flashes, stutters, "felt faster". These count as data, especially for visual problems that logs don't capture.

For each experiment, write one line: **hypothesis → result (with noise verdict) → status** (adopted / rejected / inconclusive / parked).

## 2. Regroup: rebuild the problem map

Lay out where things stand as of now, not as of the last cycle:

- **Current best setup:** build plus env plus menu settings, and its numbers per regime, with run counts.
- **Ranked problems.** Rank by how much of the goal each one costs, with:
  - certainty: measured / inferred / suspected;
  - evidence: which runs and which numbers;
  - expected size of a fix.
- **Ruled out**, with the run that ruled it out, so nobody tries it again without a new reason.
- **Corrections.** Every earlier claim that the new data contradicts, stated plainly: "I said X; Y shows it was wrong / overstated." If you posted it publicly, offer a correction post.

Checks that have caught real mistakes before:
- **Measurement distortion.** Was the result taken with a costly diagnostic on? Profilers and audits change timing; never compare their fps with clean runs.
- **Noise.** One run per side can't call anything under about 2 fps. Two per side is a screen, three or more is a call. Look at the runs one by one, not just the average.
- **Copy and identity errors.** Is the log really from the run it's filed under (env against the log's own switch lines, build in the boot trace)? Use `checkrun.py`.
- **Regime mix.** Is a change in overall fps just more or fewer heavy windows?
- **Moved, not removed.** A wait that disappears at one site often reappears at the next one. Check the total, not just the site you targeted.

## 3. Rethink: challenge the approach

Ask these out loud and answer them with evidence:

1. **Is the current path the one most likely to give a certain, meaningful result, even if it is hard work?** Don't pick a path because it is the cheapest or because it comes next. Say what result would prove it worked, and how big that result could be against the goal.
2. **Which assumption, if wrong, changes the plan the most?** What is the cheapest decisive test of it?
3. **Are we measuring the right thing?** Is there a missing log or tool that would settle the open question faster than another experiment?
4. **What would an independent reviewer say?** For a big decision or a surprising result, offer a second opinion: a fresh agent given the data and the question, **not** your conclusion, or given your conclusion with an explicit order to challenge it.
5. **What are collaborators already doing?** Don't duplicate their work. Reuse their tools and data.

## 4. Replan: the next steps

Write a numbered plan. Each step has:
- **what** (build, run, analysis or code change) and **why** (which problem, which open question);
- **expected outcome** and **decision rule**, for example "if heavy-window fps rises by 2 or more across 3 runs, adopt; if not, drop and do step N";
- **needs:** the user at the console or not; a new build or not; how many runs per side; what the user should watch for while playing (flashes, stutter, where).

Order the steps so that work which doesn't need the console can go on while the user is away. Put run setups in clearly named folders, one per run, with an env file. Say what changes from the everyday env.

## 5. Deliver

1. **Write-up for the user**, in this order and kept short:
   1. What happened (runs and results, one line each).
   2. What we learned.
   3. Where things stand (a problem table with certainty).
   4. What changed in our thinking, including corrections.
   5. The plan.
   6. Decisions you need from them, asked as clear questions with a recommendation.

   Offer a published page if the cycle is big or will be shared.
2. **Update the notes:** the project memory and notes files, the shared repo's docs. Record retractions too, not only new findings.
3. **Draft posts** for the collaborators' threads if useful. **Never post without the user's approval.** Never name private repos or collaborators the user has kept private.
4. **Prepare what the plan needs:** envs, build kicked off, analysis started. Tell the user when builds finish.

## Principles

- Evidence over narrative. Every claim carries its numbers and run ids; separate what was measured from what was inferred.
- Retract errors explicitly and early, including your own.
- Per-regime, per-run, noise-aware comparisons only.
- Certain and meaningful beats cheap.
- Keep the user's constraints and privacy rules in front of every action.
