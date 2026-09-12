import unittest

from armslore.config import MAX_THROTTLED, OUTCOME_TEXT


class OutcomeOrderTest(unittest.TestCase):
    def test_missed_is_read_before_read_and_read_is_last(self):
        names = [name for name, _phrases in OUTCOME_TEXT]

        self.assertLess(names.index("missed"), names.index("read"))
        self.assertEqual(names[-1], "read")

    def test_every_bucket_has_its_own_phrases(self):
        names = [name for name, _phrases in OUTCOME_TEXT]

        self.assertEqual(len(names), len(set(names)))

        for _name, phrases in OUTCOME_TEXT:
            self.assertGreater(len(phrases), 0)

    def test_unskilled_saving_and_throttled_are_all_distinct_buckets(self):
        names = [name for name, _phrases in OUTCOME_TEXT]

        self.assertIn("unskilled", names)
        self.assertIn("saving", names)
        self.assertIn("throttled", names)


class ThrottleTest(unittest.TestCase):
    def test_max_throttled_is_positive(self):
        self.assertGreater(MAX_THROTTLED, 0)


if __name__ == "__main__":
    unittest.main()
