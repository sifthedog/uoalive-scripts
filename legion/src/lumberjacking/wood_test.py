import unittest

from lumberjacking.wood import Wood
from test_support.uo import install, item

LOGS = set([0x1BDD])
BOARDS = set([0x1BD7])


class WoodTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.logs = set(LOGS)
        self.boards = set(BOARDS)
        self.wood = Wood(self.logs, ["log", "logs"], self.boards, ["board", "boards"],
                         self.said.append)

    def test_matches_a_known_log_art(self):
        self.assertTrue(self.wood.is_log(item(graphic=0x1BDD)))

    def test_learns_a_log_art_from_the_plural(self):
        self.assertTrue(self.wood.is_log(item(graphic=0x9999, name="Oak Logs")))
        self.assertIn(0x9999, self.logs)

    def test_does_not_take_a_word_it_is_only_inside(self):
        self.assertFalse(self.wood.is_log(item(graphic=0x9999, name="a stick of logic")))

    def test_a_board_is_not_a_log(self):
        self.assertFalse(self.wood.is_log(item(graphic=0x1BD7)))
        self.assertTrue(self.wood.is_board(item(graphic=0x1BD7)))

    def test_totals_logs_whatever_the_hue(self):
        self.api.hold(item(serial=1, graphic=0x1BDD, hue=0, amount=10),
                      item(serial=2, graphic=0x1BDD, hue=0x0483, amount=5))

        self.assertEqual(self.wood.log_total(), 15)

    def test_lists_the_biggest_log_pile_first(self):
        self.api.hold(item(serial=1, graphic=0x1BDD, amount=5),
                      item(serial=2, graphic=0x1BDD, amount=40))

        self.assertEqual([pile.Serial for pile in self.wood.log_piles()], [2, 1])

    def test_board_piles_leave_the_logs_out(self):
        self.api.hold(item(serial=1, graphic=0x1BDD, amount=5),
                      item(serial=2, graphic=0x1BD7, amount=40))

        self.assertEqual([pile.Serial for pile in self.wood.board_piles()], [2])

    def test_nothing_matches_a_missing_item(self):
        self.assertFalse(self.wood.is_log(None))
        self.assertFalse(self.wood.is_board(None))
