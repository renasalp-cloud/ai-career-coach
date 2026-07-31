"""Normalize safe presentation variations before Pydantic validation."""

import re
from typing import Any


PLACEHOLDER = re.compile(
    r"^(?:no\s+information\s+available|not\s+provided|none|n/?a|unknown)\s*[.:;-]*$",
    re.IGNORECASE,
)
WRAPPED_SUFFIX = re.compile(
    r"\b([A-Za-z]{3,})[ \t]+(s|ls|es|ed|er|ers|ing|ion|ions|ly|ment|ments|ness|ths)\b"
)


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


def normalize_final_career_analysis_output(data: Any, candidate_summary: str) -> Any:
    """Normalize the final presentation fields after all analysis processors."""

    normalized = normalize_career_analysis_output(data)
    if not isinstance(normalized, dict):
        return normalized

    if not normalized.get("professional_summary"):
        summary = normalize_presentation_text(candidate_summary)
        if summary:
            normalized["professional_summary"] = summary
    return normalized


def _strip_strings(value: Any) -> Any:
    if isinstance(value, str):
        return normalize_presentation_text(value)
    if isinstance(value, list):
        return [_strip_strings(item) for item in value]
    if isinstance(value, dict):
        return {key: _strip_strings(item) for key, item in value.items()}
    return value


def normalize_presentation_text(value: str) -> str:
    """Remove non-content artifacts without adding or interpreting facts."""

    text = " ".join(value.split())
    if PLACEHOLDER.fullmatch(text):
        return ""
    text = WRAPPED_SUFFIX.sub(r"\1\2", text)
    text = re.sub(r"([.!?])(?:\s*\1)+", r"\1", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip()


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
