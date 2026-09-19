import unittest

from spellweaving.config import (HEAL_ATTEMPTS, HEAL_FLOOR, HEAL_OUTCOME_TEXT, HEAL_SPELL, HEAL_TO,
                                 HURT_FLOOR, OUTCOME_TEXT)
from test_support.uo import install
from uo.journal import matched_bucket


def names_of(buckets):
    return [name for name, _phrases in buckets]


class FloorsTest(unittest.TestCase):
    # The guard runs right after the mend, so a stop at or above the trigger would end the run
    # before a heal ever went off
    def test_the_run_stops_below_the_mark_it_heals_at(self):
        self.assertLess(HURT_FLOOR, HEAL_FLOOR)

    def test_heals_past_the_floor_that_asked_for_it(self):
        self.assertLess(HEAL_FLOOR, HEAL_TO)

    def test_aims_at_full_hits(self):
        self.assertEqual(HEAL_TO, 1.0)

    def test_gives_a_mend_more_than_one_cast(self):
        self.assertGreater(HEAL_ATTEMPTS, 1)


class HealSpellTest(unittest.TestCase):
    # cast.py reads target_kind only on a self row, and a kind on anything else is dead config
    def test_is_a_self_row_naming_the_cursor_the_shard_raises(self):
        self.assertEqual(HEAL_SPELL["target"], "self")
        self.assertEqual(HEAL_SPELL["target_kind"], "beneficial")

    def test_costs_mana_the_loop_can_gather_before_it(self):
        self.assertGreater(HEAL_SPELL["mana"], 0)


class HealTextTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_every_phrase_reads_as_its_own_bucket(self):
        for name, phrases in HEAL_OUTCOME_TEXT:
            for phrase in phrases:
                self.api.journal = [phrase]

                self.assertEqual(matched_bucket(HEAL_OUTCOME_TEXT), name, phrase)

    def test_already_casting_is_read_before_the_bare_throttle_and_throttled_last(self):
        names = names_of(HEAL_OUTCOME_TEXT)

        self.assertLess(names.index("alreadyCasting"), names.index("throttled"))
        self.assertEqual(names[-1], "throttled")

    # Greater Heal is the only thing this run casts that spends reagents, and the book itself has
    # none, so the bucket belongs here and nowhere else
    def test_names_the_reagents_the_spellweaving_table_never_needs(self):
        self.assertIn("noReagents", names_of(HEAL_OUTCOME_TEXT))
        self.assertNotIn("noReagents", names_of(OUTCOME_TEXT))

    def test_retires_on_the_two_refusals_the_healer_cannot_answer(self):
        names = names_of(HEAL_OUTCOME_TEXT)

        self.assertIn("noReagents", names)
        self.assertIn("unskilled", names)

