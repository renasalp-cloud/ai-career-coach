import unittest

from app.models import RequirementProfile, RequirementSkill
from app.requirements.validator import (
    RequirementProfileValidationError,
    RequirementProfileValidator,
)


class RequirementProfileValidatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = RequirementProfileValidator()

    def test_returns_valid_profile_unchanged(self) -> None:
        profile = self._profile(RequirementSkill(name="Skill", priority="required"))

        result = self.validator.validate(profile)

        self.assertIs(result, profile)

    def test_rejects_profile_with_no_skills(self) -> None:
        with self.assertRaisesRegex(RequirementProfileValidationError, "at least one skill"):
            self.validator.validate(RequirementProfile())

    def test_rejects_empty_skill_name(self) -> None:
        self._assert_invalid_name("")

    def test_rejects_whitespace_only_skill_name(self) -> None:
        self._assert_invalid_name(" \t\n ")

    def test_rejects_exact_duplicate(self) -> None:
        self._assert_duplicate("Skill", "Skill")

    def test_rejects_case_insensitive_duplicate(self) -> None:
        self._assert_duplicate("Skill", "sKiLl")

    def test_rejects_whitespace_insensitive_duplicate(self) -> None:
        self._assert_duplicate("Data Analysis", "Data\tAnalysis")

    def test_rejects_invalid_priority(self) -> None:
        invalid_skill = RequirementSkill.model_construct(
            name="Skill", priority="urgent"
        )
        profile = self._profile(invalid_skill)

        with self.assertRaisesRegex(
            RequirementProfileValidationError, "Unsupported.*priority"
        ):
            self.validator.validate(profile)

    def _assert_invalid_name(self, name: str) -> None:
        profile = self._profile(
            RequirementSkill(name=name, priority="required")
        )
        with self.assertRaisesRegex(
            RequirementProfileValidationError, "empty or whitespace-only"
        ):
            self.validator.validate(profile)

    def _assert_duplicate(self, first: str, second: str) -> None:
        profile = self._profile(
            RequirementSkill(name=first, priority="required"),
            RequirementSkill(name=second, priority="preferred"),
        )
        with self.assertRaisesRegex(RequirementProfileValidationError, "Duplicate"):
            self.validator.validate(profile)

    @staticmethod
    def _profile(*skills: RequirementSkill) -> RequirementProfile:
        return RequirementProfile(skills=list(skills))


if __name__ == "__main__":
    unittest.main()
