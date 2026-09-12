import unittest

from test_support.uo import install
from uo.cast import Caster


class NeverAnswers(object):
    def answer(self):
        return False


class Spends(object):
    """The reading taken before the cast, then the one the shard is left holding."""

    def __init__(self, *readings):
        self._readings = list(readings)

    def __call__(self):
        return self._readings.pop(0) if len(self._readings) > 1 else self._readings[0]


class Arrives(object):
    """A buff the bar publishes on the call after the one that reads it before the cast."""

    def __init__(self):
        self._asked = 0

    def __call__(self, stage):
        self._asked += 1

        return self._asked > 1


class PreTargetTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []

    def caster(self):
        return Caster([], lambda stage: False, NeverAnswers(), False, 0.2, 0.1, 0.1, 0.1,
                      self.said.append)

    def test_a_self_row_that_names_no_kind_queues_a_beneficial_cursor(self):
        self.caster().cast_once({"spell": "Stone Form", "target": "self"})

        self.assertEqual(self.api.pre_targeted, [(self.api.Player.Serial, "beneficial")])

    def test_a_self_row_queues_the_kind_it_names(self):
        self.caster().cast_once({"spell": "Hail Storm", "target": "self",
                                 "target_kind": "harmful"})

        self.assertEqual(self.api.pre_targeted, [(self.api.Player.Serial, "harmful")])

    def test_a_row_with_no_cursor_to_answer_queues_nothing(self):
        self.caster().cast_once({"spell": "Nether Bolt"})

        self.assertEqual(self.api.pre_targeted, [])
        self.assertEqual(self.api.cancelled_pre_targets, 0)

    def test_the_queued_target_is_taken_back_down_after_the_cast(self):
        self.caster().cast_once({"spell": "Stone Form", "target": "self"})

        self.assertEqual(self.api.cancelled_pre_targets, 1)


class SpendProofTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []

    def caster(self, spent=None, standing=lambda stage: False):
        return Caster([], standing, NeverAnswers(), False, 0.2, 0.1, 0.1, 0.1,
                      self.said.append, spent)

    def test_a_silent_outcome_that_spent_the_currency_reads_as_a_fizzle(self):
        caster = self.caster(Spends(10, 0))

        self.assertEqual(caster.cast_once({"spell": "Holy Light"}), "fizzled")

    def test_a_silent_outcome_that_spent_nothing_is_still_unread(self):
        caster = self.caster(Spends(10, 10))

        self.assertIsNone(caster.cast_once({"spell": "Holy Light"}))

    def test_a_proved_cast_is_not_reread_as_a_fizzle_by_the_same_spending(self):
        caster = self.caster(Spends(10, 0), Arrives())

        self.assertEqual(caster.cast_once({"spell": "Divine Fury"}), "cast")

    def test_a_school_that_hands_over_no_currency_reads_the_way_it_always_did(self):
        self.assertIsNone(self.caster().cast_once({"spell": "Nether Bolt"}))


class LateLookTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []

    def caster(self, spent=None):
        return Caster([("alreadyCasting", ["not yet recovered"])], lambda stage: False,
                      NeverAnswers(), False, 0.2, 0.3, 0.1, 0.1, self.said.append, spent)

    def paces(self, caster, stage):
        caster.pace(stage)

        return [seconds for seconds in self.api.pauses if seconds == 0.3]

    def test_a_spend_that_lands_after_the_window_is_still_read(self):
        caster = self.caster(Spends(10, 10, 0))

        self.assertEqual(caster.cast_once({"spell": "Holy Light"}), "fizzled")

    def test_and_the_pace_it_stood_through_is_not_spent_again(self):
        caster = self.caster(Spends(10, 10, 0))

        caster.cast_once({"spell": "Holy Light"})

        self.assertEqual(self.paces(caster, {"spell": "Holy Light"}), [0.3])

    def test_a_wording_that_lands_after_the_window_is_still_read(self):
        caster = self.caster()

        def pause(seconds):
            self.api.pauses.append(seconds)

            if seconds == 0.3:
                self.api.hear("You have not yet recovered from casting a spell.")

        self.api.Pause = pause

        self.assertEqual(caster.cast_once({"spell": "Holy Light"}), "alreadyCasting")

    def test_an_attempt_nothing_ever_answered_for_is_still_unread(self):
        caster = self.caster(Spends(10, 10, 10))

        self.assertIsNone(caster.cast_once({"spell": "Holy Light"}))

    # Or the row that stood through no late look would go on to skip the pace it owes
    def test_an_outcome_the_window_read_pays_its_pace_as_it_always_did(self):
        caster = self.caster(Spends(10, 0))

        self.assertEqual(caster.cast_once({"spell": "Holy Light"}), "fizzled")
        self.assertEqual(self.paces(caster, {"spell": "Holy Light"}), [0.3])
