"""Deterministic decomposition of compound requirement skills."""

import re

from app.models import RequirementProfile, RequirementSkill


_WRAPPER_PATTERN = re.compile(
    r"^(?:experience\s+(?:with|in)|knowledge\s+of|proficiency\s+(?:with|in)|"
    r"familiarity\s+with|understanding\s+of|ability\s+to)\s+",
    re.IGNORECASE,
)
_EXPLICIT_SEPARATOR_PATTERN = re.compile(r"\s*(?:[,;]|\s+/\s+)\s*")
_CONJUNCTION_PATTERN = re.compile(r"\s+(?:and|or)\s+", re.IGNORECASE)
_PROTECTED_PHRASES = {
    "research and development",
    "health and safety",
    "learning and development",
    "sales and marketing",
    "continuous integration and deployment",
}
_LEADING_QUALITY_MODIFIERS = {
    "clear",
    "effective",
    "excellent",
    "exceptional",
    "good",
    "strong",
}


class RequirementDecomposer:
    """Split safely recognizable requirement lists into atomic skills."""

    def decompose(self, profile: RequirementProfile) -> RequirementProfile:
        """Return a decomposed copy of ``profile`` without mutating it."""

        decomposed_skills: list[RequirementSkill] = []
        seen_names: set[str] = set()

        for skill in profile.skills:
            for name in self._decompose_name(skill.name):
                comparison_key = name.casefold()
                if comparison_key in seen_names:
                    continue

                seen_names.add(comparison_key)
                decomposed_skills.append(
                    RequirementSkill(name=name, priority=skill.priority)
                )

        return profile.model_copy(deep=True, update={"skills": decomposed_skills})

    @staticmethod
    def _decompose_name(name: str) -> list[str]:
        stripped_name = name.strip()
        if not stripped_name:
            return []

        wrapper_match = _WRAPPER_PATTERN.match(stripped_name)
        content = _WRAPPER_PATTERN.sub("", stripped_name, count=1).strip()
        has_explicit_separator = bool(_EXPLICIT_SEPARATOR_PATTERN.search(content))
        is_ability_phrase = bool(
            wrapper_match
            and wrapper_match.group(0).strip().casefold() == "ability to"
        )
        fragments = _EXPLICIT_SEPARATOR_PATTERN.split(content)
        fragments = [
            part
            for fragment in fragments
            for part in RequirementDecomposer._split_safe_conjunction(
                fragment,
                allow_split=has_explicit_separator or not is_ability_phrase,
            )
        ]

        return [
            cleaned
            for fragment in fragments
            if (cleaned := RequirementDecomposer._clean_fragment(fragment))
        ]

    @staticmethod
    def _split_safe_conjunction(fragment: str, *, allow_split: bool) -> list[str]:
        fragment = re.sub(
            r"^(?:and|or)\s+", "", fragment.strip(), flags=re.IGNORECASE
        )
        if fragment.casefold() in _PROTECTED_PHRASES:
            return [fragment]

        parts = _CONJUNCTION_PATTERN.split(fragment)
        if not allow_split or len(parts) != 2:
            return [fragment]

        # Short concepts can stand independently without borrowing context from
        # the other side. Parallel -ing forms and longer phrases are ambiguous
        # verb structures and remain intact.
        first_words = [part.split()[0].casefold() for part in parts if part.split()]
        has_parallel_ing_forms = (
            len(first_words) == 2
            and all(word.endswith("ing") for word in first_words)
        )
        if (
            not has_parallel_ing_forms
            and all(0 < len(part.split()) <= 2 for part in parts)
        ):
            first_words = parts[0].split()
            if (
                len(first_words) == 2
                and first_words[0].casefold() in _LEADING_QUALITY_MODIFIERS
            ):
                return [fragment]
            return parts
        return [fragment]

    @staticmethod
    def _clean_fragment(fragment: str) -> str:
        cleaned = _WRAPPER_PATTERN.sub("", fragment.strip(), count=1).strip(" .")
        if not cleaned:
            return ""
        return cleaned[0].upper() + cleaned[1:]
