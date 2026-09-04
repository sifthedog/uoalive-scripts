import unittest

from lumberjacking.haul import Haul
from lumberjacking.wood import Wood
from test_support.uo import install, item, mobile

LOGS = set([0x1BDD])
BOARDS = set([0x1BD7])
ANIMALS = set([0x123])


class Boards(object):
    def __init__(self):
        self.made = 0
        self.ran = 0

    def make_boards(self):
        self.made += 1

    def run(self):
        self.ran += 1


class Saves(object):
    def __init__(self):
        self.saving = False
        self.waits = 0

    def is_saving(self):
        return self.saving

    def wait_out(self):
        self.waits += 1


class HaulTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.said = []
        self.boards = Boards()
        self.saves = Saves()
        self.wood = Wood(set(LOGS), ["log"], set(BOARDS), ["board"], self.said.append)

    def build(self, serials=None):
        return Haul(self.wood, self.boards, self.saves, {
            "serials": serials or [],
            "graphics": ANIMALS,
            "radius": 18,
            "unload_range": 2,
            "pathfind_timeout": 10,
            "move_delay": 0.7,
            "max_picks": 8,
            "pick_timeout": 60.0,
            "buffer": 120,
            "max_empty_hauls": 3,
        }, self.said.append)

    def _animal(self, serial=5, distance=1, renamable=True):
        pack = item(serial=serial + 1000)
        beast = mobile(serial=serial, graphic=0x123, name="a pack horse", distance=distance,
                       is_renamable=renamable, backpack=pack)
        self.api.see(beast)

        return beast

    def test_finds_nothing_when_none_is_in_sight(self):
        self.assertEqual(self.build().find(), [])

    def test_finds_one_by_body(self):
        self._animal()

        self.assertEqual([a.Serial for a in self.build().find()], [5])

    def test_leaves_out_the_dead(self):
        beast = self._animal()
        beast.IsDead = True

        self.assertEqual(self.build().find(), [])

    def test_prefers_your_own_pets(self):
        self._animal(serial=5, renamable=True)
        self._animal(serial=6, renamable=False)

        self.assertEqual([a.Serial for a in self.build().find()], [5])

    def test_nearest_first(self):
        self._animal(serial=5, distance=9)
        self._animal(serial=6, distance=2)

        self.assertEqual([a.Serial for a in self.build().find()][0], 6)

    def test_a_pinned_serial_is_checked_rather_than_trusted(self):
        self.assertEqual(self.build(serials=[999]).find(), [])

    def test_says_what_it_found_once(self):
        self._animal()
        haul = self.build()
        haul.find()
        haul.find()

        self.assertEqual(len([line for line in self.said if "pack animal(s) -" in line]), 1)

    def test_the_companion_is_the_one_the_last_search_settled_on(self):
        self._animal()
        haul = self.build()
        haul.find()

        self.assertEqual(haul.companion().Serial, 5)

    def test_says_once_when_there_is_no_animal(self):
        haul = self.build()

        self.assertFalse(haul.unload())
        self.assertFalse(haul.unload())
        self.assertEqual(self.said.count("no pack animal nearby"), 1)

    def test_moves_the_boards_onto_the_animal(self):
        self._animal()
        self.api.hold(item(serial=1, graphic=0x1BD7, amount=20))

        def move(serial, container, amount=-1):
            self.api.moved.append((serial, container, amount))
            self.api.containers[self.api.Backpack] = []

            return True

        self.api.MoveItem = move

        self.assertTrue(self.build().unload())
        self.assertEqual(self.api.moved, [(1, 1005, -1)])

    def test_an_animal_that_takes_nothing_is_left_out_of_the_rest_of_the_run(self):
        self._animal()
        self.api.hold(item(serial=1, graphic=0x1BD7, amount=20))
        haul = self.build()
        haul.unload()

        self.assertTrue(any("took nothing, leaving it out" in line for line in self.said))

    def test_a_save_is_not_read_as_the_animals_verdict(self):
        self._animal()
        self.api.hold(item(serial=1, graphic=0x1BD7, amount=20))
        self.saves.saving = True
        self.build().unload()

        self.assertTrue(any("while the world is saving" in line for line in self.said))
        self.assertFalse(any("leaving it out" in line for line in self.said))

    def test_no_animal_latches_hauling_off(self):
        haul = self.build()
        self.api.Player.Weight = 350
        haul.haul_now()

        self.assertFalse(haul.hauling())
        self.assertIn("no pack animal found, carrying on until overweight", self.said)

    def test_hauls_that_free_nothing_latch_it_off(self):
        self._animal()
        self.api.Player.Weight = 350
        haul = self.build()

        for _attempt in range(3):
            haul.haul_now()

        self.assertFalse(haul.hauling())

    def test_a_haul_that_freed_weight_forgives_the_count(self):
        self._animal()
        self.api.Player.Weight = 350
        haul = self.build()
        haul.haul_now()
        haul.haul_now()

        self.api.Player.Weight = 100
        haul.haul_now()
        self.api.Player.Weight = 350
        haul.haul_now()

        self.assertTrue(haul.hauling())

    def test_under_the_buffer_there_is_nothing_to_do(self):
        self.api.Player.Weight = 100

        self.assertIsNone(self.build().haul_for_room())

    def test_once_hauling_is_off_it_only_converts(self):
        haul = self.build()
        self.api.Player.Weight = 350
        haul.haul_now()

        self.assertIsNone(haul.haul_for_room())
        self.assertEqual(self.boards.ran, 1)

    def test_two_hauls_do_not_share_what_is_full(self):
        self._animal()
        self.api.hold(item(serial=1, graphic=0x1BD7, amount=20))
        self.build().unload()
        other = self.build()
        other.unload()

        self.assertTrue(any("took nothing, leaving it out" in line for line in self.said))
