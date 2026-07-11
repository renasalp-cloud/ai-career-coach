import unittest

from app.requirements.extractor import extract_requirement_profile


class RequirementExtractorTest(unittest.TestCase):
    def test_extracts_skills_with_priorities(self) -> None:
        role_profile = """
Role: AI Engineer

Critical Skills:
- Python
- Machine learning fundamentals

Important Skills:
- Docker
- Git and GitHub

Optional Skills:
- MLOps
- Research experience
"""

        profile = extract_requirement_profile("AI Engineer", role_profile)

        self.assertEqual(profile.title, "AI Engineer")
        self.assertEqual(profile.source, "local_role_profile")
        self.assertEqual(
            [skill.model_dump() for skill in profile.skills],
            [
                {"name": "Python", "priority": "required"},
                {"name": "Machine learning fundamentals", "priority": "required"},
                {"name": "Docker", "priority": "preferred"},
                {"name": "Git and GitHub", "priority": "preferred"},
                {"name": "MLOps", "priority": "optional"},
                {"name": "Research experience", "priority": "optional"},
            ],
        )


    def test_ignores_unrelated_sections(self) -> None:
        role_profile = """
Critical Skills:
- Python

Evaluation Notes:
- Do not mark a skill as missing if it already appears in the CV.
- Prioritize practical project experience over certificates.
"""

        profile = extract_requirement_profile("AI Engineer", role_profile)

        self.assertEqual(
            [skill.model_dump() for skill in profile.skills],
            [
                {"name": "Python", "priority": "required"},
            ],
        )


    def test_empty_input_returns_empty_skills(self) -> None:
        profile = extract_requirement_profile("AI Engineer", "")

        self.assertEqual(profile.title, "AI Engineer")
        self.assertEqual(profile.source, "local_role_profile")
        self.assertEqual(profile.skills, [])
