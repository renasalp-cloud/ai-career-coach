"""Summarize validated requirement matches deterministically."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.models import RequirementProfile, SkillMatch


class RequirementAssessmentError(ValueError):
    """Raised when requirements and validated matches are inconsistent."""


class EvidenceStrength(str, Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NONE = "none"


EVIDENCE_STRENGTH_THRESHOLDS = (
    (75, EvidenceStrength.STRONG),
    (50, EvidenceStrength.MODERATE),
    (1, EvidenceStrength.WEAK),
)


class AssessedRequirement(BaseModel):
    name: str
    status: Literal["demonstrated", "missing"]
    evidence_strength: EvidenceStrength


class RequirementAssessment(BaseModel):
    """Deterministic coverage and gap facts for a requirement profile."""

    total_requirements: int
    demonstrated_requirements: int
    missing_requirements: int
    overall_coverage_percentage: int
    required_total: int
    required_demonstrated: int
    required_coverage_percentage: int
    preferred_total: int
    preferred_demonstrated: int
    preferred_coverage_percentage: int
    optional_total: int
    optional_demonstrated: int
    optional_coverage_percentage: int
    assessed_requirements: list[AssessedRequirement] = Field(default_factory=list)
    demonstrated_skills: list[str] = Field(default_factory=list)
    critical_missing_skills: list[str] = Field(default_factory=list)
    preferred_missing_skills: list[str] = Field(default_factory=list)
    optional_missing_skills: list[str] = Field(default_factory=list)


class RequirementAssessmentEngine:
    """Build an assessment from profile priorities and validated statuses."""

    _SUPPORTED_STATUSES = {"demonstrated", "missing"}

    @staticmethod
    def _percentage(demonstrated: int, total: int) -> int:
        return int(demonstrated / total * 100 + 0.5) if total else 0

    @staticmethod
    def _append_unique(values: list[str], value: str) -> None:
        if value not in values:
            values.append(value)

    @staticmethod
    def _evidence_strength(match: SkillMatch) -> EvidenceStrength:
        if match.status == "missing":
            return EvidenceStrength.NONE

        scores = [
            evidence.quality_score
            for evidence in match.evidence
            if evidence.quality_score is not None
        ]
        if not scores:
            return EvidenceStrength.NONE

        strongest_score = max(scores)
        for minimum_score, strength in EVIDENCE_STRENGTH_THRESHOLDS:
            if strongest_score >= minimum_score:
                return strength
        return EvidenceStrength.NONE

    def assess(
        self,
        requirement_profile: RequirementProfile,
        validated_skill_matches: list[SkillMatch],
    ) -> RequirementAssessment:
        requirements_by_name = {
            requirement.name: requirement for requirement in requirement_profile.skills
        }
        matches_by_name: dict[str, SkillMatch] = {}

        for match in validated_skill_matches:
            if match.role_skill not in requirements_by_name:
                raise RequirementAssessmentError(
                    f"Validated match refers to unknown requirement: {match.role_skill!r}."
                )
            if match.role_skill in matches_by_name:
                raise RequirementAssessmentError(
                    f"Multiple validated matches for requirement: {match.role_skill!r}."
                )
            if match.status not in self._SUPPORTED_STATUSES:
                raise RequirementAssessmentError(
                    f"Unsupported validated match status for {match.role_skill!r}: "
                    f"{match.status!r}."
                )
            matches_by_name[match.role_skill] = match

        for requirement in requirement_profile.skills:
            if requirement.name not in matches_by_name:
                raise RequirementAssessmentError(
                    f"Requirement has no validated match: {requirement.name!r}."
                )

        totals = {"required": 0, "preferred": 0, "optional": 0}
        demonstrated = {"required": 0, "preferred": 0, "optional": 0}
        demonstrated_skills: list[str] = []
        missing = {"required": [], "preferred": [], "optional": []}
        assessed_requirements: list[AssessedRequirement] = []

        for requirement in requirement_profile.skills:
            totals[requirement.priority] += 1
            match = matches_by_name[requirement.name]
            assessed_requirements.append(
                AssessedRequirement(
                    name=requirement.name,
                    status=match.status,
                    evidence_strength=self._evidence_strength(match),
                )
            )
            if match.status == "demonstrated":
                demonstrated[requirement.priority] += 1
                self._append_unique(demonstrated_skills, requirement.name)
            else:
                self._append_unique(missing[requirement.priority], requirement.name)

        total = len(requirement_profile.skills)
        demonstrated_total = sum(demonstrated.values())
        missing_total = total - demonstrated_total

        return RequirementAssessment(
            total_requirements=total,
            demonstrated_requirements=demonstrated_total,
            missing_requirements=missing_total,
            overall_coverage_percentage=self._percentage(demonstrated_total, total),
            required_total=totals["required"],
            required_demonstrated=demonstrated["required"],
            required_coverage_percentage=self._percentage(
                demonstrated["required"], totals["required"]
            ),
            preferred_total=totals["preferred"],
            preferred_demonstrated=demonstrated["preferred"],
            preferred_coverage_percentage=self._percentage(
                demonstrated["preferred"], totals["preferred"]
            ),
            optional_total=totals["optional"],
            optional_demonstrated=demonstrated["optional"],
            optional_coverage_percentage=self._percentage(
                demonstrated["optional"], totals["optional"]
            ),
            assessed_requirements=assessed_requirements,
            demonstrated_skills=demonstrated_skills,
            critical_missing_skills=missing["required"],
            preferred_missing_skills=missing["preferred"],
            optional_missing_skills=missing["optional"],
        )
