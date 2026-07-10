"""Normalize extracted candidate profile data."""

from app.candidate_profile.models import CandidateProfile, SkillEntry


SKILL_ALIASES = {
    "machine learning": "Machine Learning",
    "ml model evaluation": "Machine Learning Evaluation",
    "generative ai (genai) & llm basics": "Generative AI",
    "python (computer programming)": "Python",
    "web design(wordpress)": "WordPress",
    "git & github": "Git and GitHub",
}

SKILL_RELATIONS = {
    "image preprocessing": "Computer Vision",
    "image classification": "Computer Vision",
    "image preprocessing and image classification": "Computer Vision",
}


def normalize_candidate_profile(profile: CandidateProfile) -> CandidateProfile:
    """Normalize a candidate profile without inventing unsupported skills."""

    profile.skills = _normalize_skills(profile.skills)
    return profile


def _clean_text(value: str) -> str:
    """Fix common PDF ligatures and normalize whitespace."""

    cleaned = (
        value.replace("ﬁ", "fi")
        .replace("ﬂ", "fl")
        .replace("Responsiveweb", "Responsive web")
    )

    return " ".join(cleaned.split())


def _normalize_skills(skills: list[SkillEntry]) -> list[SkillEntry]:
    """Normalize aliases and add supported canonical skill relations."""

    normalized: dict[str, SkillEntry] = {}

    for skill in skills:
        cleaned_name = _clean_text(skill.name)

        if not cleaned_name:
            continue

        lookup_key = cleaned_name.lower()
        canonical_name = SKILL_ALIASES.get(lookup_key, cleaned_name)
        canonical_key = canonical_name.lower()

        normalized.setdefault(
            canonical_key,
            SkillEntry(
                name=canonical_name,
                source=skill.source,
            ),
        )

        related_skill = SKILL_RELATIONS.get(lookup_key)

        if related_skill:
            normalized.setdefault(
                related_skill.lower(),
                SkillEntry(
                    name=related_skill,
                    source="semantic_normalization",
                ),
            )

    return sorted(
        normalized.values(),
        key=lambda item: item.name.lower(),
    )