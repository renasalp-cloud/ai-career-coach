import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

import app.ai.analyzer as analyzer


def _learning_roadmap(weeks: int = 4) -> list[dict]:
    return [
        {
            "week": week,
            "goal": "Practice deployment",
            "topics": ["Docker"],
            "practical_task": "Containerize a simple API.",
            "expected_outcome": "A working containerized API.",
        }
        for week in range(1, weeks + 1)
    ]


def _complete_response_json() -> str:
    return json.dumps(
        {
            "overall_match_score": 80,
            "professional_summary": "Candidate has relevant experience.",
            "strengths": [
                {
                    "title": "Python",
                    "evidence": "Python appears in the profile.",
                }
            ],
            "missing_skills": {
                "critical": [],
                "important": [],
                "optional": [],
            },
            "career_gap_analysis": "The candidate needs more deployment evidence.",
            "recommendations": [
                {
                    "priority": "high",
                    "title": "Build a deployment project",
                    "reason": "Deployment evidence is limited.",
                    "action": "Deploy one API with Docker.",
                }
            ],
            "learning_roadmap": _learning_roadmap(),
        }
    )


def _invalid_response_json() -> str:
    response = json.loads(_complete_response_json())
    response["learning_roadmap"] = _learning_roadmap(3)
    return json.dumps(response)


