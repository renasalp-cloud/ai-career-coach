"""Models defining the provider-independent application boundary."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator

from app.candidate_profile.models import CandidateProfile
from app.models import CareerAnalysis
from app.requirements.source import RequirementSource


class CVSource(BaseModel):
    """Location of a candidate CV supplied for analysis."""

    model_config = ConfigDict(frozen=True)

    file_path: Path


class AnalysisRequest(BaseModel):
    """Inputs required to request a career analysis."""

    model_config = ConfigDict(frozen=True)

    cv_source: CVSource
    requirement_source: RequirementSource
    target_role: str | None = None

    @field_validator("target_role")
    @classmethod
    def normalize_target_role(cls, target_role: str | None) -> str | None:
        if target_role is None:
            return None

        normalized = target_role.strip()
        if not normalized:
            raise ValueError("target_role must not be empty")
        return normalized


class AnalysisResponse(BaseModel):
    """Validated result returned by the application boundary."""

    model_config = ConfigDict(frozen=True)

    candidate_profile: CandidateProfile
    analysis: CareerAnalysis
