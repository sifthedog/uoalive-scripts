import unittest

from test_support.uo import install, mobile
from uo.travel import chase, keep_up


class ChaseTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.animal = mobile(serial=5, distance=8)
        self.api.see(self.animal)

    def test_a_pathfind_that_arrives_reads_as_closed(self):
        self.api.reachable = True

        self.assertEqual(chase(5, 2, 10), "closed")

    def test_ground_made_up_reads_as_gained(self):
        def pathfind(serial, within, wait=False, timeout=None, run=False):
            self.animal.Distance = 5

            return False

        self.api.PathfindEntity = pathfind

        self.assertEqual(chase(5, 2, 10), "gained")

    def test_no_ground_made_up_reads_as_stuck(self):
        self.assertEqual(chase(5, 2, 10), "stuck")

    def test_a_mobile_that_vanished_reads_as_stuck(self):
        def pathfind(serial, within, wait=False, timeout=None, run=False):
            del self.api.mobiles[5]

            return False

        self.api.PathfindEntity = pathfind

        self.assertEqual(chase(5, 2, 10), "stuck")


class KeepUpTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.see(mobile(serial=5, distance=8))

    def test_follows_a_mobile_that_walked_off(self):
        keep_up(5, 2, 10)

        self.assertEqual(self.api.pathfound, [(5, 2)])

    def test_leaves_a_mobile_in_reach_alone(self):
        self.api.see(mobile(serial=5, distance=1))
        keep_up(5, 2, 10)

        self.assertEqual(self.api.pathfound, [])

    def test_does_not_reissue_while_already_pathfinding(self):
        self.api.pathfinding = True
        keep_up(5, 2, 10)

        self.assertEqual(self.api.pathfound, [])
