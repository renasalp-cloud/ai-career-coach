from app.pdf_reader import extract_text
from app.ai.analyzer import analyze_cv


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
        cv_text = extract_text(cv_path)

        print("\nAnalyzing CV...\n")

        analysis = analyze_cv(cv_text, target_role)

        print_analysis(analysis)

    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()