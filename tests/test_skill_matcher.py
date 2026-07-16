import copy
import unittest

from app.candidate_profile.models import ExperienceEntry, SkillEntry
from app.evidence.models import CandidateEvidence, ScoredCandidateEvidence
from app.evidence.ranker import EvidenceRanker
from app.evidence.scorer import EvidenceQualityScorer
from app.models import CandidateProfile, RequirementProfile, RequirementSkill
from app.semantic.alias_registry import SkillAliasRegistry
from app.semantic.matcher import SkillMatcher


class FakeEvidenceCollector:
    def __init__(self) -> None:
        self.call_count = 0

    def collect(self, candidate: CandidateProfile) -> list[CandidateEvidence]:
        self.call_count += 1
        return [
            CandidateEvidence(skill="Python", source_type="skills_section", source_text="Python", source_label="Skills section"),
            CandidateEvidence(skill="Used Python", source_type="work_experience", source_text="Used Python for data preprocessing", source_label="Engineer"),
            CandidateEvidence(skill="Built Docker", source_type="work_experience", source_text="Built Docker containers", source_label="Engineer"),
        ]


class StaticEvidenceCollector:
    def __init__(self, evidence: list[CandidateEvidence]) -> None:
        self.evidence = evidence

    def collect(self, candidate: CandidateProfile) -> list[CandidateEvidence]:
        return self.evidence


class TrackingScorer(EvidenceQualityScorer):
    def __init__(self) -> None:
        self.calls = 0

    def score_all(
        self, evidence: list[CandidateEvidence]
    ) -> list[ScoredCandidateEvidence]:
        self.calls += 1
        return super().score_all(evidence)


class TrackingRanker(EvidenceRanker):
    def __init__(self) -> None:
        self.calls = 0

    def select_top(
        self, evidence: list[ScoredCandidateEvidence], limit: int
    ) -> list[ScoredCandidateEvidence]:
        self.calls += 1
        return super().select_top(evidence, limit)


