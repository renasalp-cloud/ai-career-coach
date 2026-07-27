"""Application service contract."""

from abc import ABC, abstractmethod

from app.application.models import AnalysisRequest, AnalysisResponse


class ApplicationService(ABC):
    """Contract for application-level analysis orchestration."""

    @abstractmethod
    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        """Execute the candidate analysis use case."""
