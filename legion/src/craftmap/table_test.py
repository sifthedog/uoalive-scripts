import unittest

from craftmap.table import recipes_block


class RecipesBlockTest(unittest.TestCase):
    def test_every_row_sits_under_its_group_keyed_lowercase(self):
        block = recipes_block("CARPENTRY MENU", "2026-09-13",
                              [("Other", 1), ("Misc. Add-Ons", 121)],
                              {1: [("barrel staves", 2)],
                               121: [("bulletin board", 2), ("bulletin board", 22),
                                     ("Ballot Box", 362)]})

        self.assertEqual(block.split("\n"), [
            "# CARPENTRY MENU, read off the menu on 2026-09-13",
            "CATEGORY_NAMES = [",
            '    "other",',
            '    "misc. add-ons",',
            "]",
            "",
            "RECIPES = {",
            "    # Other (button 1)",
            '    "barrel staves": (1, 2),',
            "    # Misc. Add-Ons (button 121)",
            '    "bulletin board": (121, 2),',
            '    # "bulletin board": (121, 22),  listed again, the first kept',
            '    "ballot box": (121, 362),',
            "}",
            "",
        ])

    def test_a_group_with_no_rows_read_still_heads_its_block(self):
        block = recipes_block("TINKERING MENU", "2026-09-13", [("Tools", 1)], {})

        self.assertIn("    # Tools (button 1)\n}", block)

    def test_the_block_is_python(self):
        block = recipes_block("CARPENTRY MENU", "2026-09-13", [("Other", 1)],
                              {1: [("barrel staves", 2), ("barrel staves", 22)]})
        scope = {}
        exec(block, scope)

        self.assertEqual(scope["RECIPES"], {"barrel staves": (1, 2)})
        self.assertEqual(scope["CATEGORY_NAMES"], ["other"])
