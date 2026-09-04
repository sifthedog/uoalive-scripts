import unittest

from test_support.uo import install
from uo.journal import matched_bucket, read_outcome, said

BUCKETS = [("empty", ["there is nothing here"]), ("saving", ["saving"])]


class SaidTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_is_false_on_an_empty_journal(self):
        self.assertFalse(said(["anything"]))

    def test_matches_a_substring(self):
        self.api.hear("You put the ore in your pack")

        self.assertTrue(said(["put the ore"]))

    def test_leaves_the_line_for_the_next_read(self):
        self.api.hear("world is saving")
        said(["saving"])

        self.assertTrue(said(["saving"]))


class MatchedBucketTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_is_none_when_nothing_was_said(self):
        self.assertIsNone(matched_bucket(BUCKETS))

    def test_names_the_bucket_that_matched(self):
        self.api.hear("there is nothing here to mine")

        self.assertEqual(matched_bucket(BUCKETS), "empty")

    def test_clears_the_match_so_it_answers_once(self):
        self.api.hear("there is nothing here to mine")
        matched_bucket(BUCKETS)

        self.assertIsNone(matched_bucket(BUCKETS))

    def test_takes_the_first_bucket_in_order(self):
        self.api.hear("there is nothing here", "world is saving")

        self.assertEqual(matched_bucket(BUCKETS), "empty")


class ReadOutcomeTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_returns_none_after_the_budget(self):
        self.assertIsNone(read_outcome(BUCKETS, 1.0, 0.2))

    def test_reads_before_it_waits(self):
        self.api.hear("world is saving")

        self.assertEqual(read_outcome(BUCKETS, 1.0, 0.2), "saving")
        self.assertEqual(self.api.paused, 0.0)

    def test_spends_the_whole_budget_on_silence(self):
        read_outcome(BUCKETS, 1.0, 0.5)

        self.assertAlmostEqual(self.api.paused, 1.0)
