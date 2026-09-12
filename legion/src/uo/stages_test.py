import unittest

from uo.stages import (band_for, band_rows, cycle_cost, describe_plan, goal_of, make_plan,
                       stage_now)

STAGES = [
    {"up_to": 80.0, "spell": "Invisibility"},
    {"up_to": 45.0, "spell": "Bless"},
    {"up_to": 60.0, "spell": "Arch Protection"},
]


class PlanTest(unittest.TestCase):
    def setUp(self):
        self.plan = make_plan(STAGES)

    def test_orders_the_bands_by_where_they_end(self):
        self.assertEqual([stage["spell"] for stage in self.plan],
                         ["Bless", "Arch Protection", "Invisibility"])

    def test_the_goal_is_the_last_band(self):
        self.assertEqual(goal_of(self.plan), 80.0)

    def test_an_empty_plan_has_no_goal(self):
        self.assertEqual(goal_of([]), 0.0)

    def test_describes_the_bands_in_order(self):
        self.assertEqual(describe_plan(self.plan),
                         "Bless to 45.0, Arch Protection to 60.0, Invisibility to 80.0")


class StageNowTest(unittest.TestCase):
    def setUp(self):
        self.plan = make_plan(STAGES)

    def test_picks_the_first_band_the_value_is_under(self):
        self.assertEqual(stage_now(self.plan, 44.9)["spell"], "Bless")

    def test_the_bands_butt_together_on_the_exclusive_edge(self):
        self.assertEqual(stage_now(self.plan, 45.0)["spell"], "Arch Protection")

    def test_is_none_once_the_last_band_is_finished(self):
        self.assertIsNone(stage_now(self.plan, 80.0))


BANDS = [(60.0, "bow"), (70.0, "crossbow"), (None, "repeating crossbow")]


class BandForTest(unittest.TestCase):
    def test_the_ceiling_is_exclusive(self):
        self.assertEqual(band_for(BANDS, 59.9), "bow")
        self.assertEqual(band_for(BANDS, 60.0), "crossbow")

    def test_a_none_ceiling_catches_everything_above(self):
        self.assertEqual(band_for(BANDS, 119.9), "repeating crossbow")

    def test_an_unread_skill_has_no_band(self):
        self.assertIsNone(band_for(BANDS, None))

    def test_past_the_last_finite_ceiling_is_uncovered(self):
        self.assertIsNone(band_for([(60.0, "bow")], 60.0))


class CycleCostTest(unittest.TestCase):
    def test_adds_the_rows_own_timeout_and_delay(self):
        self.assertAlmostEqual(cycle_cost({"cast_timeout": 3.0, "cast_delay": 0.3}, 2.0, 0.75), 3.3)

    def test_falls_back_for_a_row_that_names_neither(self):
        self.assertAlmostEqual(cycle_cost({}, 2.0, 0.75), 2.75)

    def test_never_reads_as_free(self):
        self.assertAlmostEqual(cycle_cost({"cast_timeout": 0.0, "cast_delay": 0.0}, 0.0, 0.0), 0.1)


class BandRowsTest(unittest.TestCase):
    def test_each_band_is_a_row_from_the_floor_up_with_the_current_one_marked(self):
        rows = band_rows(BANDS, 65.0, lambda product: "bowyer", 30.0)

        self.assertEqual(rows, [("30 - 60  bow  bowyer", False),
                                ("60 - 70  crossbow  bowyer", True),
                                ("70 - cap  repeating crossbow  bowyer", False)])

    def test_a_fractional_edge_keeps_its_decimal(self):
        rows = band_rows([(40.7, "dartboard"), (None, "box")], 0.0, lambda product: "", 0.0)

        self.assertEqual(rows[0][0], "0 - 40.7  dartboard  ")
