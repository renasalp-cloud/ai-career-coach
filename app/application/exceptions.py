"""Transport-agnostic application exceptions."""


class ApplicationError(Exception):
    """Base exception for application-layer failures."""


class InvalidCVSourceError(ApplicationError):
    """Raised when a CV source cannot be accepted."""


class CVProcessingError(ApplicationError):
    """Raised when candidate CV processing fails."""


class RequirementProcessingError(ApplicationError):
    """Raised when requirement processing fails."""


class AnalysisExecutionError(ApplicationError):
    """Raised when analysis execution fails."""
