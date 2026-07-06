"""CV analysis logic using the configured AI provider."""

import json
from pathlib import Path
from app.models import CareerAnalysis
from app.cv_parser import parse_cv

from app.ai.ollama_provider import generate


PROMPT_PATH = Path("app/prompts/cv_analysis.txt")

def extract_json(text: str) -> str:
    """Extract JSON from an AI response."""

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:].strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    return text


def analyze_cv(cv_text: str, target_role: str) -> dict:
    """Analyze a CV for a target role and return structured data."""

    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    cv_sections = parse_cv(cv_text)

    prompt = f"""
{prompt_template}

Target Role:
{target_role}

 Structured CV Sections:
<CV>
{cv_sections}
</CV>
"""

    response_text = generate(prompt)

    json_text = extract_json(response_text)

    analysis = CareerAnalysis.model_validate_json(json_text)
    return analysis.model_dump()