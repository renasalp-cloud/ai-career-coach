"""Data models for AI career analysis responses."""

from typing import Literal

from pydantic import BaseModel, Field

from app.candidate_profile.models import CandidateProfile


class Strength(BaseModel):
    title: str = ""
    evidence: str = ""


class MissingSkill(BaseModel):
    skill: str = ""
    reason: str = ""


class MissingSkills(BaseModel):
    critical: list[MissingSkill] = Field(default_factory=list)
    important: list[MissingSkill] = Field(default_factory=list)
    optional: list[MissingSkill] = Field(default_factory=list)


class Recommendation(BaseModel):
    priority: str = ""
    title: str = ""
    reason: str = ""
    action: str = ""


class LearningWeek(BaseModel):
    week: int
    goal: str = ""
    topics: list[str] = Field(default_factory=list)
    practical_task: str = ""
    expected_outcome: str = ""


class SkillEvidence(BaseModel):
    source: str
    text: str


class SkillMatch(BaseModel):
    role_skill: str
    candidate_skill: str | None = None
    evidence: list[SkillEvidence] = Field(default_factory=list)
    status: Literal["demonstrated", "partial", "missing"] | None = None
    confidence: float | None = None


class RequirementSkill(BaseModel):
    name: str
    priority: Literal["required", "preferred", "optional"]


class RequirementProfile(BaseModel):
    title: str = ""
    skills: list[RequirementSkill] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
    source: str = ""


class CareerAnalysis(BaseModel):
    overall_match_score: int = 0
    professional_summary: str = ""
    strengths: list[Strength] = Field(default_factory=list)
    missing_skills: MissingSkills = Field(default_factory=MissingSkills)
    career_gap_analysis: str = ""
    recommendations: list[Recommendation] = Field(default_factory=list)
    learning_roadmap: list[LearningWeek] = Field(default_factory=list)
