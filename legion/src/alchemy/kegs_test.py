import unittest

from alchemy.config import KEG_FILLED_TEXT, KEG_GRAPHICS, KEG_NAME_WORDS
from alchemy.kegs import Kegs
from uo.dump import Dump
from test_support.uo import install, item

POISON = 0x0F0A
KEG = 0x1940

CONFIG = {"graphics": KEG_GRAPHICS, "words": KEG_NAME_WORDS, "filled_text": KEG_FILLED_TEXT,
          "move_delay": 0.0}


class KegsTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.started = item(serial=1, graphic=KEG, name="A keg of Poison potions")
        self.api.hold(self.started)
        self.dump = Dump(None, {"poison": set([POISON])}, {"keep_existing": True}, self.api.SysMsg)
        self.kegs = Kegs(self.dump, CONFIG, self.api.SysMsg)

        def move(serial, container, amount=-1):
            self.api.moved.append((serial, container, amount))
            self.api.take(serial)

            return True

        self.api.MoveItem = move

    def test_the_bottled_potion_lands_on_the_first_empty_keg(self):
        empty = item(serial=2, graphic=KEG, name="A specially lined keg")
        made = item(serial=3, graphic=POISON, name="a poison potion")
        self.api.hold(self.started, empty, made)

        self.assertEqual(self.kegs.empty().Serial, 2)
        self.assertEqual(self.kegs.run(), 1)
        self.assertEqual(self.api.moved, [(3, 2, 1)])
        self.assertIn("poured 1 into 'A specially lined keg'", "\n".join(self.api.messages))

    def test_no_empty_keg_moves_nothing_and_says_so(self):
        self.api.hold(self.started, item(serial=3, graphic=POISON, name="a poison potion"))

        self.assertIsNone(self.kegs.empty())
        self.assertEqual(self.kegs.run(), 0)
        self.assertEqual(self.api.moved, [])
        self.assertIn("no empty keg in the pack for the 1 potions", "\n".join(self.api.messages))

    def test_nothing_made_is_no_miss_to_report(self):
        self.api.hold(self.started, item(serial=2, graphic=KEG, name="A specially lined keg"))

        self.assertEqual(self.kegs.run(), 0)
        self.assertEqual(self.api.messages, [])
