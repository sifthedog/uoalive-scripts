import unittest

from test_support.uo import install, item, skill
from uo.guards import (dead, first_reason, hurt, no_follower_slots, overweight, pack_full,
                       skill_capped, stopped)


class FirstReasonTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_is_none_when_every_clause_passes(self):
        self.assertIsNone(first_reason([dead(), pack_full(120)]))

    def test_returns_the_first_clause_that_fires(self):
        self.api.StopRequested = True
        self.api.Player.IsDead = True

        self.assertEqual(first_reason([stopped("stopped from the script manager"), dead()]),
                         "stopped from the script manager")

    def test_order_decides_which_reason_is_reported(self):
        self.api.StopRequested = True
        self.api.Player.IsDead = True

        self.assertEqual(first_reason([dead(), stopped("stopped")]), "you are dead")


class ClauseTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_dead_is_quiet_with_no_player(self):
        self.api.Player = None

        self.assertIsNone(dead()())

    def test_pack_full_counts_the_top_level(self):
        self.api.hold(*[item(serial=n) for n in range(120)])

        self.assertEqual(pack_full(120)(), "the pack is at its item cap")

    def test_pack_full_is_quiet_under_the_cap(self):
        self.api.hold(*[item(serial=n) for n in range(119)])

        self.assertIsNone(pack_full(120)())

    def test_overweight_names_the_reading(self):
        self.api.Player.Weight = 380
        self.api.Player.WeightMax = 400

        self.assertEqual(overweight(50)(), "overweight at 380/400")

    def test_skill_capped_ignores_a_client_that_has_not_answered(self):
        self.api.skills["Bowcraft"] = skill(0.0, 0.0)

        self.assertIsNone(skill_capped("Bowcraft")())

    def test_skill_capped_fires_at_the_cap(self):
        self.api.skills["Bowcraft"] = skill(100.0, 100.0)

        self.assertEqual(skill_capped("Bowcraft")(), "Bowcraft is capped at 100.0")

    def test_skill_capped_is_quiet_for_no_skill_name(self):
        self.assertIsNone(skill_capped(None)())

    def test_skill_capped_reads_the_base_and_not_what_jewelry_adds(self):
        self.api.skills["Magery"] = skill(105.0, 100.0)
        self.api.skills["Magery"].Base = 99.0

        self.assertIsNone(skill_capped("Magery")())

    def test_skill_capped_reports_the_base(self):
        self.api.skills["Magery"] = skill(115.0, 100.0)
        self.api.skills["Magery"].Base = 100.0

        self.assertEqual(skill_capped("Magery")(), "Magery is capped at 100.0")

    def test_hurt_ignores_a_hitsmax_of_zero(self):
        self.api.Player.Hits = 1
        self.api.Player.HitsMax = 0

        self.assertIsNone(hurt(0.5)())

    def test_hurt_fires_below_the_floor(self):
        self.api.Player.Hits = 40
        self.api.Player.HitsMax = 100

        self.assertEqual(hurt(0.5)(), "hurt (40/100)")

    def test_follower_slots_ignore_a_max_of_zero(self):
        self.api.Player.Followers = 5
        self.api.Player.FollowersMax = 0

        self.assertIsNone(no_follower_slots()())

    def test_follower_slots_fire_when_full(self):
        self.api.Player.Followers = 5
        self.api.Player.FollowersMax = 5

        self.assertEqual(no_follower_slots()(), "no follower slots left")
