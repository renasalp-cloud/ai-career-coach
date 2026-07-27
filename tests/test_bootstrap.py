import importlib
import inspect
import sys
import unittest
from unittest.mock import patch

from app.ai import analyzer
from app.ai.ollama_provider import generate
from app.application import ApplicationService, CareerAnalysisApplicationService


class BootstrapTest(unittest.TestCase):
    def test_import_has_no_execution_side_effects(self) -> None:
        sys.modules.pop("app.bootstrap", None)

        with (
            patch("builtins.input") as input_mock,
            patch("app.ai.analyzer.analyze_cv") as analyze_mock,
            patch("app.ai.ollama_provider.generate") as provider_mock,
        ):
            importlib.import_module("app.bootstrap")

        input_mock.assert_not_called()
        analyze_mock.assert_not_called()
        provider_mock.assert_not_called()

    def test_factory_returns_concrete_application_service(self) -> None:
        from app.bootstrap import create_application_service

        service = create_application_service()

        self.assertIsInstance(service, ApplicationService)
        self.assertIsInstance(service, CareerAnalysisApplicationService)

    def test_factory_wires_current_provider_through_analyzer(self) -> None:
        from app.bootstrap import create_application_service

        service = create_application_service()

        self.assertIs(service._analyzer, analyzer.analyze_cv)
        self.assertIs(analyzer.generate, generate)

    def test_main_uses_factory_without_constructing_dependency_graph(self) -> None:
        import app.main as main_module

        source = inspect.getsource(main_module)

        self.assertIn("create_application_service().analyze(request)", source)
        self.assertNotIn("CareerAnalysisApplicationService(", source)
        self.assertNotIn("RequirementPipeline(", source)
        self.assertNotIn("def _create_application_service(", source)


if __name__ == "__main__":
    unittest.main()
