import unittest

from app.requirements.category_classifier import RequirementCategoryClassifier


class RequirementCategoryClassifierTest(unittest.TestCase):
    def setUp(self) -> None:
        self.classifier = RequirementCategoryClassifier()

    def test_classifies_supported_requirement_categories(self) -> None:
        examples = {
            "Bachelor's degree required": "education",
            "Three years of relevant experience": "experience",
            "Must hold the required license": "certification",
            "Fluent English": "language",
            "Proficiency with office software": "tool",
            "Strong communication skills": "soft_skill",
            "Knowledge of regulatory requirements": "domain_knowledge",
            "Project planning": "skill",
        }

        for requirement, expected in examples.items():
            with self.subTest(requirement=requirement):
                self.assertEqual(self.classifier.classify(requirement), expected)

    def test_tool_cues_take_precedence_over_experience_and_knowledge_wrappers(self) -> None:
        for requirement in (
            "Experience using inventory systems",
            "Knowledge of design tools",
        ):
            with self.subTest(requirement=requirement):
                self.assertEqual(self.classifier.classify(requirement), "tool")

    def test_ambiguous_requirement_falls_back_to_other(self) -> None:
        self.assertEqual(self.classifier.classify("Reliable and proactive"), "other")

    def test_remains_profession_independent_across_fixture_domains(self) -> None:
        examples = (
            ("Technical troubleshooting", "skill"),
            ("Document preparation", "skill"),
            ("Time management", "soft_skill"),
        )

        for requirement, expected in examples:
            with self.subTest(requirement=requirement):
                self.assertEqual(self.classifier.classify(requirement), expected)

    def test_classification_has_no_target_role_input(self) -> None:
        self.assertEqual(
            list(self.classifier.classify.__annotations__),
            ["requirement_text", "return"],
        )


if __name__ == "__main__":
    unittest.main()
