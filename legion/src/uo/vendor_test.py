import unittest

from test_support.uo import install, mobile
from uo.vendor import Vendor

CONFIG = {
    "serial": None,
    "scan_radius": 18,
    "range": 1,
    "steps": 3,
    "pathfind_timeout": 10,
    "step_delay": 0.0,
    "sell_entry": "sell",
    "sell_phrase": "vendor sell",
    "context_timeout": 3.0,
    "sell_timeout": 1.0,
    "sell_poll": 0.5,
    "opl_wait": 0.0,
    "text_limit": 160,
}


class Menu(object):
    def current_id(self):
        return 0

    def is_craft_gump(self, ident):
        return False


class Heartbeat(object):
    def reset(self):
        pass


class SellTripTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.held = [10]
        self.vendor = Vendor(Menu(), CONFIG, self.said.append, Heartbeat(), lambda: self.held[0])

    # The tooltip wait pauses too, so the pack only drops once the vendor has been asked
    def sells_on_the_first_poll(self):
        def pause(seconds):
            if self.api.menus or self.api.said_aloud:
                self.held[0] = 0

        self.api.Pause = pause

    def test_finds_the_vendor_by_name_and_sells(self):
        self.api.see(mobile(serial=5, name="Alger the bowyer", distance=1))
        self.api.menu_entries = set(["sell"])
        self.sells_on_the_first_poll()

        self.assertTrue(self.vendor.sell_trip(["bowyer"], "bowyer"))
        self.assertEqual(self.api.menus, [(5, "sell")])
        self.assertEqual(self.api.opl_requests, [])

    def test_a_title_only_in_the_tooltip_costs_one_opl_round_trip(self):
        self.api.see(mobile(serial=5, name="Alger", props="Alger the bowyer", distance=1))
        self.sells_on_the_first_poll()

        self.assertTrue(self.vendor.sell_trip(["bowyer"], "bowyer"))
        self.assertEqual(self.api.opl_requests, [[5]])

    def test_a_menu_without_a_sell_entry_falls_back_to_the_phrase(self):
        self.api.see(mobile(serial=5, name="Alger the bowyer", distance=1))
        self.sells_on_the_first_poll()

        self.vendor.sell_trip(["bowyer"], "bowyer")

        self.assertEqual(self.api.said_aloud, ["vendor sell"])

    def test_a_vendor_that_buys_nothing_is_a_miss(self):
        self.api.see(mobile(serial=5, name="Alger the bowyer", distance=1))

        self.assertFalse(self.vendor.sell_trip(["bowyer"], "bowyer"))
        self.assertIn("the vendor bought nothing - is the auto-sell agent on?", self.said)

    def test_each_vendor_the_band_asks_for_is_reported_missing_once(self):
        self.api.see(mobile(serial=5, name="Alger the bowyer", distance=1))

        self.assertFalse(self.vendor.sell_trip(["jeweler"], "jeweler"))
        self.assertFalse(self.vendor.sell_trip(["jeweler"], "jeweler"))
        self.assertFalse(self.vendor.sell_trip(["provisioner"], "provisioner"))

        self.assertEqual(self.said, [
            "no jeweler within 18 - looked at 1: Alger the bowyer",
            "no provisioner within 18 - looked at 1: Alger the bowyer",
        ])

    def test_nobody_around_reads_as_nobody(self):
        self.assertFalse(self.vendor.sell_trip(["bowyer"], "bowyer"))
        self.assertEqual(self.said, ["no bowyer within 18 - looked at 0: nobody"])
