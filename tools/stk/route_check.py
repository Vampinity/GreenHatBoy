#!/usr/bin/env python3
"""Did a scripted run actually run its route? (contract item 3)

Original: waveydude, 16 Nov 2026. One change by
GrowingBlackBeans, to offer back: END is not a check. It only ends the script and confirms nothing, so
moves before it and after the last STEER/WAIT are a tail nothing confirms. Counting END as a check made
the new-game route (door presses, a 30 s stand, END) and the field route (120 s with no input after the
load, END) score `completed`.

Reads the test harness's EDEN_TEST lines (stderr.log) and, when it can find it, the route script itself, and
answers with one of:
  completed     every STEER leg was met, no required WAIT timed out, and the route's last check passed
  tail_unverified  every STEER leg and required WAIT passed, but the script has moves after its last check
                   (a timed push, a stand) that nothing confirms; the run may still have gone off the path
  failed        a STEER leg or a required WAIT timed out, or the script stopped early
  manual        no script ran (hand-played or recorded)
  unknown       not enough lines to tell (a pull before the end, a lost stderr)

Why tail_unverified exists: on 16 Nov 2026 two 9.40 runs met all 13 STEER points and then a timed push ran Link
into the river by town; the harness lines of those runs look exactly like a good run's. A route that ends with a
check in its destination (a STEER to a point there, or a LOOK only that place matches) turns them into
completed or failed. A MAYBE that times out is expected and never fails a run.

  route_check.py <run dir> [--route FILE]     prints JSON
Usable as a module: check(stderr_text, route_text=None) -> dict.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

TEST = re.compile(r'EDEN_TEST (\w+)(.*)')
LINE = re.compile(r'\bline=(\d+)')
POINT = re.compile(r'\bpoint=(\d+)/(\d+)')
CHECKS = re.compile(r'^\s*[\d.]+\s+(STEER|WAIT|MAYBE|END)\b')


def route_checks(route_text: str) -> list[tuple[int, str]]:
    """(line number, kind) of every STEER / WAIT / MAYBE / END in a route, numbered as the harness numbers them."""
    out = []
    for number, line in enumerate(route_text.splitlines(), start=1):
        m = CHECKS.match(line)
        if m:
            out.append((number, m.group(1)))
    return out


def tail_moves(route_text: str) -> int:
    """Lines that press or push after the route's last STEER/WAIT (MAYBEs and END don't confirm anything)."""
    lines = route_text.splitlines()
    last = 0
    for number, line in enumerate(lines, start=1):
        m = CHECKS.match(line)
        if m and m.group(1) in ('STEER', 'WAIT'):
            last = number
    moves = 0
    for line in lines[last:]:
        s = line.strip()
        if s and not s.startswith('#') and not CHECKS.match(s):
            moves += 1
    return moves


def check(stderr_text: str, route_text: str | None = None) -> dict:
    events = []
    for raw in stderr_text.splitlines():
        m = TEST.search(raw)
        if m:
            events.append((m.group(1), m.group(2)))
    kinds = [k for k, _ in events]
    result = {
        'route_result': 'unknown', 'route_reason': '', 'steer_legs_met': 0, 'steer_legs_expected': None,
        'required_waits_met': 0, 'required_waits_expected': None, 'route_sha256_12': None,
    }
    if route_text is not None:
        result['route_sha256_12'] = hashlib.sha256(route_text.encode()).hexdigest()[:12]
    if not any(k in ('script_start', 'steer_met', 'wait_met', 'script_done', 'script_end') for k in kinds):
        if any(k in ('record_start',) for k in kinds) or not kinds or 'on' in kinds:
            result.update(route_result='manual', route_reason='no script ran')
        return result
    met_lines = {int(LINE.search(a).group(1)) for k, a in events if k == 'steer_met' and LINE.search(a)}
    wait_lines = {int(LINE.search(a).group(1)) for k, a in events if k == 'wait_met' and LINE.search(a)}
    result['steer_legs_met'] = len(met_lines)
    result['required_waits_met'] = len(wait_lines)
    for k, a in events:
        if k in ('steer_timeout', 'wait_timeout'):
            where = LINE.search(a)
            point = POINT.search(a)
            result.update(route_result='failed', route_reason=f'{k} at line {where.group(1) if where else "?"}'
                          + (f', point {point.group(1)}/{point.group(2)}' if point else ''))
            return result
        if k == 'script_stopped':
            result.update(route_result='failed', route_reason='script stopped early')
            return result
        if k in ('script_error', 'wait_error'):
            result.update(route_result='failed', route_reason=f'{k}{a[:60]}')
            return result
    if route_text is not None:
        checks = route_checks(route_text)
        steers = [n for n, kind in checks if kind == 'STEER']
        waits = [n for n, kind in checks if kind == 'WAIT']
        result['steer_legs_expected'] = len(steers)
        result['required_waits_expected'] = len(waits)
        missing = [n for n in steers if n not in met_lines]
        missing_waits = [n for n in waits if n not in wait_lines]
        if missing or missing_waits:
            result.update(route_result='unknown',
                          route_reason=f'not reached (pulled before the end?): STEER lines {missing}, WAIT lines {missing_waits}')
            return result
        if tail_moves(route_text):
            result.update(route_result='tail_unverified',
                          route_reason=f'all {len(steers)} STEER legs and {len(waits)} WAITs passed; '
                                       f'{tail_moves(route_text)} move lines after the last check are unconfirmed')
            return result
        result.update(route_result='completed', route_reason=f'all {len(steers)} STEER legs and {len(waits)} WAITs passed')
        return result
    # No route file: judge by the harness lines alone.
    if 'script_done' in kinds or 'script_end' in kinds:
        result.update(route_result='completed', route_reason='script ran to its end (route file not found: legs not counted)')
    else:
        result.update(route_result='unknown', route_reason='no end line and no route file to count legs against')
    return result


def find_route(run_dir: Path, name: str | None) -> Path | None:
    if not name:
        return None
    for cand in (run_dir / name, run_dir / 'route.txt', run_dir.parent.parent / name, run_dir.parent.parent / 'routes' / name):
        if cand.is_file():
            return cand
    return None


def main(argv: list[str]) -> int:
    run = Path(argv[1])
    route = None
    if '--route' in argv:
        route = Path(argv[argv.index('--route') + 1])
    stderr = (run / 'stderr.log').read_text(errors='replace') if (run / 'stderr.log').is_file() else ''
    if route is None:
        env = (run / 'env.txt').read_text(errors='replace') if (run / 'env.txt').is_file() else ''
        m = re.search(r'^EDEN_TEST_SCRIPT=(\S+)', env, re.M)
        route = find_route(run, m.group(1) if m else None)
    out = check(stderr, route.read_text(errors='replace') if route else None)
    out['route_file'] = str(route) if route else None
    print(json.dumps(out, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
