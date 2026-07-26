"""Domain models for candidate claims supported by deterministic data."""

from enum import Enum

from pydantic import BaseModel, Field, field_validator

from app.evidence.models import CandidateEvidence


class ClaimType(str, Enum):
    EDUCATION = "education"
    EXPERIENCE = "experience"
    PROJECT = "project"
    CERTIFICATION = "certification"
    LANGUAGE = "language"
    SKILL = "skill"


class ClaimSupportLevel(str, Enum):
    VERIFIED_FACT = "verified_fact"
    STRONG_EVIDENCE = "strong_evidence"
    MODERATE_EVIDENCE = "moderate_evidence"
    WEAK_EVIDENCE = "weak_evidence"
    DECLARED_ONLY = "declared_only"


class RestrictedClaimType(str, Enum):
    SENIORITY = "seniority"
    EXPERTISE_LEVEL = "expertise_level"
    LEADERSHIP = "leadership"
    YEARS_OF_EXPERIENCE = "years_of_experience"
    PRODUCTION_EXPERIENCE = "production_experience"
    RESEARCH_STATUS = "research_status"
    SCALE_OR_IMPACT = "scale_or_impact"


class AllowedClaim(BaseModel):
    claim_type: ClaimType
    claim_value: str
    support_level: ClaimSupportLevel
    supporting_evidence: list[CandidateEvidence] = Field(default_factory=list)

    @field_validator("claim_value")
    @classmethod
    def normalize_claim_value(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("claim_value must not be empty")
        return normalized


class AllowedClaims(BaseModel):
    factual_claims: list[AllowedClaim] = Field(default_factory=list)
    skill_claims: list[AllowedClaim] = Field(default_factory=list)
    restricted_claim_types: list[RestrictedClaimType] = Field(
        default_factory=lambda: list(RestrictedClaimType)
    )
