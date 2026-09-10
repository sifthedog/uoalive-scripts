import unittest

from test_support.uo import install, item
from uo.convert import Converter


class Saves(object):
    def is_saving(self):
        return False


class ConverterTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.converted = []
        self.after = None

    def perform(self, stack):
        if self.after is not None:
            self.api.hold(*self.after)

        return True

    def build(self):
        stacks = [item(serial=1, graphic=0x19B9, hue=0, amount=10)]

        return Converter({
            "noun": "ore",
            "attempts": 3,
            "passes": 1,
            "delay": 0.0,
            "timeout": 1.0,
            "poll": 0.5,
            "throttled_text": ["wait"],
            "unskilled_text": ["no idea"],
            "wait_on_save": False,
            "saving_message": "saving",
            "next_source": lambda skip: stacks[0],
            "perform": self.perform,
            "blocked": lambda: None,
            "learn_product": lambda gained: None,
            "converted": lambda gained, lost: self.converted.append((gained, lost)),
            "nothing_to_do": lambda skip: None,
            "about_to_convert": lambda: None,
        }, self.said.append, Saves())

    def test_the_converted_hook_sees_what_the_pack_gained_and_lost(self):
        self.api.hold(item(serial=1, graphic=0x19B9, hue=0, amount=10))
        self.after = [item(serial=2, graphic=0x1BF2, hue=0, amount=5)]

        self.build().run()

        self.assertEqual(self.converted, [({(0x1BF2, 0): 5}, {(0x19B9, 0): 10})])

    def test_a_pack_that_held_still_is_not_a_conversion(self):
        self.api.hold(item(serial=1, graphic=0x19B9, hue=0, amount=10))

        self.build().run()

        self.assertEqual(self.converted, [])
