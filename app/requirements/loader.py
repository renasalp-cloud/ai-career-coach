"""Load raw requirement text from supported sources."""

from pathlib import Path

from app.requirements.source import RequirementSource, RequirementSourceType


class RequirementSourceLoader:
    """Obtain raw requirement text without extracting or normalizing it."""

    def load(self, source: RequirementSource) -> str:
        """Return trimmed requirement text from the configured source."""
        if source.source_type == RequirementSourceType.PASTED_TEXT:
            return source.content.strip()

        path = Path(source.content)
        if not path.is_file():
            raise FileNotFoundError(f"Requirement source file not found: {path}")

        content = path.read_text(encoding="utf-8").strip()
        if not content:
            raise ValueError(f"Requirement source file is empty: {path}")

        return content
