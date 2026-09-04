import unittest

from uo.pace import Pace


class PaceTest(unittest.TestCase):
    def setUp(self):
        self.pace = Pace(1.5, 0.4, 8.0, 5)

    def test_starts_at_the_floor(self):
        self.assertAlmostEqual(self.pace.delay(), 1.5)

    def test_a_refusal_raises_it_by_a_step(self):
        self.assertAlmostEqual(self.pace.refused(), 1.9)

    def test_it_stops_rising_at_the_cap(self):
        for _ in range(100):
            self.pace.refused()

        self.assertAlmostEqual(self.pace.delay(), 8.0)

    def test_one_success_does_not_ease_it(self):
        self.pace.refused()

        self.assertAlmostEqual(self.pace.landed(), 1.9)

    def test_it_eases_after_a_run_of_successes(self):
        self.pace.refused()

        for _ in range(5):
            last = self.pace.landed()

        self.assertAlmostEqual(last, 1.5)

    def test_it_never_eases_below_the_floor(self):
        for _ in range(50):
            self.pace.landed()

        self.assertAlmostEqual(self.pace.delay(), 1.5)

    def test_a_refusal_forgets_the_run_of_successes(self):
        self.pace.refused()
        self.pace.refused()

        for _ in range(4):
            self.pace.landed()

        self.pace.refused()

        for _ in range(4):
            self.pace.landed()

        self.assertGreater(self.pace.delay(), 1.5)

    def test_two_paces_do_not_share_a_delay(self):
        self.pace.refused()

        self.assertAlmostEqual(Pace(1.5, 0.4, 8.0, 5).delay(), 1.5)
