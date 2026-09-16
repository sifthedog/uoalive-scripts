import unittest

from spellweaving.config import FIRST_BAND, STAGES
from uo.stages import goal_of, make_plan, stage_now


class ShippedStagesTest(unittest.TestCase):
    def setUp(self):
        self.plan = make_plan(STAGES)

    def test_the_table_is_already_in_the_order_it_trains_in(self):
        self.assertEqual(STAGES, self.plan)

    def test_the_last_band_is_where_a_power_scroll_leaves_off(self):
        self.assertEqual(goal_of(self.plan), 120.0)

    def test_the_first_band_ends_where_a_solo_run_can_start(self):
        self.assertEqual(self.plan[0]["up_to"], FIRST_BAND)

    def test_every_band_costs_mana(self):
        for stage in STAGES:
            self.assertGreater(stage["mana"], 0, stage["spell"])

    # A kind with no cursor to answer is dead config: cast.py only reads it on a self row
    def test_a_band_naming_a_cursor_kind_also_answers_a_cursor(self):
        for stage in STAGES:
            if "target_kind" in stage:
                self.assertEqual(stage.get("target"), "self", stage["spell"])

    # The one row the trance has to work around: index.py stows the weapon and draws it again
    def test_only_immolating_weapon_wants_a_weapon(self):
        armed = [stage["spell"] for stage in STAGES if stage.get("needs_weapon")]

        self.assertEqual(armed, ["Immolating Weapon"])

    # Each band takes the hardest spell it can cast, so an easier row above a harder one is a table
    # that has slipped
    def test_the_spells_get_harder_band_by_band(self):
        rank = [(stage["min_skill"], stage["mana"]) for stage in self.plan]

        self.assertEqual(rank, sorted(rank))

    # A band opening under its spell's minimum is a band that can only fizzle
    def test_no_band_opens_below_what_its_spell_needs(self):
        floor = 0.0

        for stage in self.plan:
            self.assertLessEqual(stage["min_skill"], floor, stage["spell"])
            floor = stage["up_to"]

    # Nothing reads the row's timeout back, so a row that named neither would silently fall to the
    # 2.0s fallback and read every long cast as unreadable
    def test_every_band_paces_itself(self):
        for stage in STAGES:
            self.assertIn("cast_timeout", stage, stage["spell"])
            self.assertIn("cast_delay", stage, stage["spell"])

    def test_picks_immolating_weapon_on_the_exclusive_edge_of_the_first_band(self):
        self.assertEqual(stage_now(self.plan, 20.0)["spell"], "Immolating Weapon")

    def test_picks_arcane_circle_below_it(self):
        self.assertEqual(stage_now(self.plan, 19.9)["spell"], "Arcane Circle")

    def test_is_still_training_one_tenth_short_of_the_goal(self):
        self.assertEqual(stage_now(self.plan, 119.9)["spell"], "Word of Death")

    def test_is_finished_at_the_goal(self):
        self.assertIsNone(stage_now(self.plan, 120.0))
