"""Default configurable aliases for deterministic skill matching."""

from app.semantic.alias_registry import SkillAliasRegistry


def build_default_skill_alias_registry() -> SkillAliasRegistry:
    return SkillAliasRegistry(
        {
            "Model training and evaluation": [
                "Built and evaluated machine learning models",
            ],
            "LLM application development": [
                "LLM based applications",
                "LLM-based applications",
                "Built LLM-based applications",
                "Developed generative AI applications",
                "Hands-on experience with LLM-based applications",
                "Implemented LLM workflows",
            ],
        }
    )