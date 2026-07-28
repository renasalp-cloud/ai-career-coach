import unittest

from app.ai.prompt_builder import PromptContext, build_cv_analysis_prompt
from app.assessment.requirement_assessment import RequirementAssessment
from app.claims.models import (
    AllowedClaim,
    AllowedClaims,
    ClaimSupportLevel,
    ClaimType,
    RestrictedClaimType,
)
from app.evidence.models import CandidateEvidence, EvidenceSourceType
from app.models import CandidateProfile, RequirementProfile


def _assessment() -> RequirementAssessment:
    return RequirementAssessment(
        total_requirements=0,
        demonstrated_requirements=0,
        missing_requirements=0,
        overall_coverage_percentage=0,
        required_total=0,
        required_demonstrated=0,
        required_coverage_percentage=0,
        preferred_total=0,
        preferred_demonstrated=0,
        preferred_coverage_percentage=0,
        optional_total=0,
        optional_demonstrated=0,
        optional_coverage_percentage=0,
    )


def _context(allowed_claims: AllowedClaims, template: str = "Template") -> PromptContext:
    return PromptContext(
        template=template,
        requirement_profile=RequirementProfile(title="Coordinator"),
        candidate_profile=CandidateProfile(languages=["English"]),
        validated_skill_matches=[],
        requirement_assessment=_assessment(),
        allowed_claims=allowed_claims,
    )


def _section(prompt: str, tag: str) -> str:
    start = f"<{tag}>"
    end = f"</{tag}>"
    return prompt.split(start, 1)[1].split(end, 1)[0].strip()


class AllowedClaimsPromptTest(unittest.TestCase):
    def test_serializes_claims_with_support_and_evidence_associations(self) -> None:
        claims = AllowedClaims(
            factual_claims=[
                AllowedClaim(
                    claim_type=ClaimType.EXPERIENCE,
                    claim_value="Coordinated workshops",
                    support_level=ClaimSupportLevel.VERIFIED_FACT,
                    supporting_evidence=[
                        CandidateEvidence(
                            skill="Coordination",
                            source_type=EvidenceSourceType.WORK_EXPERIENCE,
                            source_label="Community Cooperative",
                            source_text="Coordinated weekly workshops",
                        )
                    ],
                )
            ],
            skill_claims=[
                AllowedClaim(
                    claim_type=ClaimType.SKILL,
                    claim_value="Planning",
                    support_level=ClaimSupportLevel.STRONG_EVIDENCE,
                    supporting_evidence=[
                        CandidateEvidence(
                            skill="Planning",
                            source_type=EvidenceSourceType.PROJECT,
                            source_label="Community project",
                            source_text="Planned the delivery schedule",
                        )
                    ],
                )
            ],
            restricted_claim_types=[
                RestrictedClaimType.SENIORITY,
                RestrictedClaimType.LEADERSHIP,
            ],
        )
        section = _section(build_cv_analysis_prompt(_context(claims)), "ALLOWED_CANDIDATE_CLAIMS")
        factual, skill_and_restricted = section.split("Skill Claims:", 1)
        skill, restricted = skill_and_restricted.split("Restricted Claim Types:", 1)

        self.assertRegex(
            factual,
            r"Claim value: Coordinated workshops\n  Claim type: experience\n"
            r"  Support level: verified_fact\n  Supporting evidence:\n"
            r"    - Source type: work_experience\n"
            r"      Source label: Community Cooperative\n"
            r"      Source text: Coordinated weekly workshops",
        )
        self.assertRegex(
            skill,
            r"Skill name: Planning\n  Claim type: skill\n"
            r"  Support level: strong_evidence\n  Supporting evidence:\n"
            r"    - Source type: project\n"
            r"      Source label: Community project\n"
            r"      Source text: Planned the delivery schedule",
        )
        self.assertEqual(restricted.strip().splitlines(), ["- seniority", "- leadership"])

    def test_preserves_order_is_repeatable_and_does_not_mutate_input(self) -> None:
        claims = AllowedClaims(
            skill_claims=[
                AllowedClaim(
                    claim_type=ClaimType.SKILL,
                    claim_value=name,
                    support_level=level,
                )
                for name, level in [
                    ("First", ClaimSupportLevel.MODERATE_EVIDENCE),
                    ("Second", ClaimSupportLevel.WEAK_EVIDENCE),
                    ("Third", ClaimSupportLevel.DECLARED_ONLY),
                ]
            ],
            restricted_claim_types=[],
        )
        original = claims.model_dump()
        first = build_cv_analysis_prompt(_context(claims))
        second = build_cv_analysis_prompt(_context(claims))
        section = _section(first, "ALLOWED_CANDIDATE_CLAIMS")

        positions = [section.index(f"Skill name: {name}") for name in ("First", "Second", "Third")]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("Support level: declared_only\n  Supporting evidence:\n    None", section)
        self.assertEqual(first, second)
        self.assertEqual(claims.model_dump(), original)

    def test_empty_claims_have_explicit_sections_and_existing_context_remains(self) -> None:
        prompt = build_cv_analysis_prompt(
            _context(AllowedClaims(restricted_claim_types=[]), template="Unique template rule")
        )
        section = _section(prompt, "ALLOWED_CANDIDATE_CLAIMS")

        self.assertEqual(
            section,
            "Factual Claims:\nNone\n\nSkill Claims:\nNone\n\n"
            "Restricted Claim Types:\nNone",
        )
        self.assertIn("Unique template rule", prompt)
        for tag in (
            "REQUIREMENT_PROFILE",
            "CANDIDATE_PROFILE",
            "VALIDATED_SKILL_MATCHES",
            "REQUIREMENT_ASSESSMENT",
        ):
            self.assertTrue(_section(prompt, tag))

    def test_template_contains_claim_safety_and_support_semantics(self) -> None:
        template = open("app/prompts/cv_analysis.txt", encoding="utf-8").read()

        for level in (
            "verified_fact",
            "strong_evidence",
            "moderate_evidence",
            "weak_evidence",
            "declared_only",
        ):
            self.assertRegex(template, rf"- {level}: [^\n]+")
        self.assertIn(
            "Job requirements are role expectations, not candidate evidence.", template
        )
        self.assertIn(
            "declared skill and must not be described as demonstrated experience",
            template,
        )

    def test_template_limits_analysis_to_dynamic_authoritative_input(self) -> None:
        template = open("app/prompts/cv_analysis.txt", encoding="utf-8").read()

        self.assertIn("Use only the supplied requirement profile.", template)
        self.assertIn("Do not add requirements based on", template)
        self.assertIn("treat them as alternatives", template)
        self.assertIn("do not require the candidate to satisfy every", template)
        self.assertIn("Use only supplied candidate evidence.", template)


if __name__ == "__main__":
    unittest.main()
