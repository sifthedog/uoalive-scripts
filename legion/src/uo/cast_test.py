import unittest

from test_support.uo import install
from uo.cast import Caster


class NeverAnswers(object):
    def answer(self):
        return False


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
