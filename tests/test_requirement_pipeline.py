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
        self.normalizer = Mock()
        self.normalizer.normalize.return_value = self.normalized_profile
        self.validated_profile = RequirementProfile(
            title="Target role",
            skills=[RequirementSkill(name="Skill", priority="required")],
        )
        self.validator = Mock()
        self.validator.validate.return_value = self.validated_profile
        self.pipeline = RequirementPipeline(
            loader=self.loader,
            extractor=self.extractor,
            normalizer=self.normalizer,
            validator=self.validator,
        )

    def test_passes_source_to_loader(self) -> None:
        self.pipeline.build(self.source)

        self.loader.load.assert_called_once_with(self.source)

    def test_passes_loaded_text_to_extractor(self) -> None:
        self.pipeline.build(self.source)

        self.extractor.assert_called_once_with("Target role", self.loaded_text)

    def test_passes_extracted_profile_to_normalizer(self) -> None:
        self.pipeline.build(self.source)

        self.normalizer.normalize.assert_called_once_with(self.extracted_profile)

    def test_passes_normalized_profile_to_validator(self) -> None:
        self.pipeline.build(self.source)

        self.validator.validate.assert_called_once_with(self.normalized_profile)

    def test_returns_validated_profile(self) -> None:
        result = self.pipeline.build(self.source)

        self.assertIs(result, self.validated_profile)

    def test_calls_components_in_order(self) -> None:
        calls: list[str] = []
        self.loader.load.side_effect = lambda source: calls.append("loader") or self.loaded_text
        self.extractor.side_effect = (
            lambda target_role, text: calls.append("extractor") or self.extracted_profile
        )
        self.normalizer.normalize.side_effect = (
            lambda profile: calls.append("normalizer") or self.normalized_profile
        )
        self.validator.validate.side_effect = (
            lambda profile: calls.append("validator") or self.validated_profile
        )

        self.pipeline.build(self.source)

        self.assertEqual(calls, ["loader", "extractor", "normalizer", "validator"])

    def test_loader_error_propagates_unchanged(self) -> None:
        error = RuntimeError("loader failed")
        self.loader.load.side_effect = error

        with self.assertRaises(RuntimeError) as context:
            self.pipeline.build(self.source)

        self.assertIs(context.exception, error)
        self.extractor.assert_not_called()
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

    def test_normalizer_error_propagates_unchanged(self) -> None:
        error = RuntimeError("normalizer failed")
        self.normalizer.normalize.side_effect = error

        with self.assertRaises(RuntimeError) as context:
            self.pipeline.build(self.source)

        self.assertIs(context.exception, error)
        self.validator.validate.assert_not_called()

if __name__ == "__main__":
    unittest.main()
