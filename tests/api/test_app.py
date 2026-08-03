import importlib
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.application import (
    AnalysisExecutionError,
    AnalysisResponse,
    ApplicationService,
    CVProcessingError,
    InvalidCVSourceError,
    RequirementProcessingError,
)
from app.candidate_profile.models import CandidateProfile
from app.models import CareerAnalysis


PDF_BYTES = b"%PDF-1.4\n% transport-only test payload\n%%EOF"


def _analysis_response() -> AnalysisResponse:
    return AnalysisResponse(
        candidate_profile=CandidateProfile(
            summary="Structured candidate",
            education=[
                {
                    "degree": "Bachelor degree",
                    "institution": "Example University",
                    "start_date": "2016",
                    "end_date": "2020",
                    "status": "completed",
                }
            ],
            experience=[
                {
                    "organization": "Example Organization",
                    "title": "Coordinator",
                    "start_date": "2020",
                    "end_date": "2024",
                    "location": "Remote",
                    "highlights": ["Coordinated cross-functional delivery"],
                }
            ],
            skills=[{"name": "Planning", "source": "skills"}],
            languages=["English"],
            projects=["Workflow improvement"],
            certifications=[],
        ),
        analysis=CareerAnalysis(
            overall_match_score=75,
            professional_summary="Structured analysis",
            strengths=[
                {
                    "title": "Planning",
                    "evidence": "Coordinated cross-functional delivery",
                }
            ],
            missing_skills={
                "critical": [
                    {
                        "skill": "Written communication",
                        "reason": "No supporting evidence was found.",
                    }
                ],
                "important": [],
                "optional": [],
            },
            career_gap_analysis="No material gaps.",
            recommendations=[
                {
                    "priority": "required",
                    "title": "Build written communication evidence",
                    "reason": "The requirement is currently missing.",
                    "action": "Create a concise written project update.",
                }
            ],
            learning_roadmap=[
                {
                    "week": week,
                    "goal": "Improve written communication",
                    "topics": ["Clear structure"] if week == 1 else [],
                    "practical_task": "Draft a project update",
                    "expected_outcome": "A concise written artifact",
                }
                for week in range(1, 5)
            ],
        ),
    )


def _multipart_data() -> dict[str, str]:
    return {
        "target_role": "  Operations Manager  ",
        "job_description": "  Clear written communication  ",
    }


def _multipart_files(content: bytes = PDF_BYTES) -> dict[str, tuple[str, bytes, str]]:
    return {"cv_file": ("candidate.pdf", content, "application/pdf")}


