import unittest
from pathlib import Path

from pydantic import ValidationError

from app.application import AnalysisRequest, AnalysisResponse, CVSource
from app.candidate_profile.models import CandidateProfile
from app.models import CareerAnalysis
from app.requirements.source import RequirementSource, RequirementSourceType


def _requirement_source() -> RequirementSource:
    return RequirementSource(
        source_type=RequirementSourceType.PASTED_TEXT,
        content="Clear written communication",
    )


def _career_analysis() -> CareerAnalysis:
    return CareerAnalysis(
        overall_match_score=75,
        professional_summary="The candidate demonstrates relevant experience.",
        strengths=[],
        missing_skills={"critical": [], "important": [], "optional": []},
        career_gap_analysis="No material gaps were identified.",
        recommendations=[],
        learning_roadmap=[
            {
                "week": week,
                "goal": "",
                "topics": [],
                "practical_task": "",
                "expected_outcome": "",
            }
            for week in range(1, 5)
        ],
    )


class CVSourceTest(unittest.TestCase):
    def test_accepts_path(self) -> None:
        file_path = Path("candidate.pdf")

        source = CVSource(file_path=file_path)

        self.assertEqual(source.file_path, file_path)

    def test_converts_path_string_to_path(self) -> None:
        source = CVSource(file_path="candidate.pdf")

        self.assertEqual(source.file_path, Path("candidate.pdf"))
        self.assertIsInstance(source.file_path, Path)

    def test_does_not_require_path_to_exist(self) -> None:
        source = CVSource(file_path=Path("missing/candidate.unsupported"))

        self.assertEqual(source.file_path, Path("missing/candidate.unsupported"))

    def test_is_immutable(self) -> None:
        source = CVSource(file_path=Path("candidate.pdf"))

        with self.assertRaises(ValidationError):
            source.file_path = Path("other.pdf")


class AnalysisRequestTest(unittest.TestCase):
    def test_accepts_existing_requirement_source(self) -> None:
        requirement_source = _requirement_source()

        request = AnalysisRequest(
            cv_source=CVSource(file_path="candidate.pdf"),
            requirement_source=requirement_source,
        )

        self.assertIs(request.requirement_source, requirement_source)

    def test_target_role_defaults_to_none(self) -> None:
        request = AnalysisRequest(
            cv_source=CVSource(file_path="candidate.pdf"),
            requirement_source=_requirement_source(),
        )

        self.assertIsNone(request.target_role)

    def test_target_role_is_trimmed(self) -> None:
        request = AnalysisRequest(
            cv_source=CVSource(file_path="candidate.pdf"),
            requirement_source=_requirement_source(),
            target_role="  Operations Manager  ",
        )

        self.assertEqual(request.target_role, "Operations Manager")

    def test_empty_target_role_is_rejected(self) -> None:
        for target_role in ("", " \n\t "):
            with self.subTest(target_role=target_role):
                with self.assertRaises(ValidationError):
                    AnalysisRequest(
                        cv_source=CVSource(file_path="candidate.pdf"),
                        requirement_source=_requirement_source(),
                        target_role=target_role,
                    )

    def test_is_immutable(self) -> None:
        request = AnalysisRequest(
            cv_source=CVSource(file_path="candidate.pdf"),
            requirement_source=_requirement_source(),
        )

        with self.assertRaises(ValidationError):
            request.target_role = "Other Role"


class AnalysisResponseTest(unittest.TestCase):
    def test_accepts_existing_career_analysis(self) -> None:
        analysis = _career_analysis()

        candidate_profile = CandidateProfile()
        response = AnalysisResponse(
            candidate_profile=candidate_profile,
            analysis=analysis,
        )

        self.assertIs(response.candidate_profile, candidate_profile)
        self.assertIs(response.analysis, analysis)

    def test_is_immutable(self) -> None:
        response = AnalysisResponse(
            candidate_profile=CandidateProfile(),
            analysis=_career_analysis(),
        )

        with self.assertRaises(ValidationError):
            response.analysis = _career_analysis()
        with self.assertRaises(ValidationError):
            response.candidate_profile = CandidateProfile()


if __name__ == "__main__":
    unittest.main()
