import unittest

from fishing.prompt import TilesAheadPrompt
from test_support.uo import install

CONFIG = {"text": "How many tiles ahead?", "default": 4, "hue": 996, "poll": 0.5}


class TilesAheadPromptTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.stop = [None]
        self.prompt = TilesAheadPrompt(CONFIG, self.said.append, lambda: self.stop[0])

    def schedule(self, plan):
        pauses = [0]

        def pause(seconds):
            pauses[0] += 1

            if pauses[0] in plan:
                plan[pauses[0]]()

        self.api.Pause = pause

    def test_bare_ok_takes_the_prefilled_default(self):
        self.schedule({1: lambda: self.api.press("OK")})

        self.assertEqual(self.prompt.ask(), 4)
        self.assertEqual(self.api.text_boxes()[0].Text, "4")

    def test_a_typed_number_wins(self):
        def type_and_press():
            self.api.type_into(0, "9")
            self.api.press("OK")

        self.schedule({1: type_and_press})

        self.assertEqual(self.prompt.ask(), 9)

    def test_blank_zero_negative_and_non_numeric_all_fall_back_to_the_default(self):
        for typed in ("", "0", "-3", "abc"):
            self.api = install()
            self.prompt = TilesAheadPrompt(CONFIG, self.said.append, lambda: self.stop[0])

            def type_and_press(typed=typed):
                self.api.type_into(0, typed)
                self.api.press("OK")

            self.schedule({1: type_and_press})

            self.assertEqual(self.prompt.ask(), 4)

    def test_cancel_takes_the_default_even_over_a_typed_number(self):
        def type_and_cancel():
            self.api.type_into(0, "9")
            self.api.press("Cancel")

        self.schedule({1: type_and_cancel})

        self.assertEqual(self.prompt.ask(), 4)

    def test_closing_the_gump_takes_the_default(self):
        self.schedule({1: self.api.close_drawn})

        self.assertEqual(self.prompt.ask(), 4)

    def test_a_reason_to_stop_takes_the_default(self):
        self.schedule({1: lambda: self.stop.__setitem__(0, "dead")})

        self.assertEqual(self.prompt.ask(), 4)

    def test_a_run_already_being_stopped_draws_nothing(self):
        self.api.StopRequested = True

        self.assertEqual(self.prompt.ask(), 4)
        self.assertEqual(self.api.drawn, [])

    def test_the_gump_is_drawn_centred_with_the_label_box_and_buttons(self):
        self.schedule({1: lambda: self.api.press("OK")})
        self.prompt.ask()

        gump = self.api.drawn[0]
        kinds = [child.kind for child in gump.children]

        self.assertEqual(gump.centered, 2)
        self.assertEqual(kinds, ["box", "label", "textbox", "button", "button"])
        self.assertTrue(gump.IsDisposed)
