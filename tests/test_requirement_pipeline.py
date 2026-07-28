import unittest
from unittest.mock import Mock

from app.models import RequirementProfile, RequirementSkill
from app.requirements.pipeline import RequirementPipeline
from app.requirements.source import RequirementSource, RequirementSourceType


class RequirementPipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source = RequirementSource(
            source_type=RequirementSourceType.PASTED_TEXT,
            content="source content",
            target_role="Target role",
        )
        self.loaded_text = "loaded requirement text"
        self.extracted_profile = RequirementProfile(
            title="Target role",
            skills=[RequirementSkill(name=" Skill ", priority="required")],
        )
        self.normalized_profile = RequirementProfile(
            title="Target role",
            skills=[RequirementSkill(name="Skill", priority="required")],
        )
        self.loader = Mock()
        self.loader.load.return_value = self.loaded_text
        self.extractor = Mock(return_value=self.extracted_profile)
        self.requirement_filter = Mock()
        self.filtered_profile = RequirementProfile(
            title="Target role",
            skills=[RequirementSkill(name=" Skill ", priority="required")],
        )
        self.requirement_filter.filter.return_value = self.filtered_profile
        self.decomposer = Mock()
        self.decomposed_profile = RequirementProfile(
            title="Target role",
            skills=[RequirementSkill(name=" Skill ", priority="required")],
        )
        self.decomposer.decompose.return_value = self.decomposed_profile
        self.normalizer = Mock()
        self.normalizer.normalize.return_value = self.normalized_profile
        self.category_classifier = Mock()
        self.category_classifier.classify.return_value = "skill"
        self.classified_profile = RequirementProfile(
            title="Target role",
            skills=[
                RequirementSkill(
                    name="Skill", priority="required", category="skill"
                )
            ],
        )
        self.validated_profile = RequirementProfile(
            title="Target role",
            skills=[RequirementSkill(name="Skill", priority="required")],
        )
        self.validator = Mock()
        self.validator.validate.return_value = self.validated_profile
        self.pipeline = RequirementPipeline(
            loader=self.loader,
            extractor=self.extractor,
            requirement_filter=self.requirement_filter,
            decomposer=self.decomposer,
            normalizer=self.normalizer,
            category_classifier=self.category_classifier,
            validator=self.validator,
        )

    def test_passes_source_to_loader(self) -> None:
        self.pipeline.build(self.source)

        self.loader.load.assert_called_once_with(self.source)

    def test_passes_loaded_text_to_extractor(self) -> None:
        self.pipeline.build(self.source)

        self.extractor.assert_called_once_with("Target role", self.loaded_text)

    def test_passes_extracted_profile_to_filter(self) -> None:
        self.pipeline.build(self.source)

        self.requirement_filter.filter.assert_called_once_with(self.extracted_profile)

    def test_passes_filtered_profile_to_decomposer(self) -> None:
        self.pipeline.build(self.source)

        self.decomposer.decompose.assert_called_once_with(self.filtered_profile)

    def test_passes_decomposed_profile_to_normalizer(self) -> None:
        self.pipeline.build(self.source)

        self.normalizer.normalize.assert_called_once_with(self.decomposed_profile)

    def test_passes_normalized_profile_to_validator(self) -> None:
        self.pipeline.build(self.source)

        self.validator.validate.assert_called_once_with(self.classified_profile)

    def test_classifies_normalized_requirement_text(self) -> None:
        self.pipeline.build(self.source)

        self.category_classifier.classify.assert_called_once_with("Skill")

    def test_returns_validated_profile(self) -> None:
        result = self.pipeline.build(self.source)

        self.assertIs(result, self.validated_profile)

    def test_calls_components_in_order(self) -> None:
        calls: list[str] = []
        self.loader.load.side_effect = lambda source: calls.append("loader") or self.loaded_text
        self.extractor.side_effect = (
            lambda target_role, text: calls.append("extractor") or self.extracted_profile
        )
        self.requirement_filter.filter.side_effect = (
            lambda profile: calls.append("filter") or self.filtered_profile
        )
        self.decomposer.decompose.side_effect = (
            lambda profile: calls.append("decomposer") or self.decomposed_profile
        )
        self.normalizer.normalize.side_effect = (
            lambda profile: calls.append("normalizer") or self.normalized_profile
        )
        self.category_classifier.classify.side_effect = (
            lambda name: calls.append("classifier") or "skill"
        )
        self.validator.validate.side_effect = (
            lambda profile: calls.append("validator") or self.validated_profile
        )

        self.pipeline.build(self.source)

        self.assertEqual(
            calls,
            [
                "loader",
                "extractor",
                "filter",
                "decomposer",
                "normalizer",
                "classifier",
                "validator",
            ],
        )

    def test_loader_error_propagates_unchanged(self) -> None:
        error = RuntimeError("loader failed")
        self.loader.load.side_effect = error

        with self.assertRaises(RuntimeError) as context:
            self.pipeline.build(self.source)

        self.assertIs(context.exception, error)
        self.extractor.assert_not_called()
        self.requirement_filter.filter.assert_not_called()
        self.decomposer.decompose.assert_not_called()
        self.normalizer.normalize.assert_not_called()
        self.validator.validate.assert_not_called()

    def test_filter_error_propagates_unchanged(self) -> None:
        error = RuntimeError("filter failed")
        self.requirement_filter.filter.side_effect = error

        with self.assertRaises(RuntimeError) as context:
            self.pipeline.build(self.source)

        self.assertIs(context.exception, error)
        self.decomposer.decompose.assert_not_called()
        self.normalizer.normalize.assert_not_called()
        self.validator.validate.assert_not_called()

    def test_validator_error_propagates_unchanged(self) -> None:
        error = RuntimeError("validator failed")
        self.validator.validate.side_effect = error

        with self.assertRaises(RuntimeError) as context:
            self.pipeline.build(self.source)

        self.assertIs(context.exception, error)

    def test_extractor_error_propagates_unchanged(self) -> None:
        error = RuntimeError("extractor failed")
        self.extractor.side_effect = error

        with self.assertRaises(RuntimeError) as context:
            self.pipeline.build(self.source)

        self.assertIs(context.exception, error)
        self.normalizer.normalize.assert_not_called()
        self.validator.validate.assert_not_called()

    def test_decomposer_error_propagates_unchanged(self) -> None:
        error = RuntimeError("decomposer failed")
        self.decomposer.decompose.side_effect = error

        with self.assertRaises(RuntimeError) as context:
            self.pipeline.build(self.source)

        self.assertIs(context.exception, error)
        self.normalizer.normalize.assert_not_called()
        self.validator.validate.assert_not_called()

    def test_normalizer_error_propagates_unchanged(self) -> None:
        error = RuntimeError("normalizer failed")
        self.normalizer.normalize.side_effect = error

        with self.assertRaises(RuntimeError) as context:
            self.pipeline.build(self.source)

        self.assertIs(context.exception, error)
        self.validator.validate.assert_not_called()

    def test_office_administrator_text_produces_clean_requirements(self) -> None:
        pipeline = RequirementPipeline()
        source = RequirementSource(
            source_type=RequirementSourceType.PASTED_TEXT,
            target_role="Office Administrator",
            content="""
Responsibilities
- Coordinate meetings and office supplies
Requirements
- Calendar management
- Excellent written and verbal communication
- Problem-solving skills
- Requirements
Preferred
- Document management
""",
        )

        profile = pipeline.build(source)

        self.assertEqual(
            [(skill.name, skill.priority) for skill in profile.skills],
            [
                ("Calendar management", "required"),
                ("Excellent written and verbal communication", "required"),
                ("Problem-solving skills", "required"),
                ("Document management", "preferred"),
            ],
        )
        self.assertNotIn("Excellent written", [skill.name for skill in profile.skills])

    def test_realistic_job_description_filters_non_requirement_sections(self) -> None:
        source = RequirementSource(
            source_type=RequirementSourceType.PASTED_TEXT,
            target_role="Generalist",
            content="""
Responsibilities
- Deliver services
Requirements
- Python
- Willingness to relocate
Preferred Qualifications
- Stakeholder communication
Salary
- Competitive salary based on experience
Benefits
- Health and dental insurance
About Us
- A collaborative and inclusive workplace
Equal Opportunity
- We are an equal opportunity employer
How to Apply
- Please submit your CV and cover letter
""",
        )

        profile = RequirementPipeline().build(source)

        self.assertEqual(
            [(skill.name, skill.priority) for skill in profile.skills],
            [
                ("Python", "required"),
                ("Willingness to relocate", "required"),
                ("Stakeholder communication", "preferred"),
            ],
        )

    def test_dynamic_job_descriptions_preserve_only_their_own_alternatives(self) -> None:
        pipeline = RequirementPipeline()
        finance_source = RequirementSource(
            source_type=RequirementSourceType.PASTED_TEXT,
            target_role="Financial Analyst",
            content="""
Requirements
- Degree in Accounting, Finance, Economics, or a related field
- Experience with budgeting and financial reporting
""",
        )
        healthcare_source = RequirementSource(
            source_type=RequirementSourceType.PASTED_TEXT,
            target_role="Clinical Coordinator",
            content="""
Requirements
- Degree in Nursing or another recognized healthcare discipline
- Professional proficiency in English or German
""",
        )

        finance_profile = pipeline.build(finance_source)
        healthcare_profile = pipeline.build(healthcare_source)

        self.assertEqual(
            [skill.name for skill in finance_profile.skills],
            [
                "Degree in Accounting, Finance, Economics, or a related field",
                "Budgeting",
                "Financial reporting",
            ],
        )
        self.assertEqual(
            [skill.name for skill in healthcare_profile.skills],
            [
                "Degree in Nursing or another recognized healthcare discipline",
                "Professional proficiency in English or German",
            ],
        )
        self.assertNotIn(
            finance_profile.skills[0].name,
            [skill.name for skill in healthcare_profile.skills],
        )

    def test_target_role_does_not_change_extracted_requirements(self) -> None:
        content = """
Requirements
- Experience with AWS, Azure, or another cloud platform
"""
        first = RequirementPipeline().build(
            RequirementSource(
                source_type=RequirementSourceType.PASTED_TEXT,
                target_role="Platform Specialist",
                content=content,
            )
        )
        second = RequirementPipeline().build(
            RequirementSource(
                source_type=RequirementSourceType.PASTED_TEXT,
                target_role="Unrelated Title",
                content=content,
            )
        )

        self.assertEqual(first.skills, second.skills)
        self.assertEqual(
            [skill.name for skill in first.skills],
            ["Experience with AWS, Azure, or another cloud platform"],
        )

    def test_assigns_categories_without_changing_names_or_priorities(self) -> None:
        source = RequirementSource(
            source_type=RequirementSourceType.PASTED_TEXT,
            target_role="Any title",
            content="""
Requirements
- Bachelor's degree required
- Strong communication skills
Preferred
- Experience using inventory systems
""",
        )

        profile = RequirementPipeline().build(source)

        self.assertEqual(
            [
                (skill.name, skill.priority, skill.category)
                for skill in profile.skills
            ],
            [
                ("Bachelor's degree required", "required", "education"),
                ("Strong communication skills", "required", "soft_skill"),
                (
                    "Experience using inventory systems",
                    "preferred",
                    "tool",
                ),
            ],
        )

if __name__ == "__main__":
    unittest.main()
