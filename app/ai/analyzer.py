"""CV analysis logic using the configured AI provider."""

import json
import re

from pathlib import Path
from app.models import CareerAnalysis
from app.cv_parser import parse_cv
from app.ai.prompt_builder import PromptContext, build_cv_analysis_prompt
from app.candidate_profile.models import CandidateProfile
from app.candidate_profile.extractor import extract_candidate_profile
from app.candidate_profile.normalizer import normalize_candidate_profile

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


def _normalize_skill_name(value: str) -> str:
    """Normalize a skill name for exact canonical comparison."""

    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _remove_existing_skills_from_gaps(
    analysis: CareerAnalysis,
    candidate_profile: CandidateProfile,
) -> CareerAnalysis:
    """Remove missing skills already present in the canonical candidate profile."""

    existing_skills = {
        _normalize_skill_name(skill.name)
        for skill in candidate_profile.skills
        if skill.name.strip()
    }

    for group_name in ("critical", "important", "optional"):
        missing_group = getattr(analysis.missing_skills, group_name)

        filtered_group = [
            item
            for item in missing_group
            if _normalize_skill_name(item.skill) not in existing_skills
        ]

        setattr(analysis.missing_skills, group_name, filtered_group)

    return analysis


def analyze_cv(cv_text: str, target_role: str) -> dict:
    """Analyze a CV for a target role and return structured data."""

    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")

    cv_sections = parse_cv(cv_text)
    candidate_profile = extract_candidate_profile(cv_sections)
    candidate_profile = normalize_candidate_profile(candidate_profile)

    role_profile = load_role_profile(target_role)

    prompt_context = PromptContext(
        prompt_template=prompt_template,
        target_role=target_role,
        role_profile=role_profile,
        candidate_profile=candidate_profile,
    )

    prompt = build_cv_analysis_prompt(prompt_context)

    response_text = generate(prompt)
    json_text = extract_json(response_text)

    analysis = CareerAnalysis.model_validate_json(json_text)
    analysis = _remove_existing_skills_from_gaps(
        analysis,
        candidate_profile,
    )

    return analysis.model_dump()