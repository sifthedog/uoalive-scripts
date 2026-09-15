import unittest

from assembly.prompt import StartPrompt
from test_support.uo import install

CONFIG = {
    "text": "What to make",
    "options": [("keg", "Keg"), ("potion keg", "Potion keg"), ("clock", "Clock")],
    "assembly_default": "potion keg",
    "count_text": "How many?",
    "default": 1,
    "hue": 996,
    "poll": 0.5,
}


class StartPromptTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.prompt = StartPrompt(CONFIG, lambda message: None, lambda: None)

    def schedule(self, *actions):
        steps = list(actions)

        def slice_(seconds):
            if steps:
                steps.pop(0)()

        self.api.Pause = slice_

    def test_bare_ok_takes_the_default_assembly_and_count(self):
        self.schedule(lambda: self.api.press("OK"))

        self.assertEqual(self.prompt.ask(), {"assembly": "potion keg", "wanted": 1})

    def test_a_picked_radio_wins(self):
        def pick_and_press():
            self.api.check("Clock")
            self.api.press("OK")

        self.schedule(pick_and_press)

        self.assertEqual(self.prompt.ask()["assembly"], "clock")

    def test_a_typed_number_wins(self):
        def type_and_press():
            self.api.check("Keg")
            self.api.type_into(0, "5")
            self.api.press("OK")

        self.schedule(type_and_press)

        self.assertEqual(self.prompt.ask(), {"assembly": "keg", "wanted": 5})

    # wait_for_gump disposes the gump before it returns, and a disposed radio reads as unchecked,
    # so the pick has to have been taken off it while it was still up
    def test_the_pick_survives_the_radios_going_blank(self):
        def press_and_blank():
            self.api.press("OK")
            self.api.uncheck("Clock")

        self.schedule(lambda: self.api.check("Clock"), press_and_blank)

        self.assertEqual(self.prompt.ask()["assembly"], "clock")

    def test_cancel_answers_none_even_over_a_pick(self):
        def pick_and_cancel():
            self.api.check("Clock")
            self.api.type_into(0, "5")
            self.api.press("Cancel")

        self.schedule(pick_and_cancel)

        self.assertIsNone(self.prompt.ask())
