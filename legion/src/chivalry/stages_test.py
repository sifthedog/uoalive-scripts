import unittest

from chivalry.config import FIRST_BAND, STAGES
from uo.stages import goal_of, make_plan, stage_now

# The shard's own minimum for each spell
MINIMUM = {
    "Consecrate Weapon": 15.0,
    "Divine Fury": 25.0,
    "Enemy of One": 45.0,
    "Holy Light": 55.0,
    "Noble Sacrifice": 65.0,
}


class ShippedStagesTest(unittest.TestCase):
    def setUp(self):
        self.plan = make_plan(STAGES)

    def test_the_table_is_already_in_the_order_it_trains_in(self):
        self.assertEqual(STAGES, self.plan)

    def test_the_last_band_is_where_a_power_scroll_leaves_off(self):
        self.assertEqual(goal_of(self.plan), 120.0)

    def test_every_band_costs_mana_and_tithing(self):
        for stage in STAGES:
            self.assertGreater(stage["mana"], 0, stage["spell"])
            self.assertGreater(stage["tithing"], 0, stage["spell"])

    def test_every_band_paces_itself(self):
        for stage in STAGES:
            self.assertIn("cast_timeout", stage, stage["spell"])
            self.assertIn("cast_delay", stage, stage["spell"])

    # Nothing a paladin casts here raises a cursor, and one left open breaks every action after it
    def test_no_band_answers_a_cursor(self):
        for stage in STAGES:
            self.assertNotIn("target", stage, stage["spell"])

    def test_only_the_three_self_buffs_prove_themselves_by_the_bar(self):
        buffed = [stage for stage in STAGES if "buff" in stage]

        self.assertEqual([stage["spell"] for stage in buffed],
                         ["Consecrate Weapon", "Divine Fury", "Enemy of One"])

        self.assertEqual([stage["buff"] for stage in buffed],
                         ["ConsecrateWeapon", "DivineFury", "EnemyOfOne"])

        for stage in buffed:
            self.assertEqual(stage["title"], stage["spell"])

    def test_only_consecrate_weapon_wants_a_weapon(self):
        self.assertEqual([stage["spell"] for stage in STAGES if stage.get("needs_weapon")],
                         ["Consecrate Weapon"])

    def test_every_band_opens_above_the_shards_minimum_for_its_spell(self):
        opens_at = FIRST_BAND

        for stage in self.plan:
            self.assertGreaterEqual(opens_at, MINIMUM[stage["spell"]], stage["spell"])
            opens_at = stage["up_to"]

    def test_hands_over_on_the_exclusive_edge(self):
        self.assertEqual(stage_now(self.plan, 44.9)["spell"], "Consecrate Weapon")
        self.assertEqual(stage_now(self.plan, 45.0)["spell"], "Divine Fury")
        self.assertEqual(stage_now(self.plan, 60.0)["spell"], "Enemy of One")
        self.assertEqual(stage_now(self.plan, 70.0)["spell"], "Holy Light")
        self.assertEqual(stage_now(self.plan, 90.0)["spell"], "Noble Sacrifice")
        self.assertEqual(stage_now(self.plan, 119.9)["spell"], "Noble Sacrifice")

    def test_is_finished_at_the_goal(self):
        self.assertIsNone(stage_now(self.plan, 120.0))
