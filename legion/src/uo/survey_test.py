import unittest

from uo.survey import survey


def tile(is_land, graphic, z=0, name=None):
    return {"is_land": is_land, "graphic": graphic, "z": z, "name": name}


class SurveyTest(unittest.TestCase):
    def setUp(self):
        self.said = []

    def run_survey(self, tiles, limit=10, matches=lambda tile: False, extra_marks=None):
        survey(tiles, 12, limit, matches, self.said.append, extra_marks)

    def test_logs_the_header_first(self):
        self.run_survey([])

        self.assertEqual(self.said, ["the arts within 12, commonest first:"])

    def test_ranks_the_commonest_art_first(self):
        tiles = [tile(True, 0x1) for _ in range(2)] + [tile(True, 0x2) for _ in range(5)]

        self.run_survey(tiles)

        self.assertIn("0x2", self.said[1])
        self.assertIn("x5", self.said[1])
        self.assertIn("0x1", self.said[2])
        self.assertIn("x2", self.said[2])

    def test_the_limit_truncates_the_ranking(self):
        tiles = [tile(True, 0x1)] + [tile(True, 0x2) for _ in range(2)]

        self.run_survey(tiles, limit=1)

        self.assertEqual(len(self.said), 2)
        self.assertIn("0x2", self.said[1])

    def test_a_matching_art_is_marked(self):
        tiles = [tile(True, 0x1)]

        self.run_survey(tiles, matches=lambda tile: tile["graphic"] == 0x1)

        self.assertIn("MATCHES", self.said[1])

    def test_a_static_shows_its_name_and_land_does_not(self):
        tiles = [tile(False, 0x2, name="mountain"), tile(True, 0x3)]

        self.run_survey(tiles)

        static_line = [line for line in self.said if "static" in line][0]
        land_line = [line for line in self.said if line.startswith("  land")][0]

        self.assertIn("'mountain'", static_line)
        self.assertNotIn("'", land_line)

    def test_a_static_with_no_name_is_a_question_mark(self):
        tiles = [tile(False, 0x2)]

        self.run_survey(tiles)

        self.assertIn("'?'", self.said[1])

    def test_extra_marks_are_appended(self):
        tiles = [tile(True, 0x1)]

        self.run_survey(tiles, extra_marks=lambda tile: ["CAVE"])

        self.assertIn("CAVE", self.said[1])

    def test_decimal_and_hex_are_both_shown(self):
        tiles = [tile(True, 231)]

        self.run_survey(tiles)

        self.assertIn("0xe7", self.said[1])
        self.assertIn("(231)", self.said[1])


if __name__ == "__main__":
    unittest.main()
