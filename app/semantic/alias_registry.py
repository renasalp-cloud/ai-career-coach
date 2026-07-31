"""Configurable aliases for deterministic skill matching."""


class SkillAliasRegistry:
    def __init__(self, aliases: dict[str, list[str]] | None = None) -> None:
        self.aliases = aliases if aliases is not None else {}

    def aliases_for(self, requirement_skill: str) -> list[str]:
        normalized_requirement = self._normalize(requirement_skill)

        for canonical_name, aliases in self.aliases.items():
            equivalent_names = [canonical_name, *aliases]
            if any(
                self._normalize(name) == normalized_requirement
                for name in equivalent_names
            ):
                return [
                    name
                    for name in equivalent_names
                    if self._normalize(name) != normalized_requirement
                ]

        return []

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.strip().lower().replace("-", " ").split())
