"""Concrete orchestration for the career-analysis application boundary."""

from collections.abc import Callable
from pathlib import Path

from app.ai.analyzer import AnalysisResult
from app.analysis.output_normalizer import normalize_final_career_analysis_output
from app.application.exceptions import (
    AnalysisExecutionError,
    ApplicationError,
    CVProcessingError,
    InvalidCVSourceError,
    RequirementProcessingError,
)
from app.application.models import AnalysisRequest, AnalysisResponse
from app.application.service import ApplicationService
from app.candidate_profile.models import CandidateProfile
from app.models import CareerAnalysis, RequirementProfile
from app.requirements.pipeline import RequirementPipeline


PDFReader = Callable[[str], str]
TextCleaner = Callable[[str], str]
CVParser = Callable[[str], dict[str, str]]
CandidateProfileExtractor = Callable[[dict[str, str]], CandidateProfile]
CandidateProfileNormalizer = Callable[[CandidateProfile], CandidateProfile]
Analyzer = Callable[
    [str, RequirementProfile, dict[str, str] | None, CandidateProfile],
    AnalysisResult,
]


class CareerAnalysisApplicationService(ApplicationService):
    """Coordinate existing pipelines without owning their business logic."""

    def __init__(
        self,
        pdf_reader: PDFReader,
        text_cleaner: TextCleaner,
        cv_parser: CVParser,
        candidate_profile_extractor: CandidateProfileExtractor,
        candidate_profile_normalizer: CandidateProfileNormalizer,
        requirement_pipeline: RequirementPipeline,
        analyzer: Analyzer,
    ) -> None:
        self._pdf_reader = pdf_reader
        self._text_cleaner = text_cleaner
        self._cv_parser = cv_parser
        self._candidate_profile_extractor = candidate_profile_extractor
        self._candidate_profile_normalizer = candidate_profile_normalizer
        self._requirement_pipeline = requirement_pipeline
        self._analyzer = analyzer

    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        """Execute the existing CV, requirement, and analysis pipelines."""
        cv_path = request.cv_source.file_path
        self._validate_cv_source(cv_path)

        try:
            cv_text = self._pdf_reader(str(cv_path))
            cleaned_cv_text = self._text_cleaner(cv_text)
            cv_sections = self._cv_parser(cleaned_cv_text)
            candidate_profile = self._candidate_profile_extractor(cv_sections)
            candidate_profile = self._candidate_profile_normalizer(candidate_profile)
        except ApplicationError:
            raise
        except Exception as exc:
            raise CVProcessingError(
                "Candidate CV could not be processed."
            ) from exc

        try:
            requirement_profile = self._requirement_pipeline.build(
                request.requirement_source
            )
        except ApplicationError:
            raise
        except Exception as exc:
            raise RequirementProcessingError(
                "Candidate requirements could not be processed."
            ) from exc

        try:
            result = self._analyzer(
                cleaned_cv_text,
                requirement_profile,
                cv_sections,
                candidate_profile,
            )
            final_analysis = normalize_final_career_analysis_output(
                result.analysis,
                result.candidate_profile.summary,
            )
            analysis = CareerAnalysis.model_validate(final_analysis)
        except ApplicationError:
            raise
        except Exception as exc:
            raise AnalysisExecutionError(
                "Career analysis could not be completed."
            ) from exc

        return AnalysisResponse(
            candidate_profile=result.candidate_profile,
            analysis=analysis,
        )

    @staticmethod
    def _validate_cv_source(cv_path: Path) -> None:
        if (
            not cv_path.exists()
            or not cv_path.is_file()
            or cv_path.suffix.lower() != ".pdf"
        ):
            raise InvalidCVSourceError(
                "Candidate CV must be an existing PDF file."
            )
