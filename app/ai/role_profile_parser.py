"""Parse role profile content into deterministic application data."""


def extract_required_skills(role_profile: str) -> list[str]:
    """Extract bullet-listed skills from the Required Skills section."""

    required_skills: list[str] = []
    in_required_skills = False

    for line in role_profile.splitlines():
        stripped_line = line.strip()

        if not stripped_line:
            continue

        if stripped_line.endswith(":"):
            in_required_skills = stripped_line == "Required Skills:"
            continue

        if in_required_skills and stripped_line.startswith("- "):
            required_skills.append(stripped_line[2:].strip())

    return required_skills
