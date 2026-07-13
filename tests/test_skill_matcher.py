import unittest

from app.candidate_profile.models import ExperienceEntry, SkillEntry
from app.models import CandidateProfile, RequirementProfile, RequirementSkill, SkillEvidence
from app.semantic.alias_registry import SkillAliasRegistry
from app.semantic.matcher import SkillMatcher


class FakeEvidenceCollector:
    def __init__(self) -> None:
        self.call_count = 0

    def collect(self, candidate: CandidateProfile) -> list[SkillEvidence]:
        self.call_count += 1
        return [
            SkillEvidence(
                source="skills",
                text="Python",
            ),
            SkillEvidence(
                source="experience",
                text="Used Python for data preprocessing",
            ),
            SkillEvidence(
                source="experience",
                text="Built Docker containers",
            ),
        ]


class SkillMatcherTest(unittest.TestCase):
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
        self.assertEqual(match.evidence[0].source, "training")

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
                {"source": "skills", "text": "Python"},
                {"source": "experience", "text": "Used Python for data preprocessing"},
            ],
        )
        self.assertEqual(matches[1].candidate_skill, "Docker")
        self.assertEqual(
            [item.model_dump() for item in matches[1].evidence],
            [
                {"source": "experience", "text": "Built Docker containers"},
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
