import unittest

from test_support.uo import install, item
from uo.crafttool import CraftTool
from uo.sources import Sources
from uo.stock import StockBook
from uo.toolstore import ToolStore

TOOL = 0x1022
BOARDS = 0x1BD7
CHEST = 0x40001000
EMPTY = 0x40001001
BOX = 0x40003000
GUMP = 0x5A

TABLE = {"names": ["storage box"], "graphics": set(), "title": ["storage box"],
         "rows": {"Board": ("boards", None)}, "buttons": {}}


def messages(api):
    return "\n".join(api.messages)


class ToolStoreTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.items[CHEST] = item(serial=CHEST, name="a wooden box")
        self.api.items[EMPTY] = item(serial=EMPTY, name="a crate")
        self.api.items[BOX] = item(serial=BOX, name="Logs & Boards Storage Box")
        self.api.opens[BOX] = GUMP
        self.api.gump_contents[GUMP] = "Storage Box Board 100"
        self.tools_inside = [item(serial=10, graphic=TOOL, name="fletcher's tools"),
                             item(serial=11, graphic=TOOL, name="fletcher's tools")]
        self.api.containers[CHEST] = self.tools_inside
        self.api.containers[EMPTY] = []
        self.tools = CraftTool("fletcher's tool", set([TOOL]), ["fletcher"], self.api.SysMsg)
        wood = StockBook({"noun": "wood", "kinds": [("boards", set([BOARDS]), ["board"])],
                          "types": [], "hues": {0: "regular"}, "wanted": "regular",
                          "move_delay": 0.0}, self.api.SysMsg)
        sources = Sources(wood, {"max_picks": 8, "pick_timeout": 1.0, "open_delay": 0.0,
                                 "move_delay": 0.0, "container_range": 2, "pathfind_timeout": 1,
                                 "box": TABLE, "plain": "regular", "gump_timeout": 1.0,
                                 "gump_poll": 0.1, "box_take": 200, "press_timeout": 0.2,
                                 "press_poll": 0.1}, self.api.SysMsg)
        self.store = ToolStore(self.tools, sources, {"noun": "fletcher's tools",
                                                     "pick_timeout": 1.0, "move_delay": 0.0,
                                                     "fetch_timeout": 0.3, "fetch_poll": 0.1},
                               self.api.SysMsg)

    def pick(self, serial):
        self.api.requested_target = serial

        return self.store.pick()

    def test_the_pack_is_refused(self):
        self.assertEqual(self.pick(self.api.Backpack), (None, "that is your own pack"))
        self.assertFalse(self.store.picked())

    def test_a_storage_box_is_refused(self):
        line, refusal = self.pick(BOX)

        self.assertIsNone(line)
        self.assertIn("is a storage box, which holds no fletcher's tools", refusal)

    def test_a_chest_is_picked_opened_and_counted(self):
        self.assertEqual(self.pick(CHEST),
                         ("'a wooden box' 0x40001000 - 2 fletcher's tools", None))
        self.assertEqual(self.api.used, [CHEST])
        self.assertEqual(self.store.count(), 2)

    def test_an_empty_chest_is_picked_but_flagged(self):
        line, refusal = self.pick(EMPTY)

        self.assertEqual(line, "'a crate' 0x40001001 - 0 fletcher's tools")
        self.assertEqual(refusal, "'a crate' holds no fletcher's tools")
        self.assertTrue(self.store.picked())

    def test_esc_picks_nothing(self):
        self.assertEqual(self.pick(0), (None, None))
        self.assertFalse(self.store.picked())

    def test_fetch_moves_one_tool_into_the_pack(self):
        self.pick(CHEST)

        def move(serial, container, amount=-1):
            moved = [held for held in self.tools_inside if held.Serial == serial][0]
            self.tools_inside.remove(moved)
            self.api.hold(moved)

            return True

        self.api.MoveItem = move

        self.assertTrue(self.store.fetch())
        self.assertIsNotNone(self.tools.serial())
        self.assertEqual(self.store.count(), 1)
        self.assertIn("fetched a tool from 'a wooden box', 1 left", messages(self.api))

    def test_fetch_with_nothing_picked_or_nothing_left_is_false(self):
        self.assertFalse(self.store.fetch())

        self.pick(EMPTY)

        self.assertFalse(self.store.fetch())
        self.assertIn("'a crate' has no fletcher's tools left", messages(self.api))

    def test_a_move_that_never_lands_is_false(self):
        self.pick(CHEST)

        self.assertFalse(self.store.fetch())
        self.assertIn("'a wooden box' gave up no tool", messages(self.api))
