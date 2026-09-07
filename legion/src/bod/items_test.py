import unittest

from bod.config import ARTICLES, EXCEPTIONAL_TEXT, MATERIAL_ALIASES, PLAIN_MATERIAL
from bod.items import ItemBook
from test_support.uo import install, item

CONFIG = {
    "aliases": MATERIAL_ALIASES,
    "plain": PLAIN_MATERIAL,
    "articles": ARTICLES,
    "exceptional_text": EXCEPTIONAL_TEXT,
    "opl_timeout": 1,
    "opl_settle": 0.1,
    "asks": 2,
}


def request(exceptional=False, material="iron"):
    return {"item": "platemail gorget", "done": 0, "total": 20,
            "exceptional": exceptional, "material": material}


class ItemBookTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []

    def book(self, **fields):
        return ItemBook(request(**fields), CONFIG, self.said.append)

    def test_a_plain_item_by_name(self):
        self.api.hold(item(serial=1, name="platemail gorget"), item(serial=2, name="bascinet"))
        self.api.props[1] = "platemail gorget\nDurability 40 / 40"
        self.api.props[2] = "bascinet"

        self.assertEqual(self.book().qualifying(), 1)
        self.assertTrue(self.book().is_product(1))
        self.assertFalse(self.book().is_product(2))

    def test_the_article_is_stripped(self):
        self.api.hold(item(serial=1))
        self.api.props[1] = "a platemail gorget"

        self.assertEqual(self.book().qualifying(), 1)

    def test_exceptional_is_required_when_the_deed_says_so(self):
        self.api.hold(item(serial=1), item(serial=2))
        self.api.props[1] = "platemail gorget"
        self.api.props[2] = "platemail gorget\nexceptional"

        self.assertEqual(self.book(exceptional=True).qualifying(), 2)
        self.assertEqual(self.book().qualifying(), 1)

    def test_the_material_folded_into_the_name(self):
        self.api.hold(item(serial=1), item(serial=2))
        self.api.props[1] = "platemail gorget"
        self.api.props[2] = "dull copper platemail gorget"
        book = self.book(material="dull copper")

        self.assertEqual(book.qualifying(), 2)
        self.assertTrue(book.is_product(1))

    def test_the_material_as_its_own_line(self):
        self.api.hold(item(serial=1), item(serial=2))
        self.api.props[1] = "platemail gorget\nShadow Iron"
        self.api.props[2] = "platemail gorget\nCopper"

        self.assertEqual(self.book(material="shadow iron").qualifying(), 1)
        self.assertEqual(self.book(material="copper").qualifying(), 2)

    def test_an_alias_is_a_material_too(self):
        self.api.hold(item(serial=1))
        self.api.props[1] = "shadow platemail gorget"

        self.assertEqual(self.book(material="shadow iron").qualifying(), 1)

    def test_a_rejected_item_is_never_offered_again(self):
        self.api.hold(item(serial=1), item(serial=2))
        self.api.props[1] = "platemail gorget"
        self.api.props[2] = "platemail gorget"
        book = self.book()
        book.reject(1)

        self.assertEqual(book.qualifying(), 2)

    def test_a_tooltip_is_read_once_per_serial(self):
        self.api.hold(item(serial=1))
        self.api.props[1] = "platemail gorget"
        asked = []
        real = self.api.ItemNameAndProps
        self.api.ItemNameAndProps = lambda serial, wait=False, timeout=None: (
            asked.append(serial) or real(serial, wait, timeout))
        book = self.book()
        book.qualifying()
        book.qualifying()

        self.assertEqual(asked, [1])

    def test_a_missing_tooltip_is_asked_again_only_so_often(self):
        self.api.hold(item(serial=1))
        book = self.book()

        for _pass in range(5):
            self.assertIsNone(book.qualifying())

        self.assertIsNone(book.is_product(1))

    def test_new_since_and_forget_missing(self):
        self.api.hold(item(serial=1))
        self.api.props[1] = "platemail gorget"
        book = self.book()
        before = book.serials()
        book.qualifying()
        self.api.hold(item(serial=1), item(serial=2))

        self.assertEqual([found.Serial for found in book.new_since(before)], [2])

        self.api.take(1)
        book.forget_missing()

        self.assertEqual(book._verdicts, {})
