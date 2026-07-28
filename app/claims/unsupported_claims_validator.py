"""Deterministically remove unsupported positive claims from career analysis text."""

from __future__ import annotations

import re
from collections.abc import Iterable

from app.claims.models import (
    AllowedClaim,
    AllowedClaims,
    ClaimSupportLevel,
    RestrictedClaimType,
)
from app.models import CareerAnalysis


_WORD_RE = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*", re.UNICODE)
_SENTENCE_RE = re.compile(r".+?(?:[.!?](?=\s|$)|$)", re.DOTALL)
_GAP_RE = re.compile(
    r"\b(?:no|not|missing|unmet|lacks?|lack\s+of|not\s+evidenced|"
    r"not\s+demonstrated|insufficient\s+evidence|gaps?)\b",
    re.IGNORECASE,
)
_PROSPECTIVE_RE = re.compile(
    r"\b(?:should|could|needs?\s+to|recommend(?:ed|ation)?|learn|build|"
    r"develop|improve|practice|focus|study|complete|pursue|gain|create|"
    r"strengthen|explore|plan|target|next\s+step|expected\s+outcome)\b",
    re.IGNORECASE,
)
_CANDIDATE_ASSERTION_RE = re.compile(
    r"\b(?:candidate|they|their|he|she)\b", re.IGNORECASE
)
_DECLARED_RE = re.compile(
    r"\b(?:lists?|listed|declares?|declared|mentions?|mentioned|"
    r"skills?\s+section|familiarity)\b",
    re.IGNORECASE,
)
_CAUTIOUS_RE = re.compile(
    r"\b(?:some|limited|basic)\s+(?:evidence|exposure)\b|"
    r"\b(?:has|shows?)\s+(?:some|limited)\s+evidence\s+of\b|"
    r"\bshows?\s+basic\s+exposure\s+to\b",
    re.IGNORECASE,
)
_STRONG_CAPABILITY_RE = re.compile(
    r"\b(?:strong|extensive|proven|demonstrated|professional(?:ly)?|"
    r"experienced|experience|capable|capability|applied|used|delivered|"
    r"implemented|built|managed|led)\b",
    re.IGNORECASE,
)

_RESTRICTED_PATTERNS = {
    RestrictedClaimType.SENIORITY: re.compile(
        r"\b(?:senior|principal|lead-level|seasoned)\b", re.IGNORECASE
    ),
    RestrictedClaimType.EXPERTISE_LEVEL: re.compile(
        r"\b(?:expert|expertise|advanced\s+professional|highly\s+experienced|"
        r"extensive(?:ly)?|mastery)\b",
        re.IGNORECASE,
    ),
    RestrictedClaimType.LEADERSHIP: re.compile(
        r"\b(?:leader|leadership|led\s+(?:a\s+)?teams?|managed\s+(?:a\s+)?teams?)\b",
        re.IGNORECASE,
    ),
    RestrictedClaimType.YEARS_OF_EXPERIENCE: re.compile(
        r"\b(?:(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)"
        r"(?:\s*\+)?\s+years?|years?\s+of\s+(?:professional\s+)?experience)\b",
        re.IGNORECASE,
    ),
    RestrictedClaimType.PRODUCTION_EXPERIENCE: re.compile(
        r"\b(?:production[-\s]grade|production\s+experience|"
        r"production[-\s]proven|used\s+in\s+production)\b",
        re.IGNORECASE,
    ),
    RestrictedClaimType.RESEARCH_STATUS: re.compile(
        r"\b(?:researcher|research\s+scientist|scientist)\b", re.IGNORECASE
    ),
    RestrictedClaimType.SCALE_OR_IMPACT: re.compile(
        r"\b(?:large[-\s]scale|enterprise[-\s]scale|significant\s+impact|"
        r"major\s+impact|high[-\s]impact|transformative\s+impact)\b",
        re.IGNORECASE,
    ),
}

_CONTENT_STOPWORDS = {
    "a", "an", "and", "as", "at", "candidate", "demonstrates", "demonstrated",
    "completed", "earned", "experience", "for", "from", "has", "have", "holds",
    "in", "is", "of", "on", "the", "their", "they", "through", "to", "used",
    "with", "worked",
}
_SKILL_WORDING_TOKENS = {
    "applied", "basic", "capability", "declared", "declares", "evidence",
    "exposure", "familiarity", "limited", "listed", "lists", "mentions",
    "professional", "professionally", "section", "skill", "skills", "some",
    "strong", "shows",
}


def _normalize_text(value: str) -> str:
    return " ".join(_WORD_RE.findall(value.casefold()))


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in _WORD_RE.findall(value.casefold())
        if token not in _CONTENT_STOPWORDS
    }


def _split_sentences(value: str) -> list[str]:
    return [match.group().strip() for match in _SENTENCE_RE.finditer(value) if match.group().strip()]


def _contains_restricted_positive_claim(
    sentence: str, restricted_types: Iterable[RestrictedClaimType]
) -> bool:
    return any(
        pattern.search(sentence)
        for claim_type in restricted_types
        if (pattern := _RESTRICTED_PATTERNS.get(claim_type)) is not None
    )


