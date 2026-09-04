import unittest

from magery.target import SelfTarget
from test_support.uo import install

ANSWERS = ["Target(player)", "TargetSelf", "Target(serial)"]


class SelfTargetTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.target = SelfTarget(ANSWERS, 1.0, 0.1, self.said.append)

    def test_the_first_answer_that_brings_the_cursor_down_wins(self):
        self.api.has_target = True

        self.assertTrue(self.target.answer())
        self.assertEqual(self.said, ["the cursor answers to Target(player)"])

    def test_remembers_what_worked_and_says_it_once(self):
        self.api.has_target = True
        self.target.answer()
        self.api.has_target = True
        self.target.answer()

        self.assertEqual(len(self.said), 1)
        self.assertEqual(self.api.targeted, [(self.api.Player,), (self.api.Player,)])

    def test_moves_on_when_an_answer_throws(self):
        thrown = [0]

        def target(*args):
            thrown[0] += 1

            raise Exception("overload mismatch")

        self.api.Target = target
        self.api.has_target = True

        self.assertTrue(self.target.answer())
        self.assertEqual(self.api.targeted, [("self",)])

    def test_gives_up_when_the_cursor_stays_up(self):
        self.api.Target = lambda *args: None
        self.api.TargetSelf = lambda: None
        self.api.has_target = True

        self.assertFalse(self.target.answer())
        self.assertEqual(self.said[-1], "the cursor would not take a self target")

    def test_two_targets_do_not_share_what_was_learned(self):
        self.api.has_target = True
        self.target.answer()

        other = []
        self.api.has_target = True
        SelfTarget(ANSWERS, 1.0, 0.1, other.append).answer()

        self.assertEqual(other, ["the cursor answers to Target(player)"])
