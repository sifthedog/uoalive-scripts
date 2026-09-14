import unittest

from hiding.proof import flag_outcome


class FlagOutcomeTest(unittest.TestCase):
    def test_becoming_hidden_is_a_success(self):
        self.assertEqual(flag_outcome(False, True), "hidden")

    def test_being_revealed_is_a_failure(self):
        self.assertEqual(flag_outcome(True, False), "failed")

    def test_an_unchanged_flag_proves_nothing(self):
        self.assertIsNone(flag_outcome(False, False))
        self.assertIsNone(flag_outcome(True, True))


if __name__ == "__main__":
    unittest.main()
