import copy
import unittest

from pydantic import ValidationError

from app.evidence.models import CandidateEvidence, ScoredCandidateEvidence
from app.evidence.scorer import EvidenceQualityScorer


def evidence(source_type: str, text: str = "Python", label: str = "") -> CandidateEvidence:
    return CandidateEvidence(
        skill=text, source_type=source_type, source_text=text, source_label=label
    )


class ScoredCandidateEvidenceModelTest(unittest.TestCase):
    def test_valid_creation_preserves_evidence(self) -> None:
        item = evidence("project", "Built a service", "Project")
        scored = ScoredCandidateEvidence(
            evidence=item, quality_score=60, quality_factors=["source strength"]
        )
        self.assertEqual(scored.evidence, item)

    def test_score_bounds_are_validated(self) -> None:
        for invalid_score in (-1, 101):
            with self.subTest(invalid_score=invalid_score), self.assertRaises(ValidationError):
                ScoredCandidateEvidence(
                    evidence=evidence("other"),
                    quality_score=invalid_score,
                    quality_factors=["test factor"],
                )

    def test_quality_factors_must_explain_at_least_one_reason(self) -> None:
        with self.assertRaises(ValidationError):
            ScoredCandidateEvidence(
                evidence=evidence("other"), quality_score=10, quality_factors=[]
            )


class EvidenceQualityScorerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scorer = EvidenceQualityScorer()

    def test_source_strength_scores(self) -> None:
        self.assertEqual(self.scorer.score(evidence("work_experience")).quality_score, 45)
        self.assertEqual(self.scorer.score(evidence("project")).quality_score, 40)
        self.assertEqual(self.scorer.score(evidence("skills_section")).quality_score, 15)

    def test_demonstrated_evidence_scores_above_equivalent_declaration(self) -> None:
        work = evidence("work_experience", "Python", "Work experience")
        declaration = evidence("skills_section", "Python", "Skills section")
        self.assertGreater(
            self.scorer.score(work).quality_score,
            self.scorer.score(declaration).quality_score,
        )

    def test_action_wording_increases_score_and_is_explained(self) -> None:
        plain = self.scorer.score(evidence("project", "Data service", "Project"))
        active = self.scorer.score(evidence("project", "Built data service", "Project"))
        self.assertGreater(active.quality_score, plain.quality_score)
        self.assertIn("demonstrated action: +20", active.quality_factors)

    def test_only_supported_specific_source_labels_add_context(self) -> None:
        generic = self.scorer.score(evidence("work_experience", "Python", "Work experience"))
        specific = self.scorer.score(evidence("work_experience", "Python", "Analyst - Acme"))
        project = self.scorer.score(evidence("project", "Python", "Named initiative"))
        self.assertEqual(specific.quality_score, generic.quality_score + 10)
        self.assertEqual(project.quality_score, 40)

    def test_weak_context_remains_conservative(self) -> None:
        scored = self.scorer.score(evidence("other", "Python"))
        self.assertEqual(scored.quality_score, 10)
        self.assertEqual(scored.quality_factors, ["source strength (other): +10"])

    def test_outcome_signal_is_explained(self) -> None:
        scored = self.scorer.score(evidence("project", "Improved response time by 20%"))
        self.assertIn("concrete outcome: +15", scored.quality_factors)

    def test_score_all_preserves_order(self) -> None:
        items = [evidence("other", "First"), evidence("project", "Second")]
        scored = self.scorer.score_all(items)
        self.assertEqual([item.evidence.source_text for item in scored], ["First", "Second"])

    def test_scoring_does_not_mutate_input(self) -> None:
        item = evidence("work_experience", "Built a service", "Developer - Acme")
        original = copy.deepcopy(item)
        scored = self.scorer.score(item)
        self.assertEqual(item, original)
        self.assertIsNot(scored.evidence, item)

    def test_repeated_scoring_is_identical(self) -> None:
        item = evidence("project", "Delivered a 25% improvement", "Project")
        self.assertEqual(self.scorer.score(item), self.scorer.score(item))

    def test_all_source_scores_remain_in_range(self) -> None:
        for source_type in (
            "work_experience", "project", "certification", "education",
            "summary", "skills_section", "other",
        ):
            scored = self.scorer.score(
                evidence(source_type, "Built and improved a result by 100%", "Specific context")
            )
            self.assertGreaterEqual(scored.quality_score, 0)
            self.assertLessEqual(scored.quality_score, 100)


if __name__ == "__main__":
    unittest.main()
