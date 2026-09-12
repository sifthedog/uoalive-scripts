import unittest

from test_support.uo import install
from uo.meditate import Meditation

BUCKETS = [
    ("blocked", ["You cannot focus your concentration while confused"]),
    ("unskilled", ["You are not sufficiently skilled"]),
    ("full", ["You are at peace"]),
    ("saving", ["The world is saving"]),
]


class FakeMana(object):
    def __init__(self, enough=False, watch_results=None):
        self._enough = enough
        self._watch_results = list(watch_results or [])
        self.watch_calls = []

    def enough(self, need):
        return self._enough

    def target(self, need):
        return need

    def watch(self, need, budget):
        self.watch_calls.append((need, budget))

        return self._watch_results.pop(0) if self._watch_results else False


class FakeSaves(object):
    def __init__(self):
        self.waited_out = 0

    def wait_out(self):
        self.waited_out += 1


class MeditationTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.saves = FakeSaves()
        self.meditating_flag = [False]

    def meditating(self):
        return self.meditating_flag[0]

    def make(self, mana, attempts=3, timeout=1.0, start_timeout=1.0, wait_slice=0.1,
             regen_timeout=10.0):
        return Meditation(
            "Meditation", BUCKETS, mana, self.meditating, self.said.append, self.saves,
            attempts, timeout, start_timeout, wait_slice, regen_timeout,
        )

    # UseSkill is what raises the meditation attempt; the journal answers as its side effect, the
    # same way the shard's own response would land after ClearJournal wiped what came before
    def hear_on_use(self, *phrases):
        real_use_skill = self.api.UseSkill

        def use_skill(name):
            real_use_skill(name)
            self.api.hear(*phrases)

        self.api.UseSkill = use_skill

    def test_already_enough_mana_needs_no_meditation(self):
        mana = FakeMana(enough=True)
        meditation = self.make(mana)

        self.assertTrue(meditation.regain(20, True))
        self.assertEqual(self.api.used_skills, [])

    def test_not_allowed_falls_back_to_natural_regeneration(self):
        mana = FakeMana(enough=False, watch_results=[True])
        meditation = self.make(mana)

        self.assertTrue(meditation.regain(20, False))
        self.assertEqual(self.api.used_skills, [])
        self.assertEqual(mana.watch_calls, [(20, 10.0)])

    def test_blocked_retires_meditation_for_the_run(self):
        self.hear_on_use("You cannot focus your concentration while confused")
        mana = FakeMana(enough=False, watch_results=[True])
        meditation = self.make(mana)

        self.assertTrue(meditation.regain(20, True))
        self.assertIsNotNone(meditation.refused())
        self.assertEqual(mana.watch_calls, [(20, 10.0)])

    def test_once_refused_a_later_call_never_tries_again(self):
        self.hear_on_use("You are not sufficiently skilled")
        mana = FakeMana(enough=False, watch_results=[False, True])
        meditation = self.make(mana)

        meditation.regain(20, True)
        uses_after_first = len(self.api.used_skills)
        meditation.regain(20, True)

        self.assertEqual(len(self.api.used_skills), uses_after_first)

    def test_full_is_an_immediate_success(self):
        self.hear_on_use("You are at peace, your mana is full")
        mana = FakeMana(enough=False)
        meditation = self.make(mana)

        self.assertTrue(meditation.regain(20, True))
        self.assertIsNone(meditation.refused())
        self.assertEqual(mana.watch_calls, [])

    def test_saving_waits_it_out_then_checks_mana(self):
        self.hear_on_use("The world is saving")
        mana = FakeMana(enough=False, watch_results=[True])
        meditation = self.make(mana)

        self.assertTrue(meditation.regain(20, True))
        self.assertEqual(self.saves.waited_out, 1)

    def test_silence_with_the_buff_already_up_reads_as_a_trance(self):
        self.meditating_flag[0] = True
        mana = FakeMana(enough=False, watch_results=[True])
        meditation = self.make(mana)

        self.assertTrue(meditation.regain(20, True))
        self.assertIsNone(meditation.refused())

    def test_already_meditating_skips_using_the_skill_again(self):
        self.meditating_flag[0] = True
        mana = FakeMana(enough=False, watch_results=[True])
        meditation = self.make(mana)

        meditation.regain(20, True)

        self.assertEqual(self.api.used_skills, [])

    def test_gives_up_after_every_attempt_fails(self):
        mana = FakeMana(enough=False, watch_results=[False, False, False])
        meditation = self.make(mana, attempts=3)

        self.assertFalse(meditation.regain(20, True))
        self.assertEqual(len(self.api.used_skills), 3)

    def test_a_second_attempt_can_still_succeed(self):
        mana = FakeMana(enough=False, watch_results=[False, True])
        meditation = self.make(mana, attempts=3)

        self.assertTrue(meditation.regain(20, True))
        self.assertEqual(len(self.api.used_skills), 2)


if __name__ == "__main__":
    unittest.main()
