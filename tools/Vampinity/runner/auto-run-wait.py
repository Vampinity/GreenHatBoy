#!/usr/bin/env python3
"""auto-run.py for pad scripts with WAIT lines. Same arguments, same plans, same safety; two changes:

1. The script check knows the WAIT, MAYBE and END lines of headless/test_harness.h (the same rules,
   so a line the app would refuse fails here first), and STEER (headless/minimap_steer.h):
   <s> STEER <timeout_s> <x>,<y> [...] [r=<n>] walks the player through points of the minimap and
   ends its section when the last one is reached.
   auto-run.py's own check refuses those lines.
2. A test ends when its script is done instead of at the plan's time limit:
   - EDEN_TEST script_done in stderr.log: the test ends --tail seconds later (default 10).
   - EDEN_TEST script_stopped (a WAIT timed out, the route did not run): it ends --stopped-grace
     seconds later (default 45), so a game frozen on that screen still shows as a freeze (30 s)
     or a crash first, as auto-run.py sees them.
   Crashes, freezes, GPU waits and the time limit work as in auto-run.py, which runs unchanged
   underneath: this file only loads it and replaces check_script, Batch.look and part of
   Batch.finish_run. The plan's seconds stay the upper bound: set them for a slow run.

  python3 auto-run-wait.py <plan.json> --host <console> [--tail 10] [--stopped-grace 45] [--go]

A script with no WAIT, MAYBE or END line runs exactly as with auto-run.py, to the time limit.
--no-early-end turns the early end off for every test.
"""
import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("auto_run", HERE / "auto-run.py")
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

MAX_CELLS = 256  # test_harness.h kMaxCells
DONE = re.compile(rb"EDEN_TEST script_done at=")
STOPPED = re.compile(rb"EDEN_TEST script_stopped at=|EDEN_TEST wait_error ")
OPTIONS = {"--tail": 10.0, "--stopped-grace": 45.0}
early_end = True

tool.ENDINGS["script_end"] = "script done"
tool.ENDINGS["script_stopped"] = "script stopped: a WAIT timed out"


def number(text, most):
    return tool.plain_number(text, most)


MAX_STEER_POINTS = 64  # test_harness.h kMaxSteerPoints


def check_steer(parts):
    """ParseWait's STEER branch in test_harness.h. Returns the timeout; ValueError if bad."""
    if len(parts) < 4:
        raise ValueError
    timeout = tool.script_seconds(parts[2])
    if timeout * 1000 < 1:
        raise ValueError
    points = parts[3:]
    if len(points) > 1 and points[-1][:2] == "r=":  # the radius comes last, after a point
        if not number(points[-1][2:], 100):
            raise ValueError
        points = points[:-1]
    if not 1 <= len(points) <= MAX_STEER_POINTS:
        raise ValueError
    for point in points:
        x, comma, y = point.partition(",")
        if not comma:
            raise ValueError
        number(x, 1000), number(y, 1000)
    return timeout


def check_wait(parts):
    """ParseWait in test_harness.h. Returns (seconds, timeout or None for END); ValueError if bad."""
    at = tool.script_seconds(parts[0])
    if parts[1] == "STEER":
        return at, check_steer(parts)
    if parts[1] == "END":
        if len(parts) != 2:
            raise ValueError
        return at, None
    if len(parts) not in (9, 10):
        raise ValueError
    timeout = tool.script_seconds(parts[2])
    if timeout * 1000 < 1 or parts[3] not in ("LOOK", "GONE"):  # the app keeps milliseconds
        raise ValueError
    x, y, w, h = (number(v, 1000) for v in parts[4:8])
    if not w or not h or x + w > 1000 or y + h > 1000:
        raise ValueError
    found = re.fullmatch(r"([0-9]+)x([0-9]+):(.*)", parts[8])
    if not found:
        raise ValueError
    cols, rows = number(found[1], 64), number(found[2], 64)
    if not cols or not rows or cols * rows > MAX_CELLS or len(found[3]) != 2 * cols * rows:
        raise ValueError
    if not re.fullmatch(r"[0-9a-fA-F]*", found[3]):
        raise ValueError
    cells = [int(found[3][i:i + 2], 16) for i in range(0, len(found[3]), 2)]
    mean = sum(cells) / len(cells)
    if sum((c - mean) ** 2 for c in cells) / len(cells) < 4:
        raise ValueError
    if len(parts) == 10 and not number(parts[9], 100):
        raise ValueError
    return at, timeout


