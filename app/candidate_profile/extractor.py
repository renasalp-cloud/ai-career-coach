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
EDUCATION_YEAR_RANGE_PATTERN = re.compile(
    r"^(?P<start>\d{4})\s*[-–]\s*"
    r"(?P<end>\d{4}|Present|Current|Ongoing|In Progress|Expected\s+\d{4})$",
    re.IGNORECASE,
)
EDUCATION_INLINE_YEAR_RANGE_PATTERN = re.compile(
    r"^(?P<institution>.+?)\s*(?:\||•)\s*"
    r"(?P<start>\d{4})\s*[-–]\s*"
    r"(?P<end>\d{4}|Present|Current|Ongoing|In Progress|Expected\s+\d{4})$",
    re.IGNORECASE,
)
EDUCATION_ACTIVE_MARKER_PATTERN = re.compile(
    r"^(?:Present|Current|Ongoing|In Progress|Expected\s+\d{4})$",
    re.IGNORECASE,
)
EDUCATION_DEGREE_PATTERN = re.compile(
    r"\b(?:bachelor|master|doctor|phd|degree|diploma|certificate)\b",
    re.IGNORECASE,
)
EDUCATION_INSTITUTION_PATTERN = re.compile(
    r"\b(?:university|college|institute|academy|school)\b",
    re.IGNORECASE,
)
EDUCATION_COMBINED_LINE_PATTERN = re.compile(r"^(?P<left>.+?)\s+[\-\u2013]\s+(?P<right>.+)$")
EXPERIENCE_YEAR_RANGE_PATTERN = re.compile(
    r"^(?P<start>\d{4})\s*[-–]\s*(?P<end>\d{4}|Present|Current)$",
    re.IGNORECASE,
)
EXPERIENCE_DATE_FIRST_RANGE_PATTERN = re.compile(
    r"^(?P<start>\d{2}/\d{4}|\d{2}/\d{2}/\d{4}|\d{4})\s*[-–]\s*"
    r"(?P<end>\d{2}/\d{4}|\d{2}/\d{2}/\d{4}|\d{4}|Present|Current)$",
    re.IGNORECASE,
)
EXPERIENCE_HEADER_DELIMITER_PATTERN = re.compile(r"\s+(?:-|–|\|)\s+")
EXPERIENCE_BULLET_MARKERS = ("-", "•", "●")
SKILL_PROSE_PATTERNS = (
    re.compile(
        r"^(?:.+\band )?experience working with (?P<values>.+)\.$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:.+\band )?experience with (?P<values>.+)\.$",
        re.IGNORECASE,
    ),
    re.compile(r"^Skills in (?P<values>.+)\.$", re.IGNORECASE),
    re.compile(r"^Good (?P<values>.+) skills\.$", re.IGNORECASE),
    re.compile(r"^Knowledge of (?P<values>.+)\.$", re.IGNORECASE),
    re.compile(r"^Proficient in (?P<values>.+)\.$", re.IGNORECASE),
)
INVALID_STANDALONE_SKILL_WORDS = {
    "and",
    "analyze",
    "as well as",
    "current",
    "improvements",
    "life",
    "or",
    "people",
    "present",
    "situations",
    "the",
}
INVALID_SKILL_HEADINGS = {
    "additional information",
    "computer skills",
    "professional skills",
    "skills and strengths",
    "soft skills",
    "technical skills",
}
NARRATIVE_SKILL_PREFIXES = (
    "ability to ",
    "communication with ",
    "contribute ",
    "experience ",
    "good ",
    "knowledge of ",
    "maintaining ",
    "proficient in ",
    "skills in ",
    "stay ",
    "strong motivation ",
    "towards ",
)
NARRATIVE_SKILL_PHRASES = (
    " under pressure",
    " while ",
    " to company ",
    " to grow ",
)
DESCRIPTIVE_EVIDENCE_PATTERN = re.compile(
    r"\b(?:ability to|communicat(?:e|es|ed|ing|ion)|organiz(?:e|es|ed|ing|ation|ational)|"
    r"plann?ing|priorit(?:y|ies|ize|izes|ized|izing)|problem[- ]solving|"
    r"analy(?:se|ses|sed|sing|ze|zes|zed|zing)|responsibility|"
    r"calm under pressure|logical thinking|interpersonal|time management)\b",
    re.IGNORECASE,
)
SKILL_METADATA_LABEL_PATTERN = re.compile(
    r"^(?:country|city|website|field(?:\(s\))? of study|level in eqf|"
    r"eqf level|institution|university)\s*:",
    re.IGNORECASE,
)
URL_PATTERN = re.compile(r"^(?:https?://|www\.)\S+$", re.IGNORECASE)
EDUCATION_DATE_METADATA_PATTERN = re.compile(
    r"\[\s*\d{1,2}/\d{1,2}/\d{4}\s*[^\dA-Za-z]+\s*"
    r"(?:\d{1,2}/\d{1,2}/\d{4}|current|present)\s*\]",
    re.IGNORECASE,
)
DEGREE_METADATA_PATTERN = re.compile(
    r"\b(?:degree|diploma)\b",
    re.IGNORECASE,
)


