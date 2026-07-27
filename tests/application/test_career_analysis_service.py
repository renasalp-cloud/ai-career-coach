import inspect
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

from app.ai.analyzer import AnalysisResult
from app.application import (
    AnalysisExecutionError,
    AnalysisRequest,
    AnalysisResponse,
    ApplicationService,
    CVProcessingError,
    CVSource,
    CareerAnalysisApplicationService,
    InvalidCVSourceError,
    RequirementProcessingError,
)
from app.candidate_profile.models import CandidateProfile
from app.models import CareerAnalysis, RequirementProfile
from app.requirements.source import RequirementSource, RequirementSourceType


def _career_analysis() -> CareerAnalysis:
    return CareerAnalysis(
        overall_match_score=75,
        professional_summary="Supported summary.",
        strengths=[],
        missing_skills={"critical": [], "important": [], "optional": []},
        career_gap_analysis="No material gaps.",
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


class CareerAnalysisApplicationServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.cv_path = Path(self.temporary_directory.name) / "candidate.pdf"
        self.cv_path.touch()
        self.requirement_source = RequirementSource(
            source_type=RequirementSourceType.PASTED_TEXT,
            content="Clear written communication",
        )
        self.request = AnalysisRequest(
            cv_source=CVSource(file_path=self.cv_path),
            requirement_source=self.requirement_source,
        )
        self.candidate_profile = CandidateProfile()
        self.requirement_profile = RequirementProfile(title="Target")
        self.analysis = _career_analysis()

    def _service(
        self,
        *,
        pdf_reader=None,
        text_cleaner=None,
        cv_parser=None,
        candidate_profile_extractor=None,
        candidate_profile_normalizer=None,
        requirement_pipeline=None,
        analyzer=None,
    ) -> CareerAnalysisApplicationService:
        pipeline = requirement_pipeline or Mock()
        if requirement_pipeline is None:
            pipeline.build.return_value = self.requirement_profile

        return CareerAnalysisApplicationService(
            pdf_reader=pdf_reader or Mock(return_value=" raw cv "),
            text_cleaner=text_cleaner or Mock(return_value="clean cv"),
            cv_parser=cv_parser or Mock(return_value={"skills": "Communication"}),
            candidate_profile_extractor=(
                candidate_profile_extractor
                or Mock(return_value=self.candidate_profile)
            ),
            candidate_profile_normalizer=(
                candidate_profile_normalizer
                or Mock(return_value=self.candidate_profile)
            ),
            requirement_pipeline=pipeline,
            analyzer=analyzer
            or Mock(
                return_value=AnalysisResult(
                    candidate_profile=self.candidate_profile,
                    analysis=self.analysis.model_dump(),
                )
            ),
        )

    def test_implements_application_service(self) -> None:
        self.assertTrue(
            issubclass(CareerAnalysisApplicationService, ApplicationService)
        )
        self.assertFalse(inspect.isabstract(CareerAnalysisApplicationService))

    def test_executes_collaborators_in_expected_order_and_wraps_result(self) -> None:
        calls: list[object] = []
        sections = {"skills": "Communication"}

        def read(path: str) -> str:
            calls.append(("read", path))
            return " raw cv "

        def clean(text: str) -> str:
            calls.append(("clean", text))
            return "clean cv"

        def parse(text: str) -> dict[str, str]:
            calls.append(("parse", text))
            return sections

        def extract(value: dict[str, str]) -> CandidateProfile:
            calls.append(("extract", value))
            return self.candidate_profile

        def normalize(value: CandidateProfile) -> CandidateProfile:
            calls.append(("normalize", value))
            return value

        pipeline = Mock()

        def build(source: RequirementSource) -> RequirementProfile:
            calls.append(("requirements", source))
            return self.requirement_profile

        pipeline.build.side_effect = build

        def analyze(
            text: str,
            profile: RequirementProfile,
            parsed_sections: dict[str, str] | None,
        ) -> AnalysisResult:
            calls.append(("analyze", text, profile, parsed_sections))
            return AnalysisResult(
                candidate_profile=self.candidate_profile,
                analysis=self.analysis.model_dump(),
            )

        response = self._service(
            pdf_reader=read,
            text_cleaner=clean,
            cv_parser=parse,
            candidate_profile_extractor=extract,
            candidate_profile_normalizer=normalize,
            requirement_pipeline=pipeline,
            analyzer=analyze,
        ).analyze(self.request)

        self.assertIsInstance(response, AnalysisResponse)
        self.assertIs(response.candidate_profile, self.candidate_profile)
        self.assertEqual(response.analysis, self.analysis)
        self.assertEqual(
            calls,
            [
                ("read", str(self.cv_path)),
                ("clean", " raw cv "),
                ("parse", "clean cv"),
                ("extract", sections),
                ("normalize", self.candidate_profile),
                ("requirements", self.requirement_source),
                (
                    "analyze",
                    "clean cv",
                    self.requirement_profile,
                    sections,
                ),
            ],
        )
        self.assertIs(calls[5][1], self.requirement_source)
        self.assertIs(calls[6][2], self.requirement_profile)

    def test_rejects_missing_directory_and_non_pdf_sources(self) -> None:
        directory = Path(self.temporary_directory.name)
        text_file = directory / "candidate.txt"
        text_file.touch()

        for path in (directory / "missing.pdf", directory, text_file):
            with self.subTest(path=path):
                request = self.request.model_copy(
                    update={"cv_source": CVSource(file_path=path)}
                )
                with self.assertRaisesRegex(
                    InvalidCVSourceError,
                    "Candidate CV must be an existing PDF file.",
                ):
                    self._service().analyze(request)

    def test_accepts_uppercase_pdf_suffix(self) -> None:
        uppercase_path = Path(self.temporary_directory.name) / "candidate.PDF"
        uppercase_path.touch()
        request = self.request.model_copy(
            update={"cv_source": CVSource(file_path=uppercase_path)}
        )

        response = self._service().analyze(request)

        self.assertEqual(response.analysis, self.analysis)

    def test_maps_each_cv_stage_failure_and_preserves_cause(self) -> None:
        stages = (
            "pdf_reader",
            "text_cleaner",
            "cv_parser",
            "candidate_profile_extractor",
            "candidate_profile_normalizer",
        )

        for stage in stages:
            with self.subTest(stage=stage):
                cause = RuntimeError(stage)
                failing_collaborator = Mock(side_effect=cause)
                with self.assertRaisesRegex(
                    CVProcessingError,
                    "Candidate CV could not be processed.",
                ) as raised:
                    self._service(
                        **{stage: failing_collaborator}
                    ).analyze(self.request)
                self.assertIs(raised.exception.__cause__, cause)

    def test_maps_requirement_pipeline_failure_and_preserves_cause(self) -> None:
        cause = RuntimeError("requirements")
        pipeline = Mock()
        pipeline.build.side_effect = cause

        with self.assertRaises(RequirementProcessingError) as raised:
            self._service(requirement_pipeline=pipeline).analyze(self.request)

        self.assertIs(raised.exception.__cause__, cause)

    def test_maps_analyzer_failure_and_preserves_cause(self) -> None:
        cause = RuntimeError("analysis")

        with self.assertRaises(AnalysisExecutionError) as raised:
            self._service(
                analyzer=Mock(side_effect=cause)
            ).analyze(self.request)

        self.assertIs(raised.exception.__cause__, cause)

    def test_uses_only_injected_analyzer(self) -> None:
        analyzer = Mock(
            return_value=AnalysisResult(
                candidate_profile=self.candidate_profile,
                analysis=self.analysis.model_dump(),
            )
        )

        self._service(analyzer=analyzer).analyze(self.request)

        analyzer.assert_called_once()


if __name__ == "__main__":
    unittest.main()
