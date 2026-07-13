import unittest

from app.semantic.default_aliases import build_default_skill_alias_registry


class DefaultAliasesTest(unittest.TestCase):
    def test_default_registry_contains_verified_model_training_alias(self) -> None:
        registry = build_default_skill_alias_registry()

        self.assertEqual(
            registry.aliases_for("Model training and evaluation"),
            [
                "Built and evaluated machine learning models",
            ],
        )

    def test_default_registry_contains_llm_application_evidence_aliases(self) -> None:
        registry = build_default_skill_alias_registry()

        self.assertIn(
            "Developed generative AI applications",
            registry.aliases_for("LLM application development"),
        )
