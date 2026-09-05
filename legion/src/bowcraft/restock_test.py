import unittest

from bowcraft.restock import Restock
from bowcraft.wood import WoodBook
from test_support.uo import install, item

BOARDS = 0x1BD7
CHEST = 0x40001000
PILE = 0x40001001


class LiftingBook(WoodBook):
    """A lift the inert fake cannot show: the bag's wood is already in the pack count."""

    def lift_from_bags(self):
        return 20


class ChestSources(object):
    def __init__(self, api):
        self._api = api
        self.entry = {"kind": "item", "serial": CHEST, "name": "chest", "spot": (0, 0, 0)}

    def picked(self):
        return [self.entry]

    def name_of(self, entry):
        return entry["name"]

    def reach(self, entry):
        return True

    def open(self, entry):
        return CHEST

    def container_wood(self, serial):
        return [held for held in self._api.containers.get(serial, []) if held.Amount > 0]

    def stock_left(self):
        return sum(held.Amount for held in self._api.containers.get(CHEST, []))


class RunTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.pack = item(serial=1, graphic=BOARDS, amount=20, name="boards")
        self.pile = item(serial=PILE, graphic=BOARDS, amount=1000, name="boards")
        self.api.hold(self.pack)
        self.api.containers[CHEST] = [self.pile]

        def move(serial, container, amount=-1):
            if serial == PILE:
                self.pile.Amount -= amount
                self.pack.Amount += amount

            return True

        self.api.MoveItem = move

        wood = LiftingBook({
            "kinds": [("boards", set([BOARDS]), ["board", "boards"])],
            "types": [],
            "hues": {0: "regular"},
            "wanted": "regular",
            "move_delay": 0.0,
        }, lambda text: None)
        self.restock = Restock(wood, ChestSources(self.api), {
            "batch": 300,
            "move_delay": 0.0,
            "max_empty_moves": 3,
            "return_wrong_wood": False,
        }, lambda text: None)

    def test_fills_the_pack_to_the_batch_after_a_lift(self):
        self.assertEqual(self.restock.run(), 300)
        self.assertEqual(self.pack.Amount, 300)

    def test_a_pack_already_at_the_batch_pulls_nothing(self):
        self.pack.Amount = 300

        self.assertEqual(self.restock.run(), 20)
        self.assertEqual(self.pile.Amount, 1000)
