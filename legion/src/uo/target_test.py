import unittest

from uo.target import SelfTarget, request_one
from test_support.uo import install

ANSWERS = ["Target(player)", "TargetSelf", "Target(serial)"]


class RequestOneTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_the_answered_serial_comes_back(self):
        self.api.requested_target = 0x40001234

        self.assertEqual(request_one(1.0), 0x40001234)

    def test_esc_or_a_timeout_answers_none(self):
        self.api.requested_target = 0

        self.assertIsNone(request_one(1.0))

    def test_a_stale_cursor_is_cancelled_before_the_request(self):
        self.api.has_target = True

        request_one(1.0)

        self.assertEqual(self.api.cancelled_targets, 1)

    def test_a_cursor_still_up_after_the_answer_is_cancelled_too(self):
        real_request_target = self.api.RequestTarget

        def request_target(timeout=None):
            self.api.has_target = True

            return real_request_target(timeout)

        self.api.RequestTarget = request_target
        self.api.requested_target = 0x40001234

        request_one(1.0)

        self.assertEqual(self.api.cancelled_targets, 1)


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
