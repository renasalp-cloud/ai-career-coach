"""Deterministic filtering of clearly non-requirement profile entries."""

import re

from app.models import RequirementProfile


NON_REQUIREMENT_SECTION_HEADINGS = {
    "about us",
    "application process",
    "benefits",
    "company culture",
    "compensation",
    "diversity and inclusion",
    "equal opportunity",
    "hiring process",
    "how to apply",
    "interview process",
    "our culture",
    "perks",
    "salary",
    "what we offer",
}

_CANDIDATE_EXPECTATION_PATTERN = re.compile(
    r"\b(?:ability|availability|eligible|eligibility|experience|knowledge|"
    r"must|required|willing|willingness)\b",
    re.IGNORECASE,
)
_COMPENSATION_PATTERN = re.compile(
    r"(?:[$€£]\s*\d|\b\d[\d,.]*\s*(?:per\s+(?:hour|year|annum)|"
    r"(?:hourly|annually|annual)\b)|\bcompetitive\s+(?:salary|compensation)\b|"
    r"\b(?:annual|attractive|base)\s+salary\b|"
    r"\bsalary\s+(?:of|range|based|depends)\b|"
    r"\bcompensation\s+(?:package|will\s+be\s+based)\b|"
    r"\bannual\s+(?:performance\s+)?bonus\b|"
    r"\b(?:stock|equity)\s+(?:award|grant|option|package|plan)s?\b)",
    re.IGNORECASE,
)
_BENEFIT_PATTERN = re.compile(
    r"^(?:health(?:care)?|medical|dental|vision|life)\s+(?:and\s+)?"
    r"(?:\w+\s+)?insurance\b|^(?:pension|retirement)\s+(?:benefits?|plan)\b|"
    r"^paid\s+(?:leave|time off|vacation)\b|^wellness\s+(?:benefits?|program)\b|"
    r"^office\s+perks?\b|^flexible\s+working\s+hours\b",
    re.IGNORECASE,
)
_EMPLOYER_OFFER_PATTERN = re.compile(
    r"\b(?:relocation\s+(?:assistance|package)|visa\s+sponsorship)\b"
    r".*\b(?:available|offered|provided|supported)\b|"
    r"^(?:we|the company)\s+(?:offer|offers|provide|provides)\b",
    re.IGNORECASE,
)
_CULTURE_PATTERN = re.compile(
    r"^(?:a|an|our|we are)\s+(?:collaborative|inclusive|innovative|"
    r"dynamic|supportive|fast-paced)\b.*(?:culture|environment|workplace|team)\b",
    re.IGNORECASE,
)
_EQUAL_OPPORTUNITY_PATTERN = re.compile(
    r"\b(?:equal opportunity employer|equal employment opportunity|"
    r"does not discriminate|diversity and inclusion)\b",
    re.IGNORECASE,
)
_APPLICATION_PATTERN = re.compile(
    r"^(?:please\s+)?(?:submit|send|apply)\b.*\b(?:cv|resume|résumé|"
    r"cover letter|application)\b|"
    r"^only shortlisted (?:applicants|candidates) will be contacted\b|"
    r"\b(?:interview|hiring|application) process (?:includes|consists|will)\b",
    re.IGNORECASE,
)


class RequirementProfileFilter:
    """Remove only entries deterministically identifiable as employer content."""

    def filter(self, profile: RequirementProfile) -> RequirementProfile:
        """Return a filtered deep copy without changing retained metadata."""
        retained_skills = [
            skill.model_copy(deep=True)
            for skill in profile.skills
            if self._is_requirement(skill.name)
        ]
        return profile.model_copy(deep=True, update={"skills": retained_skills})

    @staticmethod
    def _is_requirement(name: str) -> bool:
        text = name.strip()
        if text.removesuffix(":").strip().casefold() in NON_REQUIREMENT_SECTION_HEADINGS:
            return False

        if _COMPENSATION_PATTERN.search(text):
            return False

        if _CANDIDATE_EXPECTATION_PATTERN.search(text):
            return True

        return not any(
            pattern.search(text)
            for pattern in (
                _BENEFIT_PATTERN,
                _EMPLOYER_OFFER_PATTERN,
                _CULTURE_PATTERN,
                _EQUAL_OPPORTUNITY_PATTERN,
                _APPLICATION_PATTERN,
            )
        )
