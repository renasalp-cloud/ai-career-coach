"""CV analysis logic using the configured AI provider."""

import json
from pathlib import Path
from app.models import CareerAnalysis
from app.cv_parser import parse_cv
from app.ai.prompt_builder import PromptContext, build_cv_analysis_prompt

from app.ai.ollama_provider import generate


PROMPT_PATH = Path("app/prompts/cv_analysis.txt")

ROLE_PROFILE_DIR = Path("app/role_profiles")

def load_role_profile(target_role: str) -> str:
    """Load a role profile if one exists for the target role."""
    normalized_role = target_role.lower().strip().replace(" ", "_")
    profile_path = ROLE_PROFILE_DIR / f"{normalized_role}.txt"

    if profile_path.exists():
        return profile_path.read_text(encoding="utf-8")

    return "No predefined role profile available."

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
    role_profile = load_role_profile(target_role)

    prompt_context = PromptContext(
        prompt_template=prompt_template,
        target_role=target_role,
        role_profile=role_profile,
        cv_sections=cv_sections,
    )

    prompt = build_cv_analysis_prompt(prompt_context)

    response_text = generate(prompt)

    json_text = extract_json(response_text)

    analysis = CareerAnalysis.model_validate_json(json_text)
    return analysis.model_dump()