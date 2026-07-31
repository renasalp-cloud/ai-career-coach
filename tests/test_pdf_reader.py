import unittest
from unittest.mock import Mock, patch

from app.candidate_profile.extractor import extract_candidate_profile
from app.cv_parser import parse_cv
from app.pdf_reader import extract_text


def _page(
    standard_text: str,
    fragments: list[tuple[str, float, float]],
    *,
    fail_positioned: bool = False,
) -> Mock:
    page = Mock()
    page.mediabox.width = 600

    def extract_text(*, visitor_text=None):
        if visitor_text is None:
            return standard_text
        if fail_positioned:
            raise RuntimeError("positioned extraction failed")
        for text, x, y in fragments:
            visitor_text(
                text,
                [1, 0, 0, 1, x, y],
                [1, 0, 0, 1, 0, 0],
                None,
                10,
            )
        return standard_text

    page.extract_text.side_effect = extract_text
    return page


def _extract(*pages: Mock) -> str:
    reader = Mock()
    reader.pages = list(pages)
    with patch("app.pdf_reader.PdfReader", return_value=reader):
        return extract_text("synthetic.pdf")


class PdfReaderTest(unittest.TestCase):
    def test_single_column_page_remains_top_to_bottom(self) -> None:
        page = _page(
            "SUMMARY\nGeneral profile\nSKILLS\nPlanning",
            [
                ("SUMMARY", 50, 700),
                ("General profile", 50, 680),
                ("SKILLS", 50, 640),
                ("Planning", 50, 620),
            ],
        )

        self.assertEqual(
            _extract(page),
            "SUMMARY\nGeneral profile\nSKILLS\nPlanning",
        )

    def test_two_columns_are_read_column_by_column(self) -> None:
        page = _page(
            "EDUCATION\nSKILLS\nGeneral Institute\nPlanning",
            [
                ("EDUCATION", 40, 700),
                ("SKILLS", 340, 700),
                ("General Institute", 40, 680),
                ("Planning", 340, 680),
            ],
        )

        self.assertEqual(
            _extract(page),
            "EDUCATION\nGeneral Institute\nSKILLS\nPlanning",
        )

    def test_column_headings_remain_adjacent_to_their_content(self) -> None:
        page = _page(
            "",
            [
                ("LANGUAGES", 40, 700),
                ("EXPERIENCE", 340, 700),
                ("English C1", 40, 680),
                ("General Organization", 340, 680),
            ],
        )

        self.assertEqual(
            _extract(page),
            "LANGUAGES\nEnglish C1\nEXPERIENCE\nGeneral Organization",
        )

    def test_multiple_pages_are_kept_separate_and_ordered(self) -> None:
        first = _page("FIRST PAGE", [("FIRST PAGE", 40, 700), ("Content", 40, 680)])
        second = _page(
            "SECOND PAGE",
            [("SECOND PAGE", 40, 700), ("More content", 40, 680)],
        )

        self.assertEqual(
            _extract(first, second),
            "FIRST PAGE\nContent\n\nSECOND PAGE\nMore content",
        )

    def test_positioned_failure_falls_back_to_standard_extraction(self) -> None:
        page = _page("SUMMARY\nFallback content", [], fail_positioned=True)

        self.assertEqual(_extract(page), "SUMMARY\nFallback content")

    def test_empty_positioned_fragments_do_not_replace_standard_text(self) -> None:
        page = _page("SKILLS\nFallback skill", [])

        self.assertEqual(_extract(page), "SKILLS\nFallback skill")

    def test_duplicate_fragments_are_not_emitted(self) -> None:
        page = _page(
            "",
            [
                ("SUMMARY", 40, 700),
                ("SUMMARY", 40, 700),
                ("General profile", 40, 680),
            ],
        )

        self.assertEqual(_extract(page), "SUMMARY\nGeneral profile")

    def test_minor_baseline_differences_form_one_visual_line(self) -> None:
        page = _page(
            "",
            [
                ("General", 40, 700),
                ("heading", 90, 702),
                ("Content", 40, 680),
            ],
        )

        self.assertEqual(_extract(page), "General heading\nContent")

    def test_widely_separated_columns_are_not_merged_into_one_line(self) -> None:
        page = _page(
            "",
            [
                ("LEFT", 40, 700),
                ("Left content", 40, 680),
                ("RIGHT", 340, 700),
                ("Right content", 340, 680),
            ],
        )

        self.assertEqual(
            _extract(page),
            "LEFT\nLeft content\nRIGHT\nRight content",
        )

    def test_artificial_glyph_spacing_is_removed_conservatively(self) -> None:
        page = _page(
            "",
            [
                ("S K I L L S", 40, 700),
                ("P l a n n i n g ,  W r i t i n g", 40, 680),
            ],
        )

        self.assertEqual(_extract(page), "SKILLS\nPlanning, Writing")

    def test_reconstructed_modern_cv_populates_the_real_candidate_pipeline(self) -> None:
        page = _page(
            "",
            [
                ("E D U C A T I O N", 40, 700),
                ("Applied Studies", 40, 680),
                ("General Institute | 2018 - 2022", 40, 660),
                ("S K I L L S", 40, 620),
                ("Planning, Writing", 40, 600),
                ("W O R K  E X P E R I E N C E", 340, 700),
                ("General Cooperative", 340, 680),
                ("Coordinator", 340, 660),
                ("2022 - Present", 340, 640),
                ("L A N G U A G E S", 340, 600),
                ("General Language (advanced)", 340, 580),
            ],
        )

        profile = extract_candidate_profile(parse_cv(_extract(page)))

        self.assertEqual(profile.education[0].degree, "Applied Studies")
        self.assertEqual(profile.experience[0].title, "Coordinator")
        self.assertEqual(
            [skill.name for skill in profile.skills],
            ["Planning", "Writing"],
        )
        self.assertEqual(profile.languages, ["General Language (advanced)"])


if __name__ == "__main__":
    unittest.main()
