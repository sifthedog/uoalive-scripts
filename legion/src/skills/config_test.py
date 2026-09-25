import unittest

from skills.config import DELAY, SKILLS

FIELDS = ("key", "caption", "skills", "targets", "flag", "gump", "success", "failure", "outcomes")
SHARED = ("unskilled", "saving", "throttled")


class SkillsTableTest(unittest.TestCase):
    def test_keys_are_unique(self):
        keys = [row["key"] for row in SKILLS]

        self.assertEqual(len(keys), len(set(keys)))

    def test_every_row_has_every_field(self):
        for row in SKILLS:
            self.assertEqual(set(row), set(FIELDS), row["key"])

    def test_success_and_failure_are_distinct_and_never_a_shared_bucket(self):
        for row in SKILLS:
            self.assertNotEqual(row["success"], row["failure"], row["key"])
            self.assertNotIn(row["success"], SHARED, row["key"])
            self.assertNotIn(row["failure"], SHARED, row["key"])

    def test_failure_has_a_bucket_and_success_has_one_unless_proven_another_way(self):
        for row in SKILLS:
            names = [name for name, _phrases in row["outcomes"]]

            self.assertIn(row["failure"], names, row["key"])

            if not row["flag"] and not row["gump"]:
                self.assertIn(row["success"], names, row["key"])

    def test_the_shared_buckets_are_polled_by_every_row_and_throttled_is_last_of_them(self):
        for row in SKILLS:
            names = [name for name, _phrases in row["outcomes"]]

            for name in SHARED:
                self.assertIn(name, names, row["key"])

            self.assertLess(names.index("unskilled"), names.index("throttled"), row["key"])
            self.assertEqual(len(names), len(set(names)), row["key"])

            for _name, phrases in row["outcomes"]:
                self.assertGreater(len(phrases), 0, row["key"])

    def test_every_row_names_its_skill(self):
        for row in SKILLS:
            self.assertGreater(len(row["skills"]), 0, row["key"])

    def test_hiding_reads_busy_before_failed(self):
        hiding = [row for row in SKILLS if row["key"] == "hiding"][0]
        names = [name for name, _phrases in hiding["outcomes"]]

        self.assertLess(names.index("busy"), names.index("failed"))

    def test_the_pace_leaves_a_pause(self):
        self.assertGreater(DELAY, 0)


if __name__ == "__main__":
    unittest.main()
