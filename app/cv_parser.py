"""Utilities for extracting structured sections from a CV."""

from __future__ import annotations


HEADINGS = {
    "PROFILE": "profile",
    "SUMMARY": "profile",
    "EDUCATION": "education",
    "EDUCATION AND TRAINING": "education",
    "WORK EXPERIENCE": "experience",
    "EXPERIENCE": "experience",
    "PROJECTS": "projects",
    "ACADEMIC PROJECTS": "projects",
    "SKILLS": "skills",
    "CERTIFICATIONS": "certifications",
    "LANGUAGES": "languages",
    "LANGUAGE SKILLS": "languages",
    "OTHER LANGUAGE(S):": "languages",
}


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

        heading = text.upper()

        if heading in HEADINGS:
            current_section = HEADINGS[heading]
            sections.setdefault(current_section, [])
            continue

        sections.setdefault(current_section, []).append(text)

    if not sections["other"]:
        sections.pop("other")

    return {
        key: "\n".join(value)
        for key, value in sections.items()
    }
