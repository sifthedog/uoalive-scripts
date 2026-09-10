import unittest

from uo.tooltip import parse_tooltip, tooltip_key, tooltip_number

CONFIG = {
    "tier": ["Minor Magic Item", "Lesser Magic Item", "Greater Magic Item", "Major Magic Item",
             "Lesser Artifact", "Greater Artifact", "Major Artifact", "Legendary Artifact"],
    "durability": ["durability"],
    "weight": ["weight"],
    "prefixes": ["crafted by"],
}


def parse(*lines):
    return parse_tooltip(list(lines), CONFIG)


class TooltipNumberTest(unittest.TestCase):
    def test_reads_a_percentage(self):
        self.assertEqual(tooltip_number("15%"), 15)

    def test_reads_a_signed_value(self):
        self.assertEqual(tooltip_number("+20%"), 20)
        self.assertEqual(tooltip_number("-10"), -10)

    def test_reads_seconds_as_a_float(self):
        self.assertEqual(tooltip_number("2.5s"), 2.5)

    def test_refuses_what_is_not_a_number(self):
        self.assertIsNone(tooltip_number("-"))
        self.assertIsNone(tooltip_number("stones"))
        self.assertIsNone(tooltip_number("1.2.3"))
        self.assertIsNone(tooltip_number(""))

    def test_a_key_drops_its_colon(self):
        self.assertEqual(tooltip_key(["uses", "remaining:"]), "uses remaining")


class ParseTooltipTest(unittest.TestCase):
    def test_a_bare_name_has_nothing_else(self):
        parsed = parse("Longsword")

        self.assertEqual(parsed["name"], "Longsword")
        self.assertIsNone(parsed["tier"])
        self.assertIsNone(parsed["durability"])
        self.assertIsNone(parsed["weight"])
        self.assertEqual(parsed["props"], {})

    def test_the_tier_keeps_the_shards_wording(self):
        self.assertEqual(parse("Longsword", "Greater Artifact")["tier"], "Greater Artifact")
        self.assertEqual(parse("Longsword", "minor magic item")["tier"], "minor magic item")

    def test_durability_reads_both_spacings(self):
        self.assertEqual(parse("Longsword", "Durability 45 / 50")["durability"],
                         {"current": 45, "max": 50})
        self.assertEqual(parse("Longsword", "Durability: 45/50")["durability"],
                         {"current": 45, "max": 50})

    def test_weight_drops_the_unit(self):
        self.assertEqual(parse("Longsword", "Weight: 3 Stones")["weight"], 3)
        self.assertEqual(parse("Longsword", "Weight: 1 Stone")["weight"], 1)

    def test_a_percentage_becomes_a_number(self):
        self.assertEqual(parse("Longsword", "Hit Chance Increase 15%")["props"],
                         {"hit chance increase": 15})

    def test_a_sign_is_kept(self):
        self.assertEqual(parse("Longsword", "Damage Increase +20%", "Luck -10")["props"],
                         {"damage increase": 20, "luck": -10})

    def test_a_range_becomes_a_pair(self):
        self.assertEqual(parse("Longsword", "Weapon Damage 13 - 15")["props"],
                         {"weapon damage": [13, 15]})

    def test_seconds_are_a_float_not_the_digits(self):
        self.assertEqual(parse("Longsword", "Weapon Speed 2.5s")["props"], {"weapon speed": 2.5})

    def test_a_colon_and_a_trailing_unit_leave_the_number(self):
        self.assertEqual(parse("Longsword", "Lifespan: 3600 seconds", "Uses Remaining: 50")["props"],
                         {"lifespan": 3600, "uses remaining": 50})

    def test_a_colon_with_text_keeps_the_text(self):
        self.assertEqual(parse("Longsword", "Skill Required: Swordsmanship")["props"],
                         {"skill required": "Swordsmanship"})

    def test_a_line_with_nothing_to_read_is_a_flag(self):
        self.assertEqual(parse("Longsword", "Mage Armor", "Antique", "Blessed")["props"],
                         {"mage armor": True, "antique": True, "blessed": True})

    def test_a_prefix_line_keeps_the_rest_as_text(self):
        self.assertEqual(parse("Longsword", "Crafted by Kaldor")["props"], {"crafted by": "Kaldor"})

    def test_resists_are_separate_keys(self):
        self.assertEqual(parse("Longsword", "Physical Resist 10%", "Fire Resist 5%")["props"],
                         {"physical resist": 10, "fire resist": 5})

    def test_blank_lines_are_skipped_and_the_rest_trimmed(self):
        parsed = parse("  ", "Longsword", "", " Antique ")

        self.assertEqual(parsed["name"], "Longsword")
        self.assertEqual(parsed["props"], {"antique": True})

    def test_nothing_at_all_reads_as_an_empty_name(self):
        self.assertEqual(parse()["name"], "")

    def test_a_bare_number_line_is_a_flag_rather_than_an_empty_key(self):
        self.assertEqual(parse("Longsword", "42")["props"], {"42": True})


if __name__ == "__main__":
    unittest.main()