def extract_candidate_profile(cv_sections: dict[str, str]) -> CandidateProfile:
    """Extract a generic structured candidate profile from parsed CV sections."""

    return CandidateProfile(
        summary=_extract_summary(cv_sections),
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
    named_proficiency_pattern = re.compile(
        r"\((?:basic|beginner|elementary|intermediate|advanced|"
        r"proficient|fluent|native)\)",
        re.IGNORECASE,
    )

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

        if named_proficiency_pattern.search(normalized):
            languages.append(normalized)
            continue

        next_line = lines[index + 1].upper() if index + 1 < len(lines) else ""

        if (
            ":" not in normalized
            and any(level in next_line.split() for level in proficiency_levels)
        ):
            languages.append(normalized)

    return languages


def _extract_summary(cv_sections: dict[str, str]) -> str:
    """Retain profile text and explicit capability evidence from descriptive sections."""

    evidence = _extract_section_lines(cv_sections, "profile")
    for section_name in ("skills", "additional_information"):
        evidence.extend(
            line
            for line in _extract_section_lines(cv_sections, section_name)
            if DESCRIPTIVE_EVIDENCE_PATTERN.search(line)
        )
    return "\n".join(dict.fromkeys(evidence))


def _extract_skills(cv_sections: dict[str, str]) -> list[SkillEntry]:
    """Extract raw skills from the skills section."""

    skills_text = cv_sections.get("skills", "")

    if not skills_text.strip():
        return []

    return [
        SkillEntry(name=skill, source="skills_section")
        for line in _extract_skill_statements(skills_text)
        for skill in _extract_skill_line(line)
    ]


def _extract_skill_statements(skills_text: str) -> list[str]:
    """Join bounded skill prose and conservatively wrapped skill labels."""

    statements: list[str] = []
    pending = ""
    lines = [line.strip() for line in skills_text.splitlines() if line.strip()]

    for index, cleaned_line in enumerate(lines):
        if _is_skill_metadata(cleaned_line):
            if pending:
                statements.append(pending)
                pending = ""
            continue

        if pending:
            pending = f"{pending} {cleaned_line}"
            if (
                cleaned_line.endswith((".", "!", "?"))
                or not _continues_skill_line(cleaned_line, lines, index)
            ):
                statements.append(pending)
                pending = ""
            continue

        if (
            _starts_explicit_skill_prose(cleaned_line)
            and not cleaned_line.endswith((".", "!", "?"))
        ) or _continues_skill_line(cleaned_line, lines, index):
            pending = cleaned_line
        else:
            statements.append(cleaned_line)

    if pending:
        statements.append(pending)

    return statements


def _continues_skill_line(line: str, lines: list[str], index: int) -> bool:
    """Return whether the next extracted line is a bounded continuation."""

    if index + 1 >= len(lines) or _is_skill_metadata(lines[index + 1]):
        return False

    next_line = lines[index + 1]
    if line.rstrip().endswith(("&", "/")):
        return True
    if (
        next_line[:1].islower()
        and line[:1].isupper()
        and (
            "/" in line
            or any(
                any(character.isupper() for character in word[1:])
                for word in line.split()
            )
        )
    ):
        return True
    return bool(
        len(line.split()) >= 3
        and re.search(r"\b(?:and|or)\s+\S+$", line, re.IGNORECASE)
        and len(next_line.split()) <= 3
    )


def _is_skill_metadata(value: str) -> bool:
    """Reject generic education metadata and standalone web addresses."""

    normalized = value.strip().lstrip("-â€¢").strip()
    return bool(
        SKILL_METADATA_LABEL_PATTERN.match(normalized)
        or URL_PATTERN.match(normalized)
        or EDUCATION_DATE_METADATA_PATTERN.search(normalized)
        or DEGREE_METADATA_PATTERN.search(normalized)
    )


def _starts_explicit_skill_prose(line: str) -> bool:
    """Return whether a line begins a supported explicit-skill statement."""

    normalized = " ".join(line.casefold().split())
    return (
        normalized.startswith(
            (
                "experience with ",
                "experience working with ",
                "knowledge of ",
                "proficient in ",
                "skills in ",
            )
        )
        or " and experience with " in normalized
        or " and experience working with " in normalized
    )


def _extract_skill_line(line: str) -> list[str]:
    """Extract standalone skill names from one skills-section line."""

    cleaned_line = re.sub(r"^\s*(?:-|•)\s*", "", line).strip()

    if not cleaned_line or cleaned_line.casefold() == "skills":
        return []

    if ":" in cleaned_line:
        _, cleaned_line = cleaned_line.split(":", maxsplit=1)
        cleaned_line = cleaned_line.strip()

    prose_values = _extract_explicit_skill_prose(cleaned_line)
    if prose_values is not None:
        candidates = _split_explicit_skill_values(prose_values)
    elif cleaned_line.endswith((".", "!", "?")):
        return []
    else:
        candidates = _split_skill_candidates(
            cleaned_line,
            split_conjunctions=False,
        )

    return [
        skill
        for candidate in candidates
        if (skill := _clean_skill_candidate(candidate))
        and _is_standalone_skill(skill)
    ]


def _extract_explicit_skill_prose(line: str) -> str | None:
    """Return explicit values from one short, bounded skill statement."""

    if len(line) > 240 or line.count(".") != 1:
        return None

    for pattern in SKILL_PROSE_PATTERNS:
        match = pattern.fullmatch(line)
        if match:
            values = match.group("values").strip().rstrip(".,;:")
            normalized_values = f" {' '.join(values.casefold().split())} "
            if (
                values
                and len(values.split()) <= 30
                and not any(
                    phrase.strip() in normalized_values
                    for phrase in NARRATIVE_SKILL_PHRASES
                )
            ):
                return values

    return None


def _split_explicit_skill_values(values: str) -> list[str]:
    """Split explicit values while removing generic exemplar introductions."""

    parts = re.split(r"\s+\b(?:such as|including)\b\s+", values, flags=re.IGNORECASE)
    candidates: list[str] = []

    for index, part in enumerate(parts):
        part_candidates = _split_skill_candidates(part, split_conjunctions=True)
        if index < len(parts) - 1 and part_candidates:
            part_candidates.pop()
        candidates.extend(part_candidates)

    return candidates


def _split_skill_candidates(
    line: str,
    *,
    split_conjunctions: bool,
) -> list[str]:
    """Split a skill line using its established delimiters."""

    delimiter_pattern = r"\s+/\s+|\s*[,|•]\s*"
    if split_conjunctions:
        delimiter_pattern += r"|\s+\b(?:and|as well as)\b\s+"

    return re.split(delimiter_pattern, line, flags=re.IGNORECASE)


def _clean_skill_candidate(candidate: str) -> str:
    """Remove surrounding whitespace from a skill candidate."""

    return candidate.strip()


def _is_standalone_skill(value: str) -> bool:
    """Return whether a value is a conservative standalone skill label."""

    if not value or not any(character.isalnum() for character in value):
        return False

    normalized = " ".join(value.casefold().split()).strip(".,;:!?")
    if (
        not normalized
        or _is_skill_metadata(value)
        or normalized.startswith("similar ")
        or normalized in INVALID_STANDALONE_SKILL_WORDS
        or normalized in INVALID_SKILL_HEADINGS
        or normalized.startswith(NARRATIVE_SKILL_PREFIXES)
        or any(phrase in normalized for phrase in NARRATIVE_SKILL_PHRASES)
    ):
        return False

    return True


def _extract_education(cv_sections: dict[str, str]) -> list[EducationEntry]:
    """Extract generic education entries from the education section."""

    lines = _extract_section_lines(cv_sections, "education")
    entries: list[EducationEntry] = []

    pending_content: list[str] = []
    current_date: re.Match[str] | None = None
    current_content: list[str] = []

    def append_entry(date_match: re.Match[str], content: list[str], *, date_first: bool) -> None:
        entry = _build_education_entry(date_match, content, date_first=date_first)
        if entry is not None:
            entries.append(entry)

    for line in lines:
        inline_match = EDUCATION_INLINE_YEAR_RANGE_PATTERN.fullmatch(line)
        full_date_match = DATE_RANGE_PATTERN.search(line)
        standalone_match = EDUCATION_YEAR_RANGE_PATTERN.fullmatch(line)
        date_match = inline_match or full_date_match or standalone_match

        if not date_match:
            if current_date is not None:
                current_content.append(line)
            else:
                pending_content.append(line)
            continue

        if current_date is not None:
            append_entry(current_date, current_content, date_first=True)
            current_date = None
            current_content = []

        inline_content = ""
        if inline_match:
            inline_content = inline_match.group("institution").strip()
        elif full_date_match:
            inline_content = line[:full_date_match.start()].strip()

        if inline_content or pending_content:
            content = [*pending_content]
            if inline_content:
                content.append(inline_content)
            append_entry(date_match, content, date_first=False)
            pending_content = []
        else:
            current_date = date_match

    if current_date is not None:
        append_entry(current_date, current_content, date_first=True)

    return entries


def _build_education_entry(
    date_match: re.Match[str], content: list[str], *, date_first: bool
) -> EducationEntry | None:
    """Build one education entry from content bounded by a single date range."""

    if not content:
        return None

    start_date = date_match.group("start")
    end_date = date_match.group("end")
    if end_date.isdigit() and start_date.isdigit() and int(start_date) > int(end_date):
        return None

    degree, institution = _education_fields(content, date_first=date_first)
    if not degree and not institution:
        return None

    status = (
        "current"
        if EDUCATION_ACTIVE_MARKER_PATTERN.fullmatch(end_date.strip())
        else "completed"
    )
    return EducationEntry(
        degree=degree,
        institution=institution,
        start_date=start_date,
        end_date=end_date,
        status=status,
    )


def _education_fields(content: list[str], *, date_first: bool) -> tuple[str, str]:
    """Conservatively assign degree and institution within one education record."""

    cleaned = [line.strip() for line in content if line.strip()]
    if len(cleaned) == 1:
        combined_match = EDUCATION_COMBINED_LINE_PATTERN.fullmatch(cleaned[0])
        if (
            combined_match
            and EDUCATION_INSTITUTION_PATTERN.search(combined_match.group("left"))
            and EDUCATION_DEGREE_PATTERN.search(combined_match.group("right"))
        ):
            return combined_match.group("right"), combined_match.group("left")
        if EDUCATION_DEGREE_PATTERN.search(cleaned[0]):
            return cleaned[0], ""
        return "", cleaned[0]

    if date_first:
        institution, degree = cleaned[0], cleaned[1]
    else:
        degree, institution = cleaned[-2], cleaned[-1]
    return degree, institution

def _extract_experience_blocks(lines: list[str]) -> list[list[str]]:
    """Split an experience section into complete experience blocks."""

    blocks: list[list[str]] = []
    pending_headers: list[str] = []
    current_block: list[str] | None = None

    for line in lines:
        cleaned_line = line.strip()

        if not cleaned_line:
            continue

        is_date = _match_experience_date(cleaned_line) is not None
        is_highlight = cleaned_line.startswith(EXPERIENCE_BULLET_MARKERS)

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

        # A date-first block accepts one conservatively delimited header line.
        if (
            current_block
            and len(current_block) == 1
            and _match_experience_date(current_block[0]) is not None
        ):
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
            if _match_experience_date(line)
        ),
        None,
    )

    if date_index is None:
        return None

    date_line = block[date_index]
    date_match = _match_experience_date(date_line)

    if date_match is None:
        return None

    if date_index == 0:
        if len(block) < 2:
            return None
        organization_line, title = _split_date_first_experience_header(block[1])
        highlight_lines = block[2:]
    else:
        header_lines = block[:date_index]
        highlight_lines = block[date_index + 1 :]
        if len(header_lines) != 2:
            return None
        organization_line, title = _resolve_experience_headers(header_lines)

    if not organization_line or not title:
        return None

    organization, location = _split_organization_location(
        organization_line
    )
    if not organization:
        return None

    highlights = [
        line[1:].strip()
        for line in highlight_lines
        if line.startswith(EXPERIENCE_BULLET_MARKERS) and line[1:].strip()
    ]

    return ExperienceEntry(
        organization=organization,
        title=title,
        start_date=date_match.group("start"),
        end_date=date_match.group("end"),
        location=location,
        highlights=highlights,
    )

