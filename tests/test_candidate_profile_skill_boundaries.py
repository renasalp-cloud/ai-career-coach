import unittest

from app.candidate_profile.extractor import extract_candidate_profile
from app.cv_parser import parse_cv


class CandidateProfileSkillBoundariesTest(unittest.TestCase):
    @staticmethod
    def _names(text: str) -> list[str]:
        profile = extract_candidate_profile({"skills": text})
        return [skill.name for skill in profile.skills]

    def test_known_skill_heading_closes_education_section(self) -> None:
        sections = parse_cv(
            "EDUCATION AND TRAINING\n"
            "Advanced Studies\n"
            "Learning Institute [ 01/09/2022 - Current ]\n"
            "DIGITAL SKILLS\n"
            "Python\nTeamwork"
        )

        self.assertNotIn("Advanced Studies", sections["skills"])
        self.assertEqual(self._names(sections["skills"]), ["Python", "Teamwork"])

    def test_education_metadata_and_urls_are_not_skills(self) -> None:
        text = (
            "Master's Degree in Applied Systems\n"
            "Learning Institute [05/07/2025 - Current]\n"
            "Country: Exampleland\nCity: Example City\n"
            "Field(s) of study: General Studies\n"
            "Level in EQF: 7\nEQF level: 6\n"
            "Institution: Learning Institute\nUniversity: General University\n"
            "Website: https://example.test/profile\n"
            "https://example.test\nCurrent\nPresent\nPython"
        )

        self.assertEqual(self._names(text), ["Python"])

    def test_reconstructs_conservative_wrapped_skill_phrases(self) -> None:
        self.assertEqual(
            self._names(
                "Image Preprocessing and Image\n"
                "Classification\n"
                "Basic UI/UX\n"
                "improvements\n"
                "Git &\n"
                "GitHub\n"
                "Jupyter Notebook"
            ),
            [
                "Image Preprocessing and Image Classification",
                "Basic UI/UX improvements",
                "Git & GitHub",
                "Jupyter Notebook",
            ],
        )

    def test_continuation_fragments_are_not_emitted_alone(self) -> None:
        self.assertEqual(
            self._names("improvements\nas well as\nand\nCurrent\nPresent"),
            [],
        )

    def test_noisy_skills_heading_closes_and_preserves_final_education(self) -> None:
        profile = extract_candidate_profile(parse_cv(
            "Education\n2012 – 2022\nRiga Jugla Secondary School\n"
            "Skills and Streng ths\nGood communication and organizational skills."
        ))

        self.assertEqual(len(profile.education), 1)
        self.assertEqual(profile.education[0].institution, "Riga Jugla Secondary School")
        self.assertEqual(profile.education[0].status, "completed")
        self.assertNotIn("Streng ths", profile.education[0].model_dump_json())
        self.assertIn("Good communication and organizational skills.", profile.summary)

    def test_additional_information_retains_only_descriptive_evidence(self) -> None:
        profile = extract_candidate_profile(parse_cv(
            "Additional Informa tion\n"
            "Good communication and organizational skills.\n"
            "Ability to stay calm under pressure.\nDriving licence: B"
        ))

        self.assertIn("Good communication and organizational skills.", profile.summary)
        self.assertIn("Ability to stay calm under pressure.", profile.summary)
        self.assertNotIn("Additional", profile.summary)
        self.assertNotIn("Driving licence", profile.summary)

    def test_representative_pipeline_keeps_four_education_records_independent(self) -> None:
        profile = extract_candidate_profile(parse_cv(
            "Education\n2025 – Present\nUniversity One – Bachelor's Degree in Marketing\n"
            "2023 – 2024\nCollege Two\n2022 – 2023\nAcademy Three\n"
            "2012 – 2022\nRiga Jugla Secondary School\n"
            "Skills and Streng ths\nAbility to take responsibility and analyze situations."
        ))

        self.assertEqual(len(profile.education), 4)
        self.assertEqual(
            profile.education[-1].institution,
            "Riga Jugla Secondary School",
        )
        self.assertTrue(all(
            "Streng ths" not in entry.model_dump_json()
            for entry in profile.education
        ))
        self.assertIn("Ability to take responsibility", profile.summary)


if __name__ == "__main__":
    unittest.main()
