import unittest

from taming.quarry import Hunt, is_pet
from test_support.uo import install, mobile

GRAPHIC = 0x00D0


class HuntTest(unittest.TestCase):
    def setUp(self):
        self.api = install()
        self.hunt = Hunt("sifinha", 12, 1)

    def test_finds_nothing_when_nothing_is_in_sight(self):
        self.assertIsNone(self.hunt.next_quarry(GRAPHIC))

    def test_a_radius_of_zero_turns_the_hunt_off(self):
        self.api.see(mobile(serial=5, graphic=GRAPHIC, name="a llama"))

        self.assertIsNone(Hunt("sifinha", 0, 1).next_quarry(GRAPHIC))

    def test_finds_an_animal_of_the_type(self):
        self.api.see(mobile(serial=5, graphic=GRAPHIC, name="a llama"))
        quarry, in_sight = self.hunt.next_quarry(GRAPHIC)

        self.assertEqual(quarry["serial"], 5)
        self.assertEqual(in_sight, 1)

    def test_leaves_out_one_the_run_is_finished_with(self):
        self.api.see(mobile(serial=5, graphic=GRAPHIC, name="a llama"))
        self.hunt.leave_out(5)

        self.assertIsNone(self.hunt.next_quarry(GRAPHIC))

    def test_leaves_out_a_pet(self):
        self.api.see(mobile(serial=5, graphic=GRAPHIC, name="a llama", is_renamable=True))

        self.assertIsNone(self.hunt.next_quarry(GRAPHIC))

    def test_leaves_out_the_dead(self):
        self.api.see(mobile(serial=5, graphic=GRAPHIC, name="a llama", is_dead=True))

        self.assertIsNone(self.hunt.next_quarry(GRAPHIC))

    def test_leaves_out_one_already_wearing_the_pet_name(self):
        self.api.see(mobile(serial=5, graphic=GRAPHIC, name="Sifinha"))

        self.assertIsNone(self.hunt.next_quarry(GRAPHIC))

    def test_an_empty_pet_name_claims_nothing(self):
        self.api.see(mobile(serial=5, graphic=GRAPHIC, name=""))

        self.assertIsNotNone(Hunt("", 12, 1).next_quarry(GRAPHIC))

    def test_asks_for_a_tooltip_when_the_name_is_empty(self):
        self.api.see(mobile(serial=5, graphic=GRAPHIC, name="", props="a great hart\nstrong"))
        quarry, _in_sight = self.hunt.next_quarry(GRAPHIC)

        self.assertEqual(quarry["name"], "a great hart")

    def test_falls_back_to_the_serial_with_no_tooltip_either(self):
        self.api.see(mobile(serial=5, graphic=GRAPHIC, name=""))
        quarry, _in_sight = self.hunt.next_quarry(GRAPHIC)

        self.assertEqual(quarry["name"], hex(5))

    def test_two_hunts_do_not_share_what_was_skipped(self):
        self.api.see(mobile(serial=5, graphic=GRAPHIC, name="a llama"))
        self.hunt.leave_out(5)

        self.assertIsNotNone(Hunt("sifinha", 12, 1).next_quarry(GRAPHIC))


class IsPetTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_a_missing_mobile_is_not_a_pet(self):
        self.assertFalse(is_pet(5))

    def test_renamable_is_what_says_it_is_yours(self):
        self.api.see(mobile(serial=5, is_renamable=True))

        self.assertTrue(is_pet(5))

    def test_a_destroyed_mobile_is_not_a_pet(self):
        self.api.see(mobile(serial=5, is_renamable=True, is_destroyed=True))

        self.assertFalse(is_pet(5))
