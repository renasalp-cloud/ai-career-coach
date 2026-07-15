import unittest

from app.assessment.requirement_assessment import (
    RequirementAssessmentEngine,
    RequirementAssessmentError,
)
from app.models import RequirementProfile, RequirementSkill, SkillMatch


def _profile(*skills: tuple[str, str]) -> RequirementProfile:
    return RequirementProfile(
        skills=[RequirementSkill(name=name, priority=priority) for name, priority in skills]
    )


def _match(name: str, status: str) -> SkillMatch:
    return SkillMatch.model_construct(role_skill=name, status=status)


class RequirementAssessmentEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = RequirementAssessmentEngine()

    def test_calculates_overall_and_priority_coverage(self) -> None:
        profile = _profile(
            ("A", "required"),
            ("B", "required"),
            ("C", "preferred"),
            ("D", "preferred"),
            ("E", "optional"),
        )
        assessment = self.engine.assess(
            profile,
            [
                _match("A", "demonstrated"),
                _match("B", "missing"),
                _match("C", "demonstrated"),
                _match("D", "demonstrated"),
                _match("E", "missing"),
            ],
        )

        self.assertEqual(assessment.total_requirements, 5)
        self.assertEqual(assessment.demonstrated_requirements, 3)
        self.assertEqual(assessment.missing_requirements, 2)
        self.assertEqual(assessment.overall_coverage_percentage, 60)
        self.assertEqual((assessment.required_total, assessment.required_demonstrated), (2, 1))
        self.assertEqual(assessment.required_coverage_percentage, 50)
        self.assertEqual((assessment.preferred_total, assessment.preferred_demonstrated), (2, 2))
        self.assertEqual(assessment.preferred_coverage_percentage, 100)
        self.assertEqual((assessment.optional_total, assessment.optional_demonstrated), (1, 0))
        self.assertEqual(assessment.optional_coverage_percentage, 0)

    def test_zero_totals_return_zero_percentages(self) -> None:
        assessment = self.engine.assess(RequirementProfile(), [])

        self.assertEqual(assessment.overall_coverage_percentage, 0)
        self.assertEqual(assessment.required_coverage_percentage, 0)
        self.assertEqual(assessment.preferred_coverage_percentage, 0)
        self.assertEqual(assessment.optional_coverage_percentage, 0)

    def test_percentages_round_to_whole_numbers(self) -> None:
        profile = _profile(*[(str(index), "required") for index in range(8)])
        assessment = self.engine.assess(
            profile,
            [
                _match(str(index), "demonstrated" if index == 0 else "missing")
                for index in range(8)
            ],
        )

        self.assertEqual(assessment.overall_coverage_percentage, 13)
        self.assertEqual(assessment.required_coverage_percentage, 13)

    def test_collects_and_groups_skills_in_requirement_order(self) -> None:
        profile = _profile(
            ("Required missing", "required"),
            ("Demonstrated one", "preferred"),
            ("Preferred missing", "preferred"),
            ("Demonstrated two", "optional"),
            ("Optional missing", "optional"),
        )
        assessment = self.engine.assess(
            profile,
            [
                _match("Optional missing", "missing"),
                _match("Demonstrated two", "demonstrated"),
                _match("Preferred missing", "missing"),
                _match("Demonstrated one", "demonstrated"),
                _match("Required missing", "missing"),
            ],
        )

        self.assertEqual(assessment.demonstrated_skills, ["Demonstrated one", "Demonstrated two"])
        self.assertEqual(assessment.critical_missing_skills, ["Required missing"])
        self.assertEqual(assessment.preferred_missing_skills, ["Preferred missing"])
        self.assertEqual(assessment.optional_missing_skills, ["Optional missing"])

    def test_duplicate_output_skill_names_are_prevented(self) -> None:
        profile = _profile(("Repeated", "required"), ("Repeated", "required"))
        assessment = self.engine.assess(profile, [_match("Repeated", "demonstrated")])

        self.assertEqual(assessment.demonstrated_skills, ["Repeated"])

    def test_missing_validated_match_is_rejected(self) -> None:
        with self.assertRaisesRegex(RequirementAssessmentError, "no validated match"):
            self.engine.assess(_profile(("A", "required")), [])

    def test_duplicate_validated_matches_are_rejected(self) -> None:
        with self.assertRaisesRegex(RequirementAssessmentError, "Multiple validated matches"):
            self.engine.assess(
                _profile(("A", "required")),
                [_match("A", "missing"), _match("A", "missing")],
            )

    def test_unknown_requirement_match_is_rejected(self) -> None:
        with self.assertRaisesRegex(RequirementAssessmentError, "unknown requirement"):
            self.engine.assess(_profile(("A", "required")), [_match("B", "missing")])

    def test_unsupported_match_status_is_rejected(self) -> None:
        with self.assertRaisesRegex(RequirementAssessmentError, "Unsupported.*status"):
            self.engine.assess(_profile(("A", "required")), [_match("A", "partial")])


if __name__ == "__main__":
    unittest.main()
