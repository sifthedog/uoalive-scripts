import unittest

from chivalry.config import HEAL_OUTCOME_TEXT, OUTCOME_TEXT
from uo.journal import matched_bucket
from test_support.uo import install


def names_of(buckets):
    return [name for name, _phrases in buckets]


class OutcomeTextTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_every_phrase_reads_as_its_own_bucket(self):
        for name, phrases in OUTCOME_TEXT:
            for phrase in phrases:
                self.api.journal = [phrase]

                self.assertEqual(matched_bucket(OUTCOME_TEXT), name, phrase)

    def test_no_phrase_sits_in_two_buckets(self):
        phrases = [phrase for _name, bucket in OUTCOME_TEXT for phrase in bucket]

        self.assertEqual(len(set(phrases)), len(phrases))

    def test_already_casting_is_read_before_the_bare_throttle_and_throttled_last(self):
        names = names_of(OUTCOME_TEXT)

        self.assertLess(names.index("alreadyCasting"), names.index("throttled"))
        self.assertEqual(names[-1], "throttled")

    def test_has_the_endings_a_paladin_reaches(self):
        names = names_of(OUTCOME_TEXT)

        self.assertIn("noTithing", names)
        self.assertIn("noWeapon", names)

    def test_a_karma_refusal_reads_as_unskilled(self):
        self.api.journal = ["Your karma is not high enough to cast this spell"]

        self.assertEqual(matched_bucket(OUTCOME_TEXT), "unskilled")

    def test_writes_down_no_bucket_this_run_cannot_reach(self):
        names = names_of(OUTCOME_TEXT)

        self.assertNotIn("noReagents", names)
        self.assertNotIn("formLocked", names)


class HealTextTest(unittest.TestCase):
    def test_throttled_is_last(self):
        self.assertEqual(names_of(HEAL_OUTCOME_TEXT)[-1], "throttled")

    def test_names_the_two_failures_that_change_the_run(self):
        self.assertIn("noBandages", names_of(HEAL_OUTCOME_TEXT))
        self.assertIn("healed", names_of(HEAL_OUTCOME_TEXT))
