import unittest

from uo.mana import ManaWatch
from test_support.uo import install


class ManaWatchTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.stop = [None]
        self.tranced = [False]

    def watch(self, to_full=True, log_every=10.0):
        return ManaWatch(to_full, 0.5, log_every, self.said.append, lambda: self.stop[0],
                         lambda: self.tranced[0])

    def test_tops_up_to_the_ceiling_when_asked(self):
        self.api.Player.ManaMax = 50

        self.assertEqual(self.watch().target(20), 50)

    def test_asks_only_for_what_is_needed_otherwise(self):
        self.api.Player.ManaMax = 50

        self.assertEqual(self.watch(to_full=False).target(20), 20)

    def test_a_manamax_of_zero_falls_back_to_the_need(self):
        self.api.Player.ManaMax = 0

        self.assertEqual(self.watch().target(20), 20)

    def test_a_pool_past_the_target_is_enough(self):
        self.api.Player.Mana = 50
        self.api.Player.ManaMax = 50

        self.assertTrue(self.watch().enough(20))

    def test_returns_at_once_when_the_pool_is_already_there(self):
        self.api.Player.Mana = 50
        self.api.Player.ManaMax = 50

        self.assertTrue(self.watch().watch(20, 60.0))
        self.assertEqual(self.api.paused, 0.0)

    def test_a_reason_to_stop_ends_the_wait(self):
        self.api.Player.Mana = 0
        self.stop[0] = "you are dead"

        self.assertFalse(self.watch().watch(20, 60.0))
        self.assertEqual(self.api.paused, 0.0)

    def test_gives_up_after_the_budget(self):
        self.api.Player.Mana = 0

        self.assertFalse(self.watch().watch(20, 2.0))
        self.assertAlmostEqual(self.api.paused, 2.0)

    def test_reports_the_pool_on_its_own_cadence(self):
        self.api.Player.Mana = 0
        self.api.Player.ManaMax = 50
        self.watch(log_every=1.0).watch(20, 2.0)

        self.assertEqual(self.said, ["0/50 mana", "0/50 mana"])

    def test_says_when_it_is_meditating(self):
        self.api.Player.Mana = 0
        self.api.Player.ManaMax = 50
        self.tranced[0] = True
        self.watch(log_every=1.0).watch(20, 1.0)

        self.assertEqual(self.said, ["0/50 mana, meditating"])
