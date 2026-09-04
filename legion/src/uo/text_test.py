import unittest

from test_support.uo import install
from uo.text import any_in, clipped, word_in, words_of


class WordsOfTest(unittest.TestCase):
    def setUp(self):
        install()

    def test_splits_on_punctuation_and_lowercases(self):
        self.assertEqual(words_of("You put the Iron Ore in your pack!"),
                         ["you", "put", "the", "iron", "ore", "in", "your", "pack"])

    def test_treats_none_as_empty(self):
        self.assertEqual(words_of(None), [])

    def test_keeps_digits(self):
        self.assertEqual(words_of("valorite ore x2"), ["valorite", "ore", "x2"])


class WordInTest(unittest.TestCase):
    def test_matches_a_whole_word_only(self):
        self.assertTrue(word_in("a pile of logs", ["logs"]))
        self.assertFalse(word_in("a pile of logs", ["log"]))

    def test_is_true_when_any_word_matches(self):
        self.assertTrue(word_in("oak boards", ["logs", "boards"]))

    def test_is_false_for_no_words(self):
        self.assertFalse(word_in("oak boards", []))


class AnyInTest(unittest.TestCase):
    def test_matches_a_fragment_anywhere(self):
        self.assertTrue(any_in("That is too far away", ["too far"]))

    def test_is_case_insensitive_on_the_text_only(self):
        self.assertTrue(any_in("TOO FAR AWAY", ["too far"]))


class ClippedTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(clipped("a\n  b\tc", 40), "a b c")

    def test_marks_what_it_cut(self):
        self.assertEqual(clipped("abcdefghij", 4), "abcd...")

    def test_leaves_a_short_string_alone(self):
        self.assertEqual(clipped("abcd", 4), "abcd")
