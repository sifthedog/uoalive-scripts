import unittest

from test_support.uo import install
from uo.choice import Choice

CONFIG = {"text": "what happens to the scrolls?", "hue": 996, "poll": 0.5, "timeout": 5.0}
OPTIONS = [("sell", "Sell"), ("unload", "Unload"), ("keep", "Keep")]


class ChoiceTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.stop = [None]
        self.choice = Choice(CONFIG, self.said.append, lambda: self.stop[0])

    def after_pauses(self, count, action):
        pauses = [0]

        def pause(seconds):
            pauses[0] += 1

            if pauses[0] == count:
                action()

        self.api.Pause = pause

    def test_the_pressed_button_is_the_answer(self):
        self.after_pauses(2, lambda: self.api.press("Unload"))

        self.assertEqual(self.choice.ask(OPTIONS), "unload")
        self.assertEqual(self.said, ["asking - what happens to the scrolls?",
                                     "'Unload' was pressed"])
        self.assertTrue(self.api.drawn[-1].IsDisposed)

    def test_each_button_answers_with_its_own_key(self):
        self.after_pauses(1, lambda: self.api.press("Keep"))

        self.assertEqual(self.choice.ask(OPTIONS), "keep")

    def test_closing_the_gump_answers_nothing(self):
        self.after_pauses(2, self.api.close_drawn)

        self.assertIsNone(self.choice.ask(OPTIONS))
        self.assertEqual(self.said[-1], "the gump was closed")

    def test_a_reason_to_stop_answers_nothing(self):
        self.after_pauses(1, lambda: self.stop.__setitem__(0, "dead"))

        self.assertIsNone(self.choice.ask(OPTIONS))
        self.assertEqual(self.said[-1], "the run has a reason to stop")

    def test_the_timeout_answers_nothing(self):
        self.api.Pause = lambda seconds: None

        self.assertIsNone(self.choice.ask(OPTIONS))
        self.assertEqual(self.said[-1], "nothing was pressed in 5s")

    def test_a_stop_request_ends_the_wait(self):
        self.after_pauses(1, lambda: setattr(self.api, "StopRequested", True))

        self.assertIsNone(self.choice.ask(OPTIONS))
        self.assertEqual(self.said[-1], "the run is being stopped")
