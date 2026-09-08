import unittest

from bod.fill import SmallFill
from test_support.uo import install

CONFIG = {
    "combine_target": 0x40000001,
    "bag": None,
    "salvage": False,
    "salvage_entries": ["Salvage All"],
    "context_timeout": 1.0,
    "salvage_settle": 0.1,
    "ingots": {"ingot_graphics": set(), "ingot_words": [], "materials": [], "hues": {}},
    "max_cycles": 50,
    "max_unknown": 3,
    "max_throttled": 3,
    "max_no_tool": 2,
    "max_no_cursor": 2,
    "backoff": 0.1,
    "backoff_max": 0.2,
    "step_delay": 0.0,
}


class FakeDeed(object):
    def __init__(self, done, total):
        self.serial = 1
        self.request = {"item": "axe", "done": done, "total": total, "material": "iron",
                        "exceptional": False, "large": False, "entries": [("axe", done)]}

    def settle_after_combine(self, count):
        return count


class FakeItems(object):
    def __init__(self):
        self.waiting = []
        self.rejected = []

    def qualifying(self):
        return [serial for serial in self.waiting if serial not in self.rejected]

    def reject(self, *serials):
        self.rejected.extend(serials)

    def forget_missing(self):
        pass

    def leftovers(self):
        return []


class FakeCrafter(object):
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []
        self._proven = False

    def proven(self, item):
        return self._proven

    def craft_once(self, item, material):
        self.calls.append(("once", 1))
        outcome = self.outcomes.pop(0)

        if outcome == "made":
            self._proven = True

        return outcome

    def craft_batch(self, item, material, amount):
        self.calls.append(("batch", amount))

        return self.outcomes.pop(0)


class FakeCombiner(object):
    def __init__(self, items):
        self._items = items
        self.answer = "combined"

    def combine(self, target, offered):
        if self.answer == "combined":
            self._items.waiting = []

            return "combined", list(offered)

        return self.answer, []


class FakePicker(object):
    def forget(self):
        pass


class FakeWatch(object):
    def __init__(self):
        self.progress = 0

    def end_cycle(self, phase, cycle, tally):
        pass

    def reason(self):
        return None

    def progressed(self):
        self.progress += 1

    def is_saving(self):
        return False


class SmallFillTest(unittest.TestCase):
    def setUp(self):
        install()
        self.said = []
        self.items = FakeItems()
        self.combiner = FakeCombiner(self.items)
        self.watch = FakeWatch()

    def fill(self, deed, crafter):
        return SmallFill(deed, self.items, crafter, FakePicker(), self.combiner, CONFIG,
                         self.said.append,
                         {"heartbeat": None, "stall": self.watch, "saves": self.watch,
                          "stop_reason": lambda: None})

    def test_a_full_deed_does_nothing(self):
        fill = self.fill(FakeDeed(10, 10), FakeCrafter([]))

        self.assertIsNone(fill.run())
        self.assertEqual(fill.combined, 0)

    def test_proves_the_row_then_batches_the_rest_and_combines(self):
        crafter = FakeCrafter([("made", 9, 1)])

        def batch(item, material, amount):
            crafter.calls.append(("batch", amount))
            self.items.waiting = [101, 102, 103]

            return crafter.outcomes.pop(0)

        crafter.craft_batch = batch
        fill = self.fill(FakeDeed(0, 10), crafter)

        def once(item, material):
            crafter.calls.append(("once", 1))
            crafter._proven = True
            self.items.waiting = [100]

            return "made"

        crafter.craft_once = once
        fill._deed.settle_after_combine = lambda count: 10 if count > 1 else count

        self.assertIsNone(fill.run())
        self.assertEqual(crafter.calls, [("once", 1), ("batch", 9)])
        self.assertEqual(fill.summary(), "4 combined, 10 made, 1 failed, 10/10 in the deed")

    def test_out_of_ingots_stops_with_the_count_owed(self):
        fill = self.fill(FakeDeed(3, 10), FakeCrafter(["noMaterial"]))

        stop = fill.run()

        self.assertIn("not enough iron ingots", stop)
        self.assertIn("7 still owed", stop)

    def test_a_refused_batch_of_pieces_is_rejected_and_the_run_goes_on(self):
        self.items.waiting = [100, 101]
        self.combiner.answer = "notExceptional"
        crafter = FakeCrafter(["noAnvil"])
        fill = self.fill(FakeDeed(0, 10), crafter)

        self.assertEqual(fill.run(), "stand next to an anvil and a forge")
        self.assertEqual(self.items.rejected, [100, 101])

    def test_the_shard_saying_full_ends_it_as_full(self):
        self.items.waiting = [100]
        self.combiner.answer = "full"
        fill = self.fill(FakeDeed(9, 10), FakeCrafter([]))

        self.assertIsNone(fill.run())
        self.assertEqual(fill.done, 10)
