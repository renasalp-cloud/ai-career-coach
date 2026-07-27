"""Application composition root."""

from app.ai.analyzer import analyze_cv
from app.application import ApplicationService, CareerAnalysisApplicationService
from app.candidate_profile.extractor import extract_candidate_profile
from app.candidate_profile.normalizer import normalize_candidate_profile
from app.cv_parser import parse_cv
from app.pdf_reader import clean_text, extract_text
from app.requirements.pipeline import RequirementPipeline


def create_application_service() -> ApplicationService:
    """Construct the concrete career-analysis application service."""
    return CareerAnalysisApplicationService(
        pdf_reader=extract_text,
        text_cleaner=clean_text,
        cv_parser=parse_cv,
        candidate_profile_extractor=extract_candidate_profile,
        candidate_profile_normalizer=normalize_candidate_profile,
        requirement_pipeline=RequirementPipeline(),
        analyzer=analyze_cv,
    )
