"""Deterministically align a CareerAnalysis with validated candidate facts."""

import re

from app.candidate_profile.models import CandidateProfile
from app.models import (
    CareerAnalysis,
    MissingSkill,
    Recommendation,
    RequirementProfile,
    SkillMatch,
    Strength,
)


PRIORITY_TO_MISSING_GROUP = {
    "required": "critical",
    "preferred": "important",
    "optional": "optional",
}
MISSING_LANGUAGE = re.compile(
    r"\b(missing|lacks?|lacking|does not (?:have|demonstrate|show)|"
    r"not demonstrated|no (?:evidence|experience)|needs? (?:more )?experience)\b",
    re.IGNORECASE,
)
TITLE_INTRODUCTIONS = (
    re.compile(r"^\s*(?:a|an)\s+(.+?)(?=\s+(?:with|who)\b|[,.])", re.IGNORECASE),
    re.compile(
        r"^\s*(?:the\s+)?candidate\s+is\s+(?:a|an)\s+(.+?)"
        r"(?=\s+(?:with|who)\b|[,.])",
        re.IGNORECASE,
    ),
)
PROFICIENCY_QUALIFIERS = (
    "proficient",
    "expert",
    "advanced",
    "strong",
    "extensive",
    "highly skilled",
)
INTERNAL_SYSTEM_LANGUAGE = re.compile(
    r"\b(?:validated missing requirement|deterministic evidence|pipeline output|"
    r"schema validation)\b",
    re.IGNORECASE,
)


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized_text = f" {_normalize(text)} "
    normalized_phrase = _normalize(phrase)
    return bool(normalized_phrase) and f" {normalized_phrase} " in normalized_text


