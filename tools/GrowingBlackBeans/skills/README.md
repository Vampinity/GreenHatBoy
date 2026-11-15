# Skills for Green Hat Boy work (Claude Code)

Two skills that do the session steps in `docs/WORKFLOW.md` (while it's a proposal: `docs/GrowingBlackBeans/workflow-proposal.md`) for you. They're optional: the workflow
itself is plain markdown and works with any assistant.

| Skill | What it does |
|---|---|
| `ghb-session` | `/ghb-session open` reads your work folder's OVERVIEW, TECHNICAL and the latest brief, fetches this repo and says what's next. `/ghb-session close` files the day into `sessions/<date>/`, runs a review and writes the next brief |
| `review-regroup-replan` | A stop-and-think cycle over your runs: what happened, what we learned, corrections, and a plan with decision rules |

**Install:** copy both folders into `~/.claude/skills/`. The first time you run `/ghb-session open`, tell it
where your work folder is and what your GitHub name is.