class AnalyzerValidationRepairTest(unittest.TestCase):
    def _capture_failed_repair(
        self,
        artifact_path: Path,
    ) -> analyzer.CareerAnalysisGenerationError:
        with (
            patch.object(analyzer, "generate", return_value="{}"),
            patch.object(analyzer, "DEBUG_ARTIFACT_PATH", artifact_path),
            self.assertRaises(analyzer.CareerAnalysisGenerationError) as raised,
        ):
            analyzer._validate_analysis_response(
                json_text=_invalid_response_json(),
                original_prompt="original prompt",
            )

        return raised.exception

    def test_valid_analysis_root_passes_without_retry(self) -> None:
        original_generate = analyzer.generate

        def unexpected_generate(prompt: str) -> str:
            raise AssertionError("generate should not be called")

        try:
            analyzer.generate = unexpected_generate
            analysis = analyzer._validate_analysis_response(
                _complete_response_json(),
                "original prompt",
            )
        finally:
            analyzer.generate = original_generate

        self.assertEqual(analysis.overall_match_score, 80)

    def test_wrong_root_retries_original_prompt_once_without_repair(self) -> None:
        prompts: list[str] = []
        original_generate = analyzer.generate

        def fake_generate(prompt: str) -> str:
            prompts.append(prompt)
            return _complete_response_json()

        try:
            analyzer.generate = fake_generate
            analysis = analyzer._validate_analysis_response(
                json.dumps({"candidate_profile": {"skills": []}}),
                "original prompt",
            )
        finally:
            analyzer.generate = original_generate

        self.assertEqual(prompts, ["original prompt"])
        self.assertEqual(analysis.overall_match_score, 80)

    def test_wrong_root_after_retry_raises_clear_exception(self) -> None:
        prompts: list[str] = []
        original_generate = analyzer.generate

        def fake_generate(prompt: str) -> str:
            prompts.append(prompt)
            return "{}"

        try:
            analyzer.generate = fake_generate
            with self.assertRaisesRegex(
                analyzer.CareerAnalysisGenerationError,
                "required CareerAnalysis root keys after one retry",
            ):
                analyzer._validate_analysis_response("not json", "original prompt")
        finally:
            analyzer.generate = original_generate

        self.assertEqual(prompts, ["original prompt"])

    def test_invalid_analysis_json_triggers_one_successful_repair_attempt(self) -> None:
        invalid_json = json.dumps(
            {
                "overall_match_score": 80,
                "professional_summary": "Candidate has relevant experience.",
                "strengths": [],
                "missing_skills": {"critical": [], "important": [], "optional": []},
                "career_gap_analysis": "Gap analysis is present.",
                "recommendations": [],
                "learning_roadmap": _learning_roadmap(3),
            }
        )
        prompts: list[str] = []
        original_prompt = "Original analysis prompt with candidate profile evidence."
        original_generate = analyzer.generate

        def fake_generate(prompt: str) -> str:
            prompts.append(prompt)
            return _complete_response_json()

        try:
            analyzer.generate = fake_generate

            analysis = analyzer._validate_analysis_response(
                json_text=invalid_json,
                original_prompt=original_prompt,
            )
        finally:
            analyzer.generate = original_generate

        self.assertEqual(len(prompts), 1)
        self.assertIn(invalid_json, prompts[0])
        self.assertIn(original_prompt, prompts[0])
        self.assertIn("<ORIGINAL_REQUEST>", prompts[0])
        self.assertIn("<INVALID_RESPONSE>", prompts[0])
        self.assertIn("Do not return input structures such as:", prompts[0])
        self.assertIn("Validation errors:", prompts[0])
        self.assertIn("Required schema:", prompts[0])
        self.assertEqual(analysis.overall_match_score, 80)
        self.assertEqual(analysis.learning_roadmap[0].week, 1)

    def test_failed_repair_raises_clear_exception_after_one_attempt(self) -> None:
        invalid_json = _invalid_response_json()
        original_prompt = "Original analysis prompt with candidate profile evidence."
        original_generate = analyzer.generate
        prompts: list[str] = []

        def fake_generate(prompt: str) -> str:
            prompts.append(prompt)
            return "{}"

        with tempfile.TemporaryDirectory() as temporary_directory:
            original_artifact_path = analyzer.DEBUG_ARTIFACT_PATH
            try:
                analyzer.generate = fake_generate
                analyzer.DEBUG_ARTIFACT_PATH = (
                    Path(temporary_directory) / "debug" / "last_failed_analysis.json"
                )

                with self.assertRaisesRegex(
                    analyzer.CareerAnalysisGenerationError,
                    "schema validation failed after one repair attempt",
                ):
                    analyzer._validate_analysis_response(
                        json_text=invalid_json,
                        original_prompt=original_prompt,
                    )
            finally:
                analyzer.generate = original_generate
                analyzer.DEBUG_ARTIFACT_PATH = original_artifact_path

        self.assertEqual(len(prompts), 1)
        self.assertIn("Repair formatting and structure only", prompts[0])

    def test_failed_repair_preserves_original_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            error = self._capture_failed_repair(
                Path(temporary_directory) / "debug" / "last_failed_analysis.json"
            )

        self.assertIsInstance(error.original_error, ValidationError)
        self.assertIn("learning_roadmap", str(error.original_error.errors()))

    def test_failed_repair_preserves_repaired_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            error = self._capture_failed_repair(
                Path(temporary_directory) / "debug" / "last_failed_analysis.json"
            )

        self.assertIsInstance(error.repair_error, ValidationError)
        self.assertIn("overall_match_score", str(error.repair_error.errors()))

    def test_final_exception_includes_both_failure_stages_and_responses(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            error = self._capture_failed_repair(
                Path(temporary_directory) / "debug" / "last_failed_analysis.json"
            )

        message = str(error)
        self.assertIn("Original Validation Errors:", message)
        self.assertIn("Repaired Validation Errors:", message)
        self.assertIn("Original Response:", message)
        self.assertIn(_invalid_response_json(), message)
        self.assertIn("Repaired Response:\n{}", message)

    def test_failed_repair_creates_debug_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact_path = (
                Path(temporary_directory) / "debug" / "last_failed_analysis.json"
            )
            self._capture_failed_repair(artifact_path)
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))

        self.assertEqual(artifact["original_response"], _invalid_response_json())
        self.assertTrue(artifact["original_errors"])
        self.assertEqual(artifact["repaired_response"], "{}")
        self.assertTrue(artifact["repaired_errors"])

    def test_successful_analysis_does_not_create_debug_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact_path = (
                Path(temporary_directory) / "debug" / "last_failed_analysis.json"
            )
            with patch.object(analyzer, "DEBUG_ARTIFACT_PATH", artifact_path):
                analyzer._validate_analysis_response(
                    _complete_response_json(),
                    "original prompt",
                )

            self.assertFalse(artifact_path.exists())
