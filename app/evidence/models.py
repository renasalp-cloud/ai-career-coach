"""Provider-independent models for deterministic candidate evidence."""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class EvidenceSourceType(str, Enum):
    WORK_EXPERIENCE = "work_experience"
    PROJECT = "project"
    EDUCATION = "education"
    CERTIFICATION = "certification"
    SKILLS_SECTION = "skills_section"
    SUMMARY = "summary"
    OTHER = "other"


class CandidateEvidence(BaseModel):
    # ``skill`` temporarily contains the available deterministic evidence text
    # where the collector has no separately extracted concept.
    skill: str
    source_type: EvidenceSourceType
    source_text: str
    source_label: str

    @field_validator("skill", "source_text")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be empty")
        return normalized

    @field_validator("source_label")
    @classmethod
    def normalize_label(cls, value: str) -> str:
        return value.strip()


class ScoredCandidateEvidence(BaseModel):
    evidence: CandidateEvidence
    quality_score: int = Field(ge=0, le=100)
    quality_factors: list[str] = Field(min_length=1)
