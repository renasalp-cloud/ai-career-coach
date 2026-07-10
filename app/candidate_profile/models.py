"""Domain models for generic candidate profile extraction."""

from pydantic import BaseModel, Field


class EducationEntry(BaseModel):
    degree: str = ""
    institution: str = ""
    start_date: str = ""
    end_date: str = ""
    status: str = "unknown"


class ExperienceEntry(BaseModel):
    organization: str = ""
    title: str = ""
    start_date: str = ""
    end_date: str = ""
    location: str = ""
    highlights: list[str] = Field(default_factory=list)


class SkillEntry(BaseModel):
    name: str = ""
    source: str = ""


class CandidateProfile(BaseModel):
    summary: str = ""
    education: list[EducationEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    skills: list[SkillEntry] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)