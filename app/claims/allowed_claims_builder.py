"""Build allowed candidate claims without inference or LLM involvement."""

from collections.abc import Iterable

from app.assessment.requirement_assessment import EvidenceStrength, RequirementAssessment
from app.candidate_profile.models import CandidateProfile, EducationEntry, ExperienceEntry
from app.claims.models import (
    AllowedClaim,
    AllowedClaims,
    ClaimSupportLevel,
    ClaimType,
)
from app.evidence.models import (
    CandidateEvidence,
    EvidenceSourceType,
    ScoredCandidateEvidence,
)
from app.models import SkillMatch


_SUPPORT_BY_STRENGTH = {
    EvidenceStrength.STRONG: ClaimSupportLevel.STRONG_EVIDENCE,
    EvidenceStrength.MODERATE: ClaimSupportLevel.MODERATE_EVIDENCE,
    EvidenceStrength.WEAK: ClaimSupportLevel.WEAK_EVIDENCE,
}

_LEGACY_EVIDENCE_SOURCES = {
    EvidenceSourceType.WORK_EXPERIENCE: "experience",
    EvidenceSourceType.PROJECT: "projects",
    EvidenceSourceType.EDUCATION: "education",
    EvidenceSourceType.CERTIFICATION: "certification",
    EvidenceSourceType.SKILLS_SECTION: "skills",
    EvidenceSourceType.SUMMARY: "summary",
    EvidenceSourceType.OTHER: "other",
}


def _joined(parts: Iterable[str], separator: str = " | ") -> str:
    return separator.join(part.strip() for part in parts if part.strip())


def _normalized(value: str) -> str:
    return " ".join(value.split()).casefold()


def _education_value(entry: EducationEntry) -> str:
    if not any(
        part.strip()
        for part in (entry.degree, entry.institution, entry.start_date, entry.end_date)
    ):
        return ""
    return _joined(
        (entry.degree, entry.institution, entry.start_date, entry.end_date, entry.status)
    )


def _experience_value(entry: ExperienceEntry) -> str:
    return _joined(
        (
            entry.title,
            entry.organization,
            entry.start_date,
            entry.end_date,
            entry.location,
            *entry.highlights,
        )
    )


class AllowedClaimsBuilder:
    """Construct only claims directly supported by supplied domain inputs."""

    @staticmethod
    def _append_unique(
        claims: list[AllowedClaim],
        seen: set[tuple[ClaimType, str]],
        claim: AllowedClaim,
    ) -> None:
        identity = (claim.claim_type, claim.claim_value.casefold())
        if identity not in seen:
            seen.add(identity)
            claims.append(claim)

    @staticmethod
    def _factual_claim(
        claim_type: ClaimType,
        value: str,
        source_type: EvidenceSourceType,
        source_label: str,
    ) -> AllowedClaim | None:
        value = value.strip()
        if not value:
            return None
        evidence = CandidateEvidence(
            skill=value,
            source_type=source_type,
            source_text=value,
            source_label=source_label,
        )
        return AllowedClaim(
            claim_type=claim_type,
            claim_value=value,
            support_level=ClaimSupportLevel.VERIFIED_FACT,
            supporting_evidence=[evidence],
        )

    def _build_factual_claims(self, profile: CandidateProfile) -> list[AllowedClaim]:
        claims: list[AllowedClaim] = []
        seen: set[tuple[ClaimType, str]] = set()

        sources = (
            (
                ClaimType.EDUCATION,
                ((_education_value(item), EvidenceSourceType.EDUCATION, "Education") for item in profile.education),
            ),
            (
                ClaimType.EXPERIENCE,
                ((_experience_value(item), EvidenceSourceType.WORK_EXPERIENCE, "Work experience") for item in profile.experience),
            ),
            (
                ClaimType.PROJECT,
                ((item, EvidenceSourceType.PROJECT, "Project") for item in profile.projects),
            ),
            (
                ClaimType.CERTIFICATION,
                ((item, EvidenceSourceType.CERTIFICATION, "Certification") for item in profile.certifications),
            ),
            (
                ClaimType.LANGUAGE,
                ((item, EvidenceSourceType.OTHER, "Languages section") for item in profile.languages),
            ),
        )
        for claim_type, values in sources:
            for value, source_type, label in values:
                claim = self._factual_claim(claim_type, value, source_type, label)
                if claim is not None:
                    self._append_unique(claims, seen, claim)
        return claims

    @staticmethod
    def _structured_support(
        match: SkillMatch,
        ranked_evidence: list[ScoredCandidateEvidence],
    ) -> list[CandidateEvidence]:
        selected = {
            (_normalized(item.source), _normalized(item.text), item.quality_score)
            for item in match.evidence
        }
        support: list[CandidateEvidence] = []
        seen: set[tuple[EvidenceSourceType, str, str]] = set()
        for item in ranked_evidence:
            evidence = item.evidence
            source_names = {
                _normalized(evidence.source_type.value),
                _normalized(evidence.source_label),
                _normalized(_LEGACY_EVIDENCE_SOURCES[evidence.source_type]),
            }
            if not any(
                (source, _normalized(evidence.source_text), item.quality_score)
                in selected
                for source in source_names
            ):
                continue
            identity = (
                evidence.source_type,
                _normalized(evidence.source_text),
                _normalized(evidence.source_label),
            )
            if identity not in seen:
                seen.add(identity)
                support.append(evidence.model_copy(deep=True))
        return support

    def _build_skill_claims(
        self,
        ranked_evidence: list[ScoredCandidateEvidence],
        validated_skill_matches: list[SkillMatch],
        requirement_assessment: RequirementAssessment,
    ) -> list[AllowedClaim]:
        matches: dict[str, SkillMatch] = {}
        for match in validated_skill_matches:
            if match.status == "demonstrated":
                matches.setdefault(_normalized(match.role_skill), match)
        claims: list[AllowedClaim] = []
        seen: set[tuple[ClaimType, str]] = set()

        for assessed in requirement_assessment.assessed_requirements:
            if assessed.status != "demonstrated":
                continue
            match = matches.get(_normalized(assessed.name))
            if match is None:
                continue
            support = self._structured_support(match, ranked_evidence)
            declared_only = bool(support) and all(
                evidence.source_type == EvidenceSourceType.SKILLS_SECTION
                for evidence in support
            )
            if declared_only:
                support_level = ClaimSupportLevel.DECLARED_ONLY
            else:
                support_level = _SUPPORT_BY_STRENGTH.get(assessed.evidence_strength)
            if support_level is None:
                continue
            claim = AllowedClaim(
                claim_type=ClaimType.SKILL,
                claim_value=assessed.name,
                support_level=support_level,
                supporting_evidence=support,
            )
            self._append_unique(claims, seen, claim)
        return claims

    def build(
        self,
        candidate_profile: CandidateProfile,
        ranked_candidate_evidence: list[ScoredCandidateEvidence],
        validated_skill_matches: list[SkillMatch],
        requirement_assessment: RequirementAssessment,
    ) -> AllowedClaims:
        return AllowedClaims(
            factual_claims=self._build_factual_claims(candidate_profile),
            skill_claims=self._build_skill_claims(
                ranked_candidate_evidence,
                validated_skill_matches,
                requirement_assessment,
            ),
        )
