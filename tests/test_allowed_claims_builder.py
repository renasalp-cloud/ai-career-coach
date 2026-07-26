import unittest

from app.assessment.requirement_assessment import (
    AssessedRequirement,
    EvidenceStrength,
    RequirementAssessment,
)
from app.candidate_profile.models import (
    CandidateProfile,
    EducationEntry,
    ExperienceEntry,
)
from app.claims import (
    AllowedClaimsBuilder,
    ClaimSupportLevel,
    ClaimType,
    RestrictedClaimType,
)
from app.evidence.models import CandidateEvidence, ScoredCandidateEvidence
from app.models import SkillEvidence, SkillMatch


def _assessment(*items: tuple[str, str, EvidenceStrength]) -> RequirementAssessment:
    assessed = [
        AssessedRequirement(name=name, status=status, evidence_strength=strength)
        for name, status, strength in items
    ]
    demonstrated = sum(item.status == "demonstrated" for item in assessed)
    return RequirementAssessment(
        total_requirements=len(assessed),
        demonstrated_requirements=demonstrated,
        missing_requirements=len(assessed) - demonstrated,
        overall_coverage_percentage=0,
        required_total=len(assessed),
        required_demonstrated=demonstrated,
        required_coverage_percentage=0,
        preferred_total=0,
        preferred_demonstrated=0,
        preferred_coverage_percentage=0,
        optional_total=0,
        optional_demonstrated=0,
        optional_coverage_percentage=0,
        assessed_requirements=assessed,
    )


def _evidence(skill: str, source: str, score: int) -> ScoredCandidateEvidence:
    return ScoredCandidateEvidence(
        evidence=CandidateEvidence(
            skill=skill,
            source_type=source,
            source_text=f"{skill} evidence",
            source_label=source,
        ),
        quality_score=score,
        quality_factors=["test"],
    )


def _match(skill: str, status: str, evidence: ScoredCandidateEvidence | None = None) -> SkillMatch:
    selected = []
    if evidence:
        selected.append(
            SkillEvidence(
                source=evidence.evidence.source_label,
                text=evidence.evidence.source_text,
                quality_score=evidence.quality_score,
            )
        )
    return SkillMatch(
        role_skill=skill,
        candidate_skill=skill if status == "demonstrated" else None,
        evidence=selected,
        status=status,
    )


class AllowedClaimsBuilderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = AllowedClaimsBuilder()

    def test_builds_all_profile_fact_types_without_inference(self) -> None:
        profile = CandidateProfile(
            education=[
                EducationEntry(
                    degree="MSc Physics",
                    institution="Example University",
                    start_date="2020",
                    end_date="2022",
                    status="completed",
                )
            ],
            experience=[
                ExperienceEntry(
                    organization="Example Cooperative",
                    title="Coordinator",
                    start_date="2022",
                    end_date="2024",
                    location="Remote",
                    highlights=["Scheduled community workshops"],
                )
            ],
            projects=["Built a water-quality survey"],
            certifications=["First Aid Certificate"],
            languages=["Turkish"],
        )

        result = self.builder.build(profile, [], [], _assessment())

        self.assertEqual(
            [claim.claim_type for claim in result.factual_claims],
            [
                ClaimType.EDUCATION,
                ClaimType.EXPERIENCE,
                ClaimType.PROJECT,
                ClaimType.CERTIFICATION,
                ClaimType.LANGUAGE,
            ],
        )
        self.assertTrue(
            all(
                claim.support_level == ClaimSupportLevel.VERIFIED_FACT
                and claim.supporting_evidence
                for claim in result.factual_claims
            )
        )
        combined = " ".join(claim.claim_value for claim in result.factual_claims).casefold()
        for unsupported in ("senior", "leader", "researcher", "years of experience", "production"):
            self.assertNotIn(unsupported, combined)

    def test_maps_demonstrated_evidence_strength_and_preserves_order(self) -> None:
        strong = _evidence("Planning", "work_experience", 80)
        moderate = _evidence("Communication", "project", 60)
        weak = _evidence("Budgeting", "certification", 20)
        items = [
            ("Planning", "demonstrated", EvidenceStrength.STRONG),
            ("Communication", "demonstrated", EvidenceStrength.MODERATE),
            ("Budgeting", "demonstrated", EvidenceStrength.WEAK),
        ]

        result = self.builder.build(
            CandidateProfile(),
            [strong, moderate, weak],
            [
                _match("Budgeting", "demonstrated", weak),
                _match("Planning", "demonstrated", strong),
                _match("Communication", "demonstrated", moderate),
            ],
            _assessment(*items),
        )

        self.assertEqual(
            [(claim.claim_value, claim.support_level) for claim in result.skill_claims],
            [
                ("Planning", ClaimSupportLevel.STRONG_EVIDENCE),
                ("Communication", ClaimSupportLevel.MODERATE_EVIDENCE),
                ("Budgeting", ClaimSupportLevel.WEAK_EVIDENCE),
            ],
        )

    def test_declaration_is_not_upgraded_and_missing_is_not_a_claim(self) -> None:
        declaration = _evidence("Python", "skills_section", 15)
        result = self.builder.build(
            CandidateProfile(),
            [declaration],
            [
                _match("Python", "demonstrated", declaration),
                _match("Leadership", "missing"),
            ],
            _assessment(
                ("Python", "demonstrated", EvidenceStrength.WEAK),
                ("Leadership", "missing", EvidenceStrength.NONE),
            ),
        )

        self.assertEqual(len(result.skill_claims), 1)
        self.assertEqual(result.skill_claims[0].claim_value, "Python")
        self.assertEqual(
            result.skill_claims[0].support_level, ClaimSupportLevel.DECLARED_ONLY
        )

    def test_restrictions_are_complete_by_default(self) -> None:
        result = self.builder.build(CandidateProfile(), [], [], _assessment())
        self.assertEqual(result.restricted_claim_types, list(RestrictedClaimType))

    def test_deduplicates_case_insensitively_but_preserves_distinct_claims(self) -> None:
        first = _evidence("Facilitation", "project", 50)
        second = _evidence("facilitation", "work_experience", 80)
        distinct = _evidence("Negotiation", "work_experience", 80)
        result = self.builder.build(
            CandidateProfile(projects=["Community garden", "community garden", "Food bank"]),
            [first, second, distinct],
            [
                _match("Facilitation", "demonstrated", first),
                _match("facilitation", "demonstrated", second),
                _match("Negotiation", "demonstrated", distinct),
            ],
            _assessment(
                ("Facilitation", "demonstrated", EvidenceStrength.MODERATE),
                ("facilitation", "demonstrated", EvidenceStrength.STRONG),
                ("Negotiation", "demonstrated", EvidenceStrength.STRONG),
            ),
        )

        self.assertEqual(
            [claim.claim_value for claim in result.factual_claims],
            ["Community garden", "Food bank"],
        )
        self.assertEqual(
            [claim.claim_value for claim in result.skill_claims],
            ["Facilitation", "Negotiation"],
        )

    def test_preserves_first_duplicate_demonstrated_skill_and_its_support(self) -> None:
        first = _evidence("Facilitation", "project", 50)
        later = _evidence("facilitation", "work_experience", 80)

        result = self.builder.build(
            CandidateProfile(),
            [later, first],
            [
                _match("Facilitation", "demonstrated", first),
                _match("  facilitation  ", "demonstrated", later),
            ],
            _assessment(
                ("Facilitation", "demonstrated", EvidenceStrength.MODERATE),
                ("facilitation", "demonstrated", EvidenceStrength.STRONG),
            ),
        )

        self.assertEqual(len(result.skill_claims), 1)
        claim = result.skill_claims[0]
        self.assertEqual(claim.claim_value, "Facilitation")
        self.assertEqual(
            claim.support_level, ClaimSupportLevel.MODERATE_EVIDENCE
        )
        self.assertEqual(len(claim.supporting_evidence), 1)
        self.assertEqual(claim.supporting_evidence[0].source_type, "project")
        self.assertEqual(claim.supporting_evidence[0].source_label, "project")

    def test_reconstructs_evidence_using_source_text_and_score(self) -> None:
        project = _evidence("Coordination", "project", 60)
        experience = _evidence("Coordination", "work_experience", 60)
        match = _match("Coordination", "demonstrated", experience)
        match.evidence[0].source = "  WORK_EXPERIENCE "
        match.evidence[0].text = "  Coordination   evidence "

        result = self.builder.build(
            CandidateProfile(),
            [project, experience],
            [match],
            _assessment(
                ("Coordination", "demonstrated", EvidenceStrength.MODERATE)
            ),
        )

        support = result.skill_claims[0].supporting_evidence
        self.assertEqual(len(support), 1)
        self.assertEqual(support[0].source_type, "work_experience")
        self.assertEqual(support[0].source_label, "work_experience")

    def test_is_immutable_repeatable_and_handles_empty_sections(self) -> None:
        profile = CandidateProfile(languages=["English"])
        evidence = _evidence("Writing", "project", 55)
        matches = [_match("Writing", "demonstrated", evidence)]
        assessment = _assessment(
            ("Writing", "demonstrated", EvidenceStrength.MODERATE)
        )
        originals = (
            profile.model_dump(),
            [evidence.model_dump()],
            [match.model_dump() for match in matches],
            assessment.model_dump(),
        )

        first = self.builder.build(profile, [evidence], matches, assessment)
        second = self.builder.build(profile, [evidence], matches, assessment)

        self.assertEqual(first, second)
        self.assertEqual(
            originals,
            (
                profile.model_dump(),
                [evidence.model_dump()],
                [match.model_dump() for match in matches],
                assessment.model_dump(),
            ),
        )
        empty = self.builder.build(
            CandidateProfile(education=[EducationEntry()]), [], [], _assessment()
        )
        self.assertEqual(empty.factual_claims, [])
        self.assertEqual(empty.skill_claims, [])


if __name__ == "__main__":
    unittest.main()
