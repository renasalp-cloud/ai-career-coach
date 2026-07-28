"""Orchestration for building normalized requirement profiles."""

from collections.abc import Callable

from app.models import RequirementProfile, RequirementSkill
from app.requirements.category_classifier import RequirementCategoryClassifier
from app.requirements.decomposer import RequirementDecomposer
from app.requirements.extractor import extract_requirement_profile
from app.requirements.filter import RequirementProfileFilter
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
        requirement_filter: RequirementProfileFilter | None = None,
        decomposer: RequirementDecomposer | None = None,
        normalizer: RequirementProfileNormalizer | None = None,
        category_classifier: RequirementCategoryClassifier | None = None,
        validator: RequirementProfileValidator | None = None,
    ) -> None:
        self._loader = loader or RequirementSourceLoader()
        self._extractor = extractor or extract_requirement_profile
        self._filter = requirement_filter or RequirementProfileFilter()
        self._decomposer = decomposer or RequirementDecomposer()
        self._normalizer = normalizer or RequirementProfileNormalizer()
        self._category_classifier = (
            category_classifier or RequirementCategoryClassifier()
        )
        self._validator = validator or RequirementProfileValidator()

    def build(self, source: RequirementSource) -> RequirementProfile:
        """Build a normalized profile from ``source``."""
        requirement_text = self._loader.load(source)
        target_role = source.target_role or ""
        extracted_profile = self._extractor(target_role, requirement_text)
        filtered_profile = self._filter.filter(extracted_profile)
        decomposed_profile = self._decomposer.decompose(filtered_profile)
        normalized_profile = self._normalizer.normalize(decomposed_profile)
        classified_profile = normalized_profile.model_copy(
            deep=True,
            update={
                "skills": [
                    RequirementSkill(
                        name=requirement.name,
                        priority=requirement.priority,
                        category=self._category_classifier.classify(requirement.name),
                    )
                    for requirement in normalized_profile.skills
                ]
            },
        )
        return self._validator.validate(classified_profile)
