import unittest

from magery.config import STAGES
from uo.stages import goal_of, make_plan, stage_now


class ShippedStagesTest(unittest.TestCase):
    def setUp(self):
        self.plan = make_plan(STAGES)

    def test_the_table_is_already_in_the_order_it_trains_in(self):
        self.assertEqual(STAGES, self.plan)

    def test_the_last_band_is_where_the_table_stops(self):
        self.assertEqual(goal_of(self.plan), 120.0)

    def test_every_band_costs_mana(self):
        for stage in STAGES:
            self.assertGreater(stage["mana"], 0, stage["spell"])

    def test_mana_climbs_band_by_band(self):
        costs = [stage["mana"] for stage in self.plan]

        self.assertEqual(costs, sorted(costs))

    # Nothing reads the row's timeout back, so a row that named neither would silently fall to the
    # fallback and read every long cast as unreadable
    def test_every_band_paces_itself(self):
        for stage in STAGES:
            self.assertIn("cast_timeout", stage, stage["spell"])
            self.assertIn("cast_delay", stage, stage["spell"])

    # Earthquake hits everything nearby rather than the caster, so the mana falling is its only
    # proof - every other band has a buff to check first
    def test_only_earthquake_has_no_buff_to_prove_itself_by(self):
        buffless = [stage for stage in STAGES if "buff" not in stage]

        self.assertEqual([stage["spell"] for stage in buffless], ["Earthquake"])

    def test_picks_earthquake_on_the_exclusive_edge_of_the_last_band(self):
        self.assertEqual(stage_now(self.plan, 80.0)["spell"], "Earthquake")

    def test_picks_invisibility_below_it(self):
        self.assertEqual(stage_now(self.plan, 79.9)["spell"], "Invisibility")

    def test_is_still_training_one_tenth_short_of_the_goal(self):
        self.assertEqual(stage_now(self.plan, 119.9)["spell"], "Earthquake")

    def test_is_finished_at_the_goal(self):
        self.assertIsNone(stage_now(self.plan, 120.0))


if __name__ == "__main__":
    unittest.main()
