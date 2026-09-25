import unittest

from skills.proof import flag_outcome, gump_outcome


class FlagOutcomeTest(unittest.TestCase):
    def test_becoming_hidden_is_a_success(self):
        self.assertEqual(flag_outcome(False, True), "hidden")

    def test_being_revealed_is_a_failure(self):
        self.assertEqual(flag_outcome(True, False), "failed")

    def test_an_unchanged_flag_proves_nothing(self):
        self.assertIsNone(flag_outcome(False, False))
        self.assertIsNone(flag_outcome(True, True))


class GumpOutcomeTest(unittest.TestCase):
    def test_a_new_gump_is_a_read(self):
        self.assertEqual(gump_outcome(0, 0x1234), "read")
        self.assertEqual(gump_outcome(0x1111, 0x1234), "read")

    def test_the_same_gump_still_up_proves_nothing(self):
        self.assertIsNone(gump_outcome(0x1234, 0x1234))

    def test_no_gump_proves_nothing(self):
        self.assertIsNone(gump_outcome(0, 0))
        self.assertIsNone(gump_outcome(0x1234, 0))


if __name__ == "__main__":
    unittest.main()
