"""Orchestration for building normalized requirement profiles."""

from collections.abc import Callable

from app.models import RequirementProfile
from app.requirements.extractor import extract_requirement_profile
from app.requirements.loader import RequirementSourceLoader
from app.requirements.normalizer import RequirementProfileNormalizer
from app.requirements.source import RequirementSource
from app.requirements.validator import RequirementProfileValidator


RequirementExtractor = Callable[[str, str], RequirementProfile]


class RequirementPipeline:
    """Coordinate requirement loading, extraction, and normalization."""

    def __init__(
        self,
        loader: RequirementSourceLoader | None = None,
        extractor: RequirementExtractor | None = None,
        normalizer: RequirementProfileNormalizer | None = None,
        validator: RequirementProfileValidator | None = None,
    ) -> None:
        self._loader = loader or RequirementSourceLoader()
        self._extractor = extractor or extract_requirement_profile
        self._normalizer = normalizer or RequirementProfileNormalizer()
        self._validator = validator or RequirementProfileValidator()

    def build(self, source: RequirementSource) -> RequirementProfile:
        """Build a normalized profile from ``source``."""
        requirement_text = self._loader.load(source)
        target_role = source.target_role or ""
        extracted_profile = self._extractor(target_role, requirement_text)
        normalized_profile = self._normalizer.normalize(extracted_profile)
        return self._validator.validate(normalized_profile)
