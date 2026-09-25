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

    def test_rows_stacks_the_buttons_in_a_scroll_area_that_still_answers_a_press(self):
        self.choice = Choice(dict(CONFIG, rows=2), self.said.append, lambda: self.stop[0])
        self.after_pauses(1, lambda: self.api.press("Keep"))

        self.assertEqual(self.choice.ask(OPTIONS), "keep")

        gump = self.api.drawn[-1]
        area = [child for child in gump.children if child.kind == "scroll"][0]

        self.assertEqual([child.text for child in area.children], ["Sell", "Unload", "Keep"])
        self.assertEqual([child.rect[1] for child in area.children], [0, 34, 68])

    def test_a_run_already_being_stopped_draws_nothing(self):
        self.api.StopRequested = True

        self.assertIsNone(self.choice.ask(OPTIONS))
        self.assertEqual(self.said, ["not asking - the run is being stopped"])
        self.assertEqual(self.api.drawn, [])
