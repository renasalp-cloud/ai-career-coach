import unittest

from app.models import RequirementProfile, RequirementSkill
from app.requirements.decomposer import RequirementDecomposer


class RequirementDecomposerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.decomposer = RequirementDecomposer()

    def test_decomposes_comma_list_and_final_conjunction(self) -> None:
        result = self.decomposer.decompose(
            self._profile("Experience with Python, Docker, and cloud deployment")
        )
        self.assertEqual([skill.name for skill in result.skills], ["Python", "Docker", "Cloud deployment"])

    def test_decomposes_conjunction_list_with_wrapper(self) -> None:
        result = self.decomposer.decompose(self._profile("Knowledge of planning or risk management"))
        self.assertEqual([skill.name for skill in result.skills], ["Planning", "Risk management"])

    def test_decomposes_semicolon_and_spaced_slash_lists(self) -> None:
        result = self.decomposer.decompose(self._profile("Planning; communication / risk management"))
        self.assertEqual([skill.name for skill in result.skills], ["Planning", "Communication", "Risk management"])

    def test_preserves_priority_and_profile_metadata(self) -> None:
        profile = RequirementProfile(
            title="Coordinator", source="source", responsibilities=["Coordinate"],
            qualifications=["Relevant experience"],
            skills=[RequirementSkill(name="Planning, communication", priority="preferred")],
        )
        result = self.decomposer.decompose(profile)
        self.assertEqual([skill.priority for skill in result.skills], ["preferred", "preferred"])
        self.assertEqual(result.title, "Coordinator")
        self.assertEqual(result.source, "source")
        self.assertEqual(result.responsibilities, ["Coordinate"])
        self.assertEqual(result.qualifications, ["Relevant experience"])

    def test_removes_duplicates_and_empty_fragments_in_first_occurrence_order(self) -> None:
        profile = RequirementProfile(skills=[
            RequirementSkill(name="Python, , Docker", priority="required"),
            RequirementSkill(name="python", priority="optional"),
        ])
        result = self.decomposer.decompose(profile)
        self.assertEqual(result.skills, [
            RequirementSkill(name="Python", priority="required"),
            RequirementSkill(name="Docker", priority="required"),
        ])

    def test_does_not_mutate_input(self) -> None:
        profile = self._profile("Experience with Python, Docker")
        original = profile.model_dump()
        result = self.decomposer.decompose(profile)
        result.responsibilities.append("Changed")
        self.assertEqual(profile.model_dump(), original)

    def test_protected_concepts_are_not_split(self) -> None:
        for phrase in (
            "Research and development", "Health and safety", "Learning and development",
            "Sales and marketing", "Continuous integration and deployment",
        ):
            with self.subTest(phrase=phrase):
                result = self.decomposer.decompose(self._profile(phrase))
                self.assertEqual([skill.name for skill in result.skills], [phrase])

    def test_preserves_protected_phrase_inside_comma_list(self) -> None:
        result = self.decomposer.decompose(
            self._profile("Experience with research and development, Python")
        )
        self.assertEqual(
            [skill.name for skill in result.skills],
            ["Research and development", "Python"],
        )

    def test_preserves_protected_phrase_inside_semicolon_list(self) -> None:
        result = self.decomposer.decompose(
            self._profile("Health and safety; risk management")
        )
        self.assertEqual(
            [skill.name for skill in result.skills],
            ["Health and safety", "Risk management"],
        )

    def test_does_not_split_design_and_implementation_verb_phrase(self) -> None:
        requirement = "Ability to design and implement scalable systems"
        result = self.decomposer.decompose(self._profile(requirement))
        self.assertEqual(
            [skill.name for skill in result.skills],
            ["Design and implement scalable systems"],
        )

    def test_does_not_split_short_ability_verb_phrase(self) -> None:
        result = self.decomposer.decompose(
            self._profile("Ability to design and implement")
        )
        self.assertEqual(
            [skill.name for skill in result.skills],
            ["Design and implement"],
        )

    def test_does_not_split_monitoring_and_improving_verb_phrase(self) -> None:
        requirement = "Experience in monitoring and improving system performance"
        result = self.decomposer.decompose(self._profile(requirement))
        self.assertEqual(
            [skill.name for skill in result.skills],
            ["Monitoring and improving system performance"],
        )

    def test_explicit_three_item_list_still_decomposes(self) -> None:
        result = self.decomposer.decompose(
            self._profile("Planning, communication and risk management")
        )
        self.assertEqual(
            [skill.name for skill in result.skills],
            ["Planning", "Communication", "Risk management"],
        )

    def test_simple_two_item_noun_concept_list_decomposes(self) -> None:
        result = self.decomposer.decompose(
            self._profile("Knowledge of planning or risk management")
        )
        self.assertEqual(
            [skill.name for skill in result.skills],
            ["Planning", "Risk management"],
        )

    def test_simple_atomic_requirement_remains_unchanged(self) -> None:
        result = self.decomposer.decompose(self._profile("Stakeholder communication"))
        self.assertEqual([skill.name for skill in result.skills], ["Stakeholder communication"])

    def test_preserves_written_and_verbal_communication_without_fragments(self) -> None:
        result = self.decomposer.decompose(
            self._profile("Excellent written and verbal communication")
        )

        names = [skill.name for skill in result.skills]
        self.assertEqual(names, ["Excellent written and verbal communication"])
        self.assertNotIn("Excellent written", names)

    @staticmethod
    def _profile(name: str) -> RequirementProfile:
        return RequirementProfile(
            skills=[RequirementSkill(name=name, priority="required")],
            responsibilities=[],
        )


if __name__ == "__main__":
    unittest.main()
