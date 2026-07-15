"""Deterministic normalization for requirement profiles."""

from app.models import RequirementProfile, RequirementSkill


class RequirementProfileNormalizer:
    """Normalize requirement skill names without changing their meaning."""

    def normalize(self, profile: RequirementProfile) -> RequirementProfile:
        """Return a normalized copy of ``profile`` without mutating the input."""

        normalized_skills: list[RequirementSkill] = []
        seen_names: set[str] = set()

        for skill in profile.skills:
            name = skill.name.strip()

            if not name:
                continue

            comparison_key = name.casefold()

            if comparison_key in seen_names:
                continue

            seen_names.add(comparison_key)
            normalized_skills.append(
                RequirementSkill(name=name, priority=skill.priority)
            )

        return profile.model_copy(
            deep=True,
            update={"skills": normalized_skills},
        )
