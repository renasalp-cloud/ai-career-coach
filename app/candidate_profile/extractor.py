"""Generic candidate profile extraction from parsed CV sections."""

import re

from app.candidate_profile.models import (
    CandidateProfile,
    EducationEntry,
    ExperienceEntry,
    SkillEntry,
)


DATE_RANGE_PATTERN = re.compile(
    r"\[\s*(?P<start>\d{2}/\d{2}/\d{4})\s*[^\dA-Za-z]+\s*(?P<end>\d{2}/\d{2}/\d{4}|Current)\s*\]"
)


def extract_candidate_profile(cv_sections: dict[str, str]) -> CandidateProfile:
    """Extract a generic structured candidate profile from parsed CV sections."""

    return CandidateProfile(
        education=_extract_education(cv_sections),
        experience=_extract_experience(cv_sections),
        skills=_extract_skills(cv_sections),
        languages=_extract_languages(cv_sections),
    )


def _extract_section_lines(cv_sections: dict[str, str], section_name: str) -> list[str]:
    """Extract non-empty lines from a CV section."""

    section_text = cv_sections.get(section_name, "")

    return [
        line.strip()
        for line in section_text.splitlines()
        if line.strip()
    ]


def _extract_languages(cv_sections: dict[str, str]) -> list[str]:
    """Extract language-related lines without including personal information."""

    lines = _extract_section_lines(cv_sections, "languages")
    languages: list[str] = []

    proficiency_levels = ("A1", "A2", "B1", "B2", "C1", "C2")

    for index, line in enumerate(lines):
        normalized = line.strip()
        upper = normalized.upper()
        lower = normalized.lower()

        if lower.startswith("levels:"):
            continue

        if lower.startswith("mother tongue"):
            languages.append(normalized)
            continue

        if any(level in upper.split() for level in proficiency_levels):
            languages.append(normalized)
            continue

        next_line = lines[index + 1].upper() if index + 1 < len(lines) else ""

        if (
            ":" not in normalized
            and any(level in next_line.split() for level in proficiency_levels)
        ):
            languages.append(normalized)

    return languages


def _extract_skills(cv_sections: dict[str, str]) -> list[SkillEntry]:
    """Extract raw skills from the skills section."""

    skills_text = cv_sections.get("skills", "")

    if not skills_text.strip():
        return []

    normalized_text = " ".join(skills_text.splitlines())

    raw_skills = re.split(
        r"\s+\/\s+|\s*,\s*",
        normalized_text,
    )

    return [
        SkillEntry(name=skill.strip(), source="skills_section")
        for skill in raw_skills
        if skill.strip()
    ]


def _extract_education(cv_sections: dict[str, str]) -> list[EducationEntry]:
    """Extract generic education entries from the education section."""

    lines = _extract_section_lines(cv_sections, "education")
    entries: list[EducationEntry] = []

    for index, line in enumerate(lines):
        date_match = DATE_RANGE_PATTERN.search(line)

        if not date_match:
            continue

        degree = lines[index - 1] if index > 0 else ""
        institution = line.split("[")[0].strip()

        end_date = date_match.group("end")
        status = "current" if end_date.lower() == "current" else "completed"

        entries.append(
            EducationEntry(
                degree=degree,
                institution=institution,
                start_date=date_match.group("start"),
                end_date=end_date,
                status=status,
            )
        )

    return entries

def _extract_experience_blocks(lines: list[str]) -> list[list[str]]:
    """Split an experience section into complete experience blocks."""

    blocks: list[list[str]] = []
    pending_headers: list[str] = []
    current_block: list[str] | None = None

    for line in lines:
        cleaned_line = line.strip()

        if not cleaned_line:
            continue

        is_date = DATE_RANGE_PATTERN.search(cleaned_line) is not None
        is_highlight = cleaned_line.startswith(("-", "•"))

        if is_date:
            if current_block:
                blocks.append(current_block)

            current_block = [*pending_headers, cleaned_line]
            pending_headers = []
            continue

        if is_highlight:
            if current_block:
                current_block.append(cleaned_line)
            continue

        # A normal line after an existing experience block
        # indicates the beginning of the next experience header.
        if current_block:
            blocks.append(current_block)
            current_block = None

        pending_headers.append(cleaned_line)

    if current_block:
        blocks.append(current_block)

    return blocks

def _extract_experience(cv_sections: dict[str, str]) -> list[ExperienceEntry]:
    """Extract generic experience entries from the experience section."""

    lines = _extract_section_lines(cv_sections, "experience")
    blocks = _extract_experience_blocks(lines)

    return [
        entry
        for block in blocks
        if (entry := _parse_experience_block(block)) is not None
    ]

def _parse_experience_block(block: list[str]) -> ExperienceEntry | None:
    """Parse a single experience block."""

    date_index = next(
        (
            index
            for index, line in enumerate(block)
            if DATE_RANGE_PATTERN.search(line)
        ),
        None,
    )

    if date_index is None:
        return None

    date_line = block[date_index]
    date_match = DATE_RANGE_PATTERN.search(date_line)

    if date_match is None:
        return None

    header_lines = block[:date_index]
    highlight_lines = block[date_index + 1 :]

    organization_line = header_lines[0] if header_lines else ""
    title = header_lines[1] if len(header_lines) > 1 else ""

    organization, location = _split_organization_location(
        organization_line
    )

    highlights = [
        line.lstrip("-•").strip()
        for line in highlight_lines
        if line.lstrip().startswith(("-", "•"))
    ]

    return ExperienceEntry(
        organization=organization,
        title=title,
        start_date=date_match.group("start"),
        end_date=date_match.group("end"),
        location=location,
        highlights=highlights,
    )

def _split_organization_location(line: str) -> tuple[str, str]:
    """Split an organization line into organization and location."""

    cleaned_line = line.replace("", "").strip()

    if "–" in cleaned_line:
        organization, location = cleaned_line.split("–", maxsplit=1)
        return organization.strip(), location.strip()

    if "-" in cleaned_line:
        organization, location = cleaned_line.split("-", maxsplit=1)
        return organization.strip(), location.strip()

    return cleaned_line, ""