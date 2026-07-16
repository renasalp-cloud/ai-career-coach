import unittest

from app.candidate_profile.models import SkillEntry
from app.models import CandidateProfile, RequirementProfile, RequirementSkill
from app.semantic.matcher import SkillMatcher
from app.semantic.validator import SkillValidator


class SemanticPipelineTest(unittest.TestCase):
    def test_requirement_matching_pipeline_validates_matches(self) -> None:
        candidate = CandidateProfile(
            skills=[
                SkillEntry(
                    name="Python",
                    source="skills",
                )
            ]
        )
        requirements = RequirementProfile(
            skills=[
                RequirementSkill(
                    name="Python",
                    priority="required",
                ),
                RequirementSkill(
                    name="Docker",
                    priority="preferred",
                ),
            ]
        )

        matches = SkillMatcher().match(candidate, requirements)
        validated_matches = SkillValidator().validate(matches)

        self.assertEqual(len(validated_matches), 2)

        demonstrated_match = validated_matches[0]
        self.assertEqual(demonstrated_match.role_skill, "Python")
        self.assertEqual(demonstrated_match.candidate_skill, "Python")
        self.assertEqual(demonstrated_match.status, "demonstrated")
        self.assertEqual(demonstrated_match.confidence, 1.0)
        self.assertEqual(len(demonstrated_match.evidence), 1)
        self.assertEqual(demonstrated_match.evidence[0].source, "skills")
        self.assertEqual(demonstrated_match.evidence[0].text, "Python")
        self.assertEqual(demonstrated_match.evidence[0].quality_score, 15)

        missing_match = validated_matches[1]
        self.assertEqual(missing_match.role_skill, "Docker")
        self.assertIsNone(missing_match.candidate_skill)
        self.assertEqual(missing_match.status, "missing")
        self.assertEqual(missing_match.confidence, 1.0)
        self.assertEqual(missing_match.evidence, [])
