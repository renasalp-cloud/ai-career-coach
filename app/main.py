from app.pdf_reader import extract_text
from app.ai.analyzer import analyze_cv
from app.candidate_profile.models import CandidateProfile
from app.cv_parser import parse_cv
from app.requirements.pipeline import RequirementPipeline
from app.requirements.source import RequirementSource, RequirementSourceType


def _read_pasted_requirement_text(input_func=input) -> str:
    """Read job-description lines until a line containing only END."""
    print("Paste the job description. Enter END on its own line when finished:")
    lines = []
    while True:
        line = input_func()
        if line.strip() == "END":
            return "\n".join(lines)
        lines.append(line)


def collect_requirement_source(target_role: str, input_func=input) -> RequirementSource:
    """Collect a supported requirement source from interactive CLI input."""
    print("\nRequirement source:")
    print("1. Paste job description")
    print("2. Job-description TXT file")
    selection = input_func("Select requirement source (1 or 2): ").strip()

    if selection == "1":
        content = _read_pasted_requirement_text(input_func)
        return RequirementSource(
            source_type=RequirementSourceType.PASTED_TEXT,
            content=content,
            name="Pasted job description",
            target_role=target_role,
        )

    if selection == "2":
        path = input_func("Job-description TXT file path: ").strip()
        return RequirementSource(
            source_type=RequirementSourceType.TEXT_FILE,
            content=path,
            name=path,
            target_role=target_role,
        )

    raise ValueError("Invalid requirement source selection. Enter 1 or 2.")

def _format_value(value) -> str:
    if value is None:
        return "Not provided."

    if isinstance(value, str):
        text = value.strip()
        return text if text else "Not provided."

    if isinstance(value, list):
        if not value:
            return "Not provided."
        return ", ".join(_format_value(item) for item in value)

    if isinstance(value, dict):
        if not value:
            return "Not provided."
        return "; ".join(
            f"{str(key).replace('_', ' ').title()}: {_format_value(item)}"
            for key, item in value.items()
        )

    return str(value)


def _print_section(title: str, value) -> None:
    print(f"\n{title}:")
    print(_format_value(value))


def _print_bullets(items, formatter) -> None:
    if not items:
        print("Not provided.")
        return

    for item in items:
        print(f"- {formatter(item)}")


def print_candidate_profile(candidate_profile: CandidateProfile) -> None:
    print("=" * 60)
    print("Candidate Profile")

    _print_section("Summary", candidate_profile.summary)

    print("\nEducation:")
    _print_bullets(
        candidate_profile.education,
        lambda item: " | ".join(
            part
            for part in (
                _format_value(item.degree),
                _format_value(item.institution),
                f"{_format_value(item.start_date)} - {_format_value(item.end_date)}",
                _format_value(item.status),
            )
            if part != "Not provided."
        ) or "Not provided.",
    )

    print("\nExperience:")
    _print_bullets(
        candidate_profile.experience,
        lambda item: " | ".join(
            part
            for part in (
                _format_value(item.title),
                _format_value(item.organization),
                f"{_format_value(item.start_date)} - {_format_value(item.end_date)}",
                _format_value(item.location),
                _format_value(item.highlights),
            )
            if part != "Not provided."
        ) or "Not provided.",
    )

    _print_section("Projects", candidate_profile.projects)
    _print_section("Skills", [skill.name for skill in candidate_profile.skills])
    _print_section("Languages", candidate_profile.languages)
    _print_section("Certifications", candidate_profile.certifications)

    print("=" * 60)


def _print_strengths(strengths) -> None:
    print("\nStrengths:")

    if not strengths:
        print("Not provided.")
        return

    for item in strengths:
        if isinstance(item, dict):
            title = _format_value(item.get("title"))
            evidence = _format_value(item.get("evidence"))
            if title == "Not provided." and evidence == "Not provided.":
                print("- Not provided.")
            elif evidence == "Not provided.":
                print(f"- {title}")
            else:
                print(f"- {title}: {evidence}")
        else:
            print(f"- {_format_value(item)}")