def _match_experience_date(line: str) -> re.Match[str] | None:
    """Match a supported complete experience date range."""

    date_match = DATE_RANGE_PATTERN.search(line)
    if date_match is None:
        date_match = EXPERIENCE_YEAR_RANGE_PATTERN.fullmatch(line)
    if date_match is None:
        date_match = EXPERIENCE_DATE_FIRST_RANGE_PATTERN.fullmatch(line)

    if date_match is None:
        return None

    start_date = date_match.group("start")
    end_date = date_match.group("end")
    start_key = _experience_date_sort_key(start_date)
    end_key = _experience_date_sort_key(end_date)
    if start_key is None or (
        end_key is not None
        and start_key > end_key
    ):
        return None

    return date_match

def _experience_date_sort_key(value: str) -> tuple[int, int, int] | None:
    """Return a comparable key for a supported experience date."""

    if value.casefold() in {"present", "current"}:
        return None

    parts = value.split("/")
    try:
        if len(parts) == 1:
            return int(parts[0]), 1, 1
        if len(parts) == 2:
            month, year = (int(part) for part in parts)
            if not 1 <= month <= 12:
                return None
            return year, month, 1
        if len(parts) == 3:
            day, month, year = (int(part) for part in parts)
            if not 1 <= month <= 12 or not 1 <= day <= 31:
                return None
            return year, month, day
    except ValueError:
        return None

    return None

