# runPlay7: hand play that crashed at 49.5 min (22 Nov 2026)

**What this is.** Hand play on alpha T186 (01.219.028), handheld 1x, play6's settings plus five leads (`env.txt`;
`env-fallback.txt` is play6). Not a measured start: it proves nothing about any one line.

**The logs are the crash copy.** The app relaunched after the crash and overwrote its main log, so `eden_log.txt`,
`stderr.log` and `heap.log` here are the console's crash copies (`crash-20261122-082253-*`), renamed so the toolkit
reads them as the run. The relaunch's short stderr and heap files and both boot traces are left out: neither boot
trace could be matched to the crashed process.

**The crash** (`crash-20261122-082253.txt`): SIGSEGV on CPUCore_4, 2,970 s after the app started, at an address
outside the app's code (a system library or generated code), with the largest free block at 1 MiB. The last log
lines before it are a Hang watch report and a GPU split line with 10 s list waits: the memory wall, then the crash.
Nothing in the log ties the crash to any of the five leads, and runPlay8 leaves three of them out.
