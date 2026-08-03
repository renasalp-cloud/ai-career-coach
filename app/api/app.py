"""FastAPI delivery adapter for the career-analysis application."""

from collections.abc import Callable
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool
from starlette.middleware.cors import CORSMiddleware

from app.application import (
    AnalysisExecutionError,
    AnalysisRequest,
    AnalysisResponse,
    ApplicationService,
    CVProcessingError,
    CVSource,
    InvalidCVSourceError,
    RequirementProcessingError,
)
from app.bootstrap import create_application_service
from app.api.settings import APISettings
from app.requirements.source import RequirementSource, RequirementSourceType

ServiceFactory = Callable[[], ApplicationService]

class HealthResponse(BaseModel):
    """API availability status."""

    status: str


class ErrorResponse(BaseModel):
    """Safe error response returned by the API."""

    detail: str


def get_application_service(request: Request) -> ApplicationService:
    """Resolve the application boundary configured for this API instance."""
    return request.app.state.application_service_factory()


def create_app(
    service_factory: ServiceFactory = create_application_service,
    settings: APISettings | None = None,
) -> FastAPI:
    """Create an import-safe API with replaceable application dependencies."""
    api_settings = settings or APISettings.from_environment()
    api = FastAPI(
        title=api_settings.title,
        version=api_settings.version,
        description=api_settings.description,
        openapi_tags=[
            {"name": "System", "description": "API availability information."},
            {"name": "Analysis", "description": "Structured career analysis."},
        ],
    )
    api.add_middleware(
        CORSMiddleware,
        allow_origins=list(api_settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    api.state.application_service_factory = service_factory

    @api.get(
        "/health",
        tags=["System"],
        summary="Check API health",
        description="Return API availability without running the analysis pipeline.",
        operation_id="get_health",
        response_model=HealthResponse,
        response_description="The API is available.",
    )
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @api.exception_handler(AnalysisExecutionError)
    async def analysis_execution_error(
        _request: Request, _error: AnalysisExecutionError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "Career analysis could not be completed."},
        )

    @api.exception_handler(Exception)
    async def unexpected_error(
        _request: Request, _error: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error."},
        )

    @api.post(
        "/analyses",
        tags=["Analysis"],
        summary="Analyze a candidate CV",
        description=(
            "Upload a candidate CV as a PDF and compare it with the supplied job "
            "description, which is the authoritative requirement source. "
            "`target_role` provides context and presentation only. The endpoint "
            "delegates analysis to the Application Service. Uploaded files are "
            "temporary and are not persisted after request completion. The response "
            "is structured JSON containing the candidate profile, validated career "
            "analysis, deterministic strengths and gaps, and recommendations and a "
            "learning roadmap derived from validated requirement gaps. It is neither "
            "CLI-formatted text nor raw LLM output."
        ),
        response_model=AnalysisResponse,
        response_description="Structured and validated career analysis.",
        responses={
            400: {
                "model": ErrorResponse,
                "description": "Invalid uploaded file or user-supplied content.",
                "content": {
                    "application/json": {
                        "example": {"detail": "cv_file must not be empty."}
                    }
                },
            },
            422: {"description": "Missing or malformed multipart request fields."},
            500: {
                "model": ErrorResponse,
                "description": "Analysis execution failure or unexpected internal error.",
                "content": {
                    "application/json": {
                        "example": {"detail": "Career analysis could not be completed."}
                    }
                },
            },
        },
    )
    async def create_analysis(
        cv_file: UploadFile = File(
            ..., description="Candidate CV uploaded as a PDF."
        ),
        target_role: str = Form(
            ...,
            description="Target role label used for context and presentation.",
            examples=["Target role"],
        ),
        job_description: str = Form(
            ...,
            description=(
                "Supplied job description used as the authoritative requirement source."
            ),
            examples=["The role requires clear communication and planning."],
        ),
        service: ApplicationService = Depends(get_application_service),
    ) -> AnalysisResponse:
        normalized_role = target_role.strip()
        normalized_description = job_description.strip()
        if not normalized_role:
            raise HTTPException(status_code=400, detail="target_role must not be empty.")
        if not normalized_description:
            raise HTTPException(
                status_code=400,
                detail="job_description must not be empty.",
            )
        if cv_file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail="cv_file must use the application/pdf content type.",
            )

        temporary_path: Path | None = None
        try:
            with NamedTemporaryFile(suffix=".pdf", delete=False) as temporary_file:
                temporary_path = Path(temporary_file.name)
                while chunk := await cv_file.read(1024 * 1024):
                    temporary_file.write(chunk)

            if temporary_path.stat().st_size == 0:
                raise HTTPException(status_code=400, detail="cv_file must not be empty.")

            request = AnalysisRequest(
                cv_source=CVSource(file_path=temporary_path),
                requirement_source=RequirementSource(
                    source_type=RequirementSourceType.PASTED_TEXT,
                    content=normalized_description,
                    name="Pasted job description",
                    target_role=normalized_role,
                ),
                target_role=normalized_role,
            )
            return await run_in_threadpool(service.analyze, request)
        except InvalidCVSourceError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except CVProcessingError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except RequirementProcessingError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        finally:
            await cv_file.close()
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    return api


app = create_app()