def _print_missing_skill_group(label: str, skills) -> None:
    print(f"  {label}:")

    if not skills:
        print("  Not provided.")
        return

    for item in skills:
        if isinstance(item, dict):
            skill = _format_value(item.get("skill"))
            reason = _format_value(item.get("reason"))
            if skill == "Not provided." and reason == "Not provided.":
                print("  - Not provided.")
            elif reason == "Not provided.":
                print(f"  - {skill}")
            else:
                print(f"  - {skill}: {reason}")
        else:
            print(f"  - {_format_value(item)}")


def _print_missing_skills(missing_skills) -> None:
    print("\nMissing Skills:")

    if not isinstance(missing_skills, dict) or not missing_skills:
        print("Not provided.")
        return

    for level in ("critical", "important", "optional"):
        _print_missing_skill_group(level.title(), missing_skills.get(level))


def _print_recommendations(recommendations) -> None:
    print("\nRecommendations:")

    if not recommendations:
        print("Not provided.")
        return

    for item in recommendations:
        if isinstance(item, dict):
            priority = _format_value(item.get("priority"))
            title = _format_value(item.get("title"))
            reason = _format_value(item.get("reason"))
            action = _format_value(item.get("action"))

            if priority != "Not provided.":
                print(f"- Priority: {priority}")
            if title != "Not provided.":
                print(f"  Title: {title}")
            if reason != "Not provided.":
                print(f"  Reason: {reason}")
            if action != "Not provided.":
                print(f"  Action: {action}")

            if all(value == "Not provided." for value in (priority, title, reason, action)):
                print("- Not provided.")
        else:
            print(f"- {_format_value(item)}")


def _print_learning_roadmap(learning_roadmap) -> None:
    print("\nLearning Roadmap:")

    if not learning_roadmap:
        print("Not provided.")
        return

    for index, item in enumerate(learning_roadmap, start=1):
        if isinstance(item, dict):
            week = _format_value(item.get("week"))
            if week == "Not provided.":
                week = str(index)

            print(f"- Week {week}")
            print(f"  Goal: {_format_value(item.get('goal'))}")
            print(f"  Topics: {_format_value(item.get('topics'))}")
            print(f"  Practical Task: {_format_value(item.get('practical_task'))}")
            print(f"  Expected Outcome: {_format_value(item.get('expected_outcome'))}")
        else:
            print(f"- {_format_value(item)}")


def print_analysis(analysis: dict) -> None:
    print("=" * 60)
    score = analysis.get("overall_match_score") if isinstance(analysis, dict) else None
    print(f"Overall Match Score: {_format_value(score)}/100" if score is not None else "Overall Match Score: Not provided.")

    _print_section("Professional Summary", analysis.get("professional_summary") if isinstance(analysis, dict) else None)
    _print_strengths(analysis.get("strengths") if isinstance(analysis, dict) else None)
    _print_missing_skills(analysis.get("missing_skills") if isinstance(analysis, dict) else None)
    _print_section("Career Gap Analysis", analysis.get("career_gap_analysis") if isinstance(analysis, dict) else None)
    _print_recommendations(analysis.get("recommendations") if isinstance(analysis, dict) else None)
    _print_learning_roadmap(analysis.get("learning_roadmap") if isinstance(analysis, dict) else None)

    print("=" * 60)


def main():
    print("Welcome to AI Career Coach")
    print("-" * 27)

    cv_path = input("Please enter your CV PDF path: ")
    target_role = input("Target role: ")

    try:
        requirement_source = collect_requirement_source(target_role, input)
    except Exception as error:
        print(f"\nRequirement source error: {error}")
        return

    try:
        requirement_profile = RequirementPipeline().build(requirement_source)
    except Exception as error:
        print(f"\nRequirement extraction error: {error}")
        return

    try:
        cv_text = extract_text(cv_path)
        
        sections = parse_cv(cv_text)

        print("\nDetected CV Sections")
        print("-" * 27)

        for section, content in sections.items():
            print(f"\n[{section.upper()}]")
            print(content[:300])

        print("\nAnalyzing CV...\n")

        analysis_result = analyze_cv(cv_text, requirement_profile, sections)

        print_candidate_profile(analysis_result.candidate_profile)
        print_analysis(analysis_result.analysis)

    except Exception as error:
        print(f"\nAnalyzer error: {error}")


if __name__ == "__main__":
    main()
