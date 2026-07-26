"""Normalize safe formatting variations before Pydantic validation."""

from typing import Any


def normalize_career_analysis_output(data: Any) -> Any:
    """Normalize formatting without creating or reinterpreting semantic content."""

    if not isinstance(data, dict):
        return data

    normalized = _strip_strings(data)
    recommendations = normalized.get("recommendations")
    if isinstance(recommendations, list):
        normalized["recommendations"] = [
            _normalize_recommendation_priority(item) for item in recommendations
        ]
    return normalized


def _strip_strings(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return [_strip_strings(item) for item in value]
    if isinstance(value, dict):
        return {key: _strip_strings(item) for key, item in value.items()}
    return value


def _normalize_recommendation_priority(value: Any) -> Any:
    if not isinstance(value, dict):
        return value

    normalized = dict(value)
    priority = normalized.get("priority")
    if not isinstance(priority, str):
        return normalized

    mapping = {
        "critical": "high",
        "required": "high",
        "important": "medium",
        "preferred": "medium",
        "optional": "low",
    }
    normalized["priority"] = mapping.get(priority.casefold(), priority.casefold())
    return normalized
