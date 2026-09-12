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


class Memory(object):
    def __init__(self):
        self.unreachable = []

    def mark_unreachable(self, spot):
        self.unreachable.append(spot)


class NeverSaving(object):
    def is_saving(self):
        return False


CONFIG = {
    "noun": "spot",
    "idle_message": "waiting",
    "none_left": "nothing",
    "wait": False,
    "worked_out": "worked out",
    "range": 2,
    "scan_radius": 4,
    "z_range": 20,
    "survey_arts": 5,
    "max_walks": 2,
    "pathfind_timeout": 10,
    "idle_poll": 10.0,
    "idle_log_every": 60.0,
}


class RoamApproachTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.memory = Memory()
        self.saves = NeverSaving()

    def roam(self, spot, config=None, saves=None):
        merged = dict(CONFIG)
        merged.update(config or {})

        return Roam(Source((spot, None)), self.memory, saves or self.saves, Silent(), merged,
                    self.said.append, Silent(), lambda: None)

    def test_a_spot_within_range_is_the_target(self):
        spot = {"x": 1001, "y": 1001, "z": 0, "distance": 1}

        self.assertEqual(self.roam(spot).approach(), ("target", spot))

    def test_a_spot_outside_range_is_walked_towards(self):
        spot = {"x": 1050, "y": 1000, "z": 0, "distance": 999}

        self.assertEqual(self.roam(spot).approach(), ("walked",))
        self.assertEqual(self.api.pathfound, [((1050, 1000, 0), 2)])
        self.assertEqual(self.api.cancelled_pathfinding, 1)
        self.assertEqual(self.memory.unreachable, [])

    def test_getting_closer_does_not_write_the_spot_off(self):
        spot = {"x": 1050, "y": 1000, "z": 0, "distance": 50}
        self.api.Player.X = 1040

        self.roam(spot).approach()

        self.assertEqual(self.memory.unreachable, [])

    def test_no_progress_writes_the_spot_off(self):
        spot = {"x": 1050, "y": 1000, "z": 0, "distance": 50}
        self.api.Player.X = 1000

        self.roam(spot).approach()

        self.assertEqual(self.memory.unreachable, [spot])

    def test_a_step_that_does_not_move_during_a_save_is_not_a_wall(self):
        spot = {"x": 1050, "y": 1000, "z": 0, "distance": 50}
        self.api.Player.X = 1000

        class Saving(object):
            def is_saving(self):
                return True

        self.roam(spot, saves=Saving()).approach()

        self.assertEqual(self.memory.unreachable, [])

    def test_max_walks_toward_the_same_spot_writes_it_off(self):
        spot = {"x": 1050, "y": 1000, "z": 0, "distance": 50}
        self.api.Player.X = 1040
        roam = self.roam(spot, config={"max_walks": 2})

        roam.approach()
        roam.approach()
        outcome = roam.approach()

        self.assertEqual(outcome, ("walked",))
        self.assertEqual(self.memory.unreachable, [spot])

    def test_a_different_spot_resets_the_walk_count(self):
        first = {"x": 1050, "y": 1000, "z": 0, "distance": 999}
        second = {"x": 1000, "y": 1050, "z": 0, "distance": 999}
        self.api.Player.X = 1040
        roam = self.roam(first, config={"max_walks": 5})

        roam.approach()
        roam.approach()
        self.assertEqual(roam._walking_cycles, 2)

        roam._source = Source((second, None))
        roam.approach()

        self.assertEqual(roam._walking_cycles, 1)

    def test_no_walkable_route_is_reported(self):
        class Unreachable(Source):
            def skipped_unreachable(self):
                return 3

            def survey(self, radius, arts):
                pass

        roam = Roam(Unreachable((None, None)), self.memory, self.saves, Silent(), CONFIG,
                    self.said.append, Silent(), lambda: None)

        self.assertEqual(roam.approach(), ("stop", "nothing"))
        self.assertIn("3 spot(s) matched but had no walkable route", self.said)
