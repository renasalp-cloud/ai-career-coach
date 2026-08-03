"""Environment-driven configuration for the FastAPI delivery adapter."""

from collections.abc import Mapping
from dataclasses import dataclass
import os


DEFAULT_API_DESCRIPTION = """Compare a candidate CV with a supplied job description.

Deterministic components assess requirements, and the LLM explains the validated
results. The supplied job description is the authoritative requirement source;
`target_role` is used only for context and presentation.
"""


def parse_cors_origins(value: str) -> tuple[str, ...]:
    """Parse a comma-separated, ordered collection of explicit CORS origins."""
    origins = tuple(dict.fromkeys(origin.strip() for origin in value.split(",") if origin.strip()))
    if "*" in origins:
        raise ValueError("API_CORS_ORIGINS must contain explicit origins, not '*'.")
    return origins


@dataclass(frozen=True)
class APISettings:
    """Configuration owned only by the API delivery layer."""

    title: str = "AI Career Coach API"
    version: str = "0.1.0"
    description: str = DEFAULT_API_DESCRIPTION
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)

    @classmethod
    def from_environment(
        cls, environment: Mapping[str, str] | None = None
    ) -> "APISettings":
        """Build settings from process environment variables or an isolated mapping."""
        values = os.environ if environment is None else environment
        defaults = cls()
        return cls(
            title=values.get("API_TITLE", defaults.title),
            version=values.get("API_VERSION", defaults.version),
            description=values.get("API_DESCRIPTION", defaults.description),
            cors_origins=parse_cors_origins(
                values.get("API_CORS_ORIGINS", ",".join(defaults.cors_origins))
            ),
        )
