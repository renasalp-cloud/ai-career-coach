import json
import unittest
from unittest.mock import Mock, patch

import app.ai.analyzer as analyzer
from app.claims.models import (
    AllowedClaim,
    AllowedClaims,
    ClaimSupportLevel,
    ClaimType,
)
from app.evidence.models import EvidenceSourceType
from app.models import CareerAnalysis, RequirementProfile, RequirementSkill


def _response(summary: str) -> str:
    return json.dumps(
        {
            "overall_match_score": 0,
            "professional_summary": summary,
            "strengths": [],
            "missing_skills": {
                "critical": [],
                "important": [],
                "optional": [],
            },
            "career_gap_analysis": "Planning is not demonstrated.",
            "recommendations": [],
            "learning_roadmap": [
                {
                    "week": week,
                    "goal": "Develop Planning",
                    "topics": ["Planning"],
                    "practical_task": "Complete a Planning exercise.",
                    "expected_outcome": "Produce a Planning work sample.",
                }
                for week in range(1, 5)
            ],
        }
    )


class AnalyzerAllowedClaimsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.requirements = RequirementProfile(
            title="Coordinator",
            skills=[RequirementSkill(name="Planning", priority="required")],
            source="job_description",
        )
        self.sections = {
            "experience": (
                "Community Group\n"
                "Assistant\n"
                "Community Group [01/01/2024 - Current]\n"
                "- Coordinated weekly workshops"
            ),
            "skills": "",
        }
        self.allowed_claims = AllowedClaims(
            factual_claims=[
                AllowedClaim(
                    claim_type=ClaimType.EXPERIENCE,
                    claim_value="Assistant | Community Group | Coordinated weekly workshops",
                    support_level=ClaimSupportLevel.VERIFIED_FACT,
                )
            ]
        )

    def test_builds_claims_once_and_passes_same_claims_to_prompt_and_validator(self) -> None:
        builder = Mock()
        builder.build.return_value = self.allowed_claims
        validator = Mock()
        validator.validate.side_effect = lambda analysis, _claims: analysis

        with (
            patch.object(
                analyzer,
                "generate",
                return_value=_response("Planning is not demonstrated."),
            ) as generate,
            patch.object(
                analyzer,
                "build_cv_analysis_prompt",
                wraps=analyzer.build_cv_analysis_prompt,
            ) as prompt_builder,
        ):
            result = analyzer.analyze_cv(
                "",
                self.requirements,
                self.sections,
                allowed_claims_builder=builder,
                unsupported_claims_validator=validator,
            )

        builder.build.assert_called_once()
        candidate_profile, ranked_evidence, matches, assessment = (
            builder.build.call_args.args
        )
        self.assertEqual(candidate_profile, result.candidate_profile)
        self.assertTrue(ranked_evidence)
        self.assertEqual([match.role_skill for match in matches], ["Planning"])
        self.assertEqual(assessment.critical_missing_skills, ["Planning"])

        context = prompt_builder.call_args.args[0]
        self.assertIs(context.allowed_claims, self.allowed_claims)
        self.assertIn(
            "Assistant | Community Group | Coordinated weekly workshops",
            generate.call_args_list[0].args[0],
        )
        validator.validate.assert_called_once()
        self.assertIs(validator.validate.call_args.args[1], self.allowed_claims)

    def test_final_output_removes_unsupported_claims_and_preserves_supported_and_gap_text(self) -> None:
        summary = (
            "The candidate is a senior professional. "
            "The candidate has Kubernetes expertise. "
            "The candidate completed coordinated weekly workshops."
        )
        with patch.object(analyzer, "generate", return_value=_response(summary)):
            result = analyzer.analyze_cv("", self.requirements, self.sections)

        final_summary = result.analysis["professional_summary"]
        self.assertNotIn("senior", final_summary.casefold())
        self.assertNotIn("kubernetes", final_summary.casefold())
        self.assertIn("coordinated weekly workshops", final_summary.casefold())
        self.assertEqual(
            result.analysis["career_gap_analysis"],
            "Planning is not demonstrated.",
        )

    def test_repaired_analysis_is_validated_without_an_extra_llm_call(self) -> None:
        invalid = json.loads(_response("The candidate is a senior professional."))
        invalid["learning_roadmap"] = invalid["learning_roadmap"][:3]
        repaired = _response("The candidate is a senior professional.")
        builder = Mock()
        builder.build.return_value = self.allowed_claims
        validator = Mock()
        safe_analysis = CareerAnalysis.model_validate(json.loads(repaired))
        safe_analysis.professional_summary = ""
        validator.validate.return_value = safe_analysis

        with patch.object(
            analyzer,
            "generate",
            side_effect=[json.dumps(invalid), repaired],
        ) as generate:
            result = analyzer.analyze_cv(
                "",
                self.requirements,
                self.sections,
                allowed_claims_builder=builder,
                unsupported_claims_validator=validator,
            )

        self.assertEqual(generate.call_count, 2)
        validator.validate.assert_called_once()
        self.assertEqual(result.analysis["professional_summary"], "")

    def test_repeated_runs_are_deterministic_and_do_not_mutate_inputs(self) -> None:
        original_requirements = self.requirements.model_dump()
        sections = dict(self.sections)
        with patch.object(
            analyzer,
            "generate",
            return_value=_response("Planning is not demonstrated."),
        ):
            first = analyzer.analyze_cv("", self.requirements, sections)
            second = analyzer.analyze_cv("", self.requirements, sections)

        self.assertEqual(first, second)
        self.assertEqual(self.requirements.model_dump(), original_requirements)
        self.assertEqual(sections, self.sections)


if __name__ == "__main__":
    unittest.main()
