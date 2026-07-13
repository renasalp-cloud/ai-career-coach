import re

from app.models import CandidateProfile, RequirementProfile, SkillMatch
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


def _comparison_name(value: str) -> str:
    normalized = _normalize(value)
    for qualifier in LOW_LEVEL_QUALIFIERS:
        if normalized == qualifier:
            return normalized
        if normalized.endswith(f" {qualifier}"):
            return normalized[: -(len(qualifier) + 1)].strip()
    return normalized


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
        alias_registry: SkillAliasRegistry | None = None,
    ) -> None:
        self.evidence_collector = (
            evidence_collector
            if evidence_collector is not None
            else CandidateEvidenceCollector()
        )
        self.alias_registry = (
            alias_registry
            if alias_registry is not None
            else build_default_skill_alias_registry()
        )

    def match(
        self,
        candidate: CandidateProfile,
        requirements: RequirementProfile,
    ) -> list[SkillMatch]:
        evidence = self.evidence_collector.collect(candidate)
        candidate_skills = {
            _normalize(skill.name): skill
            for skill in candidate.skills
            if skill.name.strip()
        }

        matches: list[SkillMatch] = []

        for requirement_skill in requirements.skills:
            role_skill = requirement_skill.name
            normalized_role_skill = _comparison_name(role_skill)
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
                        if item.source in {"experience", "projects", "training"}
                        and ACTION_EVIDENCE.search(_normalize(item.text))
                        and _contains(item.text, practical_subject)
                    ]
                    if relevant_evidence:
                        matches.append(
                            SkillMatch(
                                role_skill=role_skill,
                                candidate_skill=practical_subject,
                                evidence=relevant_evidence,
                            )
                        )
                        continue

                relevant_evidence = [
                    item
                    for item in evidence
                    if not practical_subject
                    and _contains(item.text, normalized_role_skill)
                    and (
                        not requires_action_evidence
                        or (
                            item.source in {"experience", "projects", "training"}
                            and ACTION_EVIDENCE.search(_normalize(item.text))
                        )
                    )
                ]

                if relevant_evidence:
                    matches.append(
                        SkillMatch(
                            role_skill=role_skill,
                            candidate_skill=role_skill,
                            evidence=relevant_evidence,
                        )
                    )
                    continue

                alias_evidence = [
                    item
                    for item in evidence
                    for alias in self.alias_registry.aliases_for(role_skill)
                    if _contains(item.text, alias)
                    and (
                        not requires_action_evidence
                        or (
                            item.source in {"experience", "projects", "training"}
                            and ACTION_EVIDENCE.search(_normalize(item.text))
                        )
                    )
                ]

                if alias_evidence:
                    matches.append(
                        SkillMatch(
                            role_skill=role_skill,
                            candidate_skill=role_skill,
                            evidence=alias_evidence,
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
                if _contains(item.text, candidate_skill.name)
            ]

            matches.append(
                SkillMatch(
                    role_skill=role_skill,
                    candidate_skill=candidate_skill.name,
                    evidence=relevant_evidence,
                )
            )

        return matches
