import unittest

from lockpicking.config import (BOX_RANGE, DELAY, LOCKPICK_GRAPHIC, MAX_THROTTLED, OUTCOME_TEXT,
                                SET_TEXT)


class OutcomeOrderTest(unittest.TestCase):
    def test_throttled_is_last(self):
        names = [name for name, _phrases in OUTCOME_TEXT]

        self.assertEqual(names[-1], "throttled")

    def test_every_bucket_has_its_own_phrases(self):
        names = [name for name, _phrases in OUTCOME_TEXT]

        self.assertEqual(len(names), len(set(names)))

        for _name, phrases in OUTCOME_TEXT:
            self.assertGreater(len(phrases), 0)

    def test_picked_failed_unskilled_saving_and_throttled_are_all_buckets(self):
        names = [name for name, _phrases in OUTCOME_TEXT]

        for name in ("picked", "failed", "unskilled", "saving", "throttled"):
            self.assertIn(name, names)

    def test_the_set_line_is_not_an_outcome(self):
        for _name, phrases in OUTCOME_TEXT:
            self.assertNotIn(SET_TEXT[0], phrases)


class SettingsTest(unittest.TestCase):
    def test_leaves_a_pause_between_two_picks(self):
        self.assertGreater(DELAY, 0)

    def test_max_throttled_is_positive(self):
        self.assertGreater(MAX_THROTTLED, 0)

    def test_the_box_is_looked_for_within_reach(self):
        self.assertGreater(BOX_RANGE, 0)
        self.assertLessEqual(BOX_RANGE, 2)

    def test_the_lockpick_is_an_art_id(self):
        self.assertIsInstance(LOCKPICK_GRAPHIC, int)


if __name__ == "__main__":
    unittest.main()
