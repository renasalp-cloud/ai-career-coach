"""Utilities for extracting structured sections from a CV."""

from __future__ import annotations

import re


HEADINGS = {
    "PROFILE": "profile",
    "PROFESSIONAL PROFILE": "profile",
    "SUMMARY": "profile",
    "PROFESSIONAL SUMMARY": "profile",
    "ABOUT ME": "profile",
    "EDUCATION": "education",
    "ACADEMIC BACKGROUND": "education",
    "ACADEMIC HISTORY": "education",
    "EDUCATION AND TRAINING": "education",
    "QUALIFICATIONS": "education",
    "WORK EXPERIENCE": "experience",
    "PROFESSIONAL EXPERIENCE": "experience",
    "EMPLOYMENT HISTORY": "experience",
    "WORK HISTORY": "experience",
    "EXPERIENCE": "experience",
    "PROJECTS": "projects",
    "PERSONAL PROJECTS": "projects",
    "ACADEMIC PROJECTS": "projects",
    "SELECTED PROJECTS": "projects",
    "SKILLS": "skills",
    "SKILLS AND STRENGTHS": "skills",
    "COMPUTER SKILLS": "skills",
    "DIGITAL SKILLS": "skills",
    "PROFESSIONAL SKILLS": "skills",
    "PERSONAL SKILLS": "skills",
    "STRENGTHS": "skills",
    "TECHNICAL SKILLS": "skills",
    "CORE SKILLS": "skills",
    "KEY SKILLS": "skills",
    "COMPETENCIES": "skills",
    "CORE COMPETENCIES": "skills",
    "TOOLS": "skills",
    "TECHNOLOGIES": "skills",
    "ADDITIONAL INFORMATION": "additional_information",
    "CERTIFICATIONS": "certifications",
    "CERTIFICATES": "certifications",
    "LICENCES AND CERTIFICATIONS": "certifications",
    "LICENSES AND CERTIFICATIONS": "certifications",
    "LANGUAGES": "languages",
    "LANGUAGE SKILLS": "languages",
    "LANGUAGE PROFICIENCY": "languages",
    "OTHER LANGUAGE(S)": "languages",
}


def _normalize_heading(value: str) -> str:
    """Normalize conservative formatting differences in a possible heading."""

    normalized = " ".join(value.strip().split())
    if normalized.endswith(":"):
        normalized = normalized[:-1].rstrip()
    return normalized.upper()


_COMPACT_HEADINGS = {
    re.sub(r"\s+", "", heading): section
    for heading, section in HEADINGS.items()
}


def _heading_section(value: str) -> str | None:
    """Resolve exact headings plus conservative whitespace extraction noise."""

    normalized = _normalize_heading(value)
    if normalized in HEADINGS:
        return HEADINGS[normalized]
    return _COMPACT_HEADINGS.get(re.sub(r"\s+", "", normalized))


_HEADING_PATTERN = re.compile(
    r"(?<!\w)("
    + "|".join(
        re.escape(heading)
        for heading in sorted(HEADINGS, key=len, reverse=True)
    )
    + r")(?!\w)",
    re.IGNORECASE,
)


def _has_heading_case(value: str) -> bool:
    """Return whether a known heading is presented as uppercase or title case."""

    words = re.findall(r"[^\W\d_]+", value, re.UNICODE)
    return bool(words) and (
        value.isupper()
        or all(word[0].isupper() for word in words)
    )


def _is_inline_heading(line: str, match: re.Match[str]) -> bool:
    """Reject known words used as the beginning of ordinary prose."""

    remainder = line[match.end():]
    if remainder.lstrip().startswith(":") or not remainder.strip():
        return True
    next_word = re.search(r"[^\W\d_]+", remainder, re.UNICODE)
    return (
        match.group().isupper()
        or next_word is None
        or next_word.group()[0].isupper()
    )


def _split_line_at_headings(line: str) -> list[tuple[str | None, str]]:
    """Split one extracted line into content and conservatively styled headings."""

    if heading_section := _heading_section(line):
        return [(heading_section, "")]

    matches = [
        match
        for match in _HEADING_PATTERN.finditer(line)
        if _has_heading_case(match.group()) and _is_inline_heading(line, match)
    ]
    if line.isupper() and len(matches) == 1 and ":" not in line:
        return [(None, line.strip())]
    if not matches:
        return [(None, line.strip())]

    parts: list[tuple[str | None, str]] = []
    if content := line[:matches[0].start()].strip():
        parts.append((None, content))

    for index, match in enumerate(matches):
        content_start = match.end()
        if line[content_start:content_start + 1] == ":":
            content_start += 1
        content_end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(line)
        )
        heading = _normalize_heading(match.group())
        parts.append((HEADINGS[heading], line[content_start:content_end].strip()))

    return parts


def parse_cv(cv_text: str) -> dict:
    """
    Split a CV into logical sections based on common headings.
    """

    sections = {}
    current_section = "other"
    sections[current_section] = []

    for line in cv_text.splitlines():
        text = line.strip()

        if not text:
            continue

        for heading_section, content in _split_line_at_headings(text):
            if heading_section is not None:
                current_section = heading_section
                sections.setdefault(current_section, [])
            if content:
                sections.setdefault(current_section, []).append(content)

    if not sections["other"]:
        sections.pop("other")

    return {
        key: "\n".join(value)
        for key, value in sections.items()
    }
