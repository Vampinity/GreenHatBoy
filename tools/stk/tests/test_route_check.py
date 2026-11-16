"""Tests for route_check.py (waveydude's, 16 Nov 2026; unchanged but for the import path and the last test,
which covers the one change: END is not a check)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from route_check import check, route_checks, tail_moves  # noqa: E402

ROUTE_PUSH_TAIL = """# menu by screen
0 WAIT 180 LOOK 1 2 3 4 1x1:00
1.5 A 150
0 WAIT 240 LOOK 1 2 3 4 1x1:00
0.5 STEER 194 948,883 896,745 r=6
0.648 LSTICK 139 0 12000
13 MAYBE 10 LOOK 1 2 3 4 1x1:00
0.5 LSTICK 128 0 86400000
"""
ROUTE_CHECKED_END = """0 WAIT 180 LOOK 1 2 3 4 1x1:00
0.5 STEER 194 948,883 896,745 r=6
0.6 LSTICK 139 0 3000
0 WAIT 90 LOOK 9 9 9 9 1x1:00
60 END
"""


def lines(*events):
    return '\n'.join(f'[EglantinePS5] test: EDEN_TEST {e}' for e in events)


class RouteCheck(unittest.TestCase):
    def test_counts_harness_line_numbers(self):
        self.assertEqual(route_checks(ROUTE_PUSH_TAIL), [(2, 'WAIT'), (4, 'WAIT'), (5, 'STEER'), (7, 'MAYBE')])

    def test_tail_moves_ignore_comments_and_maybe(self):
        self.assertEqual(tail_moves(ROUTE_PUSH_TAIL), 2)   # the two pushes after the STEER; the MAYBE confirms nothing
        self.assertEqual(tail_moves(ROUTE_CHECKED_END), 0)  # END is the last line

    def test_good_run_with_push_tail_is_tail_unverified(self):
        # the 16 Nov river runs and the good runs both look like this
        err = lines('script_start file=r.txt', 'wait_met line=2 at=40', 'wait_met line=4 at=65',
                    'steer_met line=5 at=211 point=2/2', 'wait_skipped line=7 at=234')
        r = check(err, ROUTE_PUSH_TAIL)
        self.assertEqual(r['route_result'], 'tail_unverified')
        self.assertEqual((r['steer_legs_met'], r['steer_legs_expected']), (1, 1))

    def test_checked_end_is_completed(self):
        err = lines('script_start file=r.txt', 'wait_met line=1 at=40', 'steer_met line=2 at=200 point=2/2',
                    'wait_met line=4 at=230', 'script_end line=5 at=290', 'script_done at=290')
        self.assertEqual(check(err, ROUTE_CHECKED_END)['route_result'], 'completed')

    def test_steer_timeout_fails(self):
        err = lines('script_start file=r.txt', 'wait_met line=1 at=40',
                    'steer_timeout line=2 at=391 point=0/2 looks=138 seen=0', 'script_stopped at=391')
        r = check(err, ROUTE_CHECKED_END)
        self.assertEqual(r['route_result'], 'failed')
        self.assertIn('steer_timeout at line 2, point 0/2', r['route_reason'])

    def test_required_wait_timeout_fails_but_maybe_does_not(self):
        err = lines('script_start file=r.txt', 'wait_timeout line=2 at=715 best=0', 'script_stopped at=715')
        self.assertEqual(check(err, ROUTE_PUSH_TAIL)['route_result'], 'failed')
        err2 = lines('script_start file=r.txt', 'wait_met line=2', 'wait_met line=4', 'steer_met line=5 point=2/2',
                     'wait_skipped line=7 at=234')
        self.assertNotEqual(check(err2, ROUTE_PUSH_TAIL)['route_result'], 'failed')

    def test_pulled_before_the_end_is_unknown_not_completed(self):
        err = lines('script_start file=r.txt', 'wait_met line=2 at=40', 'wait_met line=4 at=65')
        r = check(err, ROUTE_PUSH_TAIL)
        self.assertEqual(r['route_result'], 'unknown')
        self.assertIn('STEER lines [5]', r['route_reason'])

    def test_recording_is_manual(self):
        self.assertEqual(check(lines('on boot= script= record=1', 'record_start file=x'))['route_result'], 'manual')

    def test_no_route_file_uses_end_line(self):
        self.assertEqual(check(lines('script_start file=r.txt', 'script_done at=300'))['route_result'], 'completed')
        self.assertEqual(check(lines('script_start file=r.txt', 'steer_met line=5 point=1/1'))['route_result'], 'unknown')

    def test_route_hash(self):
        self.assertEqual(len(check(lines('script_done at=1'), ROUTE_CHECKED_END)['route_sha256_12']), 12)


    def test_end_is_not_a_check(self):
        # the new-game route's shape: a WAIT, then presses and a stand nothing confirms, then END
        route = "0 WAIT 30 LOOK 1 2 3 4 1x1:00\n0.4 A 150\n1.4 A 150\n30 END\n"
        self.assertEqual(tail_moves(route), 2)
        err = lines('script_start file=r.txt', 'wait_met line=1 at=40', 'script_end line=4 at=72', 'script_done at=72')
        self.assertEqual(check(err, route)['route_result'], 'tail_unverified')


if __name__ == '__main__':
    unittest.main()
