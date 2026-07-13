import unittest

from pydantic import ValidationError

from app.models import CareerAnalysis


def _learning_roadmap(weeks: int) -> list[dict]:
    return [
        {
            "week": week,
            "goal": "Practice deployment basics",
            "topics": ["Docker", "FastAPI"],
            "practical_task": "Containerize a simple API.",
            "expected_outcome": "A working Dockerized API.",
        }
        for week in range(1, weeks + 1)
    ]


class CareerAnalysisModelTest(unittest.TestCase):
    def test_missing_top_level_fields_raise_validation_error(self) -> None:
        incomplete_response = {
            "overall_match_score": 75,
            "professional_summary": "Candidate has relevant experience.",
        }

        with self.assertRaises(ValidationError):
            CareerAnalysis.model_validate(incomplete_response)

    def test_complete_response_validates(self) -> None:
        complete_response = {
            "overall_match_score": 75,
            "professional_summary": "Candidate has relevant experience.",
            "strengths": [
                {
                    "title": "Python",
                    "evidence": "Python appears in the candidate profile.",
                }
            ],
            "missing_skills": {
                "critical": [],
                "important": [
                    {
                        "skill": "Docker",
                        "reason": "Docker is not demonstrated in the profile.",
                    }
                ],
                "optional": [],
            },
            "career_gap_analysis": "The candidate needs more deployment evidence.",
            "recommendations": [
                {
                    "priority": "high",
                    "title": "Build a deployment project",
                    "reason": "Deployment is an important gap.",
                    "action": "Deploy one ML API with Docker.",
                }
            ],
            "learning_roadmap": _learning_roadmap(4),
        }

        analysis = CareerAnalysis.model_validate(complete_response)

        self.assertEqual(analysis.overall_match_score, 75)
        self.assertEqual(analysis.career_gap_analysis, "The candidate needs more deployment evidence.")
        self.assertEqual(analysis.recommendations[0].title, "Build a deployment project")
        self.assertEqual(analysis.learning_roadmap[0].week, 1)

    def test_learning_roadmap_with_more_than_four_weeks_is_truncated(self) -> None:
        response = {
            "overall_match_score": 75,
            "professional_summary": "Candidate has relevant experience.",
            "strengths": [],
            "missing_skills": {
                "critical": [],
                "important": [],
                "optional": [],
            },
            "career_gap_analysis": "The candidate needs more deployment evidence.",
            "recommendations": [],
            "learning_roadmap": _learning_roadmap(6),
        }

        analysis = CareerAnalysis.model_validate(response)

        self.assertEqual(len(analysis.learning_roadmap), 4)
        self.assertEqual([week.week for week in analysis.learning_roadmap], [1, 2, 3, 4])

    def test_learning_roadmap_with_fewer_than_four_weeks_fails(self) -> None:
        response = {
            "overall_match_score": 75,
            "professional_summary": "Candidate has relevant experience.",
            "strengths": [],
            "missing_skills": {
                "critical": [],
                "important": [],
                "optional": [],
            },
            "career_gap_analysis": "The candidate needs more deployment evidence.",
            "recommendations": [],
            "learning_roadmap": _learning_roadmap(3),
        }

        with self.assertRaises(ValidationError):
            CareerAnalysis.model_validate(response)
