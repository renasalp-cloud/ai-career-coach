"""Collect deterministic structured evidence from candidate profiles."""

from app.evidence.models import CandidateEvidence, EvidenceSourceType
from app.models import CandidateProfile


class CandidateEvidenceCollector:
    def collect(self, candidate: CandidateProfile) -> list[CandidateEvidence]:
        evidence: list[CandidateEvidence] = []

        def add(
            skill: str,
            source_type: EvidenceSourceType,
            source_text: str,
            source_label: str,
        ) -> None:
            if not skill.strip() or not source_text.strip():
                return
            item = CandidateEvidence(
                skill=skill,
                source_type=source_type,
                source_text=source_text,
                source_label=source_label,
            )
            identity = (
                item.skill,
                item.source_type,
                item.source_text,
                item.source_label,
            )
            if identity not in seen:
                seen.add(identity)
                evidence.append(item)

        seen: set[tuple[str, EvidenceSourceType, str, str]] = set()

        for skill in candidate.skills:
            add(skill.name, EvidenceSourceType.SKILLS_SECTION, skill.name, "Skills section")

        for experience in candidate.experience:
            label = " - ".join(
                part.strip() for part in (experience.title, experience.organization) if part.strip()
            ) or "Work experience"
            for highlight in experience.highlights:
                add(highlight, EvidenceSourceType.WORK_EXPERIENCE, highlight, label)

        for project in candidate.projects:
            add(project, EvidenceSourceType.PROJECT, project, "Project")

        for certification in candidate.certifications:
            add(certification, EvidenceSourceType.CERTIFICATION, certification, "Certification")

        for education in candidate.education:
            education_parts = [
                education.degree,
                education.institution,
                education.start_date,
                education.end_date,
                education.status,
            ]
            text = " | ".join(part for part in education_parts if part.strip())
            label = " - ".join(
                part.strip() for part in (education.degree, education.institution) if part.strip()
            ) or "Education"
            add(text, EvidenceSourceType.EDUCATION, text, label)

        add(candidate.summary, EvidenceSourceType.SUMMARY, candidate.summary, "Candidate summary")

        for language in candidate.languages:
            add(language, EvidenceSourceType.OTHER, language, "Languages section")

        return evidence
