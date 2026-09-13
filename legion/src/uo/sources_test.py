import unittest

from uo.sources import Sources
from uo.stock import StockBook
from test_support.uo import install, item

BOARDS = 0x1BD7
BOX_ART = 0x0E80
CHEST = 0x40001000
PILE = 0x40001001
BOX = 0x40003000
GUMP = 0x5A

TABLE = {
    "names": ["storage box"],
    "graphics": set(),
    "title": ["storage box"],
    "rows": {"Board": ("boards", None), "OakBoard": ("boards", "oak")},
    "buttons": {"Board": 12},
}


def messages(api):
    return "\n".join(api.messages)


def sources(api, box=TABLE):
    wood = StockBook({
        "noun": "wood",
        "kinds": [("boards", set([BOARDS]), ["board", "boards"])],
        "types": ["oak"],
        "hues": {0: "regular"},
        "wanted": "regular",
        "move_delay": 0.0,
    }, api.SysMsg)

    return Sources(wood, {
        "max_picks": 8,
        "pick_timeout": 1.0,
        "open_delay": 0.0,
        "move_delay": 0.0,
        "container_range": 2,
        "pathfind_timeout": 1,
        "box": box,
        "plain": "regular",
        "gump_timeout": 1.0,
        "gump_poll": 0.1,
        "box_take": 200,
        "press_timeout": 0.2,
        "press_poll": 0.1,
    }, api.SysMsg)


class SourcesTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.items[CHEST] = item(serial=CHEST, name="a chest", x=5, y=5)
        self.api.items[BOX] = item(serial=BOX, name="Logs & Boards Storage Box", x=10, y=20)
        self.api.containers[CHEST] = [item(serial=PILE, graphic=BOARDS, amount=500, name="boards")]
        self.api.opens[BOX] = GUMP
        self.api.gump_contents[GUMP] = "Storage Box Board 18467 OakBoard 850"
        self.api.gump_buttons[GUMP] = [12]
        self.sources = sources(self.api)

    def pick(self, *serials, **choice):
        targets = list(serials)
        self.api.RequestTarget = lambda timeout=None: targets.pop(0) if targets else 0

        return self.sources.pick(choice.get("allowed"))

    def test_a_chest_is_an_item(self):
        self.assertEqual(self.sources.entry_for(CHEST)["kind"], "item")

    def test_a_container_in_the_pack_has_no_spot_and_is_in_reach(self):
        keg = item(serial=PILE + 1, name="a keg", x=44, y=65)
        self.api.items[keg.Serial] = keg
        self.api.hold(keg)
        entry = self.sources.entry_for(keg.Serial)

        self.assertIsNone(entry["spot"])
        self.assertTrue(self.sources.reach(entry))

    def test_the_box_is_known_by_its_name_and_keeps_its_spot(self):
        entry = self.sources.entry_for(BOX)

        self.assertEqual(entry["kind"], "box")
        self.assertEqual(entry["spot"], (10, 20, 0))

    def test_the_box_is_known_by_its_art_when_the_name_has_not_arrived(self):
        self.api.items[BOX] = item(serial=BOX, graphic=BOX_ART, name="")
        found = sources(self.api, dict(TABLE, graphics=set([BOX_ART])))

        self.assertEqual(found.entry_for(BOX)["kind"], "box")

    def test_without_a_box_table_the_box_is_a_plain_item(self):
        self.assertEqual(sources(self.api, None).entry_for(BOX)["kind"], "item")

    def test_pick_reads_the_box_off_its_gump(self):
        picked = self.pick(BOX)

        self.assertEqual([entry["kind"] for entry in picked], ["box"])
        self.assertIn("18467 boards in it (850 oak it will not use)", messages(self.api))

    def test_a_pick_for_the_box_refuses_a_chest(self):
        picked = self.pick(CHEST, BOX, allowed=["box"])

        self.assertEqual([entry["kind"] for entry in picked], ["box"])
        self.assertIn("'a chest' is a container - the gump chose the storage box",
                      messages(self.api))
        self.assertIn("target the storage box holding wood", messages(self.api))

    def test_a_pick_for_the_box_ends_at_the_first_box(self):
        self.api.items[BOX + 1] = item(serial=BOX + 1, name="Logs & Boards Storage Box")
        self.api.opens[BOX + 1] = GUMP
        picked = self.pick(BOX, BOX + 1, allowed=["box"])

        self.assertEqual([entry["serial"] for entry in picked], [BOX])
        self.assertEqual(self.api.used, [BOX])

    def test_a_pick_for_containers_refuses_the_box(self):
        picked = self.pick(BOX, CHEST, allowed=["item", "mobile"])

        self.assertEqual([entry["kind"] for entry in picked], ["item"])
        self.assertIn("is a storage box - the gump chose the container or pack animal",
                      messages(self.api))

    def test_pick_one_answers_the_line_and_keeps_the_entry(self):
        self.api.requested_target = CHEST

        self.assertEqual(self.sources.pick_one(), ("'a chest' 0x40001000, 500 boards in it", None))
        self.assertEqual(len(self.sources.picked()), 1)
        self.assertEqual(self.sources.pick_one(), (None, "0x40001000 is already picked"))

    def test_pick_one_refuses_a_second_storage_box(self):
        self.api.items[BOX + 1] = item(serial=BOX + 1, name="Logs & Boards Storage Box")
        self.api.opens[BOX + 1] = GUMP
        self.pick(BOX)
        self.api.RequestTarget = lambda timeout=None: BOX + 1

        line, refusal = self.sources.pick_one()

        self.assertIsNone(line)
        self.assertIn("is a second storage box - one holds everything", refusal)

    def test_esc_answers_nothing_at_all(self):
        self.api.requested_target = 0

        self.assertEqual(self.sources.pick_one(), (None, None))

    def test_clear_forgets_the_picks(self):
        picked = self.pick(CHEST, BOX)
        self.sources.clear()

        self.assertEqual(picked, [])
        self.assertEqual(self.sources.stock_left(), 0)

    def test_stock_left_adds_the_box_rows_to_the_chest_piles(self):
        self.pick(CHEST, BOX)

        self.assertEqual(self.sources.stock_left(), 18967)

    def test_stock_left_survives_the_gump_closing(self):
        self.pick(BOX)
        self.api.gump = 0

        self.assertEqual(self.sources.stock_left(), 18467)

    def test_a_box_that_opens_no_gump_is_not_picked(self):
        del self.api.opens[BOX]

        self.assertEqual(self.pick(BOX), [])
        self.assertIn("did not open", messages(self.api))

    def test_take_presses_the_box_and_moves_from_the_chest(self):
        chest, box = self.pick(CHEST, BOX)

        self.assertEqual(self.sources.take(box, None, 300), "Board")
        self.assertEqual(self.api.replies, [(12, GUMP)])
        self.assertIsNone(self.sources.take(chest, None, 300))
        self.assertEqual(self.api.moved, [(PILE, self.api.Backpack, 300)])

    def test_only_the_box_caps_what_a_restock_draws(self):
        chest, box = self.pick(CHEST, BOX)

        self.assertEqual(self.sources.cap(box), 200)
        self.assertIsNone(self.sources.cap(chest))

    def test_a_press_waits_for_the_pack_to_show_it(self):
        box, = self.pick(BOX)
        pack = item(serial=1, graphic=BOARDS, amount=20, name="boards")
        self.api.hold(pack)
        self.api.ReplyGump = lambda button, gump=None: setattr(pack, "Amount", 120) or True

        self.sources.take(box, None, 300)

        self.assertEqual(len(self.api.pauses), 1)

    def test_has_stock_reads_both_kinds_of_source(self):
        chest, box = self.pick(CHEST, BOX)

        self.assertTrue(self.sources.has_stock(chest, "boards"))
        self.assertTrue(self.sources.has_stock(box, "boards"))
        self.assertFalse(self.sources.has_stock(box, "logs"))

    def test_a_row_reported_wrong_is_no_longer_stock(self):
        box, = self.pick(BOX)
        self.sources.took_wrong(box, "Board", "oak")

        self.assertFalse(self.sources.has_stock(box, None))

    def test_put_back_returns_wrong_wood_to_a_chest_and_never_to_a_box(self):
        chest, box = self.pick(CHEST, BOX)
        self.api.hold(item(serial=7, graphic=BOARDS, amount=5, name="oak boards"))

        self.assertEqual(self.sources.put_back(box), 0)
        self.assertEqual(self.api.moved, [])

        self.sources.put_back(chest)

        self.assertEqual(self.api.moved, [(7, CHEST, 5)])
