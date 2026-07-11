from app.models import CandidateProfile, RequirementProfile, SkillEvidence, SkillMatch


# TODO: Move exact skill normalization to a shared semantic utility when more
# semantic components need the same trim/case-insensitive comparison.
def _normalize(value: str) -> str:
    return value.strip().lower()


class SkillMatcher:
    def match(
        self,
        candidate: CandidateProfile,
        requirements: RequirementProfile,
    ) -> list[SkillMatch]:
        candidate_skills = {
            _normalize(skill.name): skill
            for skill in candidate.skills
            if skill.name.strip()
        }

        matches: list[SkillMatch] = []

        for requirement_skill in requirements.skills:
            role_skill = requirement_skill.name
            candidate_skill = candidate_skills.get(_normalize(role_skill))

            if candidate_skill is None:
                matches.append(
                    SkillMatch(
                        role_skill=role_skill,
                        candidate_skill=None,
                        evidence=[],
                    )
                )
                continue

            matches.append(
                SkillMatch(
                    role_skill=role_skill,
                    candidate_skill=candidate_skill.name,
                    evidence=[
                        SkillEvidence(
                            source=candidate_skill.source,
                            # TODO: Replace with the original evidence text extracted from the CV.
                            text=candidate_skill.name,
                        )
                    ],
                )
            )

        return matches
