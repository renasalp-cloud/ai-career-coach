import unittest

from app.requirements.extractor import extract_requirement_profile


class RequirementExtractorTest(unittest.TestCase):
    def test_extracts_skills_with_priorities(self) -> None:
        role_profile = """
Role: AI Engineer

Critical Skills:
- Python
- Machine learning fundamentals

Important Skills:
- Docker
- Git and GitHub

Optional Skills:
- MLOps
- Research experience
"""

        profile = extract_requirement_profile("AI Engineer", role_profile)

        self.assertEqual(profile.title, "AI Engineer")
        self.assertEqual(profile.source, "extracted_requirement_text")
        self.assertEqual(
            [skill.model_dump() for skill in profile.skills],
            [
                {"name": "Python", "priority": "required"},
                {"name": "Machine learning fundamentals", "priority": "required"},
                {"name": "Docker", "priority": "preferred"},
                {"name": "Git and GitHub", "priority": "preferred"},
                {"name": "MLOps", "priority": "optional"},
                {"name": "Research experience", "priority": "optional"},
            ],
        )


    def test_ignores_unrelated_sections(self) -> None:
        role_profile = """
Critical Skills:
- Python

Evaluation Notes:
- Do not mark a skill as missing if it already appears in the CV.
- Prioritize practical project experience over certificates.
"""

        profile = extract_requirement_profile("AI Engineer", role_profile)

        self.assertEqual(
            [skill.model_dump() for skill in profile.skills],
            [
                {"name": "Python", "priority": "required"},
            ],
        )


    def test_empty_input_returns_empty_skills(self) -> None:
        profile = extract_requirement_profile("AI Engineer", "")

        self.assertEqual(profile.title, "AI Engineer")
        self.assertEqual(profile.source, "extracted_requirement_text")
        self.assertEqual(profile.skills, [])

    def test_maps_generic_headings_to_priorities(self) -> None:
        role_profile = """
Requirements
- Requirement one
Required Qualifications
- Requirement two
Must Have
- Requirement three
Preferred Qualifications
- Preference one
Nice to Have
- Preference two
Bonus Skills
- Bonus one
"""

        profile = extract_requirement_profile("Any Role", role_profile)

        self.assertEqual(
            [(skill.name, skill.priority) for skill in profile.skills],
            [
                ("Requirement one", "required"),
                ("Requirement two", "required"),
                ("Requirement three", "required"),
                ("Preference one", "preferred"),
                ("Preference two", "preferred"),
                ("Bonus one", "optional"),
            ],
        )

    def test_heading_matching_is_case_insensitive_and_supports_colons(self) -> None:
        role_profile = """
  rEqUiReD sKiLlS:  
- Clear communication
NICE-TO-HAVE:
- Facilitation
"""

        profile = extract_requirement_profile("Any Role", role_profile)

        self.assertEqual(
            [(skill.name, skill.priority) for skill in profile.skills],
            [
                ("Clear communication", "required"),
                ("Facilitation", "preferred"),
            ],
        )

    def test_supports_bullet_markers_and_preserves_order(self) -> None:
        role_profile = """
Minimum Qualifications:
- First
* Second
• Third
"""

        profile = extract_requirement_profile("Any Role", role_profile)

        self.assertEqual([skill.name for skill in profile.skills], ["First", "Second", "Third"])

    def test_does_not_introduce_duplicate_requirements(self) -> None:
        role_profile = """
Essential Skills:
- Collaboration
- collaboration
Preferred Skills:
- Collaboration
"""

        profile = extract_requirement_profile("Any Role", role_profile)

        self.assertEqual(
            [(skill.name, skill.priority) for skill in profile.skills],
            [("Collaboration", "required")],
        )

    def test_ignores_responsibility_sections_with_or_without_colons(self) -> None:
        role_profile = """
Requirements:
- Stakeholder communication
Responsibilities
- Lead weekly meetings
What You'll Do:
- Prepare reports
Preferred Qualifications:
- Facilitation
Your Role
- Manage projects
"""

        profile = extract_requirement_profile("Any Role", role_profile)

        self.assertEqual(
            [(skill.name, skill.priority) for skill in profile.skills],
            [
                ("Stakeholder communication", "required"),
                ("Facilitation", "preferred"),
            ],
        )

    def test_bulleted_section_headings_never_become_requirements(self) -> None:
        role_profile = """
Requirements:
- Calendar management
- Responsibilities
- Requirements
- Preferred
- Preferred Qualifications
- Nice to have
"""

        profile = extract_requirement_profile("Office Administrator", role_profile)

        self.assertEqual([skill.name for skill in profile.skills], ["Calendar management"])

    def test_maps_job_description_skill_headings_to_required(self) -> None:
        role_profile = """
Key Skills
Key skill
Skills
Skill
Core Skills
Core skill
Technical Skills
Technical skill
Qualifications
Qualification
"""

        profile = extract_requirement_profile("Any Role", role_profile)

        self.assertEqual(
            [(skill.name, skill.priority) for skill in profile.skills],
            [
                ("Key skill", "required"),
                ("Skill", "required"),
                ("Core skill", "required"),
                ("Technical skill", "required"),
                ("Qualification", "required"),
            ],
        )

    def test_extracts_mixed_bulleted_and_non_bulleted_lines_in_order(self) -> None:
        role_profile = """
Key Skills:
  Python
- Docker
* Cloud platforms
• Communication
python
"""

        profile = extract_requirement_profile("Any Role", role_profile)

        self.assertEqual(
            [skill.name for skill in profile.skills],
            ["Python", "Docker", "Cloud platforms", "Communication"],
        )

    def test_ignores_introductory_and_key_responsibility_content(self) -> None:
        role_profile = """
About the Job
Build products used by customers
Location
Remote
Salary
Competitive
Company Description
An international company
Key Responsibilities
Lead delivery meetings
Key Skills
Stakeholder communication
"""

        profile = extract_requirement_profile("Any Role", role_profile)

        self.assertEqual([skill.name for skill in profile.skills], ["Stakeholder communication"])

    def test_extracts_requirements_from_realistic_pasted_job_description(self) -> None:
        role_profile = """
About the Job
Join a growing team working on customer-facing services.

Key Responsibilities
Collaborate with cross-functional teams
Deliver reliable services

Qualifications
Clear written and verbal communication
Experience coordinating complex projects
- Ability to prioritize competing work

What You Will Do
Support weekly planning
"""

        profile = extract_requirement_profile("Project Coordinator", role_profile)

        self.assertEqual(
            [skill.name for skill in profile.skills],
            [
                "Clear written and verbal communication",
                "Experience coordinating complex projects",
                "Ability to prioritize competing work",
            ],
        )
