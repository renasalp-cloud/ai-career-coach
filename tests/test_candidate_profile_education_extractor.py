import unittest

from app.candidate_profile.extractor import extract_candidate_profile
from app.cv_parser import parse_cv


class CandidateProfileEducationExtractorTest(unittest.TestCase):
    def test_existing_bracketed_full_date_format_remains_supported(self) -> None:
        profile = extract_candidate_profile(
            {
                "education": (
                    "General Studies\n"
                    "Example Institution [ 01/09/2016 - 30/06/2020 ]"
                )
            }
        )

        self.assertEqual(len(profile.education), 1)
        self.assertEqual(profile.education[0].degree, "General Studies")
        self.assertEqual(profile.education[0].institution, "Example Institution")
        self.assertEqual(profile.education[0].start_date, "01/09/2016")
        self.assertEqual(profile.education[0].end_date, "30/06/2020")
        self.assertEqual(profile.education[0].status, "completed")

    def test_extracts_standalone_year_range_after_institution(self) -> None:
        profile = extract_candidate_profile(
            {"education": "Example Institution\n2016 - 2020"}
        )

        self.assertEqual(len(profile.education), 1)
        self.assertEqual(profile.education[0].degree, "")
        self.assertEqual(profile.education[0].institution, "Example Institution")
        self.assertEqual(profile.education[0].start_date, "2016")
        self.assertEqual(profile.education[0].end_date, "2020")
        self.assertEqual(profile.education[0].status, "completed")

    def test_extracts_degree_and_institution_before_standalone_range(self) -> None:
        profile = extract_candidate_profile(
            {
                "education": (
                    "General Studies\nExample Institution\n2016–Present"
                )
            }
        )

        self.assertEqual(len(profile.education), 1)
        self.assertEqual(profile.education[0].degree, "General Studies")
        self.assertEqual(profile.education[0].institution, "Example Institution")
        self.assertEqual(profile.education[0].end_date, "Present")
        self.assertEqual(profile.education[0].status, "current")

    def test_extracts_pipe_delimited_year_range(self) -> None:
        profile = extract_candidate_profile(
            {
                "education": (
                    "General Studies\nExample Institution | 2016 - 2020"
                )
            }
        )

        self.assertEqual(len(profile.education), 1)
        self.assertEqual(profile.education[0].degree, "General Studies")
        self.assertEqual(profile.education[0].institution, "Example Institution")
        self.assertEqual(profile.education[0].start_date, "2016")
        self.assertEqual(profile.education[0].end_date, "2020")

    def test_extracts_bullet_delimited_range_with_unicode_dash(self) -> None:
        profile = extract_candidate_profile(
            {"education": "Example Institution • 2016–Current"}
        )

        self.assertEqual(len(profile.education), 1)
        self.assertEqual(profile.education[0].institution, "Example Institution")
        self.assertEqual(profile.education[0].end_date, "Current")
        self.assertEqual(profile.education[0].status, "current")

    def test_rejects_ambiguous_year_range_without_institution(self) -> None:
        profile = extract_candidate_profile({"education": "2016 - 2020"})

        self.assertEqual(profile.education, [])

    def test_rejects_malformed_or_unanchored_year_ranges(self) -> None:
        malformed_sections = (
            "[ 01/09/2016 - 30/06/2020 ]",
            "Example Institution | 2016",
            "Example Institution | 2016 - unknown",
            "Example Institution | 2020 - 2016",
            "Example Institution 2016 - 2020",
            "Example Institution | attended 2016 - 2020",
        )

        for education in malformed_sections:
            with self.subTest(education=education):
                profile = extract_candidate_profile({"education": education})
                self.assertEqual(profile.education, [])

    def test_date_line_starts_a_new_entry_and_isolates_status(self) -> None:
        profile = extract_candidate_profile(
            {"education": (
                "2025 – Present\n"
                "Economics and Culture University – Bachelor's Degree in Marketing\n"
                "2023 – 2024\nRiga Distance Secondary School"
            )}
        )

        self.assertEqual(len(profile.education), 2)
        self.assertEqual(profile.education[0].institution, "Economics and Culture University")
        self.assertEqual(profile.education[0].degree, "Bachelor's Degree in Marketing")
        self.assertEqual(
            (profile.education[0].start_date, profile.education[0].end_date, profile.education[0].status),
            ("2025", "Present", "current"),
        )
        self.assertEqual(profile.education[1].institution, "Riga Distance Secondary School")
        self.assertEqual(
            (profile.education[1].start_date, profile.education[1].end_date, profile.education[1].status),
            ("2023", "2024", "completed"),
        )

    def test_preserves_four_consecutive_date_first_records(self) -> None:
        profile = extract_candidate_profile(
            {"education": (
                "2025 – Present\nEconomics and Culture University – Bachelor's Degree in Marketing\n"
                "2023 – 2024\nRiga Distance Secondary School\n"
                "2022 – 2023\nRiga 9th School\n"
                "2012 – 2022\nRiga Jugla Secondary School"
            )}
        )

        self.assertEqual(len(profile.education), 4)
        self.assertEqual(
            [(item.start_date, item.end_date) for item in profile.education],
            [("2025", "Present"), ("2023", "2024"), ("2022", "2023"), ("2012", "2022")],
        )
        self.assertEqual(profile.education[-1].institution, "Riga Jugla Secondary School")

    def test_degree_only_active_entry_does_not_inherit_later_status(self) -> None:
        profile = extract_candidate_profile(
            {"education": (
                "2025 – Present\nBachelor's Degree in Marketing\n"
                "2023 – 2024\nSecondary School"
            )}
        )

        self.assertEqual(profile.education[0].degree, "Bachelor's Degree in Marketing")
        self.assertEqual(profile.education[0].status, "current")
        self.assertEqual(profile.education[1].status, "completed")

    def test_closed_date_first_range_is_completed(self) -> None:
        profile = extract_candidate_profile(
            {"education": "2021 – 2025\nUniversity Name – Bachelor of Information Technology"}
        )

        self.assertEqual(len(profile.education), 1)
        self.assertEqual(profile.education[0].status, "completed")

    def test_active_marker_variants_are_current(self) -> None:
        for marker in ("Present", "Current", "Ongoing", "In Progress", "Expected 2027"):
            with self.subTest(marker=marker):
                profile = extract_candidate_profile(
                    {"education": f"2025 – {marker}\nBachelor's Degree in Marketing"}
                )
                self.assertEqual(profile.education[0].status, "current")

    def test_parser_to_candidate_profile_keeps_independent_records(self) -> None:
        sections = parse_cv(
            "Education\n2025 – Present\n"
            "Economics and Culture University – Bachelor's Degree in Marketing\n"
            "2023 – 2024\nRiga Distance Secondary School"
        )

        profile = extract_candidate_profile(sections)

        self.assertEqual(len(profile.education), 2)
        self.assertEqual(profile.education[0].status, "current")
        self.assertEqual(profile.education[1].institution, "Riga Distance Secondary School")


if __name__ == "__main__":
    unittest.main()
