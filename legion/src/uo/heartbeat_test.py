import unittest

import uo.heartbeat
from test_support.uo import install
from uo.heartbeat import Heartbeat


class HeartbeatTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.clock = [1000.0]
        self.said = []
        self.saved = uo.heartbeat.now
        uo.heartbeat.now = lambda: self.clock[0]
        self.beat = Heartbeat(60.0, self.said.append, "swings", lambda: "at 1,2, 100/400")

    def tearDown(self):
        uo.heartbeat.now = self.saved

    def test_the_first_call_only_starts_the_clock(self):
        self.beat.beat("digging", 1, 0)

        self.assertEqual(self.said, [])

    def test_stays_quiet_inside_the_interval(self):
        self.beat.beat("digging", 1, 0)
        self.clock[0] += 59.0
        self.beat.beat("digging", 2, 3)

        self.assertEqual(self.said, [])

    def test_reports_once_the_interval_has_passed(self):
        self.beat.beat("digging", 1, 0)
        self.clock[0] += 60.0
        self.beat.beat("digging", 9, 4)

        self.assertEqual(self.said, ["still here - digging, cycle 9, at 1,2, 100/400, 4 swings"])

    def test_the_clock_restarts_after_a_report(self):
        self.beat.beat("digging", 1, 0)
        self.clock[0] += 60.0
        self.beat.beat("digging", 2, 0)
        self.clock[0] += 59.0
        self.beat.beat("digging", 3, 0)

        self.assertEqual(len(self.said), 1)

    def test_reset_pushes_the_next_beat_a_full_interval_out(self):
        self.beat.beat("digging", 1, 0)
        self.clock[0] += 59.0
        self.beat.reset()
        self.clock[0] += 59.0
        self.beat.beat("digging", 2, 0)

        self.assertEqual(self.said, [])
