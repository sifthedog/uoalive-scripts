import unittest

from test_support.uo import install, skill
from uo.skill import SkillReader, find_skill_name, skill_value, wait_for_skill


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


class SkillReaderTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.reader = SkillReader("Magery")

    def test_a_client_that_has_not_answered_reads_as_unknown(self):
        self.api.skills["Magery"] = skill(0.0)

        self.assertIsNone(self.reader.read())

    def test_a_missing_skill_reads_as_unknown(self):
        self.assertIsNone(self.reader.read())

    def test_a_real_zero_reads_once_the_client_has_answered(self):
        self.api.skills["Magery"] = skill(41.2)
        self.reader.read()
        self.api.skills["Magery"] = skill(0.0)

        self.assertEqual(self.reader.read(), 0.0)

    def test_falls_back_to_the_configured_name(self):
        self.assertEqual(self.reader.name(), "Magery")

    def test_prefers_the_name_the_client_gives(self):
        answered = skill(41.2)
        answered.Name = "Magery (Mage)"
        self.api.skills["Magery"] = answered

        self.assertEqual(self.reader.name(), "Magery (Mage)")

    def test_waits_until_the_client_answers(self):
        pauses = [0]

        def pause(seconds):
            pauses[0] += 1

            if pauses[0] == 2:
                self.api.skills["Magery"] = skill(41.2)

        self.api.Pause = pause

        self.assertEqual(self.reader.wait(5.0, 0.5), 41.2)

    def test_gives_up_after_the_timeout(self):
        self.assertIsNone(self.reader.wait(1.0, 0.5))

    def test_a_genuine_zero_is_waited_out_then_returned(self):
        self.api.skills["Magery"] = skill(0.0)

        self.assertEqual(self.reader.wait(1.0, 0.5), 0.0)
        self.assertAlmostEqual(self.api.paused, 1.0)

    def test_a_zero_accepted_by_the_wait_keeps_reading(self):
        self.api.skills["Magery"] = skill(0.0)
        self.reader.wait(1.0, 0.5)

        self.assertEqual(self.reader.read(), 0.0)
        self.assertEqual(self.reader.last(), 0.0)

    def test_a_stop_during_the_wait_reads_as_unknown(self):
        self.api.skills["Magery"] = skill(0.0)
        self.api.StopRequested = True

        self.assertIsNone(self.reader.wait(1.0, 0.5))

    def test_two_readers_do_not_share_the_latch(self):
        self.api.skills["Magery"] = skill(41.2)
        self.reader.read()
        self.api.skills["Magery"] = skill(0.0)

        self.assertIsNone(SkillReader("Magery").read())


class FindSkillNameTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_the_first_name_the_client_answers_to(self):
        self.api.skills["Blacksmith"] = skill(70.0)

        self.assertEqual(find_skill_name(["Blacksmithy", "Blacksmith"]), "Blacksmith")

    def test_a_name_that_throws_is_skipped(self):
        def get(name):
            if name == "Blacksmithy":
                raise ValueError(name)

            return skill(70.0)

        self.api.GetSkill = get

        self.assertEqual(find_skill_name(["Blacksmithy", "Blacksmith"]), "Blacksmith")

    def test_none_when_nothing_answers(self):
        self.assertIsNone(find_skill_name(["Blacksmithy"]))


class LastReadingTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.reader = SkillReader("Magery")

    def test_last_is_the_live_reading_while_the_client_answers(self):
        self.api.skills["Magery"] = skill(41.2)

        self.assertEqual(self.reader.last(), 41.2)

    def test_last_falls_back_to_the_latest_reading_once_the_client_goes_quiet(self):
        self.api.skills["Magery"] = skill(41.2)
        self.reader.read()
        self.api.skills["Magery"] = skill(41.3)
        self.reader.read()
        del self.api.skills["Magery"]

        self.assertIsNone(self.reader.read())
        self.assertEqual(self.reader.last(), 41.3)

    def test_last_is_none_when_nothing_was_ever_read(self):
        self.assertIsNone(self.reader.last())
