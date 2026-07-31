import unittest

from app.ai.analyzer import assess_candidate_requirements
from app.candidate_profile.extractor import extract_candidate_profile
from app.candidate_profile.models import (
    CandidateProfile,
    EducationEntry,
    ExperienceEntry,
    SkillEntry,
)
from app.models import RequirementProfile, RequirementSkill
from app.cv_parser import parse_cv
from app.semantic.matcher import SkillMatcher


def _requirements(name: str) -> RequirementProfile:
    return RequirementProfile(
        skills=[RequirementSkill(name=name, priority="required")]
    )


def _education_requirement(name: str) -> RequirementProfile:
    return RequirementProfile(
        skills=[
            RequirementSkill(
                name=name,
                priority="required",
                category="education",
            )
        ]
    )


class RequirementMatchingIntegrationTest(unittest.TestCase):
    def assert_not_missing(
        self, candidate: CandidateProfile, requirement: str
    ) -> None:
        result = assess_candidate_requirements(candidate, _requirements(requirement))

        self.assertNotEqual(
            result.requirement_assessment.assessed_requirements[0].status,
            "missing",
        )

    def test_abbreviation_flows_through_public_assessment(self) -> None:
        self.assert_not_missing(
            CandidateProfile(skills=[SkillEntry(name="MS Office")]),
            "Experience working with Microsoft Office",
        )

    def test_experience_report_evidence_flows_through_public_assessment(self) -> None:
        self.assert_not_missing(
            CandidateProfile(
                experience=[ExperienceEntry(highlights=["Report preparation"])]
            ),
            "Experience preparing reports and documentation",
        )

    def test_problem_solving_flows_through_public_assessment(self) -> None:
        self.assert_not_missing(
            CandidateProfile(skills=[SkillEntry(name="Problem solving")]),
            "Strong analytical and problem-solving skills",
        )

    def test_work_coordination_flows_through_public_assessment(self) -> None:
        self.assert_not_missing(
            CandidateProfile(
                experience=[
                    ExperienceEntry(
                        highlights=[
                            "Organizing work processes and setting priorities"
                        ]
                    )
                ]
            ),
            "Experience coordinating tasks or work processes",
        )

    def test_related_product_remains_missing(self) -> None:
        result = assess_candidate_requirements(
            CandidateProfile(skills=[SkillEntry(name="MS Office")]),
            _requirements("Microsoft Project"),
        )

        self.assertEqual(
            result.requirement_assessment.assessed_requirements[0].status,
            "missing",
        )

    def test_descriptive_sections_flow_through_public_assessment(self) -> None:
        candidate = extract_candidate_profile(parse_cv(
            "Skills and Strengths\n"
            "Organizing work processes and setting priorities\n"
            "Planning and organizing own work\n"
            "Good communication skills\nCommunicating with patients"
        ))

        for requirement in (
            "Strong organizational and time management skills",
            "Ability to prioritize multiple responsibilities",
            "Excellent communication and interpersonal skills",
        ):
            with self.subTest(requirement=requirement):
                self.assert_not_missing(candidate, requirement)

    def test_descriptive_soft_skills_do_not_match_unrelated_requirements(self) -> None:
        candidate = CandidateProfile(
            summary="Good communication and organizational skills"
        )

        for requirement in (
            "Risk management experience",
            "Agile project management",
            "Microsoft Project",
        ):
            with self.subTest(requirement=requirement):
                result = assess_candidate_requirements(candidate, _requirements(requirement))
                self.assertEqual(
                    result.requirement_assessment.assessed_requirements[0].status,
                    "missing",
                )

    def test_public_assessment_calls_injected_matcher_and_uses_its_result(self) -> None:
        class RecordingMatcher(SkillMatcher):
            called = False

            def match(self, candidate, requirements):
                self.called = True
                return super().match(candidate, requirements)

        matcher = RecordingMatcher()
        result = assess_candidate_requirements(
            CandidateProfile(skills=[SkillEntry(name="MS Office")]),
            _requirements("Experience working with Microsoft Office"),
            skill_matcher=matcher,
        )

        self.assertTrue(matcher.called)
        self.assertEqual(result.validated_skill_matches[0].status, "demonstrated")
        self.assertEqual(result.requirement_assessment.missing_requirements, 0)

    def test_completed_relevant_degree_is_demonstrated(self) -> None:
        result = assess_candidate_requirements(
            CandidateProfile(
                education=[
                    EducationEntry(
                        degree="Bachelor of Computer Systems",
                        status="completed",
                    )
                ]
            ),
            _education_requirement(
                "Bachelor's degree in Computer Science or a related field"
            ),
        )

        self.assertEqual(result.validated_skill_matches[0].status, "demonstrated")
        self.assertEqual(
            result.requirement_assessment.assessed_requirements[0].status,
            "demonstrated",
        )
        self.assertEqual(result.requirement_assessment.demonstrated_requirements, 1)
        self.assertEqual(result.requirement_assessment.missing_requirements, 0)

    def test_in_progress_relevant_degree_is_partial_and_not_missing(self) -> None:
        requirement = (
            "Bachelor's degree in Business, Management, Marketing, or a related field"
        )
        result = assess_candidate_requirements(
            CandidateProfile(
                education=[
                    EducationEntry(
                        degree="Bachelor's Degree in Marketing",
                        start_date="2025",
                        end_date="Present",
                    )
                ]
            ),
            _education_requirement(requirement),
        )

        self.assertEqual(result.validated_skill_matches[0].status, "partial")
        self.assertEqual(
            result.requirement_assessment.assessed_requirements[0].status,
            "partial",
        )
        self.assertEqual(result.requirement_assessment.missing_requirements, 0)
        self.assertNotIn(
            requirement,
            result.requirement_assessment.critical_missing_skills,
        )

    def test_parsed_in_progress_degree_is_partial_and_not_missing(self) -> None:
        candidate = extract_candidate_profile(parse_cv(
            "Education\n2025 – Present\n"
            "Economics and Culture University – Bachelor's Degree in Marketing\n"
            "2023 – 2024\nSecondary School"
        ))
        result = assess_candidate_requirements(
            candidate,
            _education_requirement(
                "Bachelor's degree in Business, Management, Marketing, or a related field"
            ),
        )

        self.assertEqual(result.validated_skill_matches[0].status, "partial")
        self.assertEqual(result.requirement_assessment.missing_requirements, 0)

    def test_active_degree_marker_variants_are_partial(self) -> None:
        for end_date in ("Present", "Current", "In Progress", "Expected 2027"):
            with self.subTest(end_date=end_date):
                result = assess_candidate_requirements(
                    CandidateProfile(
                        education=[
                            EducationEntry(
                                degree="Bachelor's Degree in Marketing",
                                end_date=end_date,
                            )
                        ]
                    ),
                    _education_requirement("Bachelor's degree in Marketing"),
                )

                self.assertEqual(result.validated_skill_matches[0].status, "partial")

    def test_historical_end_date_without_status_is_completed(self) -> None:
        result = assess_candidate_requirements(
            CandidateProfile(
                education=[
                    EducationEntry(
                        degree="Bachelor of Information Technology",
                        start_date="2021",
                        end_date="2025",
                    )
                ]
            ),
            _education_requirement("Bachelor's degree in Information Technology"),
        )

        self.assertEqual(result.validated_skill_matches[0].status, "demonstrated")

    def test_non_degree_education_does_not_satisfy_degree_requirement(self) -> None:
        for degree in ("Secondary School", "AI Engineering Bootcamp"):
            with self.subTest(degree=degree):
                result = assess_candidate_requirements(
                    CandidateProfile(
                        education=[EducationEntry(degree=degree, status="completed")]
                    ),
                    _education_requirement("Bachelor's degree in Computer Science"),
                )

                self.assertEqual(result.validated_skill_matches[0].status, "missing")

    def test_unrelated_degree_does_not_match_only_on_degree_level(self) -> None:
        result = assess_candidate_requirements(
            CandidateProfile(
                education=[
                    EducationEntry(
                        degree="Bachelor's degree in Fine Arts",
                        status="completed",
                    )
                ]
            ),
            _education_requirement(
                "Bachelor's degree in Computer Science or Software Engineering"
            ),
        )

        self.assertEqual(result.validated_skill_matches[0].status, "missing")

    def test_incomplete_relevant_degree_remains_missing(self) -> None:
        result = assess_candidate_requirements(
            CandidateProfile(
                education=[
                    EducationEntry(
                        degree="Bachelor's degree in Marketing",
                        status="abandoned",
                        end_date="2025",
                    )
                ]
            ),
            _education_requirement("Degree in Marketing"),
        )

        self.assertEqual(result.validated_skill_matches[0].status, "missing")


if __name__ == "__main__":
    unittest.main()
