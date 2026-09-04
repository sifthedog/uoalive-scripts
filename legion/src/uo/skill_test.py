import unittest

from test_support.uo import install, skill
from uo.skill import skill_value, wait_for_skill


class SkillValueTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_a_client_that_has_not_answered_reads_zero(self):
        self.assertEqual(skill_value("Mining"), 0.0)

    def test_reads_the_value(self):
        self.api.skills["Mining"] = skill(63.4)

        self.assertEqual(skill_value("Mining"), 63.4)


class WaitForSkillTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_returns_as_soon_as_the_client_answers(self):
        self.api.skills["Mining"] = skill(63.4)

        self.assertEqual(wait_for_skill("Mining", 5.0, 0.5).Value, 63.4)
        self.assertEqual(self.api.paused, 0.0)

    def test_gives_up_after_the_timeout(self):
        self.assertIsNone(wait_for_skill("Mining", 1.0, 0.5))
        self.assertAlmostEqual(self.api.paused, 1.0)

    def test_a_genuine_zero_is_waited_out_then_returned(self):
        self.api.skills["Mining"] = skill(0.0)

        self.assertEqual(wait_for_skill("Mining", 1.0, 0.5).Value, 0.0)
