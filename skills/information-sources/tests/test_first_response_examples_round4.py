from pathlib import Path
import unittest


SKILL_PATH = Path(__file__).resolve().parents[1] / "SKILL.md"


class InformationSourcesRound4FirstResponseExamplesTests(unittest.TestCase):
    def test_first_response_section_includes_generic_page_route_example(self):
        text = SKILL_PATH.read_text(encoding="utf-8")

        expected_examples = [
            "### Generic page-shaped reading",
            "Source of truth: Original page or document",
            "Preferred tool: Source-specific official tool or direct original retrieval",
            "Fallback: Approved Firecrawl sources within the existing budget; otherwise report unavailable content",
        ]

        for expected in expected_examples:
            self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()