def _split_date_first_experience_header(line: str) -> tuple[str, str]:
    """Split a date-first organization/title line on one clear delimiter."""

    parts = EXPERIENCE_HEADER_DELIMITER_PATTERN.split(line.strip())
    if len(parts) != 2:
        return "", ""

    organization, title = (part.strip() for part in parts)
    if not organization or not title:
        return "", ""

    return organization, title

def _resolve_experience_headers(header_lines: list[str]) -> tuple[str, str]:
    """Resolve organization and title from two conservative header forms."""

    first, second = header_lines[-2:]

    # A single-word first line followed by a multi-word second line is the
    # narrow supported title-first form. Other layouts retain the established
    # organization-first interpretation.
    if len(first.split()) == 1 and len(second.split()) > 1:
        return second, first

    return first, second

def _split_organization_location(line: str) -> tuple[str, str]:
    """Split an organization line into organization and location."""

    cleaned_line = line.replace("", "").strip()

    if "|" in cleaned_line:
        organization, location = cleaned_line.split("|", maxsplit=1)
        return organization.strip(), location.strip()

    if "–" in cleaned_line:
        organization, location = cleaned_line.split("–", maxsplit=1)
        return organization.strip(), location.strip()

    if "-" in cleaned_line:
        organization, location = cleaned_line.split("-", maxsplit=1)
        return organization.strip(), location.strip()

    return cleaned_line, ""
