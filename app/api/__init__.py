"""FastAPI delivery adapter."""

from app.api.app import app, create_app, get_application_service
from app.api.settings import APISettings

__all__ = ["APISettings", "app", "create_app", "get_application_service"]
