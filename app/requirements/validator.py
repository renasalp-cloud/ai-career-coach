"""Deterministic validation for normalized requirement profiles."""

from app.models import RequirementProfile


class RequirementProfileValidationError(ValueError):
    """Raised when a requirement profile is not usable for matching."""


class RequirementProfileValidator:
    """Validate requirement profiles without repairing or mutating them."""

    _VALID_PRIORITIES = {"required", "preferred", "optional"}

    def validate(self, profile: RequirementProfile) -> RequirementProfile:
        """Return ``profile`` unchanged when it is valid."""
        if not profile.skills:
            raise RequirementProfileValidationError(
                "Requirement profile must contain at least one skill."
            )

        seen_names: set[str] = set()

        for skill in profile.skills:
            if not skill.name or not skill.name.strip():
                raise RequirementProfileValidationError(
                    "Requirement skill name must not be empty or whitespace-only."
                )

            comparison_key = "".join(skill.name.split()).casefold()
            if comparison_key in seen_names:
                raise RequirementProfileValidationError(
                    f"Duplicate requirement skill: {skill.name!r}."
                )
            seen_names.add(comparison_key)

            if skill.priority not in self._VALID_PRIORITIES:
                raise RequirementProfileValidationError(
                    f"Unsupported requirement skill priority: {skill.priority!r}."
                )

        return profile
