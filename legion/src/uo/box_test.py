import unittest

from uo.box import StorageBox, layout_buttons
from test_support.uo import install

BOX = 0x40003000
GUMP = 0x5A

TABLE = {
    "names": ["storage box"],
    "graphics": set(),
    "title": ["storage box"],
    "rows": {"Board": ("boards", None), "OakBoard": ("boards", "oak"), "Log": ("logs", None)},
    "buttons": {"Board": 12, "OakBoard": 13},
}
CONFIG = {"plain": "regular", "gump_timeout": 1.0, "gump_poll": 0.1}
TEXT = "Add Resource Logs & Boards Storage Box More Settings OakBoard 850 AshBoard 451 Board 18467"
PACKET = ("Add Resource\nLogs & Boards Storage Box\nSettings\nMore\nBoard\n20067\nOakBoard\n850\n"
          "page 0\nresizepic 50 10 83 495 280\nbutton 75 25 4026 4027 1 0 1\ntext 110 25 2219 0\n"
          "text 225 25 1152 1\nbutton 75 50 4005 4007 1 0 999\ntext 110 50 2219 2\npage 1\n"
          "button 425 25 4005 4006 1 0 2\ntext 460 25 2219 3\ntext 110 250 1153 4\n"
          "text 255 250 1153 5\nbutton 75 250 4029 4030 1 0 107\ntext 340 75 1153 6\n"
          "text 485 75 1153 7\nbutton 305 75 4029 4030 1 0 108\n\x00")


def messages(api):
    return "\n".join(api.messages)


class StorageBoxTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.opens[BOX] = GUMP
        self.api.gump_contents[GUMP] = TEXT
        self.api.gump_buttons[GUMP] = [1, 2, 3, 12, 13]
        self.box = StorageBox(TABLE, CONFIG, self.api.SysMsg)

    def test_open_uses_the_box_and_reads_the_rows_off_the_gump(self):
        self.assertEqual(self.box.open(BOX), GUMP)
        self.assertEqual(self.api.used, [BOX])
        self.assertEqual(self.box.rows(BOX), {"OakBoard": 850, "Board": 18467})
        self.assertIn("lists 'AshBoard'", messages(self.api))

    def test_labels_are_matched_whatever_their_case(self):
        self.api.gump_contents[GUMP] = "Storage Box oakboard 850 BOARD 18467 log 40"
        self.box.open(BOX)

        self.assertEqual(self.box.rows(BOX), {"OakBoard": 850, "Board": 18467, "Log": 40})

    def test_rows_split_across_lines_and_wrapped_in_tags_read_the_same(self):
        self.api.gump_contents[GUMP] = "<CENTER>Storage Box</CENTER>\nOakBoard 850\nBoard 18467\n"

        self.box.open(BOX)

        self.assertEqual(self.box.rows(BOX), {"OakBoard": 850, "Board": 18467})

    def test_a_gump_already_up_is_read_without_another_use(self):
        self.api.gump = GUMP

        self.assertEqual(self.box.open(BOX), GUMP)
        self.assertEqual(self.api.used, [])

    def test_counts_are_the_wanted_type_by_kind_and_the_rest_by_type(self):
        self.box.open(BOX)

        self.assertEqual(self.box.counts(BOX, "regular"), {"boards": 18467})
        self.assertEqual(self.box.other_counts(BOX, "regular"), {"oak": 850})
        self.assertEqual(self.box.counts(BOX, "oak"), {"boards": 850})

    def test_rows_are_remembered_once_the_gump_is_gone(self):
        self.box.open(BOX)
        self.api.gump = 0

        self.assertEqual(self.box.counts(BOX, "regular"), {"boards": 18467})
        self.assertTrue(self.box.has_stock(BOX, None, "regular"))

    def test_a_box_that_opens_no_gump_reads_as_empty(self):
        del self.api.opens[BOX]

        self.assertEqual(self.box.open(BOX), 0)
        self.assertEqual(self.box.counts(BOX, "regular"), {})
        self.assertFalse(self.box.has_stock(BOX, None, "regular"))

    def test_take_presses_the_rows_button_and_names_the_row(self):
        self.box.open(BOX)

        self.assertEqual(self.box.take(BOX, None, "regular"), "Board")
        self.assertEqual(self.api.replies, [(12, GUMP)])

    def test_take_of_another_type_presses_that_rows_button(self):
        self.box.open(BOX)

        self.assertEqual(self.box.take(BOX, "boards", "oak"), "OakBoard")
        self.assertEqual(self.api.replies, [(13, GUMP)])

    def test_a_kind_the_box_lacks_is_not_pressed_for(self):
        self.box.open(BOX)

        self.assertFalse(self.box.has_stock(BOX, "logs", "regular"))
        self.assertIsNone(self.box.take(BOX, "logs", "regular"))

    def test_a_row_with_no_button_is_never_pressed(self):
        self.api.gump_contents[GUMP] = "Storage Box Log 40"
        self.box.open(BOX)

        self.assertIsNone(self.box.take(BOX, "logs", "regular"))
        self.assertEqual(self.api.replies, [])
        self.assertIn("run box-probe.py", messages(self.api))
        self.assertFalse(self.box.has_stock(BOX, "logs", "regular"))

    def test_a_button_the_gump_lacks_is_never_pressed(self):
        self.api.gump_buttons[GUMP] = [1, 2, 3]
        self.box.open(BOX)

        self.assertIsNone(self.box.take(BOX, None, "regular"))
        self.assertEqual(self.api.replies, [])
        self.assertIn("has no button 12", messages(self.api))

    def test_an_unreadable_button_list_still_presses(self):
        del self.api.gump_buttons[GUMP]
        self.box.open(BOX)

        self.assertEqual(self.box.take(BOX, None, "regular"), "Board")

    def test_the_layout_pairs_each_row_with_the_button_to_its_left(self):
        self.assertEqual(layout_buttons(PACKET, ["Board", "OakBoard", "AshBoard", "More"]),
                         {"Board": 107, "OakBoard": 108, "More": 2})

    def test_the_gumps_layout_names_the_button_before_the_table_does(self):
        self.api.gump_layouts[GUMP] = PACKET
        self.api.gump_buttons[GUMP] = [1, 2, 12, 107, 108, 999]
        self.box.open(BOX)

        self.assertEqual(self.box.take(BOX, None, "regular"), "Board")
        self.assertEqual(self.api.replies, [(107, GUMP)])

    def test_a_row_that_gave_the_wrong_wood_is_not_pressed_again(self):
        self.box.open(BOX)
        self.box.wrong_row("Board", "oak")

        self.assertIsNone(self.box.take(BOX, None, "regular"))
        self.assertIn("out of date for 'Board' - it gave oak", messages(self.api))
