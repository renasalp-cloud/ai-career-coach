"""Normalize imperfect LLM output before Pydantic validation."""

from typing import Any


def normalize_career_analysis_output(data: Any) -> Any:
    """Normalize common structural mistakes in CareerAnalysis output."""

    if not isinstance(data, dict):
        return data

    normalized = dict(data)

    normalized["missing_skills"] = _normalize_missing_skills(
        normalized.get("missing_skills")
    )
    normalized["recommendations"] = _normalize_recommendations(
        normalized.get("recommendations")
    )
    normalized["learning_roadmap"] = _normalize_learning_roadmap(
        normalized.get("learning_roadmap")
    )
    normalized["career_gap_analysis"] = _normalize_career_gap_analysis(
        normalized.get("career_gap_analysis")
    )

    return normalized


def _normalize_missing_skills(value: Any) -> dict[str, list[dict[str, str]]]:
    result = {
        "critical": [],
        "important": [],
        "optional": [],
    }

    if isinstance(value, list):
        result["critical"] = [
            item
            for item in (_normalize_missing_skill(item) for item in value)
            if item is not None
        ]
        return result

    if not isinstance(value, dict):
        return result

    for category in result:
        items = value.get(category, [])

        if not isinstance(items, list):
            continue

        result[category] = [
            item
            for item in (_normalize_missing_skill(item) for item in items)
            if item is not None
        ]

    return result


def _normalize_missing_skill(value: Any) -> dict[str, str] | None:
    if isinstance(value, str):
        return {
            "skill": value,
            "reason": "",
        }

    if not isinstance(value, dict):
        return None

    skill = value.get("skill") or value.get("name") or value.get("title") or ""
    reason = value.get("reason") or value.get("description") or ""

    return {
        "skill": str(skill),
        "reason": str(reason),
    }


def _normalize_recommendations(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []

    recommendations: list[dict[str, str]] = []

    for item in value:
        if isinstance(item, str):
            recommendations.append(
                {
                    "priority": "",
                    "title": item,
                    "reason": "",
                    "action": item,
                }
            )
            continue

        if not isinstance(item, dict):
            continue

        priority = _normalize_priority(item.get("priority"))
        title = item.get("title") or item.get("skill") or ""
        reason = item.get("reason") or item.get("description") or ""
        action = item.get("action") or item.get("description") or title

        recommendations.append(
            {
                "priority": priority,
                "title": str(title),
                "reason": str(reason),
                "action": str(action),
            }
        )

    return recommendations


def _normalize_priority(value: Any) -> str:
    if value is None:
        return ""

    priority = str(value).strip().lower()

    mapping = {
        "critical": "high",
        "required": "high",
        "important": "medium",
        "preferred": "medium",
        "optional": "low",
    }

    return mapping.get(priority, priority)


def _normalize_learning_roadmap(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    roadmap: list[dict[str, Any]] = []

    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            continue

        week = item.get("week") or item.get("step") or index
        goal = item.get("goal") or item.get("goals") or item.get("action") or ""
        topics = item.get("topics", [])

        if isinstance(topics, str):
            topics = [topics]

        if not isinstance(topics, list):
            topics = []

        practical_task = (
            item.get("practical_task")
            or item.get("action")
            or item.get("task")
            or ""
        )
        expected_outcome = (
            item.get("expected_outcome")
            or item.get("outcome")
            or ""
        )

        roadmap.append(
            {
                "week": _to_int(week, index),
                "goal": str(goal),
                "topics": [str(topic) for topic in topics],
                "practical_task": str(practical_task),
                "expected_outcome": str(expected_outcome),
            }
        )

    return roadmap


def _normalize_career_gap_analysis(value: Any) -> str:
    if isinstance(value, str):
        return value

    if not isinstance(value, list):
        return ""

    parts: list[str] = []

    for item in value:
        if isinstance(item, str):
            parts.append(item)
            continue

        if not isinstance(item, dict):
            continue

        title = item.get("title") or item.get("skill") or ""
        status = item.get("status") or ""
        evidence = item.get("evidence") or ""

        text = " - ".join(
            str(part)
            for part in (title, status, evidence)
            if part not in ("", None)
        )

        if text:
            parts.append(text)

    return "; ".join(parts)


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default