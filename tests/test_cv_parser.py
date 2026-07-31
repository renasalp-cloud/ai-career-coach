import unittest

from app.candidate_profile.extractor import extract_candidate_profile
from app.cv_parser import parse_cv


class CvParserTest(unittest.TestCase):
    def test_traditional_single_column_cv_remains_supported(self) -> None:
        sections = parse_cv(
            "Professional Summary\nOrganized coordinator\n"
            "Education\nApplied Studies\nExample University\n"
            "Work Experience\nExample Cooperative\nCoordinator\n2020 - Present"
        )

        self.assertEqual(
            sections,
            {
                "profile": "Organized coordinator",
                "education": "Applied Studies\nExample University",
                "experience": "Example Cooperative\nCoordinator\n2020 - Present",
            },
        )

    def test_modern_compact_cv_supports_headings_adjacent_to_content(self) -> None:
        sections = parse_cv(
            "Professional Summary: Organized coordinator\n"
            "Technical Skills: Planning, Communication\n"
            "Languages: English C1"
        )

        self.assertEqual(
            sections,
            {
                "profile": "Organized coordinator",
                "skills": "Planning, Communication",
                "languages": "English C1",
            },
        )

    def test_consecutive_headings_without_blank_lines_are_detected(self) -> None:
        sections = parse_cv("PROFILE\nSUMMARY\nSKILLS\nPlanning")

        self.assertEqual(
            sections,
            {"profile": "", "skills": "Planning"},
        )

    def test_mixed_uppercase_and_title_case_inline_headings_are_detected(self) -> None:
        sections = parse_cv(
            "EDUCATION Applied Studies\n"
            "Work Experience Example Cooperative\n"
            "TECHNICAL SKILLS Planning"
        )

        self.assertEqual(
            sections,
            {
                "education": "Applied Studies",
                "experience": "Example Cooperative",
                "skills": "Planning",
            },
        )

    def test_adjacent_section_transitions_on_one_line_are_detected(self) -> None:
        sections = parse_cv(
            "EDUCATION Applied Studies TECHNICAL SKILLS Planning LANGUAGES English"
        )

        self.assertEqual(
            sections,
            {
                "education": "Applied Studies",
                "skills": "Planning",
                "languages": "English",
            },
        )

    def test_existing_canonical_headings_still_work(self) -> None:
        sections = parse_cv(
            "PROFILE\nOverview\nEDUCATION\nStudy\nWORK EXPERIENCE\nWork\n"
            "PROJECTS\nProject\nSKILLS\nSkill\nCERTIFICATIONS\nCertificate\n"
            "LANGUAGES\nLanguage"
        )

        self.assertEqual(
            sections,
            {
                "profile": "Overview",
                "education": "Study",
                "experience": "Work",
                "projects": "Project",
                "skills": "Skill",
                "certifications": "Certificate",
                "languages": "Language",
            },
        )

    def test_heading_normalization_is_case_and_whitespace_insensitive(self) -> None:
        sections = parse_cv(
            "  professional   summary:  \nOverview\n"
            "\ttechnical   skills : \t\nPlanning"
        )

        self.assertEqual(
            sections,
            {"profile": "Overview", "skills": "Planning"},
        )

    def test_generic_aliases_map_to_canonical_sections(self) -> None:
        aliases = {
            "ACADEMIC BACKGROUND": "education",
            "EMPLOYMENT HISTORY": "experience",
            "TECHNICAL SKILLS": "skills",
            "TOOLS": "skills",
            "LANGUAGE SKILLS": "languages",
            "SELECTED PROJECTS": "projects",
            "LICENSES AND CERTIFICATIONS": "certifications",
        }

        for alias, canonical in aliases.items():
            with self.subTest(alias=alias):
                self.assertEqual(parse_cv(f"{alias}\nContent"), {canonical: "Content"})

    def test_generic_skill_aliases_map_to_skills(self) -> None:
        aliases = (
            "SKILLS AND STRENGTHS",
            "COMPUTER SKILLS",
            "DIGITAL SKILLS",
            "PROFESSIONAL SKILLS",
            "PERSONAL SKILLS",
        )

        for alias in aliases:
            with self.subTest(alias=alias):
                self.assertEqual(parse_cv(f"{alias}\nPlanning"), {"skills": "Planning"})

    def test_skill_alias_normalization_remains_conservative(self) -> None:
        self.assertEqual(
            parse_cv("  computer   skills:  \nPlanning"),
            {"skills": "Planning"},
        )

        for sentence in (
            "Computer skills support daily operations.",
            "Professional skills overview",
            "My personal skills include communication.",
        ):
            with self.subTest(sentence=sentence):
                self.assertEqual(parse_cv(sentence), {"other": sentence})

    def test_recognized_heading_closes_previous_section_and_is_not_content(
        self,
    ) -> None:
        sections = parse_cv("EDUCATION\nApplied Studies\nTOOLS\nPlanning")

        self.assertEqual(
            sections,
            {"education": "Applied Studies", "skills": "Planning"},
        )

    def test_ordinary_sentences_and_partial_matches_are_not_headings(self) -> None:
        sections = parse_cv(
            "PROFILE\nTechnical skills support effective delivery.\n"
            "TECHNICAL SKILLS OVERVIEW\nStill profile content"
        )

        self.assertEqual(
            sections,
            {
                "profile": (
                    "Technical skills support effective delivery.\n"
                    "TECHNICAL SKILLS OVERVIEW\nStill profile content"
                )
            },
        )

    def test_unknown_uppercase_heading_is_not_mapped_to_known_section(self) -> None:
        sections = parse_cv("EDUCATION\nApplied Studies\nINTERESTS\nReading")

        self.assertEqual(
            sections,
            {"education": "Applied Studies\nINTERESTS\nReading"},
        )
        self.assertNotIn("skills", sections)

    def test_repeated_aliases_append_to_the_same_canonical_section(self) -> None:
        sections = parse_cv(
            "SKILLS AND STRENGTHS\nPlanning\n"
            "COMPUTER SKILLS\nCommunication"
        )

        self.assertEqual(sections, {"skills": "Planning\nCommunication"})

    def test_alias_sections_produce_a_populated_candidate_profile(self) -> None:
        sections = parse_cv(
            "ACADEMIC HISTORY\nApplied Studies\n"
            "General University | 2016 - 2020\n"
            "EMPLOYMENT HISTORY\nExample Cooperative\nCoordinator\n"
            "2020 - Present\n"
            "TOOLS\nPlanning, Communication\n"
            "LANGUAGE PROFICIENCY\nEnglish C1"
        )

        profile = extract_candidate_profile(sections)

        self.assertEqual(profile.education[0].degree, "Applied Studies")
        self.assertEqual(profile.experience[0].title, "Coordinator")
        self.assertEqual(
            [skill.name for skill in profile.skills],
            ["Planning", "Communication"],
        )
        self.assertEqual(profile.languages, ["English C1"])


if __name__ == "__main__":
    unittest.main()
