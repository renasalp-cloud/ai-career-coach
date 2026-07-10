"""Build prompts for career assessment."""

import json
from dataclasses import dataclass

from app.candidate_profile.models import CandidateProfile


@dataclass(frozen=True)
class PromptContext:
    """Data required to build a CV analysis prompt."""

    prompt_template: str
    target_role: str
    role_profile: str
    candidate_profile: CandidateProfile


def build_cv_analysis_prompt(context: PromptContext) -> str:
    """Build the full candidate analysis prompt."""

    formatted_candidate_profile = json.dumps(
        context.candidate_profile.model_dump(),
        indent=2,
        ensure_ascii=False,
    )

    return f"""
{context.prompt_template}

Target Role:
{context.target_role}

Role Profile:
{context.role_profile}

Candidate Profile:
<CANDIDATE_PROFILE>
{formatted_candidate_profile}
</CANDIDATE_PROFILE>
"""