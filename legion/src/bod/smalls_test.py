import unittest

from bod.config import ARTICLES, DEED_TEXT, PLAIN_MATERIAL
from bod.smalls import find_small_deeds, matches
from test_support.uo import install, item

CONFIG = {
    "text": DEED_TEXT,
    "plain": PLAIN_MATERIAL,
    "articles": ARTICLES,
    "opl_timeout": 1,
    "deed_graphics": set([0x2258]),
    "deed_words": ["bulk order deed"],
}

LARGE = {"large": True, "entries": [("bascinet", 0), ("helmet", 0), ("norse helm", 15)],
         "total": 15, "exceptional": True, "material": "iron"}


def small(item_name, done, total=15, exceptional=True, material="iron"):
    return {"large": False, "item": item_name, "done": done, "entries": [(item_name, done)],
            "total": total, "exceptional": exceptional, "material": material}


class MatchesTest(unittest.TestCase):
    def test_same_item_size_quality_and_material(self):
        self.assertTrue(matches(small("bascinet", 3), LARGE))

    def test_anything_else_does_not(self):
        self.assertFalse(matches(small("dagger", 0), LARGE))
        self.assertFalse(matches(small("bascinet", 0, total=20), LARGE))
        self.assertFalse(matches(small("bascinet", 0, exceptional=False), LARGE))
        self.assertFalse(matches(small("bascinet", 0, material="valorite"), LARGE))
        self.assertFalse(matches(dict(LARGE), LARGE))


class FindSmallDeedsTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def deed(self, serial, lines, graphic=0x2258, name=""):
        self.api.props[serial] = "\n".join(lines)

        return item(serial=serial, graphic=graphic, name=name)

    def test_finds_the_matching_smalls_and_skips_the_large(self):
        self.api.hold(
            self.deed(1, ["large bulk order", "amount to make: 15", "bascinet: 0", "helmet: 0",
                          "All items must be exceptional."]),
            self.deed(2, ["small bulk order", "amount to make: 15", "bascinet: 4",
                          "All items must be exceptional."]),
            self.deed(3, ["small bulk order", "amount to make: 15", "helmet: 0"]),
            item(serial=4, graphic=0x1BF2, name="Ingots", amount=50),
        )

        self.assertEqual(find_small_deeds(LARGE, 1, CONFIG), {"bascinet": {"serial": 2, "done": 4}})

    def test_the_fuller_of_two_wins(self):
        self.api.hold(
            self.deed(2, ["small bulk order", "amount to make: 15", "bascinet: 4",
                          "All items must be exceptional."]),
            self.deed(3, ["small bulk order", "amount to make: 15", "bascinet: 9",
                          "All items must be exceptional."]),
        )

        self.assertEqual(find_small_deeds(LARGE, 1, CONFIG)["bascinet"]["serial"], 3)

    def test_a_deed_is_known_by_name_too(self):
        self.api.hold(self.deed(2, ["small bulk order", "amount to make: 15", "helmet: 0",
                                    "All items must be exceptional."], graphic=0x1111,
                                name="a bulk order deed"))

        self.assertEqual(list(find_small_deeds(LARGE, 1, CONFIG).keys()), ["helmet"])
