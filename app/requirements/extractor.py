"""Extract generic requirement profiles from requirement source text."""

from app.models import RequirementProfile, RequirementSkill


SECTION_PRIORITIES = {
    "critical skills": "required",
    "important skills": "preferred",
    "optional skills": "optional",
    "requirements": "required",
    "required qualifications": "required",
    "must have": "required",
    "must-have": "required",
    "minimum qualifications": "required",
    "essential skills": "required",
    "required skills": "required",
    "key skills": "required",
    "skills": "required",
    "core skills": "required",
    "technical skills": "required",
    "qualifications": "required",
    "preferred qualifications": "preferred",
    "preferred": "preferred",
    "nice to have": "preferred",
    "nice-to-have": "preferred",
    "preferred skills": "preferred",
    "desired skills": "preferred",
    "additional qualifications": "preferred",
    "bonus skills": "optional",
    "advantageous skills": "optional",
}

RESPONSIBILITY_SECTIONS = {
    "responsibilities",
    "key responsibilities",
    "what you will do",
    "what you'll do",
    "your role",
}

INTRODUCTORY_SECTIONS = {
    "about the job",
    "location",
    "salary",
    "company description",
}

BULLET_MARKERS = {"-", "*", "•"}


def extract_requirement_profile(
    target_role: str,
    role_profile_text: str,
) -> RequirementProfile:
    """Extract a source-agnostic requirement profile from requirement text."""

    skills: list[RequirementSkill] = []
    seen_requirements: set[str] = set()
    current_priority: str | None = None

    for line in role_profile_text.splitlines():
        stripped_line = line.strip()

        if not stripped_line:
            continue

        content_line = stripped_line
        if content_line[:1] in BULLET_MARKERS:
            content_line = content_line[1:].strip()

        heading = content_line.removesuffix(":").strip().casefold()
        if heading in SECTION_PRIORITIES:
            current_priority = SECTION_PRIORITIES[heading]
            continue

        if (
            heading in RESPONSIBILITY_SECTIONS
            or heading in INTRODUCTORY_SECTIONS
            or stripped_line.endswith(":")
        ):
            current_priority = None
            continue

        if current_priority is not None:
            requirement_name = content_line
            requirement_key = requirement_name.casefold()
            if not requirement_name or requirement_key in seen_requirements:
                continue

            skills.append(
                RequirementSkill(
                    name=requirement_name,
                    priority=current_priority,
                )
            )
            seen_requirements.add(requirement_key)

    return RequirementProfile(
        title=target_role,
        skills=skills,
        source="extracted_requirement_text",
    )