def check_script(text):
    """(problems, the shortest the script can take): auto-run.py's check plus the WAIT lines. The
    length counts every WAIT as met the moment it starts looking, so the plan print's "last event"
    is a lower bound: a time limit under it is surely too short."""
    problems, total, section_end, ended = [], 0.0, 0.0, False
    for line_number, raw in enumerate(text.split("\n"), 1):
        parts = raw.split("#", 1)[0].split()
        if not parts:
            continue
        try:
            if ended:
                raise ValueError
            if len(parts) > 1 and parts[1] in ("WAIT", "MAYBE", "END", "STEER"):
                at, timeout = check_wait(parts)
                ended = timeout is None
                total += at
                section_end = 0.0
            else:
                wrong, last = tool_check_line(raw)
                if wrong:
                    raise ValueError
                section_end = max(section_end, last)
        except ValueError:
            problems.append(f"line {line_number}: {raw.strip()!r}")
    return problems, total + section_end


tool_check_script = tool.check_script


def tool_check_line(raw):
    return tool_check_script(raw + "\n")


def look(self, run, now, _look=tool.Batch.look):
    ending = _look(self, run, now)
    if not hasattr(run, "wait_script"):
        text = run.test.script.read_text() if run.test.script else ""
        run.wait_script = any(len(p) > 1 and p[1] in ("WAIT", "MAYBE", "END", "STEER")
                              for p in (line.split("#", 1)[0].split() for line in text.split("\n")))
    if ending or not early_end or not run.wait_script or run.game_seen is None:
        return ending
    log = run.folder / "stderr.log"
    if not hasattr(run, "wait_offset"):
        run.wait_offset, run.wait_mark = 0, None
    try:
        with open(log, "rb") as handle:
            handle.seek(max(run.wait_offset - 200, 0))
            data = handle.read()
            run.wait_offset = handle.tell()
    except OSError:
        data = b""
    if run.wait_mark is None:
        if DONE.search(data):
            run.wait_mark = ("script_end", now + OPTIONS["--tail"])
            self.say(f"Script done, the test ends in {OPTIONS['--tail']:g} s")
        elif STOPPED.search(data):
            run.wait_mark = ("script_stopped", now + OPTIONS["--stopped-grace"])
            found = re.search(rb"EDEN_TEST (wait_timeout|wait_error|steer_timeout) [^\n]*", data)
            run.wait_detail = found[0].decode(errors="replace")[:300] if found else ""
            self.say(f"Script stopped ({run.wait_detail or 'a WAIT timed out'}), "
                     f"the test ends in {OPTIONS['--stopped-grace']:g} s unless something else happens first")
    if run.wait_mark and now >= run.wait_mark[1]:
        # As at the time limit: a GPU wait being logged right now may be a freeze on its way.
        if run.last_wait is not None and now - run.last_wait < self.args.stall_grace:
            return None
        return run.wait_mark[0]
    return None


def finish_run(self, run, ending, _finish=tool.Batch.finish_run):
    if ending not in ("script_end", "script_stopped"):
        return _finish(self, run, ending)
    run.end(ending, getattr(run, "wait_detail", "") if ending == "script_stopped" else "")
    self.say(f"{tool.ENDINGS[ending].capitalize()} after {run.result['seconds']} s")
    self.quit_app()
    self.after_close(run, restarted=False)


def parse_args(_parse=tool.parse_args):
    global early_end
    argv = sys.argv[1:]
    for name in OPTIONS:
        if name in argv:
            at = argv.index(name)
            try:
                OPTIONS[name] = float(argv[at + 1])
            except (IndexError, ValueError):
                sys.exit(f"{name} needs a number of seconds")
            del argv[at:at + 2]
    if "--no-early-end" in argv:
        argv.remove("--no-early-end")
        early_end = False
    sys.argv[1:] = argv
    return _parse()


tool.check_script = check_script
tool.Batch.look = look
tool.Batch.finish_run = finish_run
tool.parse_args = parse_args

if __name__ == "__main__":
    sys.exit(tool.main())
