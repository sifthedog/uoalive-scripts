import unittest

from potionkeg.prompt import CountPrompt
from test_support.uo import install

CONFIG = {"text": "How many?", "default": 1, "hue": 996, "poll": 0.5}


class CountPromptTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.prompt = CountPrompt(CONFIG, lambda message: None, lambda: None)

    def schedule(self, action):
        self.api.Pause = lambda seconds: action()

    def test_bare_ok_takes_the_prefilled_default(self):
        self.schedule(lambda: self.api.press("OK"))

        self.assertEqual(self.prompt.ask(), 1)

    def test_a_typed_number_wins(self):
        def type_and_press():
            self.api.type_into(0, "5")
            self.api.press("OK")

        self.schedule(type_and_press)

        self.assertEqual(self.prompt.ask(), 5)

    def test_cancel_answers_none_even_over_a_typed_number(self):
        def type_and_cancel():
            self.api.type_into(0, "5")
            self.api.press("Cancel")

        self.schedule(type_and_cancel)

        self.assertIsNone(self.prompt.ask())
