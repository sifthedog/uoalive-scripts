import unittest

from mysticism.config import FIRST_BAND, STAGES
from uo.stages import goal_of, make_plan, stage_now


class ShippedStagesTest(unittest.TestCase):
    def setUp(self):
        self.plan = make_plan(STAGES)

    def test_the_table_is_already_in_the_order_it_trains_in(self):
        self.assertEqual(STAGES, self.plan)

    def test_the_last_band_is_where_a_power_scroll_leaves_off(self):
        self.assertEqual(goal_of(self.plan), 120.0)

    def test_the_first_band_ends_where_the_users_table_starts(self):
        self.assertEqual(self.plan[0]["up_to"], FIRST_BAND)

    def test_every_band_costs_mana(self):
        for stage in STAGES:
            self.assertGreater(stage["mana"], 0, stage["spell"])

    def test_mana_climbs_band_by_band(self):
        costs = [stage["mana"] for stage in self.plan]

        self.assertEqual(costs, sorted(costs))

    # A kind with no cursor to answer is dead config: cast.py only reads it on a self row
    def test_a_band_naming_a_cursor_kind_also_answers_a_cursor(self):
        for stage in STAGES:
            if "target_kind" in stage:
                self.assertEqual(stage.get("target"), "self", stage["spell"])

    def test_only_stone_form_has_a_buff_to_prove_itself_by(self):
        buffed = [stage for stage in STAGES if "buff" in stage]

        self.assertEqual([stage["spell"] for stage in buffed], ["Stone Form"])
        self.assertEqual(buffed[0]["title"], "Stone Form")

    # Nothing reads the row's timeout back, so a row that named neither would silently fall to the
    # 2.0s fallback and read every long cast as unreadable
    def test_every_band_paces_itself(self):
        for stage in STAGES:
            self.assertIn("cast_timeout", stage, stage["spell"])
            self.assertIn("cast_delay", stage, stage["spell"])

    def test_picks_stone_form_on_the_exclusive_edge_of_the_first_band(self):
        self.assertEqual(stage_now(self.plan, 40.0)["spell"], "Stone Form")

    def test_picks_nether_bolt_below_it(self):
        self.assertEqual(stage_now(self.plan, 39.9)["spell"], "Nether Bolt")

    def test_is_still_training_one_tenth_short_of_the_goal(self):
        self.assertEqual(stage_now(self.plan, 119.9)["spell"], "Nether Cyclone")

    def test_is_finished_at_the_goal(self):
        self.assertIsNone(stage_now(self.plan, 120.0))
