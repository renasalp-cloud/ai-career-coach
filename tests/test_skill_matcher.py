import unittest

from app.candidate_profile.models import SkillEntry
from app.models import CandidateProfile, RequirementProfile, RequirementSkill
from app.semantic.matcher import SkillMatcher


class SkillMatcherTest(unittest.TestCase):
    def test_exact_match_returns_candidate_skill_and_evidence(self) -> None:
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
                )
            ]
        )

        matches = SkillMatcher().match(candidate, requirements)

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].role_skill, "Python")
        self.assertEqual(matches[0].candidate_skill, "Python")
        self.assertEqual(len(matches[0].evidence), 1)
        self.assertEqual(matches[0].evidence[0].source, "skills")
        self.assertEqual(matches[0].evidence[0].text, "Python")

    def test_case_insensitive_match(self) -> None:
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
                    name="python",
                    priority="required",
                )
            ]
        )

        matches = SkillMatcher().match(candidate, requirements)

        self.assertEqual(matches[0].candidate_skill, "Python")

    def test_leading_and_trailing_whitespace_match(self) -> None:
        candidate = CandidateProfile(
            skills=[
                SkillEntry(
                    name=" Python ",
                    source="skills",
                )
            ]
        )
        requirements = RequirementProfile(
            skills=[
                RequirementSkill(
                    name="Python",
                    priority="required",
                )
            ]
        )

        matches = SkillMatcher().match(candidate, requirements)

        self.assertEqual(matches[0].candidate_skill, " Python ")
        self.assertEqual(matches[0].evidence[0].text, " Python ")

    def test_unmatched_requirement_returns_empty_candidate_and_evidence(self) -> None:
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
                    name="Docker",
                    priority="required",
                )
            ]
        )

        matches = SkillMatcher().match(candidate, requirements)

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].role_skill, "Docker")
        self.assertIsNone(matches[0].candidate_skill)
        self.assertEqual(matches[0].evidence, [])

    def test_returns_one_match_for_every_requirement_skill(self) -> None:
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
                RequirementSkill(
                    name="MLOps",
                    priority="optional",
                ),
            ]
        )

        matches = SkillMatcher().match(candidate, requirements)

        self.assertEqual(len(matches), 3)
        self.assertEqual([match.role_skill for match in matches], ["Python", "Docker", "MLOps"])
