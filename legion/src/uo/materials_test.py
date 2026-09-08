import unittest

from uo.materials import Materials
from uo.stock import StockBook
from test_support.uo import install, item

BOARDS = 0x1BD7
LOGS = 0x1BDD
FEATHER = 0x1BD1


def make():
    stock = StockBook({
        "noun": "wood",
        "kinds": [("logs", set([LOGS]), ["log"]), ("boards", set([BOARDS]), ["board"])],
        "types": ["oak", "yew"],
        "hues": {},
        "wanted": "regular",
        "move_delay": 0.0,
    }, lambda text: None)

    return Materials(stock, set([FEATHER]))


class SnapshotTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_counts_the_wood_and_the_whitelisted_materials(self):
        self.api.hold(item(serial=1, graphic=BOARDS, amount=100, name="boards"),
                      item(serial=2, graphic=FEATHER, amount=40, name="feathers"))

        self.assertEqual(make().snapshot(), {(BOARDS, 0): 100, (FEATHER, 0): 40})

    def test_anything_not_whitelisted_is_left_out(self):
        self.api.hold(item(serial=1, graphic=BOARDS, amount=100, name="boards"),
                      item(serial=2, graphic=0x0F0E, amount=5, name="greater heal potion"))

        self.assertEqual(make().snapshot(), {(BOARDS, 0): 100})

    def test_two_woods_of_one_graphic_are_kept_apart_by_hue(self):
        self.api.hold(item(serial=1, graphic=BOARDS, hue=0, amount=100, name="boards"),
                      item(serial=2, graphic=BOARDS, hue=0x07DA, amount=20, name="oak boards"))

        self.assertEqual(make().snapshot(), {(BOARDS, 0): 100, (BOARDS, 0x07DA): 20})


class SpentTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.materials = make()

    def test_reports_what_the_craft_spent(self):
        self.api.hold(item(serial=1, graphic=BOARDS, amount=100, name="boards"))
        before = self.materials.snapshot()

        self.api.hold(item(serial=1, graphic=BOARDS, amount=94, name="boards"))

        self.assertEqual(self.materials.spent(before, self.materials.snapshot()),
                         [("boards", BOARDS, 0, 6)])

    def test_a_craft_that_spent_nothing_reports_nothing(self):
        self.api.hold(item(serial=1, graphic=BOARDS, amount=100, name="boards"))
        before = self.materials.snapshot()

        self.assertEqual(self.materials.spent(before, self.materials.snapshot()), [])

    def test_every_material_a_craft_spent_gets_its_own_row(self):
        self.api.hold(item(serial=1, graphic=FEATHER, amount=40, name="feathers"),
                      item(serial=2, graphic=BOARDS, amount=100, name="boards"))
        before = self.materials.snapshot()

        self.api.hold(item(serial=1, graphic=FEATHER, amount=30, name="feathers"),
                      item(serial=2, graphic=BOARDS, amount=99, name="boards"))
        spent = self.materials.spent(before, self.materials.snapshot())

        self.assertEqual(spent, [("feathers", FEATHER, 0, 10), ("boards", BOARDS, 0, 1)])

    def test_what_the_craft_produced_is_not_reported_as_spent(self):
        self.api.hold(item(serial=1, graphic=BOARDS, amount=100, name="boards"))
        before = self.materials.snapshot()

        self.api.hold(item(serial=1, graphic=BOARDS, amount=99, name="boards"),
                      item(serial=2, graphic=FEATHER, amount=1, name="feathers"))

        self.assertEqual(self.materials.spent(before, self.materials.snapshot()),
                         [("boards", BOARDS, 0, 1)])

    def test_a_stack_spent_to_nothing_is_still_named(self):
        self.api.hold(item(serial=1, graphic=BOARDS, amount=3, name="oak boards"))
        before = self.materials.snapshot()

        self.api.containers[self.api.Backpack] = []

        self.assertEqual(self.materials.spent(before, self.materials.snapshot()),
                         [("oak boards", BOARDS, 0, 3)])

    def test_an_art_with_no_name_yet_falls_back_to_its_graphic(self):
        self.api.hold(item(serial=1, graphic=FEATHER, amount=5, name=""))
        before = self.materials.snapshot()

        self.api.containers[self.api.Backpack] = []

        self.assertEqual(self.materials.spent(before, self.materials.snapshot()),
                         [("0x1bd1", FEATHER, 0, 5)])


class SettledSnapshotTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.materials = make()

    def _refund_after_first_pause(self, serial, amount):
        landed = [False]

        def pause(seconds):
            if not landed[0]:
                landed[0] = True
                self.api.hold(item(serial=serial, graphic=BOARDS, amount=amount, name="boards"))

        self.api.Pause = pause

    def test_material_given_back_after_the_line_is_netted_off(self):
        self.api.hold(item(serial=1, graphic=BOARDS, amount=100, name="boards"))
        before = self.materials.snapshot()

        self.api.hold(item(serial=1, graphic=BOARDS, amount=93, name="boards"))
        self._refund_after_first_pause(1, 96)

        spent = self.materials.spent(before, self.materials.settled_snapshot(1.5, 0.25))

        self.assertEqual(spent, [("boards", BOARDS, 0, 4)])

    def test_a_pack_that_never_moves_reads_the_same_as_a_plain_snapshot(self):
        self.api.hold(item(serial=1, graphic=BOARDS, amount=93, name="boards"))

        self.assertEqual(self.materials.settled_snapshot(1.5, 0.25), {(BOARDS, 0): 93})

    def test_waits_through_quiet_polls_for_a_refund_that_lands_late(self):
        self.api.hold(item(serial=1, graphic=BOARDS, amount=100, name="boards"))
        before = self.materials.snapshot()

        self.api.hold(item(serial=1, graphic=BOARDS, amount=93, name="boards"))

        polls = [0]

        def pause(seconds):
            polls[0] += 1

            if polls[0] == 4:
                self.api.hold(item(serial=1, graphic=BOARDS, amount=96, name="boards"))

        self.api.Pause = pause

        spent = self.materials.spent(before, self.materials.settled_snapshot(1.5, 0.25))

        self.assertEqual(spent, [("boards", BOARDS, 0, 4)])

    def test_a_pack_that_truly_never_moves_reports_the_full_deduction(self):
        self.api.hold(item(serial=1, graphic=BOARDS, amount=93, name="boards"))

        self.assertEqual(self.materials.settled_snapshot(1.5, 0.25), {(BOARDS, 0): 93})

    def test_gives_up_on_a_pack_that_will_not_settle(self):
        counts = [90, 89, 88, 87, 86, 85, 84, 83]

        def pause(seconds):
            self.api.hold(item(serial=1, graphic=BOARDS, amount=counts.pop(0), name="boards"))

        self.api.hold(item(serial=1, graphic=BOARDS, amount=91, name="boards"))
        self.api.Pause = pause

        settled = self.materials.settled_snapshot(1.0, 0.25)

        self.assertEqual(settled, {(BOARDS, 0): 87})
