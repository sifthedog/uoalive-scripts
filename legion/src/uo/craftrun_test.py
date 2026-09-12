import unittest

from uo.craftrun import CraftRecorder, Seller, Unloader, end_cycle, make_room


class FakeStall(object):
    def __init__(self, reason=None):
        self.ended = []
        self._reason = reason

    def end_cycle(self, phase, cycle, tally):
        self.ended.append((phase, cycle, tally))

    def reason(self):
        return self._reason


class EndCycleTest(unittest.TestCase):
    def test_end_cycle_is_passed_through(self):
        stall = FakeStall()

        end_cycle(stall, "made", 3, 1, None)

        self.assertEqual(stall.ended, [("made", 3, 1)])

    def test_a_stall_reason_is_only_taken_when_the_caller_had_none(self):
        stall = FakeStall()

        self.assertIsNone(end_cycle(stall, "made", 1, 0, None))

        stall._reason = "cycles without a craft"
        self.assertEqual(end_cycle(stall, "made", 2, 0, None), "cycles without a craft")

        # The caller's own reason wins even once the stall has one of its own
        self.assertEqual(end_cycle(stall, "made", 3, 0, "the shard says you cannot make a bow"),
                         "the shard says you cannot make a bow")


class FakeDump(object):
    def __init__(self, moved):
        self._moved = list(moved)
        self.runs = 0

    def run(self):
        self.runs += 1

        return self._moved.pop(0) if self._moved else 0


class UnloaderTest(unittest.TestCase):
    def test_a_trip_that_moved_something_clears_the_misses(self):
        unloader = Unloader(FakeDump([0, 0, 2]))

        self.assertFalse(unloader.run())
        self.assertFalse(unloader.run())
        self.assertEqual(unloader.misses, 2)

        self.assertTrue(unloader.run())
        self.assertEqual(unloader.misses, 0)


class FakeVendor(object):
    def __init__(self, sells):
        self._sells = list(sells)
        self.trips = []

    def sell_trip(self, titles, noun):
        self.trips.append((titles, noun))

        return self._sells.pop(0)


class SellerTest(unittest.TestCase):
    def setUp(self):
        self.said = []

    def test_a_sale_clears_the_misses(self):
        seller = Seller(FakeVendor([True]), 3, 100, self.said.append)

        self.assertTrue(seller.sell(["a bowyer"], "bow", 1))
        self.assertEqual(seller.misses, 0)

    def test_max_misses_pauses_and_resets(self):
        seller = Seller(FakeVendor([False, False, False]), 3, 100, self.said.append)

        self.assertFalse(seller.sell(["a bowyer"], "bow", 1))
        self.assertFalse(seller.sell(["a bowyer"], "bow", 2))
        self.assertEqual(seller.misses, 2)
        self.assertEqual(seller.paused_until, 0)

        self.assertFalse(seller.sell(["a bowyer"], "bow", 3))
        self.assertEqual(seller.misses, 0)
        self.assertEqual(seller.paused_until, 103)
        self.assertEqual(len(self.said), 1)

    def test_due_compares_the_cycle_to_the_pause(self):
        seller = Seller(FakeVendor([]), 1, 100, self.said.append)
        seller.paused_until = 50

        self.assertFalse(seller.due(49))
        self.assertTrue(seller.due(50))

    def test_forget_resets_state(self):
        seller = Seller(FakeVendor([]), 1, 100, self.said.append)
        seller.misses = 5
        seller.paused_until = 50

        seller.forget()

        self.assertEqual(seller.misses, 0)
        self.assertEqual(seller.paused_until, 0)


class FakeRecorder(object):
    def __init__(self, recording):
        self._recording = recording
        self.rows = []

    def recording(self):
        return self._recording

    def record(self, skill_from, outcome, product, spent):
        self.rows.append((skill_from, outcome, product, spent))


class FakeMaterials(object):
    def __init__(self, spent):
        self._spent = spent
        self.settled = 0

    def settled_snapshot(self, settle, poll):
        self.settled += 1

        return {"after": True}

    def spent(self, before, after):
        return self._spent


class CraftRecorderTest(unittest.TestCase):
    def test_records_nothing_when_the_recorder_is_off(self):
        materials = FakeMaterials({"oak boards": 3})
        recorder = CraftRecorder(FakeRecorder(False), materials, 1.0, 0.1)

        recorder.record("made", 74.6, {}, "bow")

        self.assertEqual(materials.settled, 0)

    def test_records_what_the_craft_spent(self):
        raw = FakeRecorder(True)
        materials = FakeMaterials({"oak boards": 3})
        recorder = CraftRecorder(raw, materials, 1.0, 0.1)

        recorder.record("made", 74.6, {"before": True}, "bow")

        self.assertEqual(raw.rows, [(74.6, "made", "bow", {"oak boards": 3})])
        self.assertEqual(materials.settled, 1)


class FakeRestock(object):
    def __init__(self, refused):
        self._refused = refused

    def refused_for_weight(self):
        return self._refused


class MakeRoomTest(unittest.TestCase):
    def setUp(self):
        self.said = []

    def sell_path(self, applies=True, held=5, made="selling"):
        return (lambda: applies, lambda: held, lambda: made is not None)

    def test_nothing_to_do_when_the_pack_was_not_refused_for_weight(self):
        restock = FakeRestock(False)

        self.assertIsNone(make_room(restock, self.said.append, "wood",
                                    sell=self.sell_path()))

    def test_sells_when_this_band_sells_and_something_is_held(self):
        restock = FakeRestock(True)

        result = make_room(restock, self.said.append, "wood", sell=self.sell_path(held=5))

        self.assertEqual(result, "selling")
        self.assertEqual(self.said, ["selling 5 before loading more wood"])

    def test_a_failed_sell_trip_reports_no_room_made(self):
        restock = FakeRestock(True)
        path = (lambda: True, lambda: 5, lambda: False)

        self.assertIsNone(make_room(restock, self.said.append, "wood", sell=path))

    def test_falls_through_to_unload_when_selling_does_not_apply(self):
        restock = FakeRestock(True)
        sell = (lambda: False, lambda: 5, lambda: True)
        unload = (lambda: True, lambda: 3, lambda: True)

        result = make_room(restock, self.said.append, "wood", sell=sell, unload=unload)

        self.assertEqual(result, "unloading")
        self.assertEqual(self.said, ["unloading 3 before loading more wood"])

    def test_nothing_held_makes_no_room(self):
        restock = FakeRestock(True)
        sell = (lambda: True, lambda: 0, lambda: True)

        self.assertIsNone(make_room(restock, self.said.append, "wood", sell=sell))

    def test_an_empty_noun_leaves_the_message_bare(self):
        restock = FakeRestock(True)

        make_room(restock, self.said.append, "", sell=self.sell_path(held=2))

        self.assertEqual(self.said, ["selling 2 before loading more"])


if __name__ == "__main__":
    unittest.main()
