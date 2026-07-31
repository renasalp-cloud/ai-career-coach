import unittest

from app.candidate_profile.extractor import extract_candidate_profile
from app.candidate_profile.normalizer import normalize_candidate_profile
from app.cv_parser import parse_cv


class CandidateProfileSkillsExtractorTest(unittest.TestCase):
    def _skill_names(self, skills_text: str) -> list[str]:
        profile = extract_candidate_profile({"skills": skills_text})
        return [skill.name for skill in profile.skills]

    def test_extracts_comma_separated_skills(self) -> None:
        self.assertEqual(
            self._skill_names("Planning, Written communication"),
            ["Planning", "Written communication"],
        )

    def test_extracts_one_skill_per_line(self) -> None:
        self.assertEqual(
            self._skill_names(
                "Planning\nWritten communication\nProblem solving"
            ),
            ["Planning", "Written communication", "Problem solving"],
        )

    def test_extracts_pipe_delimited_skills(self) -> None:
        self.assertEqual(
            self._skill_names(
                "Planning | Written communication | Problem solving"
            ),
            ["Planning", "Written communication", "Problem solving"],
        )

    def test_extracts_bullet_delimited_skills(self) -> None:
        self.assertEqual(
            self._skill_names(
                "Planning • Written communication • Problem solving"
            ),
            ["Planning", "Written communication", "Problem solving"],
        )

    def test_removes_hyphen_bullet_markers(self) -> None:
        self.assertEqual(
            self._skill_names(
                "- Planning\n- Written communication\n- Problem solving"
            ),
            ["Planning", "Written communication", "Problem solving"],
        )

    def test_removes_unicode_bullet_markers(self) -> None:
        self.assertEqual(
            self._skill_names(
                "• Planning\n• Written communication\n• Problem solving"
            ),
            ["Planning", "Written communication", "Problem solving"],
        )

    def test_trims_whitespace_and_ignores_empty_tokens(self) -> None:
        self.assertEqual(
            self._skill_names(
                "  Planning  , , |  Written communication  •  "
            ),
            ["Planning", "Written communication"],
        )

    def test_duplicates_continue_to_follow_normalizer_behavior(self) -> None:
        profile = extract_candidate_profile(
            {"skills": "Planning\nplanning\nPlanning"}
        )

        normalized = normalize_candidate_profile(profile)

        self.assertEqual(
            [skill.name for skill in normalized.skills],
            ["Planning"],
        )

    def test_category_labels_do_not_become_skills(self) -> None:
        self.assertEqual(
            self._skill_names("SKILLS\nTechnical Skills:\nSoft Skills:"),
            [],
        )

    def test_category_prefixed_explicit_values_are_preserved(self) -> None:
        self.assertEqual(
            self._skill_names(
                "Technical Skills: Planning, Documentation\n"
                "Soft Skills: Written communication"
            ),
            ["Planning", "Documentation", "Written communication"],
        )

    def test_extracts_explicit_values_from_short_skill_prose(self) -> None:
        examples = {
            "Experience working with MS Office.": ["MS Office"],
            "Experience with Rkeeper, Andromeda, Saule, ZCA.": [
                "Rkeeper",
                "Andromeda",
                "Saule",
                "ZCA",
            ],
            "Skills in planning and documentation.": [
                "planning",
                "documentation",
            ],
            "Good communication and organizational skills.": [
                "communication",
                "organizational",
            ],
            "Knowledge of System One.": ["System One"],
            "Proficient in System Two.": ["System Two"],
        }

        for prose, expected in examples.items():
            with self.subTest(prose=prose):
                self.assertEqual(self._skill_names(prose), expected)

    def test_extracts_values_from_supported_natural_language_forms(self) -> None:
        examples = {
            "Experience with Atlas Engine.": ["Atlas Engine"],
            "Experience working with Beacon Grid.": ["Beacon Grid"],
            (
                "Good computer skills and experience working with "
                "Cobalt Suite and similar technologies."
            ): ["Cobalt Suite"],
            "Knowledge of Delta Console.": ["Delta Console"],
        }

        for prose, expected in examples.items():
            with self.subTest(prose=prose):
                self.assertEqual(self._skill_names(prose), expected)

    def test_splits_supported_connectors_and_comma_separated_values(self) -> None:
        examples = {
            "Experience with Ember Hub and Flux Board.": [
                "Ember Hub",
                "Flux Board",
            ],
            "Experience with Ember Hub as well as Flux Board.": [
                "Ember Hub",
                "Flux Board",
            ],
            "Knowledge of toolsets such as Gable Kit and Harbor Desk.": [
                "Gable Kit",
                "Harbor Desk",
            ],
            "Knowledge of platforms including Ion Portal and Juniper Box.": [
                "Ion Portal",
                "Juniper Box",
            ],
            "Experience with Kestrel App, Lumen Stack and Mosaic Cloud.": [
                "Kestrel App",
                "Lumen Stack",
                "Mosaic Cloud",
            ],
        }

        for prose, expected in examples.items():
            with self.subTest(prose=prose):
                self.assertEqual(self._skill_names(prose), expected)

    def test_extracts_multiline_values_after_nested_connectors(self) -> None:
        self.assertEqual(
            self._skill_names(
                "Experience with Nova Register, as well as data systems such as\n"
                "Orbit One, Prism Two, Quartz Three."
            ),
            ["Nova Register", "Orbit One", "Prism Two", "Quartz Three"],
        )

    def test_connector_extraction_still_rejects_narrative_fragments(self) -> None:
        self.assertEqual(
            self._skill_names(
                "Ability to work under pressure\n"
                "Strong motivation to grow\n"
                "Towards people\n"
                "Additional Information\n"
                "Communication with customers\n"
                "Stay calm under pressure"
            ),
            [],
        )

    def test_introductory_prose_and_implied_skills_are_not_preserved(self) -> None:
        self.assertEqual(
            self._skill_names("Experience working with MS Office."),
            ["MS Office"],
        )
        self.assertNotIn(
            "Experience working with MS Office",
            self._skill_names("Experience working with MS Office."),
        )

    def test_unbounded_descriptive_sentences_are_not_skills(self) -> None:
        self.assertEqual(
            self._skill_names(
                "Planning supports delivery across multiple teams."
            ),
            [],
        )
        self.assertEqual(
            self._skill_names(
                "Experience working with a complex platform while "
                "coordinating daily operations and preparing reports "
                "for several internal teams and external partners."
            ),
            [],
        )

    def test_generic_category_prefixes_preserve_only_explicit_values(self) -> None:
        self.assertEqual(
            self._skill_names(
                "Computer Skills: MS Office, Rkeeper\n"
                "Professional Skills:\n"
                "Skills and Strengths:"
            ),
            ["MS Office", "Rkeeper"],
        )

    def test_empty_and_punctuation_only_sections_produce_no_skills(self) -> None:
        for skills_text in ("", "-", "•", ",", "|", "-\n•\n,\n|"):
            with self.subTest(skills_text=skills_text):
                self.assertEqual(self._skill_names(skills_text), [])

    def test_other_candidate_sections_remain_unchanged(self) -> None:
        profile = extract_candidate_profile(
            {
                "education": (
                    "Applied Studies\n"
                    "General University [ 01/09/2016 - 30/06/2020 ]"
                ),
                "experience": (
                    "Example Cooperative\n"
                    "Coordinator\n"
                    "[ 01/07/2020 - Current ]"
                ),
                "skills": "Planning\nDocumentation",
                "languages": "English C1",
            }
        )

        self.assertEqual(profile.education[0].degree, "Applied Studies")
        self.assertEqual(
            profile.education[0].institution,
            "General University",
        )
        self.assertEqual(
            profile.experience[0].organization,
            "Example Cooperative",
        )
        self.assertEqual(profile.experience[0].title, "Coordinator")
        self.assertEqual(profile.languages, ["English C1"])

    def test_preserves_existing_source_attribution(self) -> None:
        profile = extract_candidate_profile(
            {"skills": "- Planning\n• Documentation"}
        )

        self.assertEqual(
            [skill.source for skill in profile.skills],
            ["skills_section", "skills_section"],
        )

    def test_additional_information_stops_skill_section(self) -> None:
        sections = parse_cv(
            "SKILLS\nMS Office\nRkeeper\n"
            "ADDITIONAL INFORMATION\n"
            "Strong motivation to grow professionally\n"
            "Ability to take responsibility"
        )

        self.assertEqual(
            self._skill_names(sections["skills"]),
            ["MS Office", "Rkeeper"],
        )
        self.assertEqual(
            sections["additional_information"],
            "Strong motivation to grow professionally\n"
            "Ability to take responsibility",
        )

    def test_rejects_headings_conjunctions_and_narrative_fragments(self) -> None:
        self.assertEqual(
            self._skill_names(
                "Additional Information\nand\nor\nthe\npeople\nlife\n"
                "analyze\nsituations\ntowards people and life\n"
                "Strong motivation to grow professionally\n"
                "Ability to take responsibility\n"
                "Experience working with MS Office\n"
                "Knowledge of System One\n"
                "stay calm under pressure\n"
                "contribute to company development"
            ),
            [],
        )

    def test_real_world_shape_preserves_only_explicit_skills(self) -> None:
        sections = parse_cv(
            "TECHNICAL SKILLS\n"
            "MS Office, Rkeeper, Andromeda, Saule, ZCA, Python, Git, Docker\n"
            "PERSONAL SKILLS\n"
            "Communication | Organizational skills | Problem solving | "
            "Time management\n"
            "ADDITIONAL INFORMATION\n"
            "and stay calm under pressure while maintaining output\n"
            "contribute to company development"
        )

        self.assertEqual(
            self._skill_names(sections["skills"]),
            [
                "MS Office",
                "Rkeeper",
                "Andromeda",
                "Saule",
                "ZCA",
                "Python",
                "Git",
                "Docker",
                "Communication",
                "Organizational skills",
                "Problem solving",
                "Time management",
            ],
        )


if __name__ == "__main__":
    unittest.main()
