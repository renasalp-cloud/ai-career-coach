import unittest

from app.models import SkillEvidence, SkillMatch
from app.semantic.validator import SkillValidator


class SkillValidatorTest(unittest.TestCase):
    def test_missing_skill_gets_missing_status_and_confidence(self) -> None:
        match = SkillMatch(
            role_skill="Docker",
            candidate_skill=None,
            evidence=[],
        )

        validated = SkillValidator().validate([match])

        self.assertEqual(len(validated), 1)
        self.assertEqual(validated[0].role_skill, "Docker")
        self.assertIsNone(validated[0].candidate_skill)
        self.assertEqual(validated[0].evidence, [])
        self.assertEqual(validated[0].status, "missing")
        self.assertEqual(validated[0].confidence, 1.0)

    def test_demonstrated_skill_gets_demonstrated_status_and_confidence(self) -> None:
        evidence = [
            SkillEvidence(
                source="skills",
                text="Python",
            )
        ]
        match = SkillMatch(
            role_skill="Python",
            candidate_skill="Python",
            evidence=evidence,
        )

        validated = SkillValidator().validate([match])

        self.assertEqual(len(validated), 1)
        self.assertEqual(validated[0].role_skill, "Python")
        self.assertEqual(validated[0].candidate_skill, "Python")
        self.assertEqual(validated[0].evidence, evidence)
        self.assertEqual(validated[0].status, "demonstrated")
        self.assertEqual(validated[0].confidence, 1.0)

    def test_original_matches_are_not_mutated(self) -> None:
        original_matches = [
            SkillMatch(role_skill="Docker"),
            SkillMatch(
                role_skill="Python",
                candidate_skill="Python",
                evidence=[
                    SkillEvidence(
                        source="skills",
                        text="Python",
                    )
                ],
            ),
        ]

        validated = SkillValidator().validate(original_matches)

        self.assertIsNone(original_matches[0].status)
        self.assertIsNone(original_matches[0].confidence)
        self.assertIsNone(original_matches[1].status)
        self.assertIsNone(original_matches[1].confidence)
        self.assertEqual(validated[0].status, "missing")
        self.assertEqual(validated[1].status, "demonstrated")
