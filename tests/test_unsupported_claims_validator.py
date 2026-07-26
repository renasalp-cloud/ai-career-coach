from copy import deepcopy

import pytest

from app.claims import (
    AllowedClaim,
    AllowedClaims,
    ClaimSupportLevel,
    ClaimType,
    UnsupportedClaimsValidator,
)
from app.models import CareerAnalysis


def _claim(
    value: str,
    claim_type: ClaimType,
    support: ClaimSupportLevel = ClaimSupportLevel.VERIFIED_FACT,
) -> AllowedClaim:
    return AllowedClaim(
        claim_type=claim_type, claim_value=value, support_level=support
    )


def _analysis(summary: str, **overrides) -> CareerAnalysis:
    data = {
        "overall_match_score": 70,
        "professional_summary": summary,
        "strengths": [],
        "missing_skills": {"critical": [], "important": [], "optional": []},
        "career_gap_analysis": "The requirement for orchestration is currently unmet.",
        "recommendations": [],
        "learning_roadmap": [
            {
                "week": week,
                "goal": "Learn orchestration",
                "topics": ["Containers"],
                "practical_task": "Build a small exercise.",
                "expected_outcome": "A completed exercise.",
            }
            for week in range(1, 5)
        ],
    }
    data.update(overrides)
    return CareerAnalysis.model_validate(data)


def test_supported_factual_claims_and_sentence_order_are_preserved() -> None:
    claims = AllowedClaims(
        factual_claims=[
            _claim(
                "Bachelor of Computer Systems | Riga Technical University",
                ClaimType.EDUCATION,
            ),
            _claim("Coordinator | Northwind | Managed schedules", ClaimType.EXPERIENCE),
            _claim("Community registration project", ClaimType.PROJECT),
            _claim("General Safety Certificate", ClaimType.CERTIFICATION),
        ]
    )
    summary = (
        "The candidate holds a Bachelor of Computer Systems from Riga Technical University. "
        "They are a senior expert. "
        "The candidate worked as Coordinator at Northwind. "
        "The candidate has Community registration project. "
        "The candidate holds General Safety Certificate."
    )

    result = UnsupportedClaimsValidator().validate(_analysis(summary), claims)

    assert result.professional_summary == (
        "The candidate holds a Bachelor of Computer Systems from Riga Technical University. "
        "The candidate worked as Coordinator at Northwind. "
        "The candidate has Community registration project. "
        "The candidate holds General Safety Certificate."
    )


@pytest.mark.parametrize(
    "unsupported",
    [
        "The candidate is senior.",
        "The candidate is an expert.",
        "The candidate is a leader who led teams.",
        "The candidate has five years of experience.",
        "The candidate has production experience.",
        "The candidate is a researcher.",
        "The candidate delivered significant impact at enterprise scale.",
        "The candidate worked at Invented Holdings.",
        "The candidate built the Invented Atlas project.",
        "The candidate holds an Invented Diploma.",
        "The candidate demonstrated Invented Technology.",
    ],
)
def test_unsupported_positive_claims_are_removed(unsupported: str) -> None:
    result = UnsupportedClaimsValidator().validate(_analysis(unsupported), AllowedClaims())
    assert result.professional_summary == ""


def test_skill_support_levels_are_enforced() -> None:
    claims = AllowedClaims(
        skill_claims=[
            _claim("Planning", ClaimType.SKILL, ClaimSupportLevel.STRONG_EVIDENCE),
            _claim("Communication", ClaimType.SKILL, ClaimSupportLevel.MODERATE_EVIDENCE),
            _claim("Budgeting", ClaimType.SKILL, ClaimSupportLevel.WEAK_EVIDENCE),
            _claim("Scheduling", ClaimType.SKILL, ClaimSupportLevel.DECLARED_ONLY),
        ]
    )
    analysis = _analysis(
        "The candidate demonstrated Planning. "
        "The candidate has Communication capability. "
        "The candidate has limited evidence of Budgeting. "
        "The candidate has strong Budgeting capability. "
        "The candidate lists Scheduling as a skill. "
        "The candidate demonstrated Scheduling experience."
    )

    result = UnsupportedClaimsValidator().validate(analysis, claims)

    assert result.professional_summary == (
        "The candidate demonstrated Planning. "
        "The candidate has Communication capability. "
        "The candidate has limited evidence of Budgeting. "
        "The candidate lists Scheduling as a skill."
    )


def test_supported_skill_does_not_validate_an_invented_employer_or_project() -> None:
    claims = AllowedClaims(
        skill_claims=[
            _claim("Planning", ClaimType.SKILL, ClaimSupportLevel.STRONG_EVIDENCE)
        ]
    )
    analysis = _analysis(
        "The candidate demonstrated Planning. "
        "The candidate used Planning at Invented Holdings. "
        "The candidate applied Planning in the Invented Atlas project."
    )

    result = UnsupportedClaimsValidator().validate(analysis, claims)

    assert result.professional_summary == "The candidate demonstrated Planning."


@pytest.mark.parametrize(
    "statement",
    [
        "No leadership experience was found.",
        "Production experience is not evidenced.",
        "The orchestration requirement is missing.",
        "The candidate is not demonstrated as a senior expert.",
    ],
)
def test_gap_statements_are_preserved(statement: str) -> None:
    result = UnsupportedClaimsValidator().validate(_analysis(statement), AllowedClaims())
    assert result.professional_summary == statement


def test_nested_items_are_independent_and_empty_strengths_are_removed() -> None:
    claims = AllowedClaims(
        skill_claims=[
            _claim("Planning", ClaimType.SKILL, ClaimSupportLevel.STRONG_EVIDENCE)
        ]
    )
    analysis = _analysis(
        "",
        strengths=[
            {"title": "Planning", "evidence": "The candidate demonstrated Planning."},
            {"title": "Invented Technology", "evidence": "The candidate is an expert."},
        ],
        recommendations=[
            {
                "priority": "high",
                "title": "Build a practice project",
                "reason": "Planning is not a gap.",
                "action": "Practice weekly.",
            }
        ],
    )

    result = UnsupportedClaimsValidator().validate(analysis, claims)

    assert len(result.strengths) == 1
    assert result.strengths[0].title == "Planning"
    assert result.recommendations[0].title == "Build a practice project"


def test_validation_is_immutable_deterministic_idempotent_and_normalized() -> None:
    claims = AllowedClaims(
        skill_claims=[
            _claim("PLANNING", ClaimType.SKILL, ClaimSupportLevel.STRONG_EVIDENCE)
        ]
    )
    analysis = _analysis("  The   candidate demonstrated planning.  ")
    analysis_before = analysis.model_dump()
    claims_before = deepcopy(claims.model_dump())
    validator = UnsupportedClaimsValidator()

    first = validator.validate(analysis, claims)
    second = validator.validate(analysis, claims)
    repeated = validator.validate(first, claims)

    assert first == second == repeated
    assert first.professional_summary == "The candidate demonstrated planning."
    assert analysis.model_dump() == analysis_before
    assert claims.model_dump() == claims_before
