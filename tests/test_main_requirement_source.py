import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import Mock, patch

from pydantic import ValidationError

from app.application import (
    AnalysisExecutionError,
    CVProcessingError,
    InvalidCVSourceError,
    RequirementProcessingError,
)
from app.main import collect_requirement_source, main
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
    @patch("app.main.create_application_service")
    @patch("builtins.input")
    def test_main_builds_request_calls_service_once_and_renders_response(
        self,
        mock_input,
        create_service,
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
        candidate_profile = Mock()
        analysis = Mock()
        analysis.model_dump.return_value = {"overall_match_score": 80}
        create_service.return_value.analyze.return_value = Mock(
            candidate_profile=candidate_profile,
            analysis=analysis,
        )

        main()

        create_service.assert_called_once_with()
        service = create_service.return_value
        service.analyze.assert_called_once()
        request = service.analyze.call_args.args[0]
        self.assertEqual(str(request.cv_source.file_path), "candidate.pdf")
        self.assertEqual(request.target_role, "Accountant")
        self.assertEqual(
            request.requirement_source.source_type,
            RequirementSourceType.PASTED_TEXT,
        )
        self.assertEqual(request.requirement_source.target_role, "Accountant")
        _print_candidate_profile.assert_called_once_with(candidate_profile)
        _print_analysis.assert_called_once_with(
            {"overall_match_score": 80}
        )

    def test_main_maps_expected_application_errors_without_traceback(self) -> None:
        cases = (
            (
                InvalidCVSourceError("bad CV"),
                "Invalid CV source: bad CV",
            ),
            (
                CVProcessingError("cannot read"),
                "CV processing error: cannot read",
            ),
            (
                RequirementProcessingError("bad requirements"),
                "Requirement processing error: bad requirements",
            ),
            (
                AnalysisExecutionError("analysis failed"),
                "Analysis execution error: analysis failed",
            ),
        )

        for error, expected_message in cases:
            with self.subTest(error=type(error).__name__):
                answers = iter(
                    [
                        "candidate.pdf",
                        "Accountant",
                        "1",
                        "Financial reporting experience required",
                        "END",
                    ]
                )
                service = Mock()
                service.analyze.side_effect = error
                output = StringIO()

                with (
                    patch("builtins.input", side_effect=answers),
                    patch(
                        "app.main.create_application_service",
                        return_value=service,
                    ),
                    redirect_stdout(output),
                ):
                    main()

                rendered = output.getvalue()
                self.assertIn(expected_message, rendered)
                self.assertNotIn("Traceback", rendered)
                service.analyze.assert_called_once()

    def test_main_does_not_orchestrate_pipeline_components(self) -> None:
        import inspect
        import app.main as main_module

        source = inspect.getsource(main_module.main)

        self.assertNotIn("analyze_cv(", source)
        self.assertNotIn("RequirementPipeline(", source)
        self.assertNotIn("extract_text(", source)
        self.assertNotIn("parse_cv(", source)

    def test_main_has_no_static_role_profile_dependency(self) -> None:
        import app.main as main_module

        self.assertFalse(hasattr(main_module, "ROLE_PROFILE_DIR"))
        self.assertFalse(hasattr(main_module, "_build_legacy_role_requirements"))


if __name__ == "__main__":
    unittest.main()
