# Run logs

One folder per run, in the layout GrowingBlackBeans proposed on 11 Nov 2026:

    runs/<author>/<date>-<run-id>/eden_log.txt.gz   the emulator's log, redacted
                                  env.txt           the settings of that run
                                  run.json          build, firmware, console, route, ending, fps summary
                                  stderr.log.gz     optional: memory census and gate lines
    index.csv (repo root)                           one row per run; start there

Adding a run: copy the run's folder off the console, then

    python3 tools/pack-run.py <run folder> --out . --author <you> --console "PS5 base 13.60" --route "..." --notes "what you saw"
    python3 tools/make-index.py .

The packer redacts home folders, LAN and MAC addresses, e-mail addresses, your login name and every word you list in
`~/.eglantine-private`. Please do not commit logs by hand. No game files, saves, keys or dumps belong here.