def _contains_claim_value(sentence: str, claim: AllowedClaim) -> bool:
    sentence_normalized = _normalize_text(sentence)
    claim_normalized = _normalize_text(claim.claim_value)
    return bool(claim_normalized) and (
        claim_normalized in sentence_normalized
        or sentence_normalized in claim_normalized
    )


def _supports_factual_sentence(sentence: str, claim: AllowedClaim) -> bool:
    if _contains_claim_value(sentence, claim):
        return True
    sentence_tokens = _tokens(sentence)
    claim_tokens = _tokens(claim.claim_value)
    return bool(sentence_tokens) and sentence_tokens <= claim_tokens


def _supports_skill_sentence(sentence: str, claim: AllowedClaim) -> bool:
    if not _contains_claim_value(sentence, claim):
        return False
    unsupported_tokens = (
        _tokens(sentence) - _tokens(claim.claim_value) - _SKILL_WORDING_TOKENS
    )
    if unsupported_tokens:
        return False
    if claim.support_level == ClaimSupportLevel.DECLARED_ONLY:
        return bool(_DECLARED_RE.search(sentence)) and not bool(
            _STRONG_CAPABILITY_RE.search(sentence)
        )
    if claim.support_level == ClaimSupportLevel.WEAK_EVIDENCE:
        return bool(_CAUTIOUS_RE.search(sentence)) and not bool(
            _STRONG_CAPABILITY_RE.search(sentence)
        )
    return True


class UnsupportedClaimsValidator:
    """Validate free-text candidate assertions against deterministic allowed claims."""

    @staticmethod
    def _is_supported(sentence: str, allowed_claims: AllowedClaims) -> bool:
        if any(
            _supports_factual_sentence(sentence, claim)
            for claim in allowed_claims.factual_claims
        ):
            return True
        return any(
            _supports_skill_sentence(sentence, claim)
            for claim in allowed_claims.skill_claims
        )

    def _validate_sentence(
        self, sentence: str, allowed_claims: AllowedClaims
    ) -> str | None:
        if _GAP_RE.search(sentence) or _PROSPECTIVE_RE.search(sentence):
            return sentence
        if _contains_restricted_positive_claim(
            sentence, allowed_claims.restricted_claim_types
        ):
            return None
        return sentence if self._is_supported(sentence, allowed_claims) else None

    def _validate_text(self, value: str, allowed_claims: AllowedClaims) -> str:
        valid = [
            " ".join(validated.split())
            for sentence in _split_sentences(value)
            if (validated := self._validate_sentence(sentence, allowed_claims))
        ]
        return " ".join(valid).strip()

    def _validate_prospective_text(
        self, value: str, allowed_claims: AllowedClaims
    ) -> str:
        """Keep future-facing content unless it explicitly asserts a candidate fact."""
        normalized = " ".join(value.split())
        if not _CANDIDATE_ASSERTION_RE.search(normalized):
            return normalized
        return self._validate_text(normalized, allowed_claims)

    def validate(
        self,
        analysis: CareerAnalysis,
        allowed_claims: AllowedClaims,
    ) -> CareerAnalysis:
        """Return a deep-copied analysis with unsupported positive claims removed."""

        result = analysis.model_copy(deep=True)
        result.professional_summary = self._validate_text(
            result.professional_summary, allowed_claims
        )
        result.career_gap_analysis = self._validate_text(
            result.career_gap_analysis, allowed_claims
        )

        validated_strengths = []
        for strength in result.strengths:
            strength.title = self._validate_text(strength.title, allowed_claims)
            strength.evidence = self._validate_text(strength.evidence, allowed_claims)
            if strength.title or strength.evidence:
                validated_strengths.append(strength)
        result.strengths = validated_strengths

        for group_name in ("critical", "important", "optional"):
            group = getattr(result.missing_skills, group_name)
            for missing_skill in group:
                missing_skill.reason = self._validate_text(
                    missing_skill.reason, allowed_claims
                )

        validated_recommendations = []
        for recommendation in result.recommendations:
            recommendation.title = self._validate_prospective_text(
                recommendation.title, allowed_claims
            )
            recommendation.reason = self._validate_text(
                recommendation.reason, allowed_claims
            )
            recommendation.action = self._validate_prospective_text(
                recommendation.action, allowed_claims
            )
            if recommendation.title or recommendation.reason or recommendation.action:
                validated_recommendations.append(recommendation)
        result.recommendations = validated_recommendations

        for week in result.learning_roadmap:
            week.goal = self._validate_prospective_text(week.goal, allowed_claims)
            week.topics = [
                self._validate_prospective_text(topic, allowed_claims)
                for topic in week.topics
                if self._validate_prospective_text(topic, allowed_claims)
            ]
            week.practical_task = self._validate_prospective_text(
                week.practical_task, allowed_claims
            )
            week.expected_outcome = self._validate_prospective_text(
                week.expected_outcome, allowed_claims
            )
        return result
