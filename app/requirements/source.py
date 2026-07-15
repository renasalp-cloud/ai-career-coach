"""Models describing generic requirement sources."""

from enum import Enum

from pydantic import BaseModel, field_validator


class RequirementSourceType(str, Enum):
    """Supported kinds of requirement source."""

    PASTED_TEXT = "pasted_text"
    ROLE_PROFILE = "role_profile"
    TEXT_FILE = "text_file"


class RequirementSource(BaseModel):
    """Requirement text and optional context about where it came from."""

    source_type: RequirementSourceType
    content: str
    name: str | None = None
    target_role: str | None = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, content: str) -> str:
        trimmed_content = content.strip()
        if not trimmed_content:
            raise ValueError("content must not be empty")
        return trimmed_content
