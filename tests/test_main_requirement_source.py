import unittest
from unittest.mock import Mock, patch

from pydantic import ValidationError

from app.main import collect_requirement_source, main
from app.models import RequirementProfile
from app.requirements.source import RequirementSourceType


class MainRequirementSourceTest(unittest.TestCase):
    def test_pasted_text_source_includes_role_and_stops_at_end(self) -> None:
        answers = iter(["1", "First line", "Second line", "  END  ", "ignored"])

        source = collect_requirement_source("Product Manager", lambda prompt="": next(answers))

        self.assertEqual(source.source_type, RequirementSourceType.PASTED_TEXT)
        self.assertEqual(source.content, "First line\nSecond line")
        self.assertEqual(source.target_role, "Product Manager")

    def test_text_file_source_includes_role_and_path(self) -> None:
        answers = iter(["2", "requirements.txt"])

        source = collect_requirement_source("Nurse", lambda prompt="": next(answers))

        self.assertEqual(source.source_type, RequirementSourceType.TEXT_FILE)
        self.assertEqual(source.content, "requirements.txt")
        self.assertEqual(source.name, "requirements.txt")
        self.assertEqual(source.target_role, "Nurse")

    def test_empty_pasted_text_is_rejected_by_source_validation(self) -> None:
        answers = iter(["1", " ", "END"])

        with self.assertRaises(ValidationError):
            collect_requirement_source("Teacher", lambda prompt="": next(answers))

    def test_invalid_selection_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid requirement source selection"):
            collect_requirement_source("Teacher", lambda prompt="": "3")

    @patch("app.main.print_analysis")
    @patch("app.main.print_candidate_profile")
    @patch("app.main.parse_cv", return_value={"summary": "Candidate"})
    @patch("app.main.extract_text", return_value="CV text")
    @patch("app.main.analyze_cv")
    @patch("app.main.RequirementPipeline")
    @patch("builtins.input")
    def test_main_passes_source_to_pipeline_and_profile_to_analyzer(
        self,
        mock_input,
        pipeline_class,
        analyze_cv,
        _extract_text,
        _parse_cv,
        _print_candidate_profile,
        _print_analysis,
    ) -> None:
        mock_input.side_effect = [
            "candidate.pdf",
            "Accountant",
            "1",
            "Financial reporting experience required",
            "END",
        ]
        profile = RequirementProfile(title="Accountant")
        pipeline_class.return_value.build.return_value = profile
        analyze_cv.return_value = Mock(candidate_profile=Mock(), analysis={})

        main()

        source = pipeline_class.return_value.build.call_args.args[0]
        self.assertEqual(source.source_type, RequirementSourceType.PASTED_TEXT)
        self.assertEqual(source.target_role, "Accountant")
        analyze_cv.assert_called_once_with(
            "CV text", profile, {"summary": "Candidate"}
        )
        _print_candidate_profile.assert_called_once_with(
            analyze_cv.return_value.candidate_profile
        )
        _print_analysis.assert_called_once_with(analyze_cv.return_value.analysis)

    def test_main_has_no_static_role_profile_dependency(self) -> None:
        import app.main as main_module

        self.assertFalse(hasattr(main_module, "ROLE_PROFILE_DIR"))
        self.assertFalse(hasattr(main_module, "_build_legacy_role_requirements"))


if __name__ == "__main__":
    unittest.main()
