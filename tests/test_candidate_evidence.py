import copy
import unittest

from pydantic import ValidationError

from app.candidate_profile.models import CandidateProfile, EducationEntry, ExperienceEntry, SkillEntry
from app.evidence.models import CandidateEvidence, EvidenceSourceType
from app.semantic.evidence_collector import CandidateEvidenceCollector


class CandidateEvidenceModelTest(unittest.TestCase):
    def test_valid_creation_and_whitespace_normalization(self) -> None:
        evidence = CandidateEvidence(
            skill=" Python ", source_type="skills_section",
            source_text=" Python ", source_label=" Skills ",
        )
        self.assertEqual(evidence.skill, "Python")
        self.assertEqual(evidence.source_text, "Python")
        self.assertEqual(evidence.source_label, "Skills")
        self.assertEqual(evidence.source_type, EvidenceSourceType.SKILLS_SECTION)

    def test_empty_skill_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            CandidateEvidence(skill=" ", source_type="other", source_text="text", source_label="Other")

    def test_empty_source_text_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            CandidateEvidence(skill="skill", source_type="other", source_text=" ", source_label="Other")

    def test_unsupported_source_type_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            CandidateEvidence(skill="skill", source_type="unknown", source_text="text", source_label="Other")


class CandidateEvidenceCollectorTest(unittest.TestCase):
    def test_collects_supported_sections_in_deterministic_order(self) -> None:
        profile = CandidateProfile(
            summary="Collaborative analyst",
            skills=[SkillEntry(name="Python")],
            experience=[ExperienceEntry(title="Analyst", organization="Acme", highlights=["Used Python"])],
            projects=["Built a forecast"],
            certifications=["Analysis certificate"],
            education=[EducationEntry(degree="BA", institution="University", status="completed")],
            languages=["English"],
        )
        evidence = CandidateEvidenceCollector().collect(profile)
        self.assertEqual(
            [item.source_type for item in evidence],
            [
                EvidenceSourceType.SKILLS_SECTION,
                EvidenceSourceType.WORK_EXPERIENCE,
                EvidenceSourceType.PROJECT,
                EvidenceSourceType.CERTIFICATION,
                EvidenceSourceType.EDUCATION,
                EvidenceSourceType.SUMMARY,
                EvidenceSourceType.OTHER,
            ],
        )
        self.assertEqual(evidence[1].source_label, "Analyst - Acme")
        self.assertEqual(evidence[4].source_label, "BA - University")

    def test_removes_exact_duplicates_but_preserves_distinct_sources_for_skill(self) -> None:
        profile = CandidateProfile(
            skills=[SkillEntry(name="Python"), SkillEntry(name="Python")],
            experience=[ExperienceEntry(highlights=["Python", "Python"])],
        )
        evidence = CandidateEvidenceCollector().collect(profile)
        self.assertEqual(len(evidence), 2)
        self.assertEqual([item.skill for item in evidence], ["Python", "Python"])
        self.assertNotEqual(evidence[0].source_type, evidence[1].source_type)

    def test_does_not_mutate_candidate_profile(self) -> None:
        profile = CandidateProfile(
            skills=[SkillEntry(name=" Python ")],
            experience=[ExperienceEntry(highlights=[" Used Python "])],
        )
        original = copy.deepcopy(profile)
        CandidateEvidenceCollector().collect(profile)
        self.assertEqual(profile, original)
