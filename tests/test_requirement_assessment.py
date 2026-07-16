import unittest

from app.ai.prompt_builder import PromptContext, build_cv_analysis_prompt
from app.assessment.requirement_assessment import (
    EvidenceStrength,
    RequirementAssessmentEngine,
    RequirementAssessmentError,
)
from app.models import CandidateProfile, RequirementProfile, RequirementSkill, SkillEvidence, SkillMatch


def _profile(*skills: tuple[str, str]) -> RequirementProfile:
    return RequirementProfile(
        skills=[RequirementSkill(name=name, priority=priority) for name, priority in skills]
    )


def _match(name: str, status: str, *scores: int) -> SkillMatch:
    return SkillMatch.model_construct(
        role_skill=name,
        status=status,
        evidence=[
            SkillEvidence(source="experience", text=f"Evidence {index}", quality_score=score)
            for index, score in enumerate(scores)
        ],
    )


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

    def test_maps_selected_evidence_scores_to_strength_categories(self) -> None:
        profile = _profile(
            ("Strong", "required"),
            ("Moderate", "preferred"),
            ("Weak", "optional"),
            ("Missing", "required"),
        )

        assessment = self.engine.assess(
            profile,
            [
                _match("Strong", "demonstrated", 75),
                _match("Moderate", "demonstrated", 74),
                _match("Weak", "demonstrated", 1),
                _match("Missing", "missing", 100),
            ],
        )

        self.assertEqual(
            [item.evidence_strength for item in assessment.assessed_requirements],
            [
                EvidenceStrength.STRONG,
                EvidenceStrength.MODERATE,
                EvidenceStrength.WEAK,
                EvidenceStrength.NONE,
            ],
        )
        self.assertEqual(
            [item.status for item in assessment.assessed_requirements],
            ["demonstrated", "demonstrated", "demonstrated", "missing"],
        )

    def test_strongest_selected_evidence_determines_strength_without_averaging(self) -> None:
        assessment = self.engine.assess(
            _profile(("A", "required"), ("B", "preferred")),
            [
                _match("A", "demonstrated", 10, 80, 10),
                _match("B", "demonstrated", 75, 75),
            ],
        )

        self.assertEqual(
            [item.evidence_strength for item in assessment.assessed_requirements],
            [EvidenceStrength.STRONG, EvidenceStrength.STRONG],
        )

    def test_weak_evidence_does_not_change_coverage_or_grouping(self) -> None:
        profile = _profile(
            ("Required demonstrated", "required"),
            ("Required missing", "required"),
            ("Preferred demonstrated", "preferred"),
            ("Optional missing", "optional"),
        )
        assessment = self.engine.assess(
            profile,
            [
                _match("Optional missing", "missing"),
                _match("Preferred demonstrated", "demonstrated", 10),
                _match("Required missing", "missing"),
                _match("Required demonstrated", "demonstrated", 10),
            ],
        )

        self.assertEqual(assessment.overall_coverage_percentage, 50)
        self.assertEqual(assessment.required_coverage_percentage, 50)
        self.assertEqual(assessment.preferred_coverage_percentage, 100)
        self.assertEqual(assessment.optional_coverage_percentage, 0)
        self.assertEqual(assessment.critical_missing_skills, ["Required missing"])
        self.assertEqual(assessment.preferred_missing_skills, [])
        self.assertEqual(assessment.optional_missing_skills, ["Optional missing"])

    def test_assessment_preserves_order_inputs_and_is_deterministic(self) -> None:
        profile = _profile(("First", "required"), ("Second", "preferred"))
        matches = [
            _match("Second", "missing"),
            _match("First", "demonstrated", 50, 80),
        ]
        original_profile = profile.model_dump()
        original_matches = [match.model_dump() for match in matches]

        first = self.engine.assess(profile, matches)
        second = self.engine.assess(profile, matches)

        self.assertEqual(
            [item.name for item in first.assessed_requirements],
            ["First", "Second"],
        )
        self.assertEqual(first, second)
        self.assertEqual(profile.model_dump(), original_profile)
        self.assertEqual([match.model_dump() for match in matches], original_matches)

    def test_prompt_builder_serializes_evidence_aware_assessment(self) -> None:
        profile = _profile(("A", "required"))
        matches = [_match("A", "demonstrated", 80)]
        assessment = self.engine.assess(profile, matches)

        prompt = build_cv_analysis_prompt(
            PromptContext(
                template="Template",
                requirement_profile=profile,
                candidate_profile=CandidateProfile(),
                validated_skill_matches=matches,
                requirement_assessment=assessment,
            )
        )

        self.assertIn('"assessed_requirements"', prompt)
        self.assertIn('"evidence_strength": "strong"', prompt)


if __name__ == "__main__":
    unittest.main()
