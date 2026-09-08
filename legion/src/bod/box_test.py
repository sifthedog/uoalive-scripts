import unittest

from bod.box import DeedBox
from test_support.uo import install, item

BOX = 0x40000B0B
LARGE = 0x40001111

CONFIG = {
    "names": ["bulk order deed box"],
    "deed_graphics": set([0x2258]),
    "deed_words": ["bulk order deed"],
    "move_delay": 0.1,
    "timeout": 1.0,
    "poll": 0.5,
}


class DeedBoxTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.box = DeedBox(CONFIG, self.said.append)
        self.large = item(serial=LARGE, graphic=0x2258, container=self.api.Backpack)
        self.api.hold(item(serial=BOX, name="Bulk Order Deed Box"), self.large)

    def test_found_by_name(self):
        self.assertEqual(self.box.find(), BOX)

    def test_none_without_one(self):
        self.api.hold(self.large)

        self.assertIsNone(self.box.find())

    def test_moves_the_large_in_uses_the_box_and_waits_for_the_deeds(self):
        def move(serial, container, amount=-1):
            self.api.moved.append((serial, container, amount))
            self.large.Container = container

        def use(serial):
            self.api.used.append(serial)
            self.large.Container = self.api.Backpack
            self.api.hold(item(serial=BOX, name="Bulk Order Deed Box"), self.large,
                          item(serial=5, graphic=0x2258), item(serial=6, graphic=0x2258))

        self.api.MoveItem = move
        self.api.UseObject = use

        self.assertEqual(self.box.generate(BOX, LARGE), [5, 6])
        self.assertEqual(self.api.moved, [(LARGE, BOX, -1)])
        self.assertEqual(self.api.used, [BOX])
        self.assertTrue(any("put 2 deed" in line for line in self.said))

    def test_a_deed_that_did_not_go_in_is_none(self):
        self.assertIsNone(self.box.generate(BOX, LARGE))
        self.assertEqual(self.api.used, [])
        self.assertTrue(any("did not go into the box" in line for line in self.said))

    def test_a_box_that_gives_nothing_is_empty_and_says_where_the_large_is(self):
        self.api.MoveItem = lambda serial, container, amount=-1: setattr(self.large, "Container",
                                                                          container)

        self.assertEqual(self.box.generate(BOX, LARGE), [])
        self.assertTrue(any("still in it" in line for line in self.said))
