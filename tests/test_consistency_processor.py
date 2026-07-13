import unittest

from app.analysis.consistency_processor import AnalysisConsistencyProcessor
from app.candidate_profile.models import CandidateProfile, EducationEntry, ExperienceEntry, SkillEntry
from app.models import CareerAnalysis, Recommendation, RequirementProfile, RequirementSkill, SkillEvidence, SkillMatch, Strength


def _analysis(summary: str = "Candidate has relevant experience.", gap: str = "Docker is missing.") -> CareerAnalysis:
    return CareerAnalysis(
        overall_match_score=70,
        professional_summary=summary,
        strengths=[],
        missing_skills={
            "critical": [{"skill": "Machine Learning", "reason": "Missing."}],
            "important": [{"skill": "ML", "reason": "Missing alias."}],
            "optional": [],
        },
        career_gap_analysis=gap,
        recommendations=[],
        learning_roadmap=[
            {"week": week, "goal": "Learn", "topics": [], "practical_task": "Practice", "expected_outcome": "Evidence"}
            for week in range(1, 5)
        ],
    )


def _requirements() -> RequirementProfile:
    return RequirementProfile(
        skills=[
            RequirementSkill(name="Machine Learning", priority="required"),
            RequirementSkill(name="Docker", priority="preferred"),
        ]
    )


class AnalysisConsistencyProcessorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.processor = AnalysisConsistencyProcessor()

    def test_demonstrated_role_skill_is_removed_from_missing_skills(self) -> None:
        result = self.processor.process(
            _analysis(), CandidateProfile(), _requirements(),
            [SkillMatch(role_skill="Machine Learning", candidate_skill="ML", status="demonstrated")],
        )
        self.assertEqual(result.missing_skills.critical, [])

    def test_demonstrated_candidate_alias_is_removed_from_missing_skills(self) -> None:
        analysis = _analysis()
        self.processor._remove_demonstrated_skills(
            analysis,
            self.processor._demonstrated_names([
                SkillMatch(role_skill="Machine Learning", candidate_skill="ML", status="demonstrated")
            ]),
        )
        self.assertEqual(analysis.missing_skills.important, [])

    def test_contradictory_gap_is_replaced_with_only_missing_requirements(self) -> None:
        result = self.processor.process(
            _analysis(gap="The candidate lacks Machine Learning experience."),
            CandidateProfile(), _requirements(),
            [
                SkillMatch(role_skill="Machine Learning", candidate_skill="ML", status="demonstrated"),
                SkillMatch(role_skill="Docker", status="missing"),
            ],
        )
        self.assertEqual(result.career_gap_analysis, "Validated missing requirements: Docker.")

    def test_valid_gap_is_preserved(self) -> None:
        gap = "Docker is missing, while Machine Learning is demonstrated."
        result = self.processor.process(
            _analysis(gap=gap), CandidateProfile(), _requirements(),
            [
                SkillMatch(role_skill="Machine Learning", status="demonstrated"),
                SkillMatch(role_skill="Docker", status="missing"),
            ],
        )
        self.assertEqual(result.career_gap_analysis, gap)

    def test_unsupported_professional_title_is_replaced(self) -> None:
        result = self.processor.process(
            _analysis(summary="A data scientist with strong analytical skills."),
            CandidateProfile(experience=[ExperienceEntry(title="Research Assistant")]),
            _requirements(), [],
        )
        self.assertNotIn("data scientist", result.professional_summary.lower())

    def test_present_professional_title_is_preserved(self) -> None:
        summary = "A research assistant with strong analytical skills."
        result = self.processor.process(
            _analysis(summary=summary),
            CandidateProfile(experience=[ExperienceEntry(title="Research Assistant")]),
            _requirements(), [],
        )
        self.assertEqual(result.professional_summary, summary)

    def test_generic_candidate_description_is_preserved(self) -> None:
        summary = "A motivated candidate with strong analytical skills."
        result = self.processor.process(
            _analysis(summary=summary), CandidateProfile(), _requirements(), []
        )
        self.assertEqual(result.professional_summary, summary)

    def test_deterministic_summary_uses_only_real_profile_facts(self) -> None:
        profile = CandidateProfile(
            education=[
                EducationEntry(degree="BSc Mathematics", institution="Real University", status="completed"),
                EducationEntry(degree="MSc Statistics", institution="Other University", status="current"),
            ],
            experience=[ExperienceEntry(organization="Real Employer", title="Research Assistant", start_date="2024")],
            certifications=["Analytics Bootcamp"],
            projects=["Secret project"],
        )
        result = self.processor.process(
            _analysis(summary="A senior engineer with ten years at Invented Corp."),
            profile, _requirements(),
            [SkillMatch(role_skill="Machine Learning", candidate_skill="ML", status="demonstrated")],
        )
        summary = result.professional_summary
        for expected in ("BSc Mathematics", "MSc Statistics", "Research Assistant", "Analytics Bootcamp", "ML"):
            self.assertIn(expected, summary)
        for excluded in ("Real University", "Other University", "Real Employer", "2024", "Secret project", "senior engineer", "ten years", "Invented Corp"):
            self.assertNotIn(excluded, summary)

    def test_unsupported_open_source_strength_is_removed(self) -> None:
        analysis = _analysis()
        analysis.strengths = [
            Strength(title="Open source contributions", evidence="Contributed to public projects."),
        ]

        result = self.processor.process(analysis, CandidateProfile(), _requirements(), [])

        self.assertEqual(result.strengths, [])

    def test_unsupported_research_publication_strength_is_removed(self) -> None:
        analysis = _analysis()
        analysis.strengths = [
            Strength(title="Published research", evidence="Authored research publications."),
        ]

        result = self.processor.process(analysis, CandidateProfile(), _requirements(), [])

        self.assertEqual(result.strengths, [])

    def test_supported_strength_is_preserved(self) -> None:
        analysis = _analysis()
        analysis.strengths = [Strength(title="Python", evidence="Used Python for automation.")]
        profile = CandidateProfile(
            skills=[SkillEntry(name="Python")],
            experience=[ExperienceEntry(highlights=["Used Python for automation."])],
        )

        result = self.processor.process(analysis, profile, _requirements(), [])

        self.assertEqual(result.strengths[0].title, "Python")

    def test_unsupported_proficient_qualifier_is_replaced(self) -> None:
        analysis = _analysis()
        analysis.strengths = [
            Strength(title="Proficient in Python", evidence="Proficient Python user.")
        ]
        profile = CandidateProfile(skills=[SkillEntry(name="Python")])

        result = self.processor.process(analysis, profile, _requirements(), [])

        self.assertEqual(result.strengths[0].model_dump(), {
            "title": "Python",
            "evidence": "Python is listed in the candidate profile.",
        })

    def test_unsupported_strong_qualifier_is_replaced(self) -> None:
        analysis = _analysis()
        analysis.strengths = [
            Strength(title="Strong Python skills", evidence="Strong command of Python.")
        ]
        profile = CandidateProfile(skills=[SkillEntry(name="Python")])

        result = self.processor.process(analysis, profile, _requirements(), [])

        strength_text = " ".join(result.strengths[0].model_dump().values()).lower()
        self.assertNotIn("strong", strength_text)
        self.assertIn("python", strength_text)

    def test_supported_neutral_strength_wording_is_preserved(self) -> None:
        strength = Strength(
            title="Data preprocessing",
            evidence="Data preprocessing is demonstrated in experience evidence.",
        )
        analysis = _analysis()
        analysis.strengths = [strength]
        profile = CandidateProfile(
            experience=[ExperienceEntry(
                highlights=["Performed data preprocessing for reporting."]
            )]
        )

        result = self.processor.process(analysis, profile, _requirements(), [])

        self.assertEqual(result.strengths[0], strength)

    def test_empty_strengths_are_rebuilt_from_demonstrated_evidence(self) -> None:
        match = SkillMatch(
            role_skill="Python", candidate_skill="Python", status="demonstrated",
            evidence=[SkillEvidence(source="experience", text="Developed Python services.")],
        )

        result = self.processor.process(_analysis(), CandidateProfile(), _requirements(), [match])

        self.assertEqual(result.strengths[0].model_dump(), {
            "title": "Python", "evidence": "Developed Python services."
        })

    def test_demonstrated_skills_are_removed_from_recommendations_and_roadmap(self) -> None:
        analysis = _analysis()
        analysis.recommendations = [Recommendation(
            priority="high", title="Learn Python", reason="Python is needed.",
            action="Take a Python course.",
        )]
        analysis.learning_roadmap[0].goal = "Master Python"
        analysis.learning_roadmap[0].topics = ["Python", "Docker"]
        analysis.learning_roadmap[0].practical_task = "Build a Python application"
        analysis.learning_roadmap[0].expected_outcome = "Advanced Python knowledge"
        match = SkillMatch(role_skill="Python", candidate_skill="Python", status="demonstrated")

        result = self.processor.process(
            analysis,
            CandidateProfile(),
            _requirements(),
            [match, SkillMatch(role_skill="Docker", status="missing")],
        )

        self.assertEqual(len(result.recommendations), 1)
        self.assertIn("Docker", result.recommendations[0].title)
        self.assertNotIn("Python", str(result.recommendations[0].model_dump()))
        self.assertEqual(result.learning_roadmap[0].topics, ["Docker"])
        for value in (
            result.learning_roadmap[0].goal,
            result.learning_roadmap[0].practical_task,
            result.learning_roadmap[0].expected_outcome,
        ):
            self.assertNotIn("python", value.lower())

    def test_recommendations_include_only_deterministic_missing_skills(self) -> None:
        analysis = _analysis()
        analysis.recommendations = [Recommendation(
            priority="high",
            title="Improve Python and Docker",
            reason="Both skills support the role.",
            action="Build a Python and Docker exercise.",
        )]
        matches = [
            SkillMatch(role_skill="Machine Learning", status="demonstrated"),
            SkillMatch(role_skill="Docker", status="missing"),
            SkillMatch(role_skill="Python", status="demonstrated"),
        ]

        result = self.processor.process(
            analysis, CandidateProfile(), _requirements(), matches
        )

        recommendation_text = " ".join(
            f"{item.title} {item.reason} {item.action}"
            for item in result.recommendations
        ).lower()
        self.assertIn("docker", recommendation_text)
        self.assertNotIn("python", recommendation_text)
        self.assertNotIn("machine learning", recommendation_text)

    def test_recommendations_split_more_than_three_missing_skills(self) -> None:
        skills = ["Docker", "Kubernetes", "Monitoring", "Cloud deployment"]
        requirements = RequirementProfile(skills=[
            RequirementSkill(name=skill, priority="required") for skill in skills
        ])
        analysis = _analysis()
        analysis.recommendations = [Recommendation(
            priority="high",
            title="Learn Docker, Kubernetes, Monitoring, and Cloud deployment",
            reason="These four areas are needed.",
            action="Complete training in Docker, Kubernetes, Monitoring, and Cloud deployment.",
        )]

        result = self.processor.process(
            analysis,
            CandidateProfile(),
            requirements,
            [SkillMatch(role_skill=skill, status="missing") for skill in skills],
        )

        self.assertEqual(len(result.recommendations), 4)
        recommendation_texts = [
            f"{item.title} {item.reason} {item.action}".lower()
            for item in result.recommendations
        ]
        for skill in skills:
            self.assertTrue(
                any(skill.lower() in text for text in recommendation_texts)
            )

    def test_roadmap_removes_internal_system_wording(self) -> None:
        analysis = _analysis()
        for week in analysis.learning_roadmap:
            week.goal = "Address validated missing requirement Docker"
            week.topics = ["Docker", "pipeline output"]
            week.practical_task = "Use deterministic evidence for Docker"
            week.expected_outcome = "Complete schema validation for Docker"

        result = self.processor.process(
            analysis,
            CandidateProfile(),
            _requirements(),
            [SkillMatch(role_skill="Docker", status="missing")],
        )

        roadmap_text = str([week.model_dump() for week in result.learning_roadmap]).lower()
        for phrase in (
            "validated missing requirement",
            "deterministic evidence",
            "pipeline output",
            "schema validation",
        ):
            self.assertNotIn(phrase, roadmap_text)
        self.assertIn("work sample", roadmap_text)


if __name__ == "__main__":
    unittest.main()