class FastAPIApplicationTest(unittest.TestCase):
    def test_module_exposes_application_with_metadata(self) -> None:
        from app.api.app import app

        self.assertIsInstance(app, FastAPI)
        self.assertEqual(app.title, "AI Career Coach API")
        self.assertEqual(app.version, "0.1.0")
        self.assertIn("supplied job description", app.description)

    def test_explicit_settings_override_application_metadata(self) -> None:
        from app.api.app import create_app
        from app.api.settings import APISettings

        api = create_app(settings=APISettings(title="Test API", version="9.8.7"))

        self.assertEqual(api.title, "Test API")
        self.assertEqual(api.version, "9.8.7")

    def test_cors_preflight_allows_default_react_origin_without_service_resolution(self) -> None:
        from app.api.app import create_app

        service_factory = Mock(side_effect=AssertionError("service was resolved"))
        with patch("app.ai.ollama_provider.generate") as provider:
            response = TestClient(create_app(service_factory)).options(
                "/analyses",
                headers={
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "http://localhost:5173",
        )
        self.assertIn("POST", response.headers["access-control-allow-methods"])
        self.assertNotIn("access-control-allow-credentials", response.headers)
        service_factory.assert_not_called()
        provider.assert_not_called()

    def test_cors_allows_only_explicit_custom_origin(self) -> None:
        from app.api.app import create_app
        from app.api.settings import APISettings

        api = create_app(settings=APISettings(cors_origins=("https://frontend.example",)))
        client = TestClient(api)

        allowed = client.get("/health", headers={"Origin": "https://frontend.example"})
        disallowed = client.get("/health", headers={"Origin": "https://other.example"})

        self.assertEqual(
            allowed.headers["access-control-allow-origin"], "https://frontend.example"
        )
        self.assertNotIn("access-control-allow-origin", disallowed.headers)

    def test_environment_settings_parse_origins_deterministically(self) -> None:
        from app.api.settings import APISettings

        settings = APISettings.from_environment(
            {
                "API_TITLE": "Environment API",
                "API_VERSION": "2.0",
                "API_DESCRIPTION": "Environment description",
                "API_CORS_ORIGINS": (
                    " https://one.example, ,https://two.example,https://one.example "
                ),
            }
        )

        self.assertEqual(settings.title, "Environment API")
        self.assertEqual(settings.version, "2.0")
        self.assertEqual(settings.description, "Environment description")
        self.assertEqual(
            settings.cors_origins,
            ("https://one.example", "https://two.example"),
        )

    def test_default_settings_never_introduce_wildcard_origin(self) -> None:
        from app.api.settings import APISettings

        settings = APISettings.from_environment({})

        self.assertEqual(settings.cors_origins, ("http://localhost:5173",))
        self.assertNotIn("*", settings.cors_origins)

    def test_wildcard_environment_origin_is_rejected(self) -> None:
        from app.api.settings import APISettings

        with self.assertRaisesRegex(ValueError, "explicit origins"):
            APISettings.from_environment({"API_CORS_ORIGINS": "*"})

    def test_openapi_documents_stable_public_contract_without_resolving_service(self) -> None:
        from app.api.app import create_app

        service_factory = Mock(side_effect=AssertionError("service was resolved"))
        with patch("app.ai.ollama_provider.generate") as provider:
            response = TestClient(create_app(service_factory)).get("/openapi.json")

        self.assertEqual(response.status_code, 200)
        schema = response.json()
        self.assertEqual(schema["info"]["title"], "AI Career Coach API")
        self.assertEqual(schema["info"]["version"], "0.1.0")
        self.assertTrue(schema["info"]["description"])

        health = schema["paths"]["/health"]["get"]
        analysis = schema["paths"]["/analyses"]["post"]
        self.assertEqual(health["tags"], ["System"])
        self.assertEqual(analysis["tags"], ["Analysis"])
        self.assertEqual(
            health["responses"]["200"]["content"]["application/json"]["schema"]["$ref"],
            "#/components/schemas/HealthResponse",
        )

        multipart = analysis["requestBody"]["content"]["multipart/form-data"]
        body_name = multipart["schema"]["$ref"].rsplit("/", 1)[-1]
        fields = schema["components"]["schemas"][body_name]["properties"]
        self.assertEqual(set(fields), {"cv_file", "target_role", "job_description"})
        for field in fields.values():
            self.assertTrue(field["description"])
        self.assertEqual(fields["cv_file"]["format"], "binary")

        success_schema = analysis["responses"]["200"]["content"][
            "application/json"
        ]["schema"]
        self.assertEqual(success_schema["$ref"], "#/components/schemas/AnalysisResponse")
        self.assertTrue({"400", "422", "500"}.issubset(analysis["responses"]))
        self.assertNotIn("ollama", str(schema).lower())
        self.assertNotIn("cli-formatted response", str(schema).lower())
        service_factory.assert_not_called()
        provider.assert_not_called()

    def test_health_returns_documented_json_without_resolving_service(self) -> None:
        from app.api.app import create_app

        service_factory = Mock(side_effect=AssertionError("service was resolved"))

        response = TestClient(create_app(service_factory)).get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/json")
        self.assertEqual(response.json(), {"status": "ok"})
        service_factory.assert_not_called()

    def test_application_service_can_be_substituted(self) -> None:
        from app.api.app import create_app, get_application_service

        stub_service = Mock(spec=ApplicationService)
        service_factory = Mock(return_value=stub_service)
        api = create_app(service_factory)
        request = Request({"type": "http", "app": api})

        self.assertIs(get_application_service(request), stub_service)
        service_factory.assert_called_once_with()

    def test_import_does_not_construct_service_or_call_provider(self) -> None:
        sys.modules.pop("app.api.app", None)
        sys.modules.pop("app.api", None)

        with (
            patch("app.bootstrap.create_application_service") as service_factory,
            patch("app.ai.ollama_provider.generate") as provider,
        ):
            imported = importlib.import_module("app.api.app")

        self.assertIsInstance(imported.app, FastAPI)
        service_factory.assert_not_called()
        provider.assert_not_called()

    def test_analysis_delegates_once_and_returns_structured_result(self) -> None:
        from app.api.app import create_app

        expected_response = _analysis_response()
        service = Mock(spec=ApplicationService)
        service.analyze.return_value = expected_response
        service_factory = Mock(return_value=service)

        response = TestClient(create_app(service_factory)).post(
            "/analyses", data=_multipart_data(), files=_multipart_files()
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/json")
        self.assertEqual(response.json(), expected_response.model_dump(mode="json"))
        self.assertEqual(response.json()["candidate_profile"]["summary"], "Structured candidate")
        self.assertEqual(response.json()["analysis"]["overall_match_score"], 75)
        self.assertNotIn("Candidate Profile", response.text)
        service_factory.assert_called_once_with()
        service.analyze.assert_called_once()

        request = service.analyze.call_args.args[0]
        self.assertEqual(request.target_role, "Operations Manager")
        self.assertEqual(request.requirement_source.content, "Clear written communication")
        self.assertEqual(request.requirement_source.target_role, "Operations Manager")
        self.assertEqual(request.cv_source.file_path.suffix, ".pdf")
        self.assertFalse(request.cv_source.file_path.exists())

    def test_browser_form_data_request_preserves_structured_json_and_cors(self) -> None:
        from app.api.app import create_app

        expected_response = _analysis_response()
        service = Mock(spec=ApplicationService)
        service.analyze.return_value = expected_response

        response = TestClient(create_app(lambda: service)).post(
            "/analyses",
            data=_multipart_data(),
            files=_multipart_files(),
            headers={"Origin": "http://localhost:5173"},
        )

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "http://localhost:5173",
        )
        self.assertNotIn("access-control-allow-credentials", response.headers)
        self.assertEqual(body, expected_response.model_dump(mode="json"))
        self.assertIsInstance(body["analysis"]["overall_match_score"], int)
        self.assertIsInstance(body["candidate_profile"]["education"], list)
        self.assertIsInstance(body["analysis"]["missing_skills"], dict)
        self.assertEqual(body["candidate_profile"]["certifications"], [])
        self.assertEqual(body["analysis"]["missing_skills"]["important"], [])
        service.analyze.assert_called_once()

        serialized = response.text.lower()
        for forbidden in (
            "candidateprofile(",
            "careeranalysis(",
            "overall match score:",
            "learning roadmap:",
            "ollama",
            "openai",
            ".pdf",
            "\\\\tmp\\\\",
            "/tmp/",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_disallowed_origin_does_not_authorize_successful_analysis(self) -> None:
        from app.api.app import create_app

        service = Mock(spec=ApplicationService)
        service.analyze.return_value = _analysis_response()

        response = TestClient(create_app(lambda: service)).post(
            "/analyses",
            data=_multipart_data(),
            files=_multipart_files(),
            headers={"Origin": "https://other.example"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("access-control-allow-origin", response.headers)
        self.assertEqual(response.json(), _analysis_response().model_dump(mode="json"))
        service.analyze.assert_called_once()

    def test_temporary_file_exists_during_service_call_and_is_cleaned(self) -> None:
        from app.api.app import create_app

        received_path: Path | None = None

        def analyze(request):
            nonlocal received_path
            received_path = request.cv_source.file_path
            self.assertTrue(received_path.is_file())
            self.assertEqual(received_path.read_bytes(), PDF_BYTES)
            return _analysis_response()

        service = Mock(spec=ApplicationService)
        service.analyze.side_effect = analyze

        response = TestClient(create_app(lambda: service)).post(
            "/analyses", data=_multipart_data(), files=_multipart_files()
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(received_path)
        self.assertFalse(received_path.exists())

    def test_missing_required_fields_return_422_without_calling_service(self) -> None:
        from app.api.app import create_app

        service = Mock(spec=ApplicationService)

        response = TestClient(create_app(lambda: service)).post("/analyses")

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.headers["content-type"], "application/json")
        self.assertIsInstance(response.json()["detail"], list)
        self.assertTrue(response.json()["detail"])
        self.assertTrue(
            {"type", "loc", "msg", "input"}.issubset(response.json()["detail"][0])
        )
        service.analyze.assert_not_called()

    def test_empty_text_fields_are_rejected(self) -> None:
        from app.api.app import create_app

        for field in ("target_role", "job_description"):
            with self.subTest(field=field):
                service = Mock(spec=ApplicationService)
                data = _multipart_data()
                data[field] = " \n\t "

                response = TestClient(create_app(lambda: service)).post(
                    "/analyses", data=data, files=_multipart_files()
                )

                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json(), {"detail": f"{field} must not be empty."})
                service.analyze.assert_not_called()

    def test_empty_upload_and_invalid_content_type_are_rejected(self) -> None:
        from app.api.app import create_app

        cases = (
            (_multipart_files(b""), "cv_file must not be empty."),
            ({"cv_file": ("candidate.txt", b"text", "text/plain")},
             "cv_file must use the application/pdf content type."),
        )
        for files, detail in cases:
            with self.subTest(detail=detail):
                service = Mock(spec=ApplicationService)
                response = TestClient(create_app(lambda: service)).post(
                    "/analyses", data=_multipart_data(), files=files
                )

                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json(), {"detail": detail})
                service.analyze.assert_not_called()

    def test_known_input_errors_map_to_400_and_clean_temporary_file(self) -> None:
        from app.api.app import create_app

        error_types = (
            InvalidCVSourceError,
            CVProcessingError,
            RequirementProcessingError,
        )
        for error_type in error_types:
            with self.subTest(error_type=error_type):
                received_path: Path | None = None

                def fail(request):
                    nonlocal received_path
                    received_path = request.cv_source.file_path
                    raise error_type("Safe input error.")

                service = Mock(spec=ApplicationService)
                service.analyze.side_effect = fail
                response = TestClient(create_app(lambda: service)).post(
                    "/analyses", data=_multipart_data(), files=_multipart_files()
                )

                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json(), {"detail": "Safe input error."})
                self.assertFalse(received_path.exists())

    def test_internal_errors_return_safe_500_responses(self) -> None:
        from app.api.app import create_app

        cases = (
            (AnalysisExecutionError("provider secret"), "Career analysis could not be completed."),
            (RuntimeError("local path and stack details"), "Internal server error."),
        )
        for error, detail in cases:
            with self.subTest(error=type(error)):
                received_path: Path | None = None

                def fail(request):
                    nonlocal received_path
                    received_path = request.cv_source.file_path
                    self.assertTrue(received_path.is_file())
                    raise error

                service = Mock(spec=ApplicationService)
                service.analyze.side_effect = fail
                response = TestClient(
                    create_app(lambda: service), raise_server_exceptions=False
                ).post("/analyses", data=_multipart_data(), files=_multipart_files())

                self.assertEqual(response.status_code, 500)
                self.assertEqual(response.json(), {"detail": detail})
                self.assertNotIn(str(error), response.text)
                self.assertIsNotNone(received_path)
                self.assertFalse(received_path.exists())


if __name__ == "__main__":
    unittest.main()
