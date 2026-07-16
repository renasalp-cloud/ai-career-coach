"""Deterministic, requirement-independent candidate evidence ranking."""

from app.evidence.models import ScoredCandidateEvidence


class EvidenceRanker:
    """Order and select scored evidence without changing the supplied items."""

    def rank(
        self, evidence: list[ScoredCandidateEvidence]
    ) -> list[ScoredCandidateEvidence]:
        """Return evidence ordered by descending score, preserving ties."""
        return sorted(evidence, key=lambda item: item.quality_score, reverse=True)

    def rank_by_skill(
        self, evidence: list[ScoredCandidateEvidence]
    ) -> dict[str, list[ScoredCandidateEvidence]]:
        """Group by normalized skill and rank evidence within each group."""
        grouped: dict[str, list[ScoredCandidateEvidence]] = {}
        for item in evidence:
            key = item.evidence.skill.strip().casefold()
            grouped.setdefault(key, []).append(item)

        return {key: self.rank(items) for key, items in grouped.items()}

    def select_top(
        self, evidence: list[ScoredCandidateEvidence], limit: int
    ) -> list[ScoredCandidateEvidence]:
        """Return at most ``limit`` items in ranked order."""
        if limit <= 0:
            raise ValueError("limit must be positive")
        return self.rank(evidence)[:limit]
