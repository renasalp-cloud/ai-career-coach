from app.models import CandidateProfile, SkillMatch


class SkillMatcher:
    def match(
        self,
        candidate: CandidateProfile,
        role_skills: list[str],
    ) -> list[SkillMatch]:
        return []
