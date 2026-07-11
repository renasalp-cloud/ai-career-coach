from app.models import SkillMatch


class SkillValidator:
    def validate(
        self,
        matches: list[SkillMatch],
    ) -> list[SkillMatch]:
        validated_matches: list[SkillMatch] = []

        for match in matches:
            status = "missing" if match.candidate_skill is None else "demonstrated"

            validated_matches.append(
                match.model_copy(
                    update={
                        "status": status,
                        "confidence": 1.0,
                    }
                )
            )

        return validated_matches
