import re

from app.evidence.models import EvidenceSourceType, ScoredCandidateEvidence
from app.evidence.ranker import EvidenceRanker
from app.evidence.scorer import EvidenceQualityScorer
from app.models import CandidateProfile, RequirementProfile, SkillEvidence, SkillMatch
from app.semantic.alias_registry import SkillAliasRegistry
from app.semantic.default_aliases import build_default_skill_alias_registry
from app.semantic.evidence_collector import CandidateEvidenceCollector


# TODO: Move exact skill normalization to a shared semantic utility when more
# semantic components need the same trim/case-insensitive comparison.
def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


LOW_LEVEL_QUALIFIERS = (
    "basic knowledge",
    "foundational knowledge",
    "fundamentals",
    "foundation",
    "basics",
)
GENERIC_SKILL_PREFIXES = (
    "proficiency in",
    "knowledge of",
    "understanding of",
    "familiarity with",
    "experience with",
    "experience using",
    "strong",
    "good",
    "solid",
    "proficient",
)
GENERIC_CAPABILITY_SUFFIXES = ("programming skills", "skill", "skills")
LANGUAGE_LEVEL = re.compile(r"\b(?:a1|a2|b1|b2|c1|c2)\b")
LANGUAGE_MODE = re.compile(
    r"\b(?:listening|writing|written|speaking|spoken|spoken production|"
    r"spoken interaction|reading)\b"
)
EDUCATION_LEVELS = {
    "bachelor": re.compile(r"\b(?:bachelor(?:'s)?|bsc|ba)\b"),
    "master": re.compile(r"\b(?:master(?:'s)?|msc|ma)\b"),
    "doctorate": re.compile(r"\b(?:doctorate|doctoral|phd)\b"),
}
EDUCATION_FIELD_STOPWORDS = {
    "a", "an", "and", "another", "bachelor", "bachelors", "degree", "field",
    "in", "of", "or", "related", "the",
}
RELATED_FIELD_FAMILIES = (
    frozenset({"computer", "computing", "software", "informatics"}),
)
ACTION_EVIDENCE = re.compile(
    r"\b(?:built|developed|implemented|trained|evaluated|deployed|created|"
    r"worked with|gained hands on experience|hands on experience|"
    r"completed (?:a )?practical(?: [a-z0-9]+){0,6} bootcamp)\b"
)
PRACTICAL_REQUIREMENT_PATTERNS = (
    re.compile(
        r"^(?:practical|hands on|applied)\s+(?:experience|knowledge)"
        r"(?:\s+(?:with|in|of))?\s+(.+)$"
    ),
    re.compile(
        r"^(?:practical|hands on|applied)\s+(.+?)\s+"
        r"(?:project\s+)?experience$"
    ),
)
APPLICATION_DEVELOPMENT_REQUIREMENT = re.compile(
    r"\bapplications?\s+development$"
)

LEGACY_EVIDENCE_SOURCES = {
    EvidenceSourceType.WORK_EXPERIENCE: "experience",
    EvidenceSourceType.PROJECT: "projects",
    EvidenceSourceType.EDUCATION: "education",
    EvidenceSourceType.CERTIFICATION: "certification",
    EvidenceSourceType.SKILLS_SECTION: "skills",
    EvidenceSourceType.SUMMARY: "summary",
    EvidenceSourceType.OTHER: "other",
}


ACTION_EVIDENCE_SOURCES = {
    EvidenceSourceType.WORK_EXPERIENCE,
    EvidenceSourceType.PROJECT,
    EvidenceSourceType.CERTIFICATION,
}


def _skill_evidence(item: ScoredCandidateEvidence) -> SkillEvidence:
    return SkillEvidence(
        source=LEGACY_EVIDENCE_SOURCES[item.evidence.source_type],
        text=item.evidence.source_text,
        quality_score=item.quality_score,
    )


def _comparison_name(value: str) -> str:
    normalized = _normalize(value)
    for prefix in GENERIC_SKILL_PREFIXES:
        if normalized.startswith(f"{prefix} "):
            normalized = normalized[len(prefix) + 1 :].strip()
            break
    for qualifier in LOW_LEVEL_QUALIFIERS:
        if normalized == qualifier:
            return normalized
        if normalized.endswith(f" {qualifier}"):
            return normalized[: -(len(qualifier) + 1)].strip()
    for suffix in GENERIC_CAPABILITY_SUFFIXES:
        if normalized.endswith(f" {suffix}"):
            return normalized[: -(len(suffix) + 1)].strip()
    return normalized


