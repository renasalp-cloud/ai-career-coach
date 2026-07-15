import unittest

from app.models import RequirementProfile, RequirementSkill
from app.requirements.normalizer import RequirementProfileNormalizer


class RequirementProfileNormalizerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.normalizer = RequirementProfileNormalizer()

    def test_trims_skill_names(self) -> None:
        profile = self._profile(RequirementSkill(name="  Python  ", priority="required"))

        normalized = self.normalizer.normalize(profile)

        self.assertEqual(normalized.skills[0].name, "Python")

    def test_removes_empty_skill_names(self) -> None:
        profile = self._profile(RequirementSkill(name="", priority="required"))

        normalized = self.normalizer.normalize(profile)

        self.assertEqual(normalized.skills, [])

    def test_removes_whitespace_only_skill_names(self) -> None:
        profile = self._profile(RequirementSkill(name=" \t\n ", priority="preferred"))

        normalized = self.normalizer.normalize(profile)

        self.assertEqual(normalized.skills, [])

    def test_removes_exact_duplicates(self) -> None:
        profile = self._profile(
            RequirementSkill(name="Python", priority="required"),
            RequirementSkill(name="Python", priority="preferred"),
        )

        normalized = self.normalizer.normalize(profile)

        self.assertEqual([skill.name for skill in normalized.skills], ["Python"])

    def test_removes_case_insensitive_duplicates(self) -> None:
        profile = self._profile(
            RequirementSkill(name="Python", priority="required"),
            RequirementSkill(name=" python ", priority="preferred"),
            RequirementSkill(name="PYTHON", priority="optional"),
        )

        normalized = self.normalizer.normalize(profile)

        self.assertEqual([skill.name for skill in normalized.skills], ["Python"])

    def test_preserves_first_occurrence(self) -> None:
        profile = self._profile(
            RequirementSkill(name=" python ", priority="preferred"),
            RequirementSkill(name="PYTHON", priority="required"),
        )

        normalized = self.normalizer.normalize(profile)

        self.assertEqual(
            normalized.skills[0],
            RequirementSkill(name="python", priority="preferred"),
        )

    def test_preserves_skill_order(self) -> None:
        profile = self._profile(
            RequirementSkill(name=" Docker ", priority="preferred"),
            RequirementSkill(name="Python", priority="required"),
            RequirementSkill(name="docker", priority="optional"),
            RequirementSkill(name="Communication", priority="optional"),
        )

        normalized = self.normalizer.normalize(profile)

        self.assertEqual(
            [skill.name for skill in normalized.skills],
            ["Docker", "Python", "Communication"],
        )

    def test_preserves_priorities(self) -> None:
        profile = self._profile(
            RequirementSkill(name="Python", priority="required"),
            RequirementSkill(name="Docker", priority="preferred"),
            RequirementSkill(name="Communication", priority="optional"),
        )

        normalized = self.normalizer.normalize(profile)

        self.assertEqual(
            [skill.priority for skill in normalized.skills],
            ["required", "preferred", "optional"],
        )

    def test_does_not_mutate_input_profile(self) -> None:
        profile = RequirementProfile(
            title=" Generalist ",
            skills=[RequirementSkill(name=" Python ", priority="required")],
            responsibilities=["Build systems"],
            qualifications=["Relevant experience"],
            source="test",
        )
        original_dump = profile.model_dump()

        normalized = self.normalizer.normalize(profile)
        normalized.responsibilities.append("New responsibility")

        self.assertIsNot(normalized, profile)
        self.assertEqual(profile.model_dump(), original_dump)

    @staticmethod
    def _profile(*skills: RequirementSkill) -> RequirementProfile:
        return RequirementProfile(skills=list(skills))


if __name__ == "__main__":
    unittest.main()
