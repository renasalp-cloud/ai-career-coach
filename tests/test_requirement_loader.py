import tempfile
import unittest
from pathlib import Path

from app.requirements.loader import RequirementSourceLoader
from app.requirements.source import RequirementSource, RequirementSourceType


class RequirementSourceLoaderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.loader = RequirementSourceLoader()

    def test_loads_pasted_text(self) -> None:
        source = RequirementSource(
            source_type=RequirementSourceType.PASTED_TEXT,
            content="Communication and planning",
        )

        self.assertEqual(self.loader.load(source), "Communication and planning")

    def test_loads_role_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "role_profile.txt"
            path.write_text("Stakeholder management", encoding="utf-8")
            source = RequirementSource(
                source_type=RequirementSourceType.ROLE_PROFILE,
                content=str(path),
            )

            self.assertEqual(self.loader.load(source), "Stakeholder management")

    def test_loads_text_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requirements.txt"
            path.write_text("Required qualifications", encoding="utf-8")
            source = RequirementSource(
                source_type=RequirementSourceType.TEXT_FILE,
                content=str(path),
            )

            self.assertEqual(self.loader.load(source), "Required qualifications")

    def test_missing_file_is_rejected(self) -> None:
        source = RequirementSource(
            source_type=RequirementSourceType.TEXT_FILE,
            content="missing-requirements.txt",
        )

        with self.assertRaisesRegex(FileNotFoundError, "Requirement source file not found"):
            self.loader.load(source)

    def test_empty_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.txt"
            path.write_text("", encoding="utf-8")
            source = RequirementSource(
                source_type=RequirementSourceType.TEXT_FILE,
                content=str(path),
            )

            with self.assertRaisesRegex(ValueError, "Requirement source file is empty"):
                self.loader.load(source)

    def test_whitespace_only_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "whitespace.txt"
            path.write_text(" \n\t ", encoding="utf-8")
            source = RequirementSource(
                source_type=RequirementSourceType.ROLE_PROFILE,
                content=str(path),
            )

            with self.assertRaisesRegex(ValueError, "Requirement source file is empty"):
                self.loader.load(source)

    def test_returned_content_is_trimmed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requirements.txt"
            path.write_text(" \n Required skills \t", encoding="utf-8")
            source = RequirementSource(
                source_type=RequirementSourceType.TEXT_FILE,
                content=str(path),
            )

            self.assertEqual(self.loader.load(source), "Required skills")


if __name__ == "__main__":
    unittest.main()
