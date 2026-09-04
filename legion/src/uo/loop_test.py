import unittest

from uo.loop import StallWatch, backoff_for


class Silent(object):
    def __init__(self):
        self.beats = []

    def beat(self, phase, cycle, tally):
        self.beats.append((phase, cycle, tally))

    def reset(self):
        pass


class BackoffForTest(unittest.TestCase):
    def test_grows_with_the_count(self):
        self.assertEqual(backoff_for(3, 2.0, 30.0), 6.0)

    def test_stops_at_the_cap(self):
        self.assertEqual(backoff_for(100, 2.0, 30.0), 30.0)


class StallWatchTest(unittest.TestCase):
    def setUp(self):
        self.said = []
        self.heartbeat = Silent()
        self.stall = StallWatch("cycles without a swing", 2, 4, self.heartbeat, self.said.append)

    def test_has_no_reason_before_the_stop_count(self):
        for cycle in range(3):
            self.stall.end_cycle("digging", cycle, 0)

        self.assertIsNone(self.stall.reason())

    def test_warns_once_at_the_warn_count(self):
        for cycle in range(4):
            self.stall.end_cycle("digging", cycle, 0)

        self.assertEqual(self.said, ["2 cycles without a swing, last was 'digging'"])

    def test_gives_a_reason_at_the_stop_count(self):
        for cycle in range(4):
            self.stall.end_cycle("digging", cycle, 0)

        self.assertEqual(self.stall.reason(), "no progress in 4 cycles, last was 'digging'")

    def test_progress_resets_the_count(self):
        for cycle in range(3):
            self.stall.end_cycle("digging", cycle, 0)

        self.stall.progressed()

        for cycle in range(3):
            self.stall.end_cycle("digging", cycle, 0)

        self.assertIsNone(self.stall.reason())

    def test_beats_the_heartbeat_every_cycle(self):
        self.stall.end_cycle("digging", 7, 2)

        self.assertEqual(self.heartbeat.beats, [("digging", 7, 2)])

    def test_two_watches_do_not_share_a_count(self):
        other = StallWatch("cycles", 2, 4, Silent(), self.said.append)

        for cycle in range(4):
            self.stall.end_cycle("digging", cycle, 0)

        self.assertIsNone(other.reason())
