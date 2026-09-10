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
            "too_far_text": ["That is too far away"],
            "capacity": 1600,
            "open_delay": 0.6,
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

        self.assertEqual(haul.unload(), "none")
        self.assertEqual(haul.unload(), "none")
        self.assertEqual(self.said.count("no pack animal nearby"), 1)

    def test_moves_the_boards_onto_the_animal(self):
        self._animal()
        self.api.hold(item(serial=1, graphic=0x1BD7, amount=20))

        def move(serial, container, amount=-1):
            self.api.moved.append((serial, container, amount))
            self.api.containers[self.api.Backpack] = []

            return True

        self.api.MoveItem = move

        self.assertEqual(self.build().unload(), "tried")
        self.assertEqual(self.api.moved, [(1, 1005, 20)])

    def test_moves_only_the_slice_the_animal_still_has_room_for(self):
        self._animal()
        self.api.containers[1005] = [item(serial=2, graphic=0x1BD7, amount=1580)]
        held = item(serial=1, graphic=0x1BD7, amount=100)
        self.api.hold(held)

        def move(serial, container, amount=-1):
            self.api.moved.append((serial, container, amount))
            held.Amount -= amount
            self.api.containers[1005][0].Amount += amount

            return True

        self.api.MoveItem = move
        haul = self.build()
        haul.unload()

        self.assertEqual(self.api.moved, [(1, 1005, 20)])
        self.assertTrue(any("took 20 of 100 boards and is full" in line for line in self.said))

        haul.unload()

        self.assertEqual(len(self.api.moved), 1)
        self.assertTrue(any("all 1 pack animal(s) are full" in line for line in self.said))

    def test_a_stack_that_fits_goes_whole_and_the_rest_waits_for_the_next_animal(self):
        self._animal(serial=5, distance=1)
        self._animal(serial=6, distance=2)
        self.api.containers[1005] = [item(serial=3, graphic=0x1BD7, amount=1550)]
        first = item(serial=1, graphic=0x1BD7, amount=30)
        second = item(serial=2, graphic=0x1BD7, amount=40)
        self.api.hold(first, second)

        def move(serial, container, amount=-1):
            self.api.moved.append((serial, container, amount))
            stack = self.api.items[serial]
            stack.Amount -= amount

            if stack.Amount == 0:
                self.api.containers[self.api.Backpack].remove(stack)

            if container == 1005:
                self.api.containers[1005][0].Amount += amount

            return True

        self.api.MoveItem = move
        self.build().unload()

        self.assertEqual(self.api.moved, [(1, 1005, 30), (2, 1005, 20), (2, 1006, 20)])

    def test_a_pack_is_opened_once_a_run_before_it_is_read(self):
        self._animal()
        self.api.hold(item(serial=1, graphic=0x1BD7, amount=20))
        haul = self.build()
        haul.unload()
        haul.unload()

        self.assertEqual(self.api.used, [1005])
        self.assertEqual(self.api.moved[0], (1, 1005, 20))

    def test_an_animal_that_takes_nothing_is_left_out_of_the_rest_of_the_run(self):
        self._animal()
        self.api.hold(item(serial=1, graphic=0x1BD7, amount=20))
        haul = self.build()
        haul.unload()

        self.assertTrue(any("took nothing, leaving it out" in line for line in self.said))

    def test_an_animal_it_cannot_reach_is_not_read_as_full(self):
        self._animal(distance=5)
        self.api.hold(item(serial=1, graphic=0x1BD7, amount=20))
        haul = self.build()

        self.assertEqual(haul.unload(), "unreached")
        self.assertTrue(any("could not get within 2 of 'a pack horse'" in line
                            for line in self.said))
        self.assertFalse(any("took nothing" in line for line in self.said))
        self.assertEqual(self.api.moved, [])

    def test_an_animal_that_walks_off_mid_load_is_tried_again_next_haul(self):
        beast = self._animal()
        self.api.hold(item(serial=1, graphic=0x1BD7, amount=20))

        def move(serial, container, amount=-1):
            self.api.moved.append((serial, container, amount))
            beast.Distance = 6

            return True

        self.api.MoveItem = move
        haul = self.build()

        self.assertEqual(haul.unload(), "unreached")
        self.assertTrue(any("moved out of reach while loading" in line for line in self.said))
        self.assertFalse(any("leaving it out" in line for line in self.said))

        beast.Distance = 1

        def move_for_real(serial, container, amount=-1):
            self.api.moved.append((serial, container, amount))
            self.api.containers[self.api.Backpack] = []

            return True

        self.api.MoveItem = move_for_real

        self.assertEqual(haul.unload(), "tried")
        self.assertEqual(len(self.api.moved), 2)

    def test_the_shard_saying_too_far_is_not_read_as_full(self):
        self._animal()
        self.api.hold(item(serial=1, graphic=0x1BD7, amount=20))

        def move(serial, container, amount=-1):
            self.api.journal.append("That is too far away.")

            return True

        self.api.MoveItem = move
        self.build().unload()

        self.assertTrue(any("moved out of reach while loading" in line for line in self.said))
        self.assertFalse(any("leaving it out" in line for line in self.said))

    def test_a_stale_too_far_line_does_not_answer_for_the_animal(self):
        self._animal()
        self.api.hold(item(serial=1, graphic=0x1BD7, amount=20))
        self.api.journal.append("That is too far away.")
        self.build().unload()

        self.assertTrue(any("leaving it out" in line for line in self.said))

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

    def test_hauls_that_could_not_reach_an_animal_do_not_count_as_full(self):
        self._animal(distance=5)
        self.api.hold(item(serial=1, graphic=0x1BD7, amount=20))
        self.api.Player.Weight = 350
        haul = self.build()

        for _attempt in range(3):
            haul.haul_now()

        self.assertTrue(haul.hauling())
        self.assertFalse(any("freed nothing" in line for line in self.said))
        self.assertEqual(self.said.count("no pack animal in reach this haul, trying again next time"),
                         3)

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
