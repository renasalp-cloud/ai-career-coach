"""Collect deterministic evidence text from candidate profiles."""

from app.models import CandidateProfile, SkillEvidence


class CandidateEvidenceCollector:
    def collect(self, candidate: CandidateProfile) -> list[SkillEvidence]:
        evidence: list[SkillEvidence] = []

        for skill in candidate.skills:
            text = skill.name.strip()

            if text:
                evidence.append(
                    SkillEvidence(
                        source=skill.source or "skills",
                        text=skill.name,
                    )
                )

        for experience in candidate.experience:
            for highlight in experience.highlights:
                if highlight.strip():
                    evidence.append(
                        SkillEvidence(
                            source="experience",
                            text=highlight,
                        )
                    )

        for project in candidate.projects:
            if project.strip():
                evidence.append(
                    SkillEvidence(
                        source="projects",
                        text=project,
                    )
                )

        for certification in candidate.certifications:
            if certification.strip():
                evidence.append(
                    SkillEvidence(
                        source="training",
                        text=certification,
                    )
                )

        for education in candidate.education:
            education_parts = [
                education.degree,
                education.institution,
                education.start_date,
                education.end_date,
                education.status,
            ]
            text = " | ".join(part for part in education_parts if part.strip())

            if text:
                evidence.append(
                    SkillEvidence(
                        source="education",
                        text=text,
                    )
                )

        return evidence
