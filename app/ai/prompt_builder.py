"""Build prompts for career assessment."""

import json
from dataclasses import dataclass

from app.assessment.requirement_assessment import RequirementAssessment
from app.models import CandidateProfile, RequirementProfile, SkillMatch


@dataclass(frozen=True)
class PromptContext:
    """Data required to build a CV analysis prompt."""

    template: str
    requirement_profile: RequirementProfile
    candidate_profile: CandidateProfile
    validated_skill_matches: list[SkillMatch]
    requirement_assessment: RequirementAssessment


def build_cv_analysis_prompt(context: PromptContext) -> str:
    """Build the full candidate analysis prompt."""

    formatted_candidate_profile = json.dumps(
        context.candidate_profile.model_dump(),
        indent=2,
        ensure_ascii=False,
    )

    formatted_skill_matches = json.dumps(
        [match.model_dump() for match in context.validated_skill_matches],
        indent=2,
        ensure_ascii=False,
    )

    formatted_requirement_profile = json.dumps(
        context.requirement_profile.model_dump(),
        indent=2,
        ensure_ascii=False,
    )

    formatted_requirement_assessment = json.dumps(
        context.requirement_assessment.model_dump(),
        indent=2,
        ensure_ascii=False,
    )

    return f"""
{context.template}

# ============================================
# ANALYSIS INPUT
# ============================================

Target Role:
{context.requirement_profile.title}

Requirement Profile:
<REQUIREMENT_PROFILE>
{formatted_requirement_profile}
</REQUIREMENT_PROFILE>

Candidate Profile:
<CANDIDATE_PROFILE>
{formatted_candidate_profile}
</CANDIDATE_PROFILE>

Validated Skill Matches:
<VALIDATED_SKILL_MATCHES>
{formatted_skill_matches}
</VALIDATED_SKILL_MATCHES>

Requirement Assessment:
<REQUIREMENT_ASSESSMENT>
{formatted_requirement_assessment}
</REQUIREMENT_ASSESSMENT>

# ============================================
# FINAL RESPONSE CONTRACT
# ============================================

The sections above are analysis input only.

Do not return:

- candidate_profile
- requirement_profile
- validated_skill_matches
- requirement_assessment
- intermediate pipeline data

Return only one valid CareerAnalysis JSON object.

The top-level keys must be exactly:

- overall_match_score
- professional_summary
- strengths
- missing_skills
- career_gap_analysis
- recommendations
- learning_roadmap

Do not use markdown.
Do not use code fences.
Do not add explanations outside the JSON object.
"""