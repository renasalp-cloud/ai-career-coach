import json
import unittest
from unittest.mock import Mock, patch

from pydantic import ValidationError

from app.ai.analyzer import analyze_cv
from app.ai.prompt_builder import PromptContext, build_cv_analysis_prompt
from app.assessment.requirement_assessment import RequirementAssessment
from app.candidate_profile.extractor import extract_candidate_profile
from app.candidate_profile.models import (
    CandidateProfile,
    EducationEntry,
    ExperienceEntry,
    SkillEntry,
)
from app.candidate_profile.normalizer import normalize_candidate_profile
from app.cv_parser import parse_cv
from app.models import RequirementProfile
from app.pdf_reader import clean_text, extract_text


CV_TEXT = """PROFILE
Collaborative professional
EDUCATION
Applied Studies
General University [ 01/09/2016 - 30/06/2020 ]
WORK EXPERIENCE
Example Cooperative - Remote
Coordinator
[ 01/07/2020 - Current ]
- Coordinated recurring activities
SKILLS
Planning, Written communication
LANGUAGES
English C1
"""


def _assessment() -> RequirementAssessment:
    return RequirementAssessment(
        total_requirements=0,
        demonstrated_requirements=0,
        missing_requirements=0,
        overall_coverage_percentage=0,
        required_total=0,
        required_demonstrated=0,
        required_coverage_percentage=0,
        preferred_total=0,
        preferred_demonstrated=0,
        preferred_coverage_percentage=0,
        optional_total=0,
        optional_demonstrated=0,
        optional_coverage_percentage=0,
    )


def _valid_analysis_response() -> str:
    return json.dumps(
        {
            "overall_match_score": 0,
            "professional_summary": "",
            "strengths": [],
            "missing_skills": {
                "critical": [],
                "important": [],
                "optional": [],
            },
            "career_gap_analysis": "",
            "recommendations": [],
            "learning_roadmap": [
                {
                    "week": week,
                    "goal": "",
                    "topics": [],
                    "practical_task": "",
                    "expected_outcome": "",
                }
                for week in range(1, 5)
            ],
        }
    )


