"""Build prompts for career assessment."""

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PromptContext:
    """Data required to build a CV analysis prompt."""

    prompt_template: str
    target_role: str
    role_profile: str
    cv_sections: dict[str, Any]


def build_cv_analysis_prompt(context: PromptContext) -> str:
    """Build the full CV analysis prompt."""

    formatted_cv_sections = json.dumps(
        context.cv_sections,
        indent=2,
        ensure_ascii=False,
    )

    return f"""
{context.prompt_template}

Target Role:
{context.target_role}

Role Profile:
{context.role_profile}

Candidate CV Sections:
<CV>
{formatted_cv_sections}
</CV>
"""