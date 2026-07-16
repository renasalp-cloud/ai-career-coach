"""Data models for AI career analysis responses."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

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
    quality_score: int | None = Field(default=None, ge=0, le=100)


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
    overall_match_score: int
    professional_summary: str
    strengths: list[Strength]
    missing_skills: MissingSkills
    career_gap_analysis: str
    recommendations: list[Recommendation]
    learning_roadmap: list[LearningWeek]

    @model_validator(mode="after")
    def enforce_learning_roadmap_length(self):
        if len(self.learning_roadmap) < 4:
            raise ValueError("learning_roadmap must contain at least 4 entries.")

        if len(self.learning_roadmap) > 4:
            self.learning_roadmap = self.learning_roadmap[:4]

        return self