class SkillMatcherTest(unittest.TestCase):
    def test_problem_solving_matches_requirement_with_generic_skills_suffix(self) -> None:
        candidate = CandidateProfile(skills=[SkillEntry(name="Problem solving")])
        requirements = RequirementProfile(
            skills=[
                RequirementSkill(
                    name="Problem-solving skills",
                    priority="required",
                )
            ]
        )

        match = SkillMatcher().match(candidate, requirements)[0]

        self.assertEqual(match.candidate_skill, "Problem solving")
        self.assertEqual(match.evidence[0].text, "Problem solving")

    def test_scores_ranks_and_limits_only_relevant_structured_evidence(self) -> None:
        evidence = [
            CandidateEvidence(
                skill="Python", source_type="skills_section",
                source_text="Python", source_label="Skills",
            ),
            CandidateEvidence(
                skill="Python", source_type="project",
                source_text="Built Python project", source_label="Project",
            ),
            CandidateEvidence(
                skill="Docker", source_type="work_experience",
                source_text="Implemented Docker deployment", source_label="Engineer",
            ),
            CandidateEvidence(
                skill="Python", source_type="work_experience",
                source_text="Implemented Python service", source_label="Engineer",
            ),
        ]
        scorer = TrackingScorer()
        ranker = TrackingRanker()
        matcher = SkillMatcher(
            evidence_collector=StaticEvidenceCollector(evidence),
            evidence_scorer=scorer,
            evidence_ranker=ranker,
            evidence_limit=2,
        )

        match = matcher.match(
            CandidateProfile(skills=[SkillEntry(name="Python")]),
            RequirementProfile(
                skills=[RequirementSkill(name="Python", priority="required")]
            ),
        )[0]

        self.assertEqual(scorer.calls, 1)
        self.assertEqual(ranker.calls, 1)
        self.assertEqual(
            [item.text for item in match.evidence],
            ["Implemented Python service", "Built Python project"],
        )

    def test_equal_score_evidence_preserves_collection_order_and_large_limit(self) -> None:
        evidence = [
            CandidateEvidence(
                skill="Python", source_type="project",
                source_text="Python first", source_label="Project",
            ),
            CandidateEvidence(
                skill="Python", source_type="project",
                source_text="Python second", source_label="Project",
            ),
        ]
        matcher = SkillMatcher(
            evidence_collector=StaticEvidenceCollector(evidence), evidence_limit=5
        )

        match = matcher.match(
            CandidateProfile(),
            RequirementProfile(
                skills=[RequirementSkill(name="Python", priority="required")]
            ),
        )[0]

        self.assertEqual(
            [item.text for item in match.evidence], ["Python first", "Python second"]
        )

    def test_matching_does_not_mutate_inputs_or_structured_evidence(self) -> None:
        candidate = CandidateProfile(skills=[SkillEntry(name="Python")])
        requirements = RequirementProfile(
            skills=[RequirementSkill(name="Python", priority="required")]
        )
        evidence = [
            CandidateEvidence(
                skill="Python", source_type="skills_section",
                source_text="Python", source_label="Skills",
            )
        ]
        originals = copy.deepcopy((candidate, requirements, evidence))
        matcher = SkillMatcher(evidence_collector=StaticEvidenceCollector(evidence))

        first = matcher.match(candidate, requirements)
        second = matcher.match(candidate, requirements)

        self.assertEqual(first, second)
        self.assertEqual((candidate, requirements, evidence), originals)

    def test_rejects_non_positive_evidence_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "evidence_limit must be positive"):
            SkillMatcher(evidence_limit=0)

    def test_machine_learning_fundamentals_matches_machine_learning(self) -> None:
        candidate = CandidateProfile(skills=[SkillEntry(name="Machine learning")])
        requirements = RequirementProfile(skills=[
            RequirementSkill(name="Machine learning fundamentals", priority="required")
        ])

        self.assertEqual(SkillMatcher().match(candidate, requirements)[0].candidate_skill, "Machine learning")

    def test_docker_basics_matches_docker(self) -> None:
        candidate = CandidateProfile(skills=[SkillEntry(name="Docker")])
        requirements = RequirementProfile(skills=[
            RequirementSkill(name="Docker basics", priority="required")
        ])

        self.assertEqual(SkillMatcher().match(candidate, requirements)[0].candidate_skill, "Docker")

    def test_advanced_qualifier_is_not_ignored(self) -> None:
        candidate = CandidateProfile(skills=[SkillEntry(name="Python")])
        requirements = RequirementProfile(
            skills=[RequirementSkill(name="Advanced Python", priority="required")]
        )

        self.assertIsNone(SkillMatcher().match(candidate, requirements)[0].candidate_skill)

    def test_practical_experience_matches_action_evidence(self) -> None:
        candidate = CandidateProfile(
            experience=[ExperienceEntry(highlights=["Built Docker containers for testing."])]
        )
        requirements = RequirementProfile(skills=[
            RequirementSkill(name="Practical experience with Docker", priority="required")
        ])

        match = SkillMatcher().match(candidate, requirements)[0]

        self.assertEqual(match.candidate_skill, "docker")
        self.assertEqual(match.evidence[0].source, "experience")

    def test_practical_experience_does_not_match_skill_list_alone(self) -> None:
        candidate = CandidateProfile(skills=[SkillEntry(name="Docker")])
        requirements = RequirementProfile(skills=[
            RequirementSkill(name="Practical experience with Docker", priority="required")
        ])

        self.assertIsNone(SkillMatcher().match(candidate, requirements)[0].candidate_skill)

    def test_practical_ai_ml_experience_matches_build_and_evaluate_evidence(self) -> None:
        candidate = CandidateProfile(
            experience=[ExperienceEntry(
                highlights=["Built and evaluated AI/ML models for a forecasting exercise."]
            )]
        )
        requirements = RequirementProfile(skills=[
            RequirementSkill(name="Practical AI/ML project experience", priority="required")
        ])

        match = SkillMatcher().match(candidate, requirements)[0]

        self.assertEqual(match.candidate_skill, "ai ml")
        self.assertEqual(match.evidence[0].source, "experience")

    def test_practical_experience_matches_applied_bootcamp_evidence(self) -> None:
        candidate = CandidateProfile(certifications=[
            "Completed a practical data analysis bootcamp involving applied work."
        ])
        requirements = RequirementProfile(skills=[
            RequirementSkill(name="Applied data analysis experience", priority="required")
        ])

        match = SkillMatcher().match(candidate, requirements)[0]

        self.assertEqual(match.candidate_skill, "data analysis")
        self.assertEqual(match.evidence[0].source, "certification")

    def test_llm_application_development_matches_hands_on_evidence(self) -> None:
        candidate = CandidateProfile(
            experience=[ExperienceEntry(
                highlights=[
                    "Gained hands-on experience with LLM-based applications for document review."
                ]
            )]
        )
        requirements = RequirementProfile(skills=[
            RequirementSkill(name="LLM application development", priority="required")
        ])

        match = SkillMatcher().match(candidate, requirements)[0]

        self.assertEqual(match.candidate_skill, "LLM application development")
        self.assertEqual(match.evidence[0].source, "experience")

    def test_llm_basics_do_not_match_llm_application_development(self) -> None:
        candidate = CandidateProfile(skills=[SkillEntry(name="LLM basics")])
        requirements = RequirementProfile(skills=[
            RequirementSkill(name="LLM application development", priority="required")
        ])

        match = SkillMatcher().match(candidate, requirements)[0]

        self.assertIsNone(match.candidate_skill)
        self.assertEqual(match.evidence, [])

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
        self.assertEqual(matches[0].evidence[0].text, "Python")

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

    def test_uses_injected_evidence_collector_once_per_match_call(self) -> None:
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
        collector = FakeEvidenceCollector()

        matches = SkillMatcher(evidence_collector=collector).match(candidate, requirements)

        self.assertEqual(collector.call_count, 1)
        self.assertEqual(len(matches[0].evidence), 2)
        self.assertEqual(
            [item.model_dump() for item in matches[0].evidence],
            [
                {
                    "source": "experience",
                    "text": "Used Python for data preprocessing",
                    "quality_score": 55,
                },
                {"source": "skills", "text": "Python", "quality_score": 15},
            ],
        )
        self.assertEqual(matches[1].candidate_skill, "Docker")
        self.assertEqual(
            [item.model_dump() for item in matches[1].evidence],
            [
                {
                    "source": "experience",
                    "text": "Built Docker containers",
                    "quality_score": 75,
                },
            ],
        )

    def test_matches_data_preprocessing_from_experience_evidence(self) -> None:
        candidate = CandidateProfile(
            experience=[
                ExperienceEntry(
                    highlights=[
                        "Performed data preprocessing on customer datasets.",
                    ]
                )
            ]
        )
        requirements = RequirementProfile(
            skills=[
                RequirementSkill(
                    name="Data preprocessing",
                    priority="required",
                )
            ]
        )

        matches = SkillMatcher().match(candidate, requirements)

        self.assertEqual(matches[0].candidate_skill, "Data preprocessing")
        self.assertEqual(len(matches[0].evidence), 1)
        self.assertEqual(matches[0].evidence[0].source, "experience")
        self.assertEqual(
            matches[0].evidence[0].text,
            "Performed data preprocessing on customer datasets.",
        )

    def test_matches_model_training_from_experience_evidence(self) -> None:
        candidate = CandidateProfile(
            experience=[
                ExperienceEntry(
                    highlights=[
                        "Handled model training and evaluation for experiments.",
                    ]
                )
            ]
        )
        requirements = RequirementProfile(
            skills=[
                RequirementSkill(
                    name="Model training",
                    priority="required",
                )
            ]
        )

        matches = SkillMatcher().match(candidate, requirements)

        self.assertEqual(matches[0].candidate_skill, "Model training")
        self.assertEqual(len(matches[0].evidence), 1)
        self.assertEqual(matches[0].evidence[0].source, "experience")
        self.assertEqual(
            matches[0].evidence[0].text,
            "Handled model training and evaluation for experiments.",
        )

    def test_unrelated_evidence_remains_unmatched(self) -> None:
        candidate = CandidateProfile(
            experience=[
                ExperienceEntry(
                    highlights=[
                        "Created product documentation.",
                    ]
                )
            ]
        )
        requirements = RequirementProfile(
            skills=[
                RequirementSkill(
                    name="Data preprocessing",
                    priority="required",
                )
            ]
        )

        matches = SkillMatcher().match(candidate, requirements)

        self.assertIsNone(matches[0].candidate_skill)
        self.assertEqual(matches[0].evidence, [])

    def test_matches_data_analysis_from_work_experience_evidence(self) -> None:
        candidate = CandidateProfile(
            experience=[
                ExperienceEntry(
                    highlights=[
                        "Prepared weekly data analysis reports for regional sales teams.",
                    ]
                )
            ]
        )
        requirements = RequirementProfile(
            skills=[
                RequirementSkill(
                    name="Data analysis",
                    priority="required",
                )
            ]
        )

        matches = SkillMatcher().match(candidate, requirements)

        self.assertEqual(matches[0].candidate_skill, "Data analysis")
        self.assertEqual(len(matches[0].evidence), 1)
        self.assertEqual(matches[0].evidence[0].source, "experience")
        self.assertEqual(
            matches[0].evidence[0].text,
            "Prepared weekly data analysis reports for regional sales teams.",
        )

    def test_matches_customer_service_from_work_experience_evidence(self) -> None:
        candidate = CandidateProfile(
            experience=[
                ExperienceEntry(
                    highlights=[
                        "Delivered customer service support for enterprise accounts.",
                    ]
                )
            ]
        )
        requirements = RequirementProfile(
            skills=[
                RequirementSkill(
                    name="Customer service",
                    priority="required",
                )
            ]
        )

        matches = SkillMatcher().match(candidate, requirements)

        self.assertEqual(matches[0].candidate_skill, "Customer service")
        self.assertEqual(len(matches[0].evidence), 1)
        self.assertEqual(matches[0].evidence[0].source, "experience")
        self.assertEqual(
            matches[0].evidence[0].text,
            "Delivered customer service support for enterprise accounts.",
        )

    def test_unrelated_non_technical_evidence_remains_unmatched(self) -> None:
        candidate = CandidateProfile(
            experience=[
                ExperienceEntry(
                    highlights=[
                        "Organized internal onboarding documents.",
                    ]
                )
            ]
        )
        requirements = RequirementProfile(
            skills=[
                RequirementSkill(
                    name="Customer service",
                    priority="required",
                )
            ]
        )

        matches = SkillMatcher().match(candidate, requirements)

        self.assertIsNone(matches[0].candidate_skill)
        self.assertEqual(matches[0].evidence, [])

    def test_matches_configured_ai_domain_alias_from_evidence(self) -> None:
        candidate = CandidateProfile(
            experience=[
                ExperienceEntry(
                    highlights=[
                        "Built and evaluated machine learning models for churn prediction.",
                    ]
                )
            ]
        )
        requirements = RequirementProfile(
            skills=[
                RequirementSkill(
                    name="Model training and evaluation",
                    priority="required",
                )
            ]
        )
        alias_registry = SkillAliasRegistry(
            {
                "Model training and evaluation": [
                    "Built and evaluated machine learning models",
                ],
            }
        )

        matches = SkillMatcher(alias_registry=alias_registry).match(candidate, requirements)

        self.assertEqual(matches[0].candidate_skill, "Model training and evaluation")
        self.assertEqual(len(matches[0].evidence), 1)
        self.assertEqual(matches[0].evidence[0].source, "experience")
        self.assertEqual(
            matches[0].evidence[0].text,
            "Built and evaluated machine learning models for churn prediction.",
        )

    def test_matches_configured_customer_support_alias_from_evidence(self) -> None:
        candidate = CandidateProfile(
            experience=[
                ExperienceEntry(
                    highlights=[
                        "Assisted customers with technical issues during onboarding.",
                    ]
                )
            ]
        )
        requirements = RequirementProfile(
            skills=[
                RequirementSkill(
                    name="Customer support",
                    priority="required",
                )
            ]
        )
        alias_registry = SkillAliasRegistry(
            {
                "Customer support": [
                    "Assisted customers with technical issues",
                ],
            }
        )

        matches = SkillMatcher(alias_registry=alias_registry).match(candidate, requirements)

        self.assertEqual(matches[0].candidate_skill, "Customer support")
        self.assertEqual(len(matches[0].evidence), 1)
        self.assertEqual(matches[0].evidence[0].source, "experience")
        self.assertEqual(
            matches[0].evidence[0].text,
            "Assisted customers with technical issues during onboarding.",
        )
