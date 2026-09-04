import unittest

from bowcraft.wood import WoodBook, total_of
from test_support.uo import install, item

LOGS = set([0x1BDD])
BOARDS = set([0x1BD7])
KINDS = [("logs", LOGS, ["log", "logs"]), ("boards", BOARDS, ["board", "boards"])]
TYPES = ["oak", "ash", "yew"]
HUES = {0: "regular", 1191: "ash", 2010: "oak"}


class WoodBookTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.kinds = [(name, set(graphics), words) for name, graphics, words in KINDS]

    def book(self, wanted="regular"):
        return WoodBook({
            "kinds": self.kinds,
            "types": TYPES,
            "hues": HUES,
            "wanted": wanted,
            "move_delay": 0.7,
        }, self.said.append)

    def test_reads_the_kind_off_the_graphic(self):
        self.assertEqual(self.book().kind_of(item(graphic=0x1BDD)), "logs")
        self.assertEqual(self.book().kind_of(item(graphic=0x1BD7)), "boards")

    def test_learns_a_kind_from_the_name(self):
        book = self.book()

        self.assertEqual(book.kind_of(item(graphic=0x9999, name="Oak Boards")), "boards")
        self.assertIn(0x9999, self.kinds[1][1])

    def test_something_that_is_not_wood_has_no_kind(self):
        self.assertIsNone(self.book().kind_of(item(graphic=0x1234, name="a bow")))

    def test_the_name_names_the_wood_before_the_hue_does(self):
        self.assertEqual(self.book().type_of(item(graphic=0x1BD7, name="Oak Boards", hue=0)),
                         "oak")

    def test_the_hue_answers_when_the_name_has_not_arrived(self):
        self.assertEqual(self.book().type_of(item(graphic=0x1BD7, name="", hue=2010)), "oak")

    def test_a_colour_in_neither_table_is_not_guessed_at(self):
        self.assertIsNone(self.book().type_of(item(graphic=0x1BD7, name="", hue=9999)))

    def test_only_the_wanted_type_is_usable(self):
        book = self.book("regular")

        self.assertTrue(book.usable(item(graphic=0x1BD7, hue=0)))
        self.assertFalse(book.usable(item(graphic=0x1BD7, hue=2010)))
        self.assertTrue(book.wrong(item(graphic=0x1BD7, hue=2010)))

    def test_counts_only_what_the_menu_will_spend(self):
        self.api.hold(item(serial=1, graphic=0x1BD7, hue=0, amount=100),
                      item(serial=2, graphic=0x1BD7, hue=2010, amount=300))
        book = self.book("regular")

        self.assertEqual(book.in_pack(), 100)
        self.assertEqual(book.pack_other(), {"oak": 300})

    def test_the_report_says_what_is_set_aside(self):
        self.api.hold(item(serial=1, graphic=0x1BD7, hue=0, amount=100),
                      item(serial=2, graphic=0x1BD7, hue=2010, amount=300))

        self.assertEqual(self.book("regular").pack_report(), "100 boards (300 oak set aside)")

    def test_an_empty_pack_reads_as_no_wood(self):
        self.assertEqual(self.book().pack_report(), "no wood")

    def test_the_kinds_are_reported_in_a_stable_order(self):
        self.api.hold(item(serial=1, graphic=0x1BD7, hue=0, amount=10),
                      item(serial=2, graphic=0x1BDD, hue=0, amount=5))

        self.assertEqual(self.book().report(self.book().pack_wood()), "5 logs, 10 boards")

    def test_the_hue_report_names_what_is_actually_in_there(self):
        self.api.hold(item(serial=1, graphic=0x1BD7, hue=2010, amount=300))

        self.assertEqual(self.book().hue_report(), "300 oak boards hue 0x7da")

    def test_totals_a_count_table(self):
        self.assertEqual(total_of({"logs": 5, "boards": 10}), 15)
