import unittest

import uo.clock
from test_support.uo import install
from uo.roam import Roam


class Frozen(object):
    def __init__(self, at):
        self.at = at

    def time(self):
        return self.at


class Source(object):
    def __init__(self, answer):
        self.answer = answer

    def scan(self):
        return self.answer

    def skipped_unreachable(self):
        return 0


class Silent(object):
    def reset(self):
        pass


class RoamWaitTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.saved = uo.clock.time
        self.clock = Frozen(1000.0)
        uo.clock.time = self.clock

    def tearDown(self):
        uo.clock.time = self.saved

    def roam(self, wait):
        return Roam(Source((None, 1000.0 + 150.0)), None, None, None, {
            "noun": "spot",
            "idle_message": "waiting",
            "none_left": "nothing",
            "wait": wait,
            "worked_out": "this ground is worked out",
            "range": 0,
            "scan_radius": 4,
            "z_range": 20,
            "survey_arts": 5,
            "max_walks": 4,
            "pathfind_timeout": 10,
            "idle_poll": 10.0,
            "idle_log_every": 60.0,
        }, self.said.append, Silent(), lambda: "stop after one slice")

    def test_stops_with_the_soonest_return_when_told_not_to_wait(self):
        self.assertEqual(self.roam(False).approach(),
                         ("stop", "this ground is worked out, the soonest is back in 2m"))
        self.assertEqual(self.api.pauses, [])

    def test_waits_otherwise(self):
        self.assertEqual(self.roam(True).approach(), ("waited",))
        self.assertEqual(self.said, ["waiting"])
