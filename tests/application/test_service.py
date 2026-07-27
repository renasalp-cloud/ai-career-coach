import ast
import inspect
import unittest
from pathlib import Path

from app.application import (
    AnalysisRequest,
    AnalysisResponse,
    ApplicationService,
    CVSource,
)
from app.candidate_profile.models import CandidateProfile
from app.models import CareerAnalysis
from app.requirements.source import RequirementSource, RequirementSourceType


def _analysis_request() -> AnalysisRequest:
    return AnalysisRequest(
        cv_source=CVSource(file_path=Path("candidate.pdf")),
        requirement_source=RequirementSource(
            source_type=RequirementSourceType.PASTED_TEXT,
            content="Clear written communication",
        ),
    )


def _analysis_response() -> AnalysisResponse:
    return AnalysisResponse(
        candidate_profile=CandidateProfile(),
        analysis=CareerAnalysis(
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
    )


class StubApplicationService(ApplicationService):
    def __init__(self, response: AnalysisResponse) -> None:
        self.request: AnalysisRequest | None = None
        self.response = response

    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        self.request = request
        return self.response


class ApplicationServiceTest(unittest.TestCase):
    def test_is_abstract(self) -> None:
        self.assertTrue(inspect.isabstract(ApplicationService))
        self.assertIn("analyze", ApplicationService.__abstractmethods__)

    def test_cannot_be_instantiated_directly(self) -> None:
        with self.assertRaises(TypeError):
            ApplicationService()

    def test_minimal_implementation_accepts_request_and_returns_response(self) -> None:
        request = _analysis_request()
        response = _analysis_response()
        service = StubApplicationService(response)

        result = service.analyze(request)

        self.assertIs(service.request, request)
        self.assertIs(result, response)

    def test_contract_has_only_application_boundary_dependencies(self) -> None:
        service_path = Path(inspect.getfile(ApplicationService))
        module = ast.parse(service_path.read_text(encoding="utf-8"))
        imported_modules = {
            node.module
            for node in ast.walk(module)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }

        self.assertEqual(
            imported_modules,
            {"abc", "app.application.models"},
        )


if __name__ == "__main__":
    unittest.main()
