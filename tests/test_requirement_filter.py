import unittest

from app.models import RequirementProfile, RequirementSkill
from app.requirements.filter import RequirementProfileFilter


class RequirementProfileFilterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.filter = RequirementProfileFilter()

    def test_filters_clear_non_requirements(self) -> None:
        names = [
            "Benefits",
            "Competitive salary based on experience",
            "We offer a competitive salary",
            "Competitive compensation package",
            "Salary range: €50,000–€70,000",
            "Base salary plus annual bonus",
            "Annual performance bonus",
            "Stock option plan",
            "Health and dental insurance",
            "Pension benefits",
            "Paid leave",
            "Wellness program",
            "Office perks",
            "Relocation assistance is available",
            "Visa sponsorship may be provided",
            "Flexible working hours",
            "A collaborative and inclusive workplace",
            "We are an equal opportunity employer",
            "Please submit your CV and cover letter",
            "Only shortlisted applicants will be contacted",
            "The interview process will include two stages",
            "We offer professional development support",
        ]

        result = self.filter.filter(self._profile(*names))

        self.assertEqual(result.skills, [])

    def test_preserves_candidate_expectations_and_ordinary_requirements(self) -> None:
        names = [
            "Willingness to relocate",
            "Must be eligible to work in the country",
            "Ability to work flexible hours",
            "Availability for occasional travel",
            "Experience managing employee benefits",
            "Knowledge of compensation and benefits administration",
            "Experience managing salary administration",
            "Ability to prepare salary reports",
            "Experience with payroll and compensation processes",
            "Knowledge of salary benchmarking",
            "Experience supporting visa and immigration processes",
            "Ability to work in a collaborative environment",
            "Python",
            "Calendar management",
        ]

        result = self.filter.filter(self._profile(*names))

        self.assertEqual([skill.name for skill in result.skills], names)

    def test_preserves_order_priorities_metadata_and_duplicates(self) -> None:
        profile = RequirementProfile(
            title="Role",
            skills=[
                RequirementSkill(name="Python", priority="required"),
                RequirementSkill(name="Health insurance", priority="preferred"),
                RequirementSkill(name="Python", priority="optional"),
            ],
            responsibilities=["Deliver work"],
            qualifications=["Relevant experience"],
            source="test",
        )

        result = self.filter.filter(profile)

        self.assertEqual(
            [(skill.name, skill.priority) for skill in result.skills],
            [("Python", "required"), ("Python", "optional")],
        )
        self.assertEqual(result.title, profile.title)
        self.assertEqual(result.responsibilities, profile.responsibilities)
        self.assertEqual(result.qualifications, profile.qualifications)
        self.assertEqual(result.source, profile.source)

    def test_does_not_mutate_input_and_repeated_execution_is_identical(self) -> None:
        profile = self._profile("Python", "Health insurance")
        original = profile.model_dump()

        first = self.filter.filter(profile)
        second = self.filter.filter(profile)
        first.skills[0].name = "Changed"

        self.assertEqual(profile.model_dump(), original)
        self.assertEqual(second.model_dump(), self.filter.filter(profile).model_dump())

    @staticmethod
    def _profile(*names: str) -> RequirementProfile:
        priorities = ("required", "preferred", "optional")
        return RequirementProfile(
            skills=[
                RequirementSkill(name=name, priority=priorities[index % 3])
                for index, name in enumerate(names)
            ]
        )


if __name__ == "__main__":
    unittest.main()
