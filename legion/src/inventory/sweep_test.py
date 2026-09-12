import unittest

import inventory.sweep
from inventory.sweep import Sweep, batches_of
from test_support.uo import FakePlayer, install, item

BAG = 0x40001000
INNER = 0x40001001
SWORD = 0x40012345
SHIELD = 0x40012346
RING = 0x40012347

PARSER = {
    "tier": ["Greater Artifact", "Minor Magic Item"],
    "durability": ["durability"],
    "weight": ["weight"],
    "prefixes": ["crafted by"],
}

SWORD_PROPS = "Longsword\nGreater Artifact\nDurability 45 / 50\nWeight: 3 Stones\n" \
              "Hit Chance Increase 15%\nWeapon Damage 13 - 15\nAntique"


class Sink(object):
    def __init__(self, throws=False):
        self.lines = []
        self.throws = throws

    def append(self, path, line):
        if self.throws:
            raise IOError("read-only")

        self.lines.append((path, line))


class BatchesTest(unittest.TestCase):
    def test_splits_into_runs_of_the_size(self):
        self.assertEqual(batches_of([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]])

    def test_nothing_makes_no_batches(self):
        self.assertEqual(batches_of([], 2), [])


class SweepTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.api.Player = FakePlayer(name="Kaldor")
        self.clock = [1000.0]
        self.saved = inventory.sweep.now
        inventory.sweep.now = lambda: self.clock[0]
        self.sink = Sink()
        self.said = []
        self.sword = item(serial=SWORD, graphic=0xF61, hue=0, amount=1, name="a longsword",
                          container=BAG)
        self.shield = item(serial=SHIELD, graphic=0x1B72, hue=1150, amount=1, name="a shield",
                           container=BAG)
        self.api.containers[BAG] = [self.sword, self.shield]
        self.api.props[SWORD] = SWORD_PROPS
        self.api.props[SHIELD] = "Bronze Shield\nPhysical Resist 10%"

    def tearDown(self):
        inventory.sweep.now = self.saved

    def config(self, **overrides):
        config = {
            "recursive": True,
            "open_delay": 0.6,
            "opl_wait": 1.0,
            "opl_timeout": 1,
            "opl_batch": 25,
            "retries": 2,
            "max_containers": 50,
            "parser": PARSER,
        }
        config.update(overrides)

        return config

    def make(self, path="bag-items.jsonl", sink=None, **overrides):
        sink = sink if sink is not None else self.sink

        return Sweep(path, "Kaldor", self.config(**overrides), self.said.append, append=sink.append)

    def lines(self):
        return [line for _path, line in self.sink.lines]

    def test_opens_the_bag_before_listing_it(self):
        self.make().run(BAG)

        self.assertEqual(self.api.used, [BAG])
        self.assertIn(0.6, self.api.pauses)

    def test_writes_one_row_per_item_in_listing_order(self):
        written, unread, opened = self.make().run(BAG)

        self.assertEqual((written, unread, opened), (2, 0, 1))
        self.assertEqual(len(self.sink.lines), 2)
        self.assertEqual(self.sink.lines[0][0], "LegionScripts/bag-items.jsonl")
        self.assertTrue(self.lines()[0].startswith('{"v":1,"scan":"0x40001000/1000000","t":1000.0,'
                                                  '"char":"Kaldor","bag":"0x40001000",'
                                                  '"serial":"0x40012345","graphic":"0xf61","hue":0,'
                                                  '"amount":1,"container":"0x40001000",'
                                                  '"name":"Longsword",'))
        self.assertIn('"serial":"0x40012346"', self.lines()[1])
        self.assertIn('"hue":1150', self.lines()[1])

    def test_the_row_carries_what_the_tooltip_said(self):
        self.make().run(BAG)
        row = self.lines()[0]

        self.assertIn('"tier":"Greater Artifact"', row)
        self.assertIn('"durability":{"current":45,"max":50}', row)
        self.assertIn('"weight":3', row)
        self.assertIn('"props":{"antique":true,"hit chance increase":15,"weapon damage":[13,15]}',
                      row)
        self.assertIn('"lines":["Longsword","Greater Artifact","Durability 45 / 50",'
                      '"Weight: 3 Stones","Hit Chance Increase 15%","Weapon Damage 13 - 15",'
                      '"Antique"]}', row)
        self.assertNotIn('"unread"', row)

    def test_a_tooltip_without_the_extras_writes_nulls(self):
        self.make().run(BAG)
        row = self.lines()[1]

        self.assertIn('"tier":null,"durability":null,"weight":null,"props":{"physical resist":10}',
                      row)

    def test_primes_the_tooltips_in_one_batch_and_waits_for_them(self):
        self.make().run(BAG)

        self.assertEqual(self.api.opl_requests, [[SWORD, SHIELD]])
        self.assertIn(1.0, self.api.pauses)

    def test_a_big_bag_is_primed_in_batches(self):
        self.make(opl_batch=1).run(BAG)

        self.assertEqual(self.api.opl_requests, [[SWORD], [SHIELD]])

    def test_a_nested_bag_is_opened_and_its_items_name_it(self):
        pouch = item(serial=INNER, graphic=0xE79, name="a pouch", container=BAG, is_container=True)
        ring = item(serial=RING, graphic=0x108A, name="a ring", container=INNER)
        self.api.containers[BAG].append(pouch)
        self.api.containers[INNER] = [ring]
        self.api.props[INNER] = "Pouch"
        self.api.props[RING] = "Gold Ring\nLuck 10"

        written, unread, opened = self.make().run(BAG)

        self.assertEqual((written, unread, opened), (4, 0, 2))
        self.assertEqual(self.api.used, [BAG, INNER])
        self.assertIn('"serial":"0x40012347","graphic":"0x108a","hue":0,"amount":1,'
                      '"container":"0x40001001"', self.lines()[3])

    def test_a_nested_bag_is_left_shut_when_not_recursive(self):
        pouch = item(serial=INNER, graphic=0xE79, name="a pouch", container=BAG, is_container=True)
        self.api.containers[BAG].append(pouch)
        self.api.containers[INNER] = [item(serial=RING, container=INNER)]
        self.api.props[INNER] = "Pouch"

        written, _unread, opened = self.make(recursive=False).run(BAG)

        self.assertEqual((written, opened), (3, 1))
        self.assertEqual(self.api.used, [BAG])

    def test_the_container_cap_holds(self):
        pouch = item(serial=INNER, graphic=0xE79, name="a pouch", container=BAG, is_container=True)
        self.api.containers[BAG].append(pouch)
        self.api.containers[INNER] = [item(serial=RING, container=INNER)]
        self.api.props[INNER] = "Pouch"

        _written, _unread, opened = self.make(max_containers=1).run(BAG)

        self.assertEqual(opened, 1)
        self.assertEqual(self.api.used, [BAG])

    def test_a_tooltip_that_never_comes_is_asked_again_then_written_unread(self):
        del self.api.props[SHIELD]

        written, unread, _opened = self.make(retries=2).run(BAG)

        self.assertEqual((written, unread), (2, 1))
        self.assertEqual(self.api.opl_requests, [[SWORD, SHIELD], [SHIELD], [SHIELD]])
        row = self.lines()[1]
        self.assertIn('"name":"a shield"', row)
        self.assertIn('"lines":[],"unread":true}', row)

    def test_a_tooltip_that_comes_on_the_retry_is_written_whole(self):
        del self.api.props[SHIELD]
        api = self.api

        def pause(seconds):
            api.pauses.append(seconds)

            if len(api.opl_requests) == 2:
                api.props[SHIELD] = "Bronze Shield"

        api.Pause = pause

        written, unread, _opened = self.make().run(BAG)

        self.assertEqual((written, unread), (2, 0))
        self.assertIn('"name":"Bronze Shield"', self.lines()[1])
        self.assertNotIn('"unread"', self.lines()[1])

    def test_an_unnamed_item_without_a_tooltip_is_named_by_its_serial(self):
        self.api.containers[BAG] = [item(serial=RING, container=BAG)]

        self.make(retries=0).run(BAG)

        self.assertIn('"name":"0x40012347"', self.lines()[0])

    def test_no_path_writes_nothing_and_still_counts(self):
        written, _unread, _opened = self.make(path="").run(BAG)

        self.assertEqual(written, 2)
        self.assertEqual(self.sink.lines, [])

    def test_a_file_that_cannot_be_written_is_said_once(self):
        sink = Sink(throws=True)

        written, _unread, _opened = self.make(sink=sink).run(BAG)

        self.assertEqual(written, 2)
        self.assertEqual(len(self.said), 2)
        self.assertIn("cannot write LegionScripts/bag-items.jsonl", self.said[1])

    def test_a_stop_ends_the_read_with_what_was_written(self):
        api = self.api

        # The stop lands on the second batch's wait, after the first item is read and written
        def pause(seconds):
            api.pauses.append(seconds)

            if len(api.opl_requests) == 2:
                api.StopRequested = True

        api.Pause = pause

        written, unread, _opened = self.make(opl_batch=1).run(BAG)

        self.assertEqual((written, unread), (1, 0))
        self.assertEqual(len(self.sink.lines), 1)


if __name__ == "__main__":
    unittest.main()
