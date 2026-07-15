import json
import unittest
from unittest.mock import patch

import app.ai.analyzer as analyzer
from app.models import RequirementProfile, RequirementSkill, SkillMatch


def _valid_response() -> str:
    return json.dumps(
        {
            "overall_match_score": 0,
            "professional_summary": "No demonstrated match.",
            "strengths": [],
            "missing_skills": {
                "critical": [],
                "important": [],
                "optional": [],
            },
            "career_gap_analysis": "Requirements are not demonstrated.",
            "recommendations": [],
            "learning_roadmap": [
                {
                    "week": week,
                    "goal": "Build evidence",
                    "topics": [],
                    "practical_task": "Complete a practical task.",
                    "expected_outcome": "Documented evidence.",
                }
                for week in range(1, 5)
            ],
        }
    )


class AnalyzerRequirementProfileTest(unittest.TestCase):
    def test_analyzer_uses_supplied_profile_for_matching_and_role_context(self) -> None:
        requirement_profile = RequirementProfile(
            title="Research Lead",
            skills=[RequirementSkill(name="Experiment design", priority="required")],
            source="job_description",
        )
        matched_profiles = []

        class RecordingMatcher:
            def __init__(self, **_kwargs):
                pass

            def match(self, _candidate_profile, requirements):
                matched_profiles.append(requirements)
                return [SkillMatch(role_skill="Experiment design")]

        with (
            patch.object(analyzer, "SkillMatcher", RecordingMatcher),
            patch.object(analyzer, "generate", return_value=_valid_response()) as generate,
        ):
            analyzer.analyze_cv(
                "",
                requirement_profile,
                {"skills": ""},
            )

        self.assertEqual(matched_profiles, [requirement_profile])
        prompt = generate.call_args.args[0]
        self.assertIn("Target Role:\nResearch Lead", prompt)
        self.assertIn('"source": "job_description"', prompt)
        self.assertIn("<REQUIREMENT_ASSESSMENT>", prompt)
        self.assertIn('"critical_missing_skills": [', prompt)
        self.assertIn('"Experiment design"', prompt)

    def test_analyzer_has_no_static_role_profile_loader_dependency(self) -> None:
        self.assertFalse(hasattr(analyzer, "load_role_profile"))
        self.assertFalse(hasattr(analyzer, "ROLE_PROFILE_DIR"))
        self.assertFalse(hasattr(analyzer, "extract_requirement_profile"))


if __name__ == "__main__":
    unittest.main()