def _language_match(
    requirement: str,
    candidate: CandidateProfile,
) -> str | None:
    normalized_requirement = _normalize(requirement)
    language_entries = [
        _normalize(language) for language in candidate.languages if language.strip()
    ]

    for entry in language_entries:
        language_name = LANGUAGE_MODE.sub(" ", LANGUAGE_LEVEL.sub(" ", entry))
        language_name = re.sub(r"\s+", " ", language_name).strip()
        if not language_name or not _contains(normalized_requirement, language_name):
            continue

        requires_written = bool(re.search(r"\b(?:written|writing)\b", normalized_requirement))
        requires_spoken = bool(re.search(r"\b(?:spoken|speaking|verbal)\b", normalized_requirement))
        same_language_entries = [
            item for item in language_entries
            if item == entry or LANGUAGE_MODE.search(item)
        ]
        has_level = any(LANGUAGE_LEVEL.search(item) for item in same_language_entries)
        has_written = any(re.search(r"\b(?:written|writing)\b", item) for item in same_language_entries)
        has_spoken = any(re.search(r"\b(?:spoken|speaking)\b", item) for item in same_language_entries)

        if has_level and (
            (not requires_written and not requires_spoken)
            or (LANGUAGE_LEVEL.search(entry))
            or ((not requires_written or has_written) and (not requires_spoken or has_spoken))
        ):
            return language_name
    return None


def _education_level(value: str) -> str | None:
    normalized = _normalize(value)
    return next(
        (level for level, pattern in EDUCATION_LEVELS.items() if pattern.search(normalized)),
        None,
    )


def _education_match(requirement: str, candidate: CandidateProfile) -> str | None:
    normalized_requirement = _normalize(requirement)
    required_level = _education_level(requirement)
    if not required_level:
        return None

    requirement_terms = set(normalized_requirement.split()) - EDUCATION_FIELD_STOPWORDS
    has_related_field = bool(re.search(r"\brelated field\b", normalized_requirement))

    for education in candidate.education:
        if education.status.casefold() != "completed":
            continue
        education_text = education.degree
        if _education_level(education_text) != required_level:
            continue
        education_terms = set(_normalize(education_text).split()) - EDUCATION_FIELD_STOPWORDS
        if requirement_terms & education_terms:
            return education.degree
        if has_related_field and any(
            requirement_terms & family and education_terms & family
            for family in RELATED_FIELD_FAMILIES
        ):
            return education.degree
    return None


def _contains(text: str, phrase: str) -> bool:
    return f" {_comparison_name(phrase)} " in f" {_normalize(text)} "


def _practical_subject(value: str) -> str | None:
    normalized = _normalize(value)
    for pattern in PRACTICAL_REQUIREMENT_PATTERNS:
        match = pattern.match(normalized)
        if match:
            return match.group(1).strip()
    return None


