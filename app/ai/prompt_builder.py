"""Build prompts for career assessment."""

import json
from dataclasses import dataclass, field

from app.assessment.requirement_assessment import RequirementAssessment
from app.claims.models import AllowedClaim, AllowedClaims
from app.models import CandidateProfile, CareerAnalysis, RequirementProfile, SkillMatch


@dataclass(frozen=True)
class PromptContext:
    """Data required to build a CV analysis prompt."""

    template: str
    requirement_profile: RequirementProfile
    candidate_profile: CandidateProfile
    validated_skill_matches: list[SkillMatch]
    requirement_assessment: RequirementAssessment
    allowed_claims: AllowedClaims = field(default_factory=AllowedClaims)


def _format_claim(claim: AllowedClaim, value_label: str) -> str:
    lines = [
        f"- {value_label}: {claim.claim_value}",
        f"  Claim type: {claim.claim_type.value}",
        f"  Support level: {claim.support_level.value}",
        "  Supporting evidence:",
    ]
    if not claim.supporting_evidence:
        lines.append("    None")
        return "\n".join(lines)

    for evidence in claim.supporting_evidence:
        lines.extend(
            [
                f"    - Source type: {evidence.source_type.value}",
                f"      Source label: {evidence.source_label}",
                f"      Source text: {evidence.source_text}",
            ]
        )
    return "\n".join(lines)


def _format_allowed_claims(allowed_claims: AllowedClaims) -> str:
    factual_claims = (
        "\n".join(
            _format_claim(claim, "Claim value")
            for claim in allowed_claims.factual_claims
        )
        or "None"
    )
    skill_claims = (
        "\n".join(
            _format_claim(claim, "Skill name") for claim in allowed_claims.skill_claims
        )
        or "None"
    )
    restricted_claim_types = (
        "\n".join(
            f"- {claim_type.value}"
            for claim_type in allowed_claims.restricted_claim_types
        )
        or "None"
    )
    return f"""Factual Claims:
{factual_claims}

Skill Claims:
{skill_claims}

Restricted Claim Types:
{restricted_claim_types}"""


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
    formatted_allowed_claims = _format_allowed_claims(context.allowed_claims)
    formatted_schema = json.dumps(
        CareerAnalysis.model_json_schema(),
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

ALLOWED CANDIDATE CLAIMS
<ALLOWED_CANDIDATE_CLAIMS>
{formatted_allowed_claims}
</ALLOWED_CANDIDATE_CLAIMS>

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

The complete current CareerAnalysis JSON schema is:
<CAREER_ANALYSIS_SCHEMA>
{formatted_schema}
</CAREER_ANALYSIS_SCHEMA>

The schema applies to the complete response. Every required field and nested
field must be present in the shape shown. Do not substitute strings for objects,
objects for strings, or arrays for objects.

overall_match_score must be an integer from 0 through 100. Never return a
decimal ratio such as 0.65.

learning_roadmap must contain at least 4 entries.

Return the complete JSON object, not a patch. Do not omit valid fields.

Do not use markdown.
Do not use code fences.
Do not add explanations outside the JSON object.
"""
