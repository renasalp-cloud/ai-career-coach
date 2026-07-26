import unittest

from app.ai.prompt_builder import PromptContext, build_cv_analysis_prompt
from app.assessment.requirement_assessment import (
    AssessedRequirement,
    EvidenceStrength,
    RequirementAssessment,
)
from app.claims.models import AllowedClaim, AllowedClaims, ClaimSupportLevel, ClaimType
from app.evidence.models import CandidateEvidence, EvidenceSourceType
from app.models import CandidateProfile, RequirementProfile, RequirementSkill


class AnalyzerRequirementAuthorityTest(unittest.TestCase):
    def test_prompt_preserves_deterministic_status_priority_and_evidence(self) -> None:
        assessment = RequirementAssessment(
            total_requirements=2,
            demonstrated_requirements=1,
            missing_requirements=1,
            overall_coverage_percentage=50,
            required_total=1,
            required_demonstrated=1,
            required_coverage_percentage=100,
            preferred_total=1,
            preferred_demonstrated=0,
            preferred_coverage_percentage=0,
            optional_total=0,
            optional_demonstrated=0,
            optional_coverage_percentage=0,
            assessed_requirements=[
                AssessedRequirement(
                    name="Planning",
                    status="demonstrated",
                    evidence_strength=EvidenceStrength.STRONG,
                ),
                AssessedRequirement(
                    name="Facilitation",
                    status="missing",
                    evidence_strength=EvidenceStrength.NONE,
                ),
            ],
            demonstrated_skills=["Planning"],
            preferred_missing_skills=["Facilitation"],
        )
        evidence_text = "Planned the weekly delivery schedule."
        claims = AllowedClaims(
            skill_claims=[
                AllowedClaim(
                    claim_type=ClaimType.SKILL,
                    claim_value="Planning",
                    support_level=ClaimSupportLevel.STRONG_EVIDENCE,
                    supporting_evidence=[
                        CandidateEvidence(
                            skill="Planning",
                            source_type=EvidenceSourceType.PROJECT,
                            source_label="Delivery schedule",
                            source_text=evidence_text,
                        )
                    ],
                ),
                AllowedClaim(
                    claim_type=ClaimType.SKILL,
                    claim_value="Version control",
                    support_level=ClaimSupportLevel.DECLARED_ONLY,
                ),
            ]
        )
        context = PromptContext(
            template=open("app/prompts/cv_analysis.txt", encoding="utf-8").read(),
            requirement_profile=RequirementProfile(
                title="Coordinator",
                skills=[
                    RequirementSkill(name="Planning", priority="required"),
                    RequirementSkill(name="Facilitation", priority="preferred"),
                ],
            ),
            candidate_profile=CandidateProfile(projects=[evidence_text]),
            validated_skill_matches=[],
            requirement_assessment=assessment,
            allowed_claims=claims,
        )

        prompt = build_cv_analysis_prompt(context)

        self.assertIn("RequirementAssessment is authoritative.", prompt)
        self.assertIn("marked demonstrated must not appear as missing", prompt)
        self.assertIn("marked missing must not be described as supported", prompt)
        self.assertIn("preferred or optional requirement must preserve", prompt)
        self.assertIn('"priority": "preferred"', prompt)
        self.assertIn(evidence_text, prompt)
        self.assertIn("exact source text or a conservative near-verbatim excerpt", prompt)
        self.assertIn("declared_only claim as demonstrated use", prompt)
        self.assertIn("degree title", prompt)
        self.assertIn("<CAREER_ANALYSIS_SCHEMA>", prompt)
        self.assertIn("learning_roadmap must contain at least 4 entries", prompt)

    def test_prompt_generation_is_deterministic_and_does_not_mutate_inputs(self) -> None:
        assessment = RequirementAssessment(
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
        requirements = RequirementProfile(title="Coordinator")
        original = requirements.model_dump()
        context = PromptContext(
            template="Template",
            requirement_profile=requirements,
            candidate_profile=CandidateProfile(),
            validated_skill_matches=[],
            requirement_assessment=assessment,
        )

        self.assertEqual(
            build_cv_analysis_prompt(context),
            build_cv_analysis_prompt(context),
        )
        self.assertEqual(requirements.model_dump(), original)


if __name__ == "__main__":
    unittest.main()
