import unittest

from test_support.uo import install
from uo.gump import await_changed, gump_says


class AwaitChangedTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_a_stale_gump_does_not_count(self):
        self.api.gump = 77

        self.assertEqual(await_changed(77, 1.0, 0.25), 0)

    def test_returns_the_new_gump(self):
        self.api.gump = 78

        self.assertEqual(await_changed(77, 1.0, 0.25), 78)

    def test_reads_a_gump_that_arrives_late(self):
        pauses = [0]

        def pause(seconds):
            pauses[0] += 1

            if pauses[0] == 2:
                self.api.gump = 78

        self.api.Pause = pause

        self.assertEqual(await_changed(0, 1.0, 0.25), 78)

    def test_gives_up_after_the_timeout(self):
        self.assertEqual(await_changed(0, 1.0, 0.25), 0)
        self.assertAlmostEqual(self.api.paused, 1.0)


class GumpSaysTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_is_false_for_an_empty_gump(self):
        self.assertFalse(gump_says(1, ["release this creature"]))

    def test_matches_any_of_the_wordings(self):
        self.api.gump_text = ["Are you sure you wish to release this creature?"]

        self.assertTrue(gump_says(1, ["nothing like it", "release this creature"]))
