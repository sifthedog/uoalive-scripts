import unittest

from uo.dump import Dump
from test_support.uo import install, item

DEED = 0x14F0
STAFF = 0x0E89
BARREL = 0x40002000
BOX = 0x40003000

CONFIG = {"pick_timeout": 1.0, "move_delay": 0.0, "keep_existing": True}


def products(*graphics):
    return dict((hex(graphic), set([graphic])) for graphic in graphics)


class BarrelSources(object):
    def __init__(self, reachable=True):
        self.reachable = reachable
        self.opened = 0

    def entry_for(self, serial):
        if serial == BOX:
            return {"kind": "box", "serial": serial, "name": "storage box", "spot": (0, 0, 0)}

        if serial != BARREL:
            return None

        return {"kind": "item", "serial": serial, "name": "trash barrel", "spot": (0, 0, 0)}

    def name_of(self, entry):
        return entry["name"]

    def reach(self, entry):
        return self.reachable

    def open(self, entry):
        self.opened += 1

        return entry["serial"]

    def container_of(self, entry):
        return None if entry["kind"] == "box" else entry["serial"]


def messages(api):
    return "\n".join(api.messages)


class DumpTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.house = item(serial=1, graphic=DEED, name="a house deed")
        self.api.hold(self.house)
        self.sources = BarrelSources()
        self.products = products(DEED, STAFF)
        self.dump = Dump(self.sources, self.products, CONFIG, self.api.SysMsg)

    def test_what_the_pack_held_at_the_start_is_never_a_product(self):
        self.assertEqual(self.dump.held(), 0)

        made = item(serial=2, graphic=DEED, name="a dartboard deed")
        self.api.hold(self.house, made)

        self.assertEqual(self.dump.held(), 1)
        self.assertEqual([held.Serial for held in self.dump.items()], [2])

    def test_keep_existing_off_counts_what_the_pack_already_held(self):
        dump = Dump(self.sources, products(DEED), dict(CONFIG, keep_existing=False),
                    self.api.SysMsg)

        self.assertEqual(dump.held(), 1)
        self.assertEqual([held.Serial for held in dump.items()], [1])

    # A restart with un-dumped stock from a previous run should not lock it out of the dump for
    # good just because it shares a graphic with a genuinely ambiguous item like a house deed
    def test_keep_graphics_narrows_what_a_restart_protects(self):
        leftover = item(serial=2, graphic=STAFF, name="a quarter staff")
        self.api.hold(self.house, leftover)
        config = dict(CONFIG, keep_graphics=set([DEED]))
        dump = Dump(self.sources, products(DEED, STAFF), config, self.api.SysMsg)

        self.assertEqual(dump.held(), 1)
        self.assertEqual([held.Serial for held in dump.items()], [2])

    # The crafter adds a shard's own art to the table mid-run, and the dump reads the table live
    def test_an_art_learned_after_the_start_counts(self):
        learned = item(serial=2, graphic=0x1234, name="a quarter staff")
        self.api.hold(self.house, learned)

        self.assertEqual(self.dump.held(), 0)

        self.products[hex(STAFF)].add(0x1234)

        self.assertEqual([held.Serial for held in self.dump.items()], [2])

    def test_pick_takes_the_container_and_never_uses_it(self):
        self.api.requested_target = BARREL

        self.assertIsNotNone(self.dump.pick())
        self.assertTrue(self.dump.picked())
        self.assertEqual(self.sources.opened, 0)
        self.assertEqual(self.dump.name(), "trash barrel")

    def test_esc_leaves_nothing_picked(self):
        self.api.requested_target = 0

        self.assertIsNone(self.dump.pick())
        self.assertFalse(self.dump.picked())

    def test_a_storage_box_is_refused(self):
        self.api.requested_target = BOX

        self.assertIsNone(self.dump.pick())
        self.assertFalse(self.dump.picked())
        self.assertEqual(self.sources.opened, 0)
        self.assertIn("is a storage box", messages(self.api))

    def test_your_own_pack_is_refused(self):
        self.api.requested_target = self.api.Backpack

        self.assertIsNone(self.dump.pick())
        self.assertIn("your own pack", messages(self.api))

    def test_run_moves_only_what_the_run_made(self):
        self.api.requested_target = BARREL
        self.dump.pick()
        made = item(serial=2, graphic=STAFF, name="a quarter staff")
        self.api.hold(self.house, made)

        def move(serial, container, amount=-1):
            self.api.take(serial)

            return True

        self.api.MoveItem = move

        self.assertEqual(self.dump.run(), 1)
        self.assertEqual([held.Serial for held in self.api.containers[self.api.Backpack]], [1])
        self.assertIn("unloaded 1 into 'trash barrel'", messages(self.api))

    def test_pick_line_answers_the_container_or_the_refusal(self):
        self.api.requested_target = BARREL

        self.assertEqual(self.dump.pick_line(), ("'trash barrel' 0x40002000", None))

        self.api.requested_target = self.api.Backpack

        self.assertEqual(self.dump.pick_line(), (None, "that is your own pack"))
        self.assertEqual(self.dump.name(), "trash barrel")

    def test_limit_to_narrows_what_counts_as_a_product(self):
        self.api.hold(self.house, item(serial=2, graphic=STAFF, name="a quarter staff"),
                      item(serial=3, graphic=DEED, name="a dartboard deed"))

        self.assertEqual(self.dump.held(), 2)

        self.dump.limit_to([hex(STAFF)])

        self.assertEqual([held.Serial for held in self.dump.items()], [2])

    def test_run_with_nothing_picked_moves_nothing(self):
        self.api.hold(self.house, item(serial=2, graphic=STAFF, name="a quarter staff"))

        self.assertEqual(self.dump.run(), 0)
        self.assertEqual(self.api.moved, [])

    def test_a_container_out_of_reach_moves_nothing_and_says_so(self):
        self.api.requested_target = BARREL
        self.dump.pick()
        self.sources.reachable = False
        self.api.hold(self.house, item(serial=2, graphic=STAFF, name="a quarter staff"))

        self.assertEqual(self.dump.run(), 0)
        self.assertEqual(self.api.moved, [])
        self.assertIn("cannot reach 'trash barrel'", messages(self.api))

    def test_a_move_the_shard_refused_reads_as_took_nothing(self):
        self.api.requested_target = BARREL
        self.dump.pick()
        self.api.hold(self.house, item(serial=2, graphic=STAFF, name="a quarter staff"))

        self.assertEqual(self.dump.run(), 0)
        self.assertEqual(len(self.api.moved), 1)
        self.assertIn("'trash barrel' took nothing", messages(self.api))
