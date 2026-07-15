import unittest

from pydantic import ValidationError

from app.requirements.source import RequirementSource, RequirementSourceType


class RequirementSourceTest(unittest.TestCase):
    def test_valid_pasted_text_source(self) -> None:
        source = RequirementSource(
            source_type=RequirementSourceType.PASTED_TEXT,
            content="Communication and planning",
            target_role="Project Manager",
        )

        self.assertEqual(source.source_type, RequirementSourceType.PASTED_TEXT)
        self.assertEqual(source.content, "Communication and planning")
        self.assertEqual(source.target_role, "Project Manager")

    def test_valid_role_profile_source(self) -> None:
        source = RequirementSource(
            source_type=RequirementSourceType.ROLE_PROFILE,
            content="Critical Skills:\n- Stakeholder management",
            name="Project manager profile",
        )

        self.assertEqual(source.source_type, RequirementSourceType.ROLE_PROFILE)
        self.assertEqual(source.name, "Project manager profile")

    def test_valid_text_file_source(self) -> None:
        source = RequirementSource(
            source_type=RequirementSourceType.TEXT_FILE,
            content="Required qualifications",
            name="requirements.txt",
        )

        self.assertEqual(source.source_type, RequirementSourceType.TEXT_FILE)

    def test_empty_content_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            RequirementSource(
                source_type=RequirementSourceType.PASTED_TEXT,
                content="",
            )

    def test_whitespace_only_content_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            RequirementSource(
                source_type=RequirementSourceType.PASTED_TEXT,
                content=" \n\t ",
            )

    def test_content_is_trimmed(self) -> None:
        source = RequirementSource(
            source_type=RequirementSourceType.PASTED_TEXT,
            content=" \n Required skills \t",
        )

        self.assertEqual(source.content, "Required skills")

    def test_optional_fields_may_be_omitted(self) -> None:
        source = RequirementSource(
            source_type=RequirementSourceType.PASTED_TEXT,
            content="Required skills",
        )

        self.assertIsNone(source.name)
        self.assertIsNone(source.target_role)
