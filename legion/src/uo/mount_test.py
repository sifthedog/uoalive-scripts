import unittest

from test_support.uo import install
from uo.mount import dismount


class DismountTest(unittest.TestCase):
    def setUp(self):
        self.api = install()

    def test_an_unmounted_character_needs_no_dismount(self):
        self.api.Player.IsMounted = False

        self.assertTrue(dismount(3, 1.0, 0.1))
        self.assertEqual(self.api.dismounts, 0)

    def test_dismounting_lands_on_the_first_attempt(self):
        self.api.Player.IsMounted = True

        def dismount_now():
            self.api.dismounts += 1
            self.api.Player.IsMounted = False

        self.api.Dismount = dismount_now

        self.assertTrue(dismount(3, 1.0, 0.1))
        self.assertEqual(self.api.dismounts, 1)

    def test_a_refusal_is_retried_up_to_attempts_times(self):
        self.api.Player.IsMounted = True

        self.assertFalse(dismount(3, 0.2, 0.1))
        self.assertEqual(self.api.dismounts, 3)

    def test_landing_on_a_later_attempt_stops_retrying(self):
        self.api.Player.IsMounted = True
        calls = [0]

        def dismount_now():
            calls[0] += 1
            self.api.dismounts += 1

            if calls[0] == 2:
                self.api.Player.IsMounted = False

        self.api.Dismount = dismount_now

        self.assertTrue(dismount(3, 0.2, 0.1))
        self.assertEqual(self.api.dismounts, 2)


if __name__ == "__main__":
    unittest.main()
