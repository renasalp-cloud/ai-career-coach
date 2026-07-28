"""Conservative deterministic classification of requirement text."""

import re

from app.models import RequirementCategory


class RequirementCategoryClassifier:
    """Classify requirement text using profession-agnostic linguistic cues."""

    _EDUCATION = re.compile(
        r"\b(?:bachelor(?:'s)?|master(?:'s)?|doctorate|doctoral|degree|diploma|"
        r"formal education|academic qualification)\b",
        re.IGNORECASE,
    )
    _CERTIFICATION = re.compile(
        r"\b(?:certification|certificate|certified|licen[cs]e|licensed)\b",
        re.IGNORECASE,
    )
    _LANGUAGE = re.compile(
        r"\b(?:fluent|fluency|language proficiency|proficiency in (?:a |another )?"
        r"language|written and spoken language|spoken and written language)\b",
        re.IGNORECASE,
    )
    _TOOL = re.compile(
        r"\b(?:software|systems?|tools?|platforms?|applications?)\b",
        re.IGNORECASE,
    )
    _SOFT_SKILL = re.compile(
        r"\b(?:communication skills?|time management|attention to detail|"
        r"leadership ability|interpersonal skills?|teamwork|collaboration|"
        r"problem[- ]solving skills?|adaptability)\b",
        re.IGNORECASE,
    )
    _DOMAIN_KNOWLEDGE = re.compile(
        r"^\s*(?:knowledge|understanding|familiarity)\s+(?:of|with)\b",
        re.IGNORECASE,
    )
    _EXPERIENCE = re.compile(
        r"\b(?:experience|years?'?\s+(?:of\s+)?.*experience)\b",
        re.IGNORECASE,
    )
    _SKILL = re.compile(
        r"\b(?:analysis|preparation|planning|troubleshooting)\b",
        re.IGNORECASE,
    )

    def classify(self, requirement_text: str) -> RequirementCategory:
        """Return the supported category most reliably signaled by the text."""
        text = requirement_text.strip()
        if not text:
            return "other"

        for category, pattern in (
            ("education", self._EDUCATION),
            ("certification", self._CERTIFICATION),
            ("language", self._LANGUAGE),
            ("tool", self._TOOL),
            ("soft_skill", self._SOFT_SKILL),
            ("domain_knowledge", self._DOMAIN_KNOWLEDGE),
            ("experience", self._EXPERIENCE),
            ("skill", self._SKILL),
        ):
            if pattern.search(text):
                return category

        return "other"
