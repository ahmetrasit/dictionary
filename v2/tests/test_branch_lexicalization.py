import unittest

from v2.scripts.branch_lexicalization import branch_lexicalization_profile


class BranchLexicalizationProfileTest(unittest.TestCase):
    def test_form_only_branch_is_bare(self):
        profile = branch_lexicalization_profile(
            [{"unit_kind": "form"}, {"unit_kind": "form"}]
        )

        self.assertEqual(profile["branch_kind"], "bare")
        self.assertFalse(profile["has_non_bare"])
        self.assertFalse(profile["has_collocation"])
        self.assertEqual(profile["unit_kind_counts"], {"form": 2})

    def test_collocation_marks_branch_non_bare(self):
        profile = branch_lexicalization_profile(
            [{"unit_kind": "form"}, {"unit_kind": "collocation"}]
        )

        self.assertEqual(profile["branch_kind"], "mixed_non_bare")
        self.assertTrue(profile["has_non_bare"])
        self.assertTrue(profile["has_collocation"])
        self.assertEqual(
            profile["unit_kind_counts"],
            {"collocation": 1, "form": 1},
        )

    def test_non_form_unit_marks_branch_non_bare(self):
        profile = branch_lexicalization_profile([{"unit_kind": "lexical_unit"}])

        self.assertEqual(profile["branch_kind"], "non_bare")
        self.assertTrue(profile["has_non_bare"])
        self.assertFalse(profile["has_collocation"])


if __name__ == "__main__":
    unittest.main()
