# First new-game play: 48 minutes to the first dungeon, no crash (12 Nov 2026)

> **Found:** A new game on t120-gbb9 with the everyday env played 48 minutes, from the start into the first dungeon, without a crash. It was playable and fun, at 28.9 fps in play. The hitches were first-time shader builds, and free memory touched 0 MiB around minute 41-44 without ending the session.
>
> **So:** For the first hour, the two things between "playable" and "good" are first-time shader builds (about 345 in the first 10 minutes) and the memory margin. Speed in the village's heavy views comes after them.

GrowingBlackBeans. Run `runs/GrowingBlackBeans/2026-11-12-Play1`. Base PS5 13.60, t120-gbb9 (T120 + my series + waveydude's 0927, two-ahead off), everyday env (`envs/GrowingBlackBeans/`, one frame ahead, copy guard 3, usage tracker, preload all), Handheld, Faster CPU on. Hand-played, not a benchmark route, so regimes and timings only, no phases. The player quit from the menu.

## The player's view

- Definitely playable: "overall it was solid, I enjoyed playing a ton."
- Above 35 fps talking to people and in houses.
- Hitches mostly the first time something new plays: a sword slash, a new jump, picking up a rupee.
- An fps drop going back into the village from a house.
- Some flicker.

## What the log shows

42 minutes in play windows (the rest is loading and menus). Play fps 28.9: light 32.0 (46% of windows), mid 29.2 (26%), heavy 23.1 (27%). 208 of 507 play windows at 30 fps or better, 28 at 35 or better.

| Minutes | fps | Heavy windows | Notes |
|---|---|---|---|
| 2-10 | 27.5-31.3, dips to 15 | up to 33% | **345 shaders built in play** in the first 10 minutes (400 in the session); hitches up to 382 ms |
| 10-18 | about 29.5 | 0% | the steadiest stretch |
| 18-38 | 24-29, dips to 16 | 25-74% | long heavy stretches: the fence wait (GPU side behind) is 17 ms a frame in heavy windows, frames up to 380 ms |
| 38-48 | 29-33 | 0-45% | more loading screens |

- **The hitches match the player's.** Every hitch in the first 10 minutes has shaders built in its window. A new animation or effect is a pipeline the cache has never seen, and preload-all can only build what's already cached. A new game is the worst case.
- **Going back into the village** is the heavy view Vampinity measured (`docs/Vampinity/findings/fps-by-view-2026-11-11.md`: the water and stepping stones in view, frame time following command-list entries). Heavy windows here wait 17 ms a frame on the fence and run at 23 fps.
- **Memory.** The driver pool's available memory (`RADV_PS5_MEMORY` in stderr) was 20 MiB at its lowest in the first 10 minutes, 4 MiB in minutes 30-40, and 0 MiB at about minutes 41-44, then recovered. Nothing was refused that ended the session, but there was no margin left. This is the roadmap's M3 wall arriving within the first hour.

## What it means for the roadmap (Discussion #3)

- **M0/M3:** the first hour runs, from one session. Note the caches were warm (a console that has run the game for days): the first-start crashes Vampinity is fixing are on a fresh install with empty caches, which this run doesn't test.
- **The biggest felt problem in a first play is first-time shader builds,** not average fps. Candidates: the background translation and kept-translation work Vampinity has in T129+ (`EDEN_UP_PREP_UNREAD_HANDLE`), async shaders (the menu switch: no hitch, but things draw late), or a shipped pre-built cache.
- **Memory:** a 48-minute session reaching 0 MiB available says the M3 exit ("never under 256 MiB at a transition") is far off, even when it doesn't crash.
