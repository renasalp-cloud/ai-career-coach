"""Deterministic, requirement-independent candidate evidence quality scoring."""

import re

from app.evidence.models import CandidateEvidence, EvidenceSourceType, ScoredCandidateEvidence


class EvidenceQualityScorer:
    """Score evidence using explicit, conservative, profession-agnostic rules."""

    SOURCE_SCORES = {
        EvidenceSourceType.WORK_EXPERIENCE: 45,
        EvidenceSourceType.PROJECT: 40,
        EvidenceSourceType.CERTIFICATION: 35,
        EvidenceSourceType.EDUCATION: 30,
        EvidenceSourceType.SUMMARY: 20,
        EvidenceSourceType.SKILLS_SECTION: 15,
        EvidenceSourceType.OTHER: 10,
    }
    ACTION_SIGNALS = frozenset({
        "built", "created", "developed", "implemented", "designed", "trained",
        "evaluated", "deployed", "managed", "configured", "analyzed", "optimized",
        "supported", "completed",
    })
    OUTCOME_SIGNALS = frozenset(
        {"achieved", "improved", "increased", "reduced", "saved", "delivered"}
    )
    GENERIC_LABELS = frozenset(
        {"work experience", "project", "certification", "education"}
    )
    CONTEXTUAL_SOURCE_TYPES = frozenset(
        {EvidenceSourceType.WORK_EXPERIENCE, EvidenceSourceType.EDUCATION}
    )

    def score(self, evidence: CandidateEvidence) -> ScoredCandidateEvidence:
        source_score = self.SOURCE_SCORES[evidence.source_type]
        score = source_score
        factors = [f"source strength ({evidence.source_type.value}): +{source_score}"]
        words = set(re.findall(r"[a-z]+", evidence.source_text.casefold()))

        if words & self.ACTION_SIGNALS:
            score += 20
            factors.append("demonstrated action: +20")

        if words & self.OUTCOME_SIGNALS or re.search(r"\b\d+(?:\.\d+)?%\b", evidence.source_text):
            score += 15
            factors.append("concrete outcome: +15")

        label = evidence.source_label.casefold()
        if (
            evidence.source_type in self.CONTEXTUAL_SOURCE_TYPES
            and label
            and label not in self.GENERIC_LABELS
        ):
            score += 10
            factors.append("specific source context: +10")

        return ScoredCandidateEvidence(
            evidence=evidence.model_copy(deep=True),
            quality_score=min(score, 100),
            quality_factors=factors,
        )

    def score_all(self, evidence: list[CandidateEvidence]) -> list[ScoredCandidateEvidence]:
        return [self.score(item) for item in evidence]
