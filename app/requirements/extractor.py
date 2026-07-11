"""Extract generic requirement profiles from requirement source text."""

from app.models import RequirementProfile, RequirementSkill


SECTION_PRIORITIES = {
    "Critical Skills:": "required",
    "Important Skills:": "preferred",
    "Optional Skills:": "optional",
}


def extract_requirement_profile(
    target_role: str,
    role_profile_text: str,
) -> RequirementProfile:
    """Extract a source-agnostic requirement profile from local role profile text."""

    skills: list[RequirementSkill] = []
    current_priority: str | None = None

    for line in role_profile_text.splitlines():
        stripped_line = line.strip()

        if not stripped_line:
            continue

        if stripped_line.endswith(":"):
            current_priority = SECTION_PRIORITIES.get(stripped_line)
            continue

        if current_priority is not None and stripped_line.startswith("- "):
            skills.append(
                RequirementSkill(
                    name=stripped_line[2:].strip(),
                    priority=current_priority,
                )
            )

    return RequirementProfile(
        title=target_role,
        skills=skills,
        source="local_role_profile",
    )