class CandidatePipelineDiagnosticsTest(unittest.TestCase):
    def test_pdf_extraction_and_cleaning_preserve_candidate_sections(self) -> None:
        page = Mock()
        page.extract_text.return_value = CV_TEXT
        reader = Mock()
        reader.pages = [page]

        with patch("app.pdf_reader.PdfReader", return_value=reader):
            extracted = extract_text("candidate.pdf")

        cleaned = clean_text(extracted)
        for value in (
            "EDUCATION",
            "Applied Studies",
            "WORK EXPERIENCE",
            "Coordinator",
            "SKILLS",
            "Planning",
            "LANGUAGES",
            "English C1",
        ):
            with self.subTest(value=value):
                self.assertIn(value, extracted)
                self.assertIn(value, cleaned)

    def test_parser_exposes_every_recognized_candidate_section(self) -> None:
        sections = parse_cv(clean_text(CV_TEXT))

        self.assertIn("Applied Studies", sections["education"])
        self.assertIn("Coordinator", sections["experience"])
        self.assertIn("Planning", sections["skills"])
        self.assertIn("English C1", sections["languages"])

    def test_tools_alias_closes_education_and_maps_content_to_skills(self) -> None:
        sections = parse_cv("EDUCATION\nApplied Studies\nTOOLS\nPlanning")

        self.assertEqual(
            sections,
            {"education": "Applied Studies", "skills": "Planning"},
        )

    def test_skill_aliases_and_explicit_prose_reach_candidate_profile(self) -> None:
        sections = parse_cv(
            "SKILLS AND STRENGTHS\n"
            "COMPUTER SKILLS\n"
            "Experience working with Office Suite.\n"
            "Experience with System One, System Two, System Three."
        )

        profile = extract_candidate_profile(sections)

        self.assertEqual(
            sections,
            {
                "skills": (
                    "Experience working with Office Suite.\n"
                    "Experience with System One, System Two, System Three."
                )
            },
        )
        self.assertEqual(
            [skill.name for skill in profile.skills],
            ["Office Suite", "System One", "System Two", "System Three"],
        )

    def test_extractor_receives_all_sections_and_builds_populated_profile(self) -> None:
        sections = parse_cv(clean_text(CV_TEXT))
        observed_sections: dict[str, str] = {}

        def diagnostic_extract(value: dict[str, str]) -> CandidateProfile:
            observed_sections.update(value)
            return extract_candidate_profile(value)

        profile = diagnostic_extract(sections)

        self.assertEqual(observed_sections, sections)
        self.assertEqual(profile.education[0].degree, "Applied Studies")
        self.assertEqual(profile.experience[0].title, "Coordinator")
        self.assertEqual(
            [skill.name for skill in profile.skills],
            ["Planning", "Written communication"],
        )
        self.assertEqual(profile.languages, ["English C1"])

    def test_extractor_supports_generic_year_ranges_across_candidate_fields(self) -> None:
        sections = {
            "education": "Applied Studies\nGeneral University | 2016 - 2020",
            "experience": "Example Cooperative\nCoordinator\n2020 - Present",
            "skills": "Planning",
            "languages": "English C1",
        }

        profile = extract_candidate_profile(sections)

        self.assertEqual(len(profile.education), 1)
        self.assertEqual(profile.education[0].degree, "Applied Studies")
        self.assertEqual(profile.education[0].institution, "General University")
        self.assertEqual(profile.education[0].start_date, "2016")
        self.assertEqual(profile.education[0].end_date, "2020")
        self.assertEqual(profile.education[0].status, "completed")
        self.assertEqual(len(profile.experience), 1)
        self.assertEqual(profile.experience[0].organization, "Example Cooperative")
        self.assertEqual(profile.experience[0].title, "Coordinator")
        self.assertEqual(profile.experience[0].start_date, "2020")
        self.assertEqual(profile.experience[0].end_date, "Present")
        self.assertEqual([skill.name for skill in profile.skills], ["Planning"])
        self.assertEqual(profile.languages, ["English C1"])

    def test_parser_and_extractor_support_date_first_experience(self) -> None:
        sections = parse_cv(
            "WORK EXPERIENCE\n"
            "02/2025 – Present\n"
            "Example Organization – Service Coordinator\n"
            "● Organizing work processes and setting priorities"
        )

        profile = extract_candidate_profile(sections)

        self.assertEqual(len(profile.experience), 1)
        self.assertEqual(profile.experience[0].organization, "Example Organization")
        self.assertEqual(profile.experience[0].title, "Service Coordinator")
        self.assertEqual(
            profile.experience[0].highlights,
            ["Organizing work processes and setting priorities"],
        )

    def test_prompt_contains_every_populated_candidate_profile_field(self) -> None:
        profile = CandidateProfile(
            summary="Collaborative professional",
            education=[EducationEntry(degree="Applied Studies")],
            experience=[ExperienceEntry(title="Coordinator")],
            skills=[SkillEntry(name="Planning")],
            languages=["English C1"],
            projects=["Community initiative"],
            certifications=["General certificate"],
        )
        prompt = build_cv_analysis_prompt(
            PromptContext(
                template="Template",
                requirement_profile=RequirementProfile(),
                candidate_profile=profile,
                validated_skill_matches=[],
                requirement_assessment=_assessment(),
            )
        )
        candidate_json = prompt.split("<CANDIDATE_PROFILE>", 1)[1].split(
            "</CANDIDATE_PROFILE>", 1
        )[0]

        self.assertEqual(json.loads(candidate_json), profile.model_dump())

    def test_populated_structured_profile_survives_validation(self) -> None:
        raw_profile = {
            "summary": "Collaborative professional",
            "education": [{"degree": "Applied Studies"}],
            "experience": [{"title": "Coordinator"}],
            "skills": [{"name": "Planning", "source": "skills_section"}],
            "languages": ["English C1"],
            "projects": ["Community initiative"],
            "certifications": ["General certificate"],
        }

        profile = CandidateProfile.model_validate(raw_profile)

        self.assertEqual(profile.model_dump(), raw_profile | {
            "education": [{
                "degree": "Applied Studies",
                "institution": "",
                "start_date": "",
                "end_date": "",
                "status": "unknown",
            }],
            "experience": [{
                "organization": "",
                "title": "Coordinator",
                "start_date": "",
                "end_date": "",
                "location": "",
                "highlights": [],
            }],
        })

    def test_one_malformed_field_rejects_the_whole_profile(self) -> None:
        with self.assertRaises(ValidationError):
            CandidateProfile.model_validate(
                {
                    "education": [{"degree": "Applied Studies"}],
                    "experience": "Coordinator",
                    "skills": [{"name": "Planning"}],
                    "languages": ["English C1"],
                }
            )

    def test_omitted_fields_silently_default_to_empty_collections(self) -> None:
        profile = CandidateProfile.model_validate({"languages": ["English C1"]})

        self.assertEqual(profile.education, [])
        self.assertEqual(profile.experience, [])
        self.assertEqual(profile.skills, [])
        self.assertEqual(profile.languages, ["English C1"])

    def test_normalization_preserves_populated_fields_and_removes_only_blank_skills(
        self,
    ) -> None:
        profile = CandidateProfile(
            education=[EducationEntry(degree="Applied Studies")],
            experience=[ExperienceEntry(title="Coordinator")],
            skills=[
                SkillEntry(name="Planning", source="skills_section"),
                SkillEntry(name=" planning ", source="other"),
                SkillEntry(name=" ", source="skills_section"),
            ],
            languages=["English C1"],
        )

        normalized = normalize_candidate_profile(profile)

        self.assertEqual(normalized.education[0].degree, "Applied Studies")
        self.assertEqual(normalized.experience[0].title, "Coordinator")
        self.assertEqual([skill.name for skill in normalized.skills], ["Planning"])
        self.assertEqual(normalized.languages, ["English C1"])

    def test_successful_extraction_reaches_analysis_prompt_before_provider_response(
        self,
    ) -> None:
        sections = parse_cv(clean_text(CV_TEXT))
        requirement_profile = RequirementProfile()
        captured_prompts: list[str] = []

        def fake_provider(prompt: str) -> str:
            captured_prompts.append(prompt)
            return _valid_analysis_response()

        with patch("app.ai.analyzer.generate", side_effect=fake_provider):
            result = analyze_cv(CV_TEXT, requirement_profile, sections)

        self.assertEqual(result.candidate_profile.education[0].degree, "Applied Studies")
        self.assertEqual(result.candidate_profile.experience[0].title, "Coordinator")
        self.assertEqual(
            [skill.name for skill in result.candidate_profile.skills],
            ["Planning", "Written communication"],
        )
        self.assertEqual(result.candidate_profile.languages, ["English C1"])
        self.assertEqual(len(captured_prompts), 1)
        for value in (
            "Applied Studies",
            "Coordinator",
            "Planning",
            "English C1",
        ):
            with self.subTest(value=value):
                self.assertIn(value, captured_prompts[0])


if __name__ == "__main__":
    unittest.main()