class AnalysisConsistencyProcessor:
    """Apply deterministic facts after the LLM response has been validated."""

    def process(
        self,
        analysis: CareerAnalysis,
        candidate_profile: CandidateProfile,
        requirements: RequirementProfile,
        validated_skill_matches: list[SkillMatch],
    ) -> CareerAnalysis:
        missing_groups = self._build_missing_groups(requirements, validated_skill_matches)
        self._apply_missing_groups(analysis, missing_groups)

        demonstrated = self._demonstrated_names(validated_skill_matches)
        self._remove_demonstrated_skills(analysis, demonstrated)
        self._validate_strengths(analysis, candidate_profile, validated_skill_matches)
        self._align_recommendations(analysis, missing_groups, demonstrated)
        self._align_roadmap(analysis, missing_groups, demonstrated)

        if self._gap_contradicts_demonstrated_skill(
            analysis.career_gap_analysis, demonstrated
        ):
            analysis.career_gap_analysis = self._build_gap_summary(
                validated_skill_matches
            )

        if self._introduces_unsupported_title(
            analysis.professional_summary, candidate_profile
        ) or self._gap_contradicts_demonstrated_skill(
            analysis.professional_summary, demonstrated
        ):
            analysis.professional_summary = self._build_candidate_summary(
                candidate_profile, validated_skill_matches
            )

        return analysis

    @classmethod
    def _validate_strengths(
        cls,
        analysis: CareerAnalysis,
        profile: CandidateProfile,
        matches: list[SkillMatch],
    ) -> None:
        facts = cls._candidate_facts(profile, matches)
        analysis.strengths = [
            strength
            for strength in analysis.strengths
            if cls._text_supported(strength.title, facts)
            or cls._text_supported(strength.evidence, facts)
        ]
        analysis.strengths = [
            cls._ground_strength_language(strength, profile, matches, facts)
            for strength in analysis.strengths
        ]
        if analysis.strengths:
            return
        analysis.strengths = [
            Strength(
                title=match.candidate_skill or match.role_skill,
                evidence=match.evidence[0].text if match.evidence else (match.candidate_skill or match.role_skill),
            )
            for match in matches
            if match.status == "demonstrated"
        ]

    @classmethod
    def _ground_strength_language(
        cls,
        strength: Strength,
        profile: CandidateProfile,
        matches: list[SkillMatch],
        facts: list[str],
    ) -> Strength:
        combined = f"{strength.title} {strength.evidence}"
        unsupported = [
            qualifier
            for qualifier in PROFICIENCY_QUALIFIERS
            if _contains_phrase(combined, qualifier)
            and not any(_contains_phrase(fact, qualifier) for fact in facts)
        ]
        if not unsupported:
            return strength

        for match in matches:
            if match.status != "demonstrated":
                continue
            names = [match.role_skill, match.candidate_skill or ""]
            if any(_contains_phrase(combined, name) for name in names if name):
                title = match.candidate_skill or match.role_skill
                evidence = (
                    match.evidence[0].text
                    if match.evidence
                    else f"{title} is listed in the candidate profile."
                )
                return Strength(title=title, evidence=evidence)

        for skill in profile.skills:
            if _contains_phrase(combined, skill.name):
                return Strength(
                    title=skill.name,
                    evidence=f"{skill.name} is listed in the candidate profile.",
                )

        return Strength(
            title=cls._remove_qualifiers(strength.title, unsupported),
            evidence=cls._remove_qualifiers(strength.evidence, unsupported),
        )

    @staticmethod
    def _remove_qualifiers(text: str, qualifiers: list[str]) -> str:
        result = text
        for qualifier in sorted(qualifiers, key=len, reverse=True):
            result = re.sub(
                rf"\b{re.escape(qualifier)}\b(?:\s+(?:in|with|at))?\s*",
                "",
                result,
                flags=re.IGNORECASE,
            )
        result = re.sub(r"\s+", " ", result).strip(" ,.-")
        return result

    @staticmethod
    def _candidate_facts(profile: CandidateProfile, matches: list[SkillMatch]) -> list[str]:
        facts = [profile.summary, *profile.languages, *profile.projects, *profile.certifications]
        facts.extend(skill.name for skill in profile.skills)
        for experience in profile.experience:
            facts.extend([experience.organization, experience.title, *experience.highlights])
        for education in profile.education:
            facts.extend([education.degree, education.institution])
        for match in matches:
            if match.status == "demonstrated":
                facts.extend([match.role_skill, match.candidate_skill or ""])
                facts.extend(item.text for item in match.evidence)
        return [fact for fact in facts if fact and fact.strip()]

    @staticmethod
    def _text_supported(text: str, facts: list[str]) -> bool:
        normalized = _normalize(text)
        if not normalized:
            return False
        return any(
            _contains_phrase(text, fact) or _contains_phrase(fact, text)
            for fact in facts
            if _normalize(fact)
        )

    @classmethod
    def _align_recommendations(
        cls,
        analysis: CareerAnalysis,
        missing_groups: dict[str, list[str]],
        demonstrated: set[str],
    ) -> None:
        prioritized_missing = list(
            dict.fromkeys(
                [
                    *missing_groups["critical"],
                    *missing_groups["important"],
                    *missing_groups["optional"],
                ]
            )
        )[:4]

        group_by_skill = {
            _normalize(skill): group
            for group, skills in missing_groups.items()
            for skill in skills
        }

        existing_by_skill: dict[str, Recommendation] = {}

        for item in analysis.recommendations:
            values = (item.title, item.reason, item.action)

            if cls._mentions_any(values, demonstrated):
                continue

            for skill in prioritized_missing:
                if any(_contains_phrase(value, skill) for value in values):
                    existing_by_skill.setdefault(_normalize(skill), item)
                    break

        aligned: list[Recommendation] = []

        for skill in prioritized_missing:
            existing = existing_by_skill.get(_normalize(skill))

            if existing is not None:
                existing.priority = {
                    "critical": "high",
                    "important": "medium",
                    "optional": "low",
                }[group_by_skill[_normalize(skill)]]

                if not existing.title.strip():
                    existing.title = f"Develop {skill}"

                if not existing.reason.strip():
                    existing.reason = (
                        f"{skill} is a prioritized development area "
                        "for the target role."
                    )

                if not existing.action.strip():
                    existing.action = (
                        f"Complete focused learning and practical work in {skill}."
                    )

                aligned.append(existing)
                continue

            aligned.append(
                cls._build_recommendation(
                    skill,
                    group_by_skill[_normalize(skill)],
                )
            )

        analysis.recommendations = aligned

    @classmethod
    def _align_roadmap(
        cls,
        analysis: CareerAnalysis,
        missing_groups: dict[str, list[str]],
        demonstrated: set[str],
    ) -> None:
        prioritized_missing = list(
            dict.fromkeys(
                [
                    *missing_groups["critical"],
                    *missing_groups["important"],
                    *missing_groups["optional"],
                ]
            )
        )

        for index, week in enumerate(analysis.learning_roadmap):
            values = (week.goal, *week.topics, week.practical_task, week.expected_outcome)

            week.week = index + 1

            if not prioritized_missing:
                week.goal = "Continue role-relevant professional development"
                week.topics = []
                week.practical_task = "Complete a role-relevant practical exercise."
                week.expected_outcome = "Produce a concrete work sample."
                continue

            focus = prioritized_missing[index % len(prioritized_missing)]

            mentions_focus = cls._mentioned_skills(values, [focus])
            mentions_other_missing = cls._mentioned_skills(
                values,
                [skill for skill in prioritized_missing if skill != focus],
            )
            mentions_demonstrated = cls._mentions_any(values, demonstrated)

            if (
                not mentions_focus
                or mentions_other_missing
                or mentions_demonstrated
                or any(INTERNAL_SYSTEM_LANGUAGE.search(value) for value in values)
            ):
                week.goal = f"Develop {focus}"
                week.practical_task = (
                    f"Complete a practical exercise focused on {focus}."
                )
                week.expected_outcome = (
                    f"Produce a work sample demonstrating {focus}."
                )

            week.topics = [focus]

    @staticmethod
    def _mentioned_skills(values: tuple[str, ...], skills: list[str]) -> list[str]:
        return [
            skill
            for skill in skills
            if any(_contains_phrase(value, skill) for value in values)
        ]

    @staticmethod
    def _mentions_any(values: tuple[str, ...], normalized_skills: set[str]) -> bool:
        return any(
            _contains_phrase(value, skill)
            for value in values
            for skill in normalized_skills
        )

    @staticmethod
    def _build_recommendation(skill: str, group: str) -> Recommendation:
        priority = {"critical": "high", "important": "medium", "optional": "low"}[group]
        return Recommendation(
            priority=priority,
            title=f"Develop {skill}",
            reason=f"{skill} is a prioritized development area for the target role.",
            action=f"Complete focused learning and practical work in {skill}.",
        )

    @staticmethod
    def _build_missing_groups(
        requirements: RequirementProfile,
        validated_skill_matches: list[SkillMatch],
    ) -> dict[str, list[str]]:
        priority_by_skill = {
            _normalize(skill.name): skill.priority for skill in requirements.skills
        }
        groups: dict[str, list[str]] = {
            "critical": [],
            "important": [],
            "optional": [],
        }
        for match in validated_skill_matches:
            if match.status != "missing":
                continue
            group = PRIORITY_TO_MISSING_GROUP.get(
                priority_by_skill.get(_normalize(match.role_skill), "")
            )
            if group and match.role_skill not in groups[group]:
                groups[group].append(match.role_skill)
        return groups

    @staticmethod
    def _apply_missing_groups(
        analysis: CareerAnalysis, groups: dict[str, list[str]]
    ) -> None:
        reasons = {
            _normalize(item.skill): item.reason
            for group_name in ("critical", "important", "optional")
            for item in getattr(analysis.missing_skills, group_name)
        }
        for group_name, skills in groups.items():
            setattr(
                analysis.missing_skills,
                group_name,
                [MissingSkill(skill=skill, reason=reasons.get(_normalize(skill), "")) for skill in skills],
            )

    @staticmethod
    def _demonstrated_names(matches: list[SkillMatch]) -> set[str]:
        names: set[str] = set()
        for match in matches:
            if match.status != "demonstrated":
                continue
            names.add(_normalize(match.role_skill))
            if match.candidate_skill:
                names.add(_normalize(match.candidate_skill))
        return {name for name in names if name}

    @staticmethod
    def _remove_demonstrated_skills(
        analysis: CareerAnalysis, demonstrated: set[str]
    ) -> None:
        for group_name in ("critical", "important", "optional"):
            group = getattr(analysis.missing_skills, group_name)
            setattr(
                analysis.missing_skills,
                group_name,
                [item for item in group if _normalize(item.skill) not in demonstrated],
            )

    @staticmethod
    def _gap_contradicts_demonstrated_skill(text: str, demonstrated: set[str]) -> bool:
        for sentence in re.split(r"(?<=[.!?;])\s+", text):
            clauses = re.split(
                r"\s*(?:,|;)\s*(?:while|but|although|whereas)?\s*",
                sentence,
                flags=re.IGNORECASE,
            )
            for clause in clauses:
                if MISSING_LANGUAGE.search(clause) and any(
                    _contains_phrase(clause, skill) for skill in demonstrated
                ):
                    return True
        return False

    @staticmethod
    def _build_gap_summary(matches: list[SkillMatch]) -> str:
        missing = list(
            dict.fromkeys(match.role_skill for match in matches if match.status == "missing")
        )
        if not missing:
            return "No validated skill gaps were identified."
        return f"Validated missing requirements: {', '.join(missing)}."

    @staticmethod
    def _introduces_unsupported_title(
        summary: str, candidate_profile: CandidateProfile
    ) -> bool:
        introduced_title = None
        for pattern in TITLE_INTRODUCTIONS:
            match = pattern.search(summary)
            if match:
                introduced_title = _normalize(match.group(1))
                break
        generic_subjects = ("candidate", "professional", "individual", "person")
        if not introduced_title or introduced_title.endswith(generic_subjects):
            return False
        actual_titles = {
            _normalize(experience.title)
            for experience in candidate_profile.experience
            if experience.title.strip()
        }
        return introduced_title not in actual_titles

    @staticmethod
    def _build_candidate_summary(
        profile: CandidateProfile, matches: list[SkillMatch]
    ) -> str:
        facts: list[str] = []
        completed = [item.degree for item in profile.education if item.status == "completed" and item.degree]
        current = [item.degree for item in profile.education if item.status == "current" and item.degree]
        titles = list(dict.fromkeys(item.title for item in profile.experience if item.title))
        training = list(dict.fromkeys(item for item in profile.certifications if item))
        skills = list(
            dict.fromkeys(
                (match.candidate_skill or match.role_skill)
                for match in matches
                if match.status == "demonstrated"
            )
        )

        if completed:
            facts.append(f"Completed education: {', '.join(completed)}")
        if current:
            facts.append(f"Current education: {', '.join(current)}")
        if titles:
            facts.append(f"Experience titles: {', '.join(titles)}")
        if training:
            facts.append(f"Training and certifications: {', '.join(training)}")
        if skills:
            facts.append(f"Demonstrated skills: {', '.join(skills)}")
        return ". ".join(facts) + "." if facts else "Candidate profile contains limited structured information."
