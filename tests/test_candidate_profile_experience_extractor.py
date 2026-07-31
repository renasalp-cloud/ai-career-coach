import unittest

from app.candidate_profile.extractor import extract_candidate_profile


class CandidateProfileExperienceExtractorTest(unittest.TestCase):
    def test_existing_bracketed_full_date_format_remains_supported(self) -> None:
        profile = extract_candidate_profile(
            {
                "experience": (
                    "Example Cooperative - Remote\n"
                    "Coordinator\n"
                    "[ 01/07/2020 - Current ]\n"
                    "- Coordinated recurring activities"
                )
            }
        )

        self.assertEqual(len(profile.experience), 1)
        entry = profile.experience[0]
        self.assertEqual(entry.organization, "Example Cooperative")
        self.assertEqual(entry.title, "Coordinator")
        self.assertEqual(entry.start_date, "01/07/2020")
        self.assertEqual(entry.end_date, "Current")
        self.assertEqual(entry.location, "Remote")
        self.assertEqual(entry.highlights, ["Coordinated recurring activities"])

    def test_extracts_organization_then_title_with_year_range(self) -> None:
        profile = extract_candidate_profile(
            {"experience": "Example Cooperative\nCoordinator\n2020 - Present"}
        )

        entry = profile.experience[0]
        self.assertEqual(entry.organization, "Example Cooperative")
        self.assertEqual(entry.title, "Coordinator")
        self.assertEqual(entry.start_date, "2020")
        self.assertEqual(entry.end_date, "Present")

    def test_extracts_conservatively_distinguishable_title_then_organization(self) -> None:
        profile = extract_candidate_profile(
            {"experience": "Coordinator\nExample Cooperative\n2020 - 2024"}
        )

        entry = profile.experience[0]
        self.assertEqual(entry.organization, "Example Cooperative")
        self.assertEqual(entry.title, "Coordinator")

    def test_extracts_pipe_delimited_location_and_unicode_dash(self) -> None:
        profile = extract_candidate_profile(
            {
                "experience": (
                    "Example Cooperative | Remote\nCoordinator\n2020–Current"
                )
            }
        )

        entry = profile.experience[0]
        self.assertEqual(entry.organization, "Example Cooperative")
        self.assertEqual(entry.location, "Remote")
        self.assertEqual(entry.start_date, "2020")
        self.assertEqual(entry.end_date, "Current")

    def test_highlights_stay_with_their_entries(self) -> None:
        profile = extract_candidate_profile(
            {
                "experience": (
                    "Example Cooperative\nCoordinator\n2020 - 2024\n"
                    "- Coordinated recurring activities\n"
                    "- Prepared recurring reports\n"
                    "Sample Association\nFacilitator\n2018 - 2019\n"
                    "• Facilitated scheduled sessions"
                )
            }
        )

        self.assertEqual(len(profile.experience), 2)
        self.assertEqual(
            profile.experience[0].highlights,
            ["Coordinated recurring activities", "Prepared recurring reports"],
        )
        self.assertEqual(
            profile.experience[1].highlights,
            ["Facilitated scheduled sessions"],
        )

    def test_extracts_date_first_month_year_entry_with_unicode_dash(self) -> None:
        profile = extract_candidate_profile(
            {
                "experience": (
                    "02/2025 – Present\n"
                    "Example Organization – Service Coordinator\n"
                    "● Coordinated recurring activities"
                )
            }
        )

        self.assertEqual(len(profile.experience), 1)
        entry = profile.experience[0]
        self.assertEqual(entry.organization, "Example Organization")
        self.assertEqual(entry.title, "Service Coordinator")
        self.assertEqual(entry.start_date, "02/2025")
        self.assertEqual(entry.end_date, "Present")
        self.assertEqual(entry.highlights, ["Coordinated recurring activities"])

    def test_extracts_date_first_year_entry_with_ascii_delimiter(self) -> None:
        profile = extract_candidate_profile(
            {"experience": "2020 - 2024\nExample Organization - Coordinator"}
        )

        entry = profile.experience[0]
        self.assertEqual(entry.organization, "Example Organization")
        self.assertEqual(entry.title, "Coordinator")

    def test_extracts_date_first_full_date_entry_with_pipe_and_current(self) -> None:
        profile = extract_candidate_profile(
            {
                "experience": (
                    "01/07/2020 - Current\n"
                    "Example Organization | Service Coordinator"
                )
            }
        )

        entry = profile.experience[0]
        self.assertEqual(entry.start_date, "01/07/2020")
        self.assertEqual(entry.end_date, "Current")
        self.assertEqual(entry.organization, "Example Organization")
        self.assertEqual(entry.title, "Service Coordinator")

    def test_separates_multiple_date_first_entries_and_their_highlights(self) -> None:
        profile = extract_candidate_profile(
            {
                "experience": (
                    "02/2025 – Present\n"
                    "Example Organization – Service Coordinator\n"
                    "- Coordinated recurring activities\n"
                    "• Prepared documentation\n"
                    "\n"
                    "09/2024 - 10/2024\n"
                    "Sample Association | Registration Specialist\n"
                    "● Prepared reports\n"
                    "● Organized daily work\n"
                    "●"
                )
            }
        )

        self.assertEqual(len(profile.experience), 2)
        self.assertEqual(
            profile.experience[0].highlights,
            ["Coordinated recurring activities", "Prepared documentation"],
        )
        self.assertEqual(
            profile.experience[1].highlights,
            ["Prepared reports", "Organized daily work"],
        )

    def test_rejects_incomplete_ambiguous_or_invalid_date_first_entries(self) -> None:
        sections = (
            "2020 - 2024",
            "02/2025 – Present",
            "02/2025 – Present\n● Coordinated recurring activities",
            "2024 - 2020\nExample Organization – Coordinator",
            "2020 - unknown\nExample Organization – Coordinator",
            "02/2025 – Present\nExample Organization Coordinator",
        )

        for experience in sections:
            with self.subTest(experience=experience):
                profile = extract_candidate_profile({"experience": experience})
                self.assertEqual(profile.experience, [])

    def test_rejects_standalone_malformed_and_reversed_ranges(self) -> None:
        sections = (
            "2020 - 2024",
            "Example Cooperative\nCoordinator\n2024 - 2020",
            "Example Cooperative\nCoordinator\n2020 - unknown",
            "Example Cooperative\n2020 - 2024",
        )

        for experience in sections:
            with self.subTest(experience=experience):
                profile = extract_candidate_profile({"experience": experience})
                self.assertEqual(profile.experience, [])

    def test_other_candidate_fields_remain_unchanged(self) -> None:
        profile = extract_candidate_profile(
            {
                "education": (
                    "General Studies\nExample Institution\n2016 - 2020"
                ),
                "experience": "Example Cooperative\nCoordinator\n2020 - Present",
                "skills": "Planning, Written communication",
                "languages": "English C1",
            }
        )

        self.assertEqual(profile.education[0].institution, "Example Institution")
        self.assertEqual(
            [skill.name for skill in profile.skills],
            ["Planning", "Written communication"],
        )
        self.assertEqual(profile.languages, ["English C1"])


if __name__ == "__main__":
    unittest.main()
