import unittest

from uo.dump import Dump
from test_support.uo import install, item

DEED = 0x14F0
STAFF = 0x0E89
BARREL = 0x40002000

CONFIG = {"pick_timeout": 1.0, "move_delay": 0.0, "keep_existing": True}


class BarrelSources(object):
    def __init__(self, reachable=True):
        self.reachable = reachable
        self.opened = 0

    def entry_for(self, serial):
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


def messages(api):
    return "\n".join(api.messages)


class DumpTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.house = item(serial=1, graphic=DEED, name="a house deed")
        self.api.hold(self.house)
        self.sources = BarrelSources()
        self.dump = Dump(self.sources, set([DEED, STAFF]), CONFIG, self.api.SysMsg)

    def test_what_the_pack_held_at_the_start_is_never_a_product(self):
        self.assertEqual(self.dump.held(), 0)

        made = item(serial=2, graphic=DEED, name="a dartboard deed")
        self.api.hold(self.house, made)

        self.assertEqual(self.dump.held(), 1)
        self.assertEqual([held.Serial for held in self.dump.items()], [2])

    def test_keep_existing_off_counts_what_the_pack_already_held(self):
        dump = Dump(self.sources, set([DEED]), dict(CONFIG, keep_existing=False), self.api.SysMsg)

        self.assertEqual(dump.held(), 1)
        self.assertEqual([held.Serial for held in dump.items()], [1])

    def test_pick_takes_the_container_and_opens_it(self):
        self.api.requested_target = BARREL

        self.assertIsNotNone(self.dump.pick())
        self.assertTrue(self.dump.picked())
        self.assertEqual(self.sources.opened, 1)
        self.assertEqual(self.dump.name(), "trash barrel")

    def test_esc_leaves_nothing_picked(self):
        self.api.requested_target = 0

        self.assertIsNone(self.dump.pick())
        self.assertFalse(self.dump.picked())

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
