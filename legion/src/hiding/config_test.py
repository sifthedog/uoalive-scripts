import unittest

from hiding.config import MAX_THROTTLED, OUTCOME_TEXT, PACE_FLOOR, PACE_MAX


class OutcomeOrderTest(unittest.TestCase):
    def test_busy_is_read_before_failed_and_throttled_is_last(self):
        names = [name for name, _phrases in OUTCOME_TEXT]

        self.assertLess(names.index("busy"), names.index("failed"))
        self.assertEqual(names[-1], "throttled")

    def test_every_bucket_has_its_own_phrases(self):
        names = [name for name, _phrases in OUTCOME_TEXT]

        self.assertEqual(len(names), len(set(names)))

        for _name, phrases in OUTCOME_TEXT:
            self.assertGreater(len(phrases), 0)

    def test_hidden_unskilled_saving_and_throttled_are_all_distinct_buckets(self):
        names = [name for name, _phrases in OUTCOME_TEXT]

        for name in ("hidden", "failed", "unskilled", "saving", "throttled"):
            self.assertIn(name, names)


class PaceTest(unittest.TestCase):
    def test_max_throttled_is_positive(self):
        self.assertGreater(MAX_THROTTLED, 0)

    def test_floor_is_under_the_ceiling(self):
        self.assertLessEqual(PACE_FLOOR, PACE_MAX)


if __name__ == "__main__":
    unittest.main()
