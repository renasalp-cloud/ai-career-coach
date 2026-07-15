# AI Career Coach Architecture

## Vision

AI Career Coach is a profession-agnostic career assessment platform.

The system evaluates how well a candidate matches a target role using deterministic processing before AI reasoning.

The LLM is a presentation and explanation component—not the decision maker.

---

# System Goal

Given:

- A candidate CV
- A target role
- A requirement source (job description or requirement document)

The system produces:

- Overall match score
- Professional summary
- Strengths
- Missing skills
- Career gap analysis
- Recommendations
- Learning roadmap

---

# High-Level Architecture

```text
                 Candidate CV                     Requirement Source
                      │                                   │
                      ▼                                   ▼
                 PDF Reader                    Requirement Source
                      │                                   │
                      ▼                                   ▼
                Text Cleaner                  Requirement Loader
                      │                                   │
                      ▼                                   ▼
                  CV Parser               Requirement Extractor
                      │                                   │
                      ▼                                   ▼
        Candidate Profile Extractor     Requirement Normalizer
                      │                                   │
                      ▼                                   ▼
     Candidate Profile Normalizer    Requirement Validator
                      │                                   │
                      └──────────────┬────────────────────┘
                                     ▼
                           Evidence Collector
                                     │
                                     ▼
                              Skill Matcher
                                     │
                                     ▼
                              Skill Validator
                                     │
                                     ▼
                    Requirement Assessment Engine
                                     │
                                     ▼
                              Prompt Builder
                                     │
                                     ▼
                                   LLM
                                     │
                                     ▼
                          Output Normalizer
                                     │
                                     ▼
                          Pydantic Validation
                                     │
                                     ▼
                  Deterministic Consistency Processor
                                     │
                                     ▼
                              CLI / Web / API
```

---

# Core Components

## Candidate Pipeline

Responsible for converting an unstructured CV into a normalized CandidateProfile.

Components:

- PDF Reader
- Text Cleaner
- CV Parser
- Candidate Profile Extractor
- Candidate Profile Normalizer

Output:

CandidateProfile

---

## Requirement Pipeline

Responsible for converting requirement text into a validated RequirementProfile.

Components:

- Requirement Source
- Requirement Loader
- Requirement Extractor
- Requirement Normalizer
- Requirement Validator

Output:

RequirementProfile

The pipeline is source-agnostic.

Requirement sources may include:

- pasted job descriptions
- text files
- future external integrations

---

## Evidence Collector

Collects supporting evidence for candidate skills from the CandidateProfile.

Evidence is later used during semantic matching and explanation generation.

---

## Skill Matcher

Matches candidate skills against requirement skills.

Responsibilities:

- exact matching
- alias matching
- deterministic matching

Business rules remain deterministic.

---

## Skill Validator

Validates every match.

Produces deterministic demonstrated/missing status.

---

## Requirement Assessment Engine

Produces deterministic assessment results.

Responsibilities include:

- requirement coverage
- required coverage
- preferred coverage
- optional coverage
- demonstrated skills
- missing requirement groups

No coverage calculations are performed by the LLM.

---

## Prompt Builder

Formats structured deterministic context for the language model.

Responsibilities:

- serialize structured objects
- assemble prompt context

It does not perform business logic.

---

## AI Provider

Responsible only for explanation and presentation.

Current provider:

- Ollama (Qwen2.5)

Future providers:

- OpenAI
- Claude
- Gemini
- Local models

Changing providers must not affect business logic.

---

## Output Pipeline

Responsible for validating AI output before presentation.

Components:

- Output Normalizer
- Pydantic Validation
- Validation Repair
- Deterministic Consistency Processor

Invalid AI output must never reach the user.

---

# Design Principles

## Deterministic Before AI

Business logic executes before AI reasoning.

The LLM explains deterministic conclusions.

---

## Single Responsibility

Each component owns exactly one responsibility.

---

## Structured Data First

Structured objects are preferred over raw text.

---

## Profession Agnostic

No profession-specific rules exist in deterministic components.

---

## Provider Agnostic

Changing LLM providers must not require business logic changes.

---

## Explainable Decisions

Every conclusion should be traceable to candidate evidence and requirement data.

---

## Validation First

Every AI response is normalized and validated before presentation.

---

# Current Implementation

Implemented:

- Candidate Pipeline
- Requirement Pipeline
- Evidence Collection
- Deterministic Skill Matching
- Skill Validation
- Requirement Assessment Engine
- Prompt Builder
- Output Normalization
- Pydantic Validation
- Validation Repair
- Deterministic Consistency Processing
- CLI Interface
- 135 Automated Tests

---

# Future Architecture

Planned improvements:

- Requirement Decomposition Engine
- Evidence Intelligence Pipeline
- Evidence Quality Scoring
- Experience Weighting
- Hallucination Guard
- ATS Optimization
- Resume Optimization
- Cover Letter Generation
- Interview Preparation
- REST API
- Web Application
- User Accounts
- Report History

---

# Guiding Principle

Every architectural change must reduce LLM responsibility and increase deterministic reasoning.

The LLM should explain decisions—not make them.