class SkillMatcher:
    def __init__(
        self,
        evidence_collector: CandidateEvidenceCollector | None = None,
        evidence_scorer: EvidenceQualityScorer | None = None,
        evidence_ranker: EvidenceRanker | None = None,
        alias_registry: SkillAliasRegistry | None = None,
        evidence_limit: int = 3,
    ) -> None:
        if evidence_limit <= 0:
            raise ValueError("evidence_limit must be positive")
        self.evidence_collector = (
            evidence_collector
            if evidence_collector is not None
            else CandidateEvidenceCollector()
        )
        self.evidence_scorer = evidence_scorer or EvidenceQualityScorer()
        self.evidence_ranker = evidence_ranker or EvidenceRanker()
        self.alias_registry = (
            alias_registry
            if alias_registry is not None
            else build_default_skill_alias_registry()
        )
        self.evidence_limit = evidence_limit

    def _select_evidence(
        self, evidence: list[ScoredCandidateEvidence]
    ) -> list[SkillEvidence]:
        selected = self.evidence_ranker.select_top(evidence, self.evidence_limit)
        return [_skill_evidence(item) for item in selected]

    def match(
        self,
        candidate: CandidateProfile,
        requirements: RequirementProfile,
    ) -> list[SkillMatch]:
        evidence = self.evidence_scorer.score_all(
            self.evidence_collector.collect(candidate)
        )
        candidate_skills = {
            _normalize(skill.name): skill
            for skill in candidate.skills
            if skill.name.strip()
        }

        matches: list[SkillMatch] = []

        for requirement_skill in requirements.skills:
            role_skill = requirement_skill.name
            normalized_role_skill = _comparison_name(role_skill)
            is_language_requirement = (
                requirement_skill.category == "language"
                or (
                    re.search(r"\b(?:written|writing)\b", normalized_role_skill)
                    and re.search(
                        r"\b(?:spoken|speaking|verbal)\b", normalized_role_skill
                    )
                )
            )
            if is_language_requirement and (
                language_name := _language_match(role_skill, candidate)
            ):
                relevant_evidence = [
                    item
                    for item in evidence
                    if item.evidence.source_label == "Languages section"
                    and _contains(item.evidence.source_text, language_name)
                ]
                matches.append(
                    SkillMatch(
                        role_skill=role_skill,
                        candidate_skill=language_name,
                        evidence=self._select_evidence(relevant_evidence),
                    )
                )
                continue
            if requirement_skill.category == "education" and (
                education_match := _education_match(role_skill, candidate)
            ):
                relevant_evidence = [
                    item
                    for item in evidence
                    if item.evidence.source_type == EvidenceSourceType.EDUCATION
                    and _contains(item.evidence.source_text, education_match)
                ]
                matches.append(
                    SkillMatch(
                        role_skill=role_skill,
                        candidate_skill=education_match,
                        evidence=self._select_evidence(relevant_evidence),
                    )
                )
                continue
            practical_subject = _practical_subject(role_skill)
            requires_action_evidence = bool(
                practical_subject
                or APPLICATION_DEVELOPMENT_REQUIREMENT.search(normalized_role_skill)
            )
            candidate_skill = (
                None
                if requires_action_evidence
                else candidate_skills.get(normalized_role_skill)
            )

            if candidate_skill is None:
                if practical_subject:
                    relevant_evidence = [
                        item
                        for item in evidence
                        if item.evidence.source_type in ACTION_EVIDENCE_SOURCES
                        and ACTION_EVIDENCE.search(_normalize(item.evidence.source_text))
                        and _contains(item.evidence.source_text, practical_subject)
                    ]
                    if relevant_evidence:
                        matches.append(
                            SkillMatch(
                                role_skill=role_skill,
                                candidate_skill=practical_subject,
                                evidence=self._select_evidence(relevant_evidence),
                            )
                        )
                        continue

                relevant_evidence = [
                    item
                    for item in evidence
                    if not practical_subject
                    and _contains(item.evidence.source_text, normalized_role_skill)
                    and (
                        not requires_action_evidence
                        or (
                            item.evidence.source_type in ACTION_EVIDENCE_SOURCES
                            and ACTION_EVIDENCE.search(
                                _normalize(item.evidence.source_text)
                            )
                        )
                    )
                ]

                if relevant_evidence:
                    matches.append(
                        SkillMatch(
                            role_skill=role_skill,
                            candidate_skill=role_skill,
                            evidence=self._select_evidence(relevant_evidence),
                        )
                    )
                    continue

                alias_evidence = [
                    item
                    for item in evidence
                    if any(
                        _contains(item.evidence.source_text, alias)
                        for alias in self.alias_registry.aliases_for(role_skill)
                    )
                    and (
                        not requires_action_evidence
                        or (
                            item.evidence.source_type in ACTION_EVIDENCE_SOURCES
                            and ACTION_EVIDENCE.search(
                                _normalize(item.evidence.source_text)
                            )
                        )
                    )
                ]

                if alias_evidence:
                    matches.append(
                        SkillMatch(
                            role_skill=role_skill,
                            candidate_skill=role_skill,
                            evidence=self._select_evidence(alias_evidence),
                        )
                    )
                    continue

                matches.append(
                    SkillMatch(
                        role_skill=role_skill,
                        candidate_skill=None,
                        evidence=[],
                    )
                )
                continue

            relevant_evidence = [
                item
                for item in evidence
                if _contains(item.evidence.source_text, candidate_skill.name)
            ]

            matches.append(
                SkillMatch(
                    role_skill=role_skill,
                    candidate_skill=candidate_skill.name,
                    evidence=self._select_evidence(relevant_evidence),
                )
            )

        return matches
