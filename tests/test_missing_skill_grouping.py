import unittest

from app.analysis.consistency_processor import AnalysisConsistencyProcessor
from app.models import CareerAnalysis, RequirementProfile, RequirementSkill, SkillMatch


def _learning_roadmap() -> list[dict]:
    return [
        {
            "week": week,
            "goal": "Practice",
            "topics": [],
            "practical_task": "Task",
            "expected_outcome": "Outcome",
        }
        for week in range(1, 5)
    ]


class MissingSkillGroupingTest(unittest.TestCase):
    def test_missing_skills_are_grouped_by_requirement_priority(self) -> None:
        requirements = RequirementProfile(
            skills=[
                RequirementSkill(name="Docker", priority="required"),
                RequirementSkill(name="Stakeholder communication", priority="preferred"),
                RequirementSkill(name="Open source contributions", priority="optional"),
                RequirementSkill(name="Computer Vision", priority="required"),
            ]
        )
        validated_skill_matches = [
            SkillMatch(role_skill="Docker", status="missing", confidence=1.0),
            SkillMatch(
                role_skill="Stakeholder communication",
                status="missing",
                confidence=1.0,
            ),
            SkillMatch(
                role_skill="Open source contributions",
                status="missing",
                confidence=1.0,
            ),
            SkillMatch(
                role_skill="Computer Vision",
                candidate_skill="Computer Vision",
                status="demonstrated",
                confidence=1.0,
            ),
        ]

        grouped_skills = AnalysisConsistencyProcessor._build_missing_groups(
            requirements,
            validated_skill_matches,
        )

        self.assertEqual(
            grouped_skills,
            {
                "critical": ["Docker"],
                "important": ["Stakeholder communication"],
                "optional": ["Open source contributions"],
            },
        )

    def test_deterministic_groups_override_llm_reclassification(self) -> None:
        analysis = CareerAnalysis(
            overall_match_score=70,
            professional_summary="Candidate has relevant experience.",
            strengths=[],
            missing_skills={
                "critical": [
                    {
                        "skill": "Open source contributions",
                        "reason": "Not demonstrated in the profile.",
                    }
                ],
                "important": [
                    {
                        "skill": "Docker",
                        "reason": "Docker is not demonstrated in the profile.",
                    }
                ],
                "optional": [],
            },
            career_gap_analysis="Some gaps remain.",
            recommendations=[],
            learning_roadmap=_learning_roadmap(),
        )
        deterministic_missing_skill_groups = {
            "critical": ["Docker"],
            "important": [],
            "optional": ["Open source contributions"],
        }

        AnalysisConsistencyProcessor._apply_missing_groups(
            analysis, deterministic_missing_skill_groups
        )
        updated_analysis = analysis

        self.assertEqual(
            [item.model_dump() for item in updated_analysis.missing_skills.critical],
            [
                {
                    "skill": "Docker",
                    "reason": "Docker is not demonstrated in the profile.",
                }
            ],
        )
        self.assertEqual(updated_analysis.missing_skills.important, [])
        self.assertEqual(
            [item.model_dump() for item in updated_analysis.missing_skills.optional],
            [
                {
                    "skill": "Open source contributions",
                    "reason": "Not demonstrated in the profile.",
                }
            ],
        )

    def test_demonstrated_requirement_is_removed_from_missing_skills(self) -> None:
        analysis = CareerAnalysis(
            overall_match_score=70,
            professional_summary="Candidate has relevant experience.",
            strengths=[],
            missing_skills={
                "critical": [
                    {
                        "skill": "Computer Vision",
                        "reason": "Misclassified by the LLM.",
                    },
                    {
                        "skill": "Docker",
                        "reason": "Docker is not demonstrated.",
                    },
                ],
                "important": [],
                "optional": [],
            },
            career_gap_analysis="Some gaps remain.",
            recommendations=[],
            learning_roadmap=_learning_roadmap(),
        )
        deterministic_missing_skill_groups = {
            "critical": ["Computer Vision", "Docker"],
            "important": [],
            "optional": [],
        }
        validated_skill_matches = [
            SkillMatch(
                role_skill="Computer Vision",
                candidate_skill="Computer Vision",
                status="demonstrated",
                confidence=1.0,
            ),
            SkillMatch(
                role_skill="Docker",
                status="missing",
                confidence=1.0,
            ),
        ]

        processor = AnalysisConsistencyProcessor()
        processor._apply_missing_groups(analysis, deterministic_missing_skill_groups)
        processor._remove_demonstrated_skills(
            analysis, processor._demonstrated_names(validated_skill_matches)
        )
        updated_analysis = analysis

        self.assertEqual(
            [item.model_dump() for item in updated_analysis.missing_skills.critical],
            [
                {
                    "skill": "Docker",
                    "reason": "Docker is not demonstrated.",
                }
            ],
        )
