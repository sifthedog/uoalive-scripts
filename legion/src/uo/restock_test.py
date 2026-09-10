import unittest

from uo.restock import Restock
from uo.stock import StockBook
from test_support.uo import install, item

BOARDS = 0x1BD7
SCROLLS = 0x0EF3
ASH = 0x0F8C
CHEST = 0x40001000
PILE = 0x40001001
SCROLL_PILE = 0x40001002
ASH_PILE = 0x40001003


class LiftingBook(StockBook):
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

    def container_wood(self, serial, kind=None):
        return [held for held in self._api.containers.get(serial, [])
                if held.Amount > 0 and (kind is None or held.kind == kind)]

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
            "noun": "wood",
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
            "heavy_text": ["That container cannot hold more weight"],
        }, lambda text: None)

    def refuse_for_weight(self):
        def move(serial, container, amount=-1):
            self.api.moved.append((serial, container, amount))
            self.api.journal.append("That container cannot hold more weight.")

            return True

        self.api.MoveItem = move

    def test_fills_the_pack_to_the_batch_after_a_lift(self):
        self.assertEqual(self.restock.run(), 300)
        self.assertEqual(self.pack.Amount, 300)

    def test_a_pack_already_at_the_batch_pulls_nothing(self):
        self.pack.Amount = 300

        self.assertEqual(self.restock.run(), 20)
        self.assertEqual(self.pile.Amount, 1000)

    def test_a_move_refused_for_weight_ends_the_pull(self):
        self.refuse_for_weight()

        self.assertEqual(self.restock.run(), 20)
        self.assertTrue(self.restock.refused_for_weight())
        self.assertEqual(len(self.api.moved), 1)

    def test_a_stall_the_shard_did_not_explain_is_not_weight(self):
        self.api.MoveItem = lambda serial, container, amount=-1: True

        self.assertEqual(self.restock.run(), 20)
        self.assertFalse(self.restock.refused_for_weight())

    def test_the_refusal_is_forgotten_by_the_next_run(self):
        self.refuse_for_weight()
        self.restock.run()
        self.setUp()

        self.assertFalse(self.restock.refused_for_weight())


class KindsTest(unittest.TestCase):
    """A table of kind -> fill-to pulls each kind to its own figure and leaves the rest alone."""

    def setUp(self):
        self.api = install()
        self.scrolls = item(serial=1, graphic=SCROLLS, amount=5, name="blank scrolls")
        self.ash = item(serial=2, graphic=ASH, amount=100, name="sulfurous ash")
        self.api.hold(self.scrolls, self.ash)
        self.scroll_pile = item(serial=SCROLL_PILE, graphic=SCROLLS, amount=500,
                                name="blank scrolls")
        self.ash_pile = item(serial=ASH_PILE, graphic=ASH, amount=500, name="sulfurous ash")
        self.pearl_pile = item(serial=PILE, graphic=0x0F7A, amount=500, name="black pearl")
        self.scroll_pile.kind = "blank scrolls"
        self.ash_pile.kind = "sulfurous ash"
        self.pearl_pile.kind = "black pearl"
        self.api.containers[CHEST] = [self.pearl_pile, self.scroll_pile, self.ash_pile]

        def move(serial, container, amount=-1):
            for pile, held in ((self.scroll_pile, self.scrolls), (self.ash_pile, self.ash)):
                if serial == pile.Serial:
                    pile.Amount -= amount
                    held.Amount += amount

            if serial == PILE:
                self.pearl_pile.Amount -= amount
                self.api.hold(self.scrolls, self.ash,
                              item(serial=3, graphic=0x0F7A, amount=amount, name="black pearl"))

            return True

        self.api.MoveItem = move

        stock = StockBook({
            "noun": "scrolls and reagents",
            "kinds": [("blank scrolls", set([SCROLLS]), ["blank scroll", "blank scrolls"]),
                      ("black pearl", set([0x0F7A]), ["black pearl"]),
                      ("sulfurous ash", set([ASH]), ["sulfurous"])],
            "types": [],
            "hues": {},
            "wanted": None,
            "move_delay": 0.0,
        }, lambda text: None)
        self.restock = Restock(stock, ChestSources(self.api), {
            "batch": 300,
            "move_delay": 0.0,
            "max_empty_moves": 3,
            "return_wrong_wood": False,
            "heavy_text": ["That container cannot hold more weight"],
        }, lambda text: None)

    def test_each_kind_is_filled_to_its_own_figure(self):
        self.assertEqual(self.restock.run({"blank scrolls": 100, "sulfurous ash": 100}), 95)
        self.assertEqual(self.scrolls.Amount, 100)
        self.assertEqual(self.ash.Amount, 100)

    def test_a_kind_not_asked_for_stays_in_the_chest(self):
        self.restock.run({"blank scrolls": 100})

        self.assertEqual(self.pearl_pile.Amount, 500)
        self.assertEqual(self.ash_pile.Amount, 500)

    def test_a_kind_the_pack_lacks_is_pulled_too(self):
        self.assertEqual(self.restock.run({"black pearl": 40}), 40)
        self.assertEqual(self.pearl_pile.Amount, 460)
