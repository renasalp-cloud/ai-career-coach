# AI Career Coach Architecture

## Vision

AI Career Coach is a profession-agnostic career assessment platform.

The system evaluates how well a candidate matches supplied requirements using deterministic processing before AI reasoning.

The LLM is a presentation and explanation component—not the decision maker.

---

# System Goal

Given:

- A candidate CV
- A target role
- A requirement source such as a job description

The system produces a structured CareerAnalysis containing:

- Overall match score
- Professional summary
- Strengths
- Missing requirements grouped by priority
- Career gap analysis
- Recommendations
- Learning roadmap

---

# High-Level Architecture

```text
Candidate CV                              Requirement Source
     ↓                                            ↓
PDF Reader                              Requirement Loader
     ↓                                            ↓
Text Cleaner                           Requirement Extractor
     ↓                                            ↓
CV Parser                              Requirement Filter
     ↓                                            ↓
Candidate Profile Extractor            Requirement Decomposer
     ↓                                            ↓
Candidate Profile Normalizer           Requirement Normalizer
     ↓                                            ↓
CandidateProfile                       Category Classifier
     │                                            ↓
     │                                  Requirement Validator
     │                                            ↓
     └──────────────────────────┬────────RequirementProfile
                                ↓
                       Evidence Collector
                                ↓
                    Evidence Quality Scorer
                                ↓
                         Evidence Ranker
                                ↓
                          Skill Matcher
                                ↓
                         Skill Validator
                                ↓
                 Requirement Assessment Engine
                                ↓
                      Allowed Claims Builder
                                ↓
                          Prompt Builder
                                ↓
                           LLM Provider
                                ↓
                       Output Normalizer
                                ↓
                      Pydantic Validation
                                ↓
                       Validation Repair
                                ↓
              Deterministic Consistency Processor
                                ↓
                Unsupported Claims Validator
                                ↓
                         CareerAnalysis
```

Delivery flow:

```text
Planned React Frontend
        ↓ HTTP
FastAPI Delivery Adapter
        ↓
Application Service
        ↓
Existing deterministic pipeline

CLI Delivery Adapter
        ↓
Application Service
```

---

# Core Components

## Candidate Pipeline

Converts extracted CV text into a normalized CandidateProfile.

Components:

- PDF Reader
- Text Cleaner
- CV Parser
- Candidate Profile Extractor
- Candidate Profile Normalizer

CandidateProfile is authoritative for candidate facts.

---

## Requirement Pipeline

Converts user-supplied requirement text into a validated RequirementProfile.

Components:

- Requirement Source and Loader
- Requirement Extractor
- Deterministic Requirement Filter
- Requirement Decomposer
- Requirement Normalizer
- Requirement Category Classifier
- Requirement Validator

Filtering excludes non-requirement content. Decomposition preserves logical alternatives and reconstructs shared-suffix expressions. Category classification preserves semantic types such as skill, experience, education, certification, language, tool, domain knowledge, and soft skill.

The pipeline is source-agnostic and does not generate requirements from the target-role title.

---

## Evidence Pipeline

Collects structured candidate evidence, assigns deterministic quality scores, and ranks evidence before matching.

Evidence retains its source, supporting text, and related skill. Evidence scoring and ranking do not determine requirement status.

---

## Deterministic Matching

The Skill Matcher and Skill Validator compare CandidateProfile evidence with RequirementProfile entries.

Supported deterministic mechanisms include:

- Exact and alias matching
- Conservative modifier-aware matching
- Explicit language matching
- Related-field education matching
- Practical and action evidence matching

Matching does not use embeddings, LLM classification, profession-specific rules, or provider-specific implementations.

---

## Requirement Assessment Engine

Produces authoritative deterministic assessment results, including:

- Overall, required, preferred, and optional coverage
- Demonstrated requirements
- Missing requirements grouped by priority
- Requirement categories
- Evidence-strength classification

The assessment is the source of truth for strengths, career gaps, recommendations, and roadmap generation. Demonstrated requirements cannot become gaps or development actions.

---

## Allowed Claims

The Allowed Claims Builder derives the maximum supported claim boundary from CandidateProfile, ranked evidence, validated matches, and RequirementAssessment.

The Unsupported Claims Validator rejects final analysis claims outside that boundary.

---

## Prompt Builder and AI Provider

The Prompt Builder serializes structured deterministic context and assembles the prompt. It does not own business rules.

The AI provider explains the supplied facts and assessment. Provider changes must not affect business logic.

---

## Output Pipeline

Components:

- Output Normalizer
- Pydantic Validation
- Validation Repair
- Deterministic Consistency Processor
- Unsupported Claims Validator

The consistency processor aligns the score and narrative sections with deterministic requirement status. Invalid or unsupported output does not reach the delivery layer.

---

## Application Layer

The Application Service owns application orchestration. Dependency construction is centralized in `app/bootstrap.py`.

The CLI and FastAPI delivery adapters depend on the Application Service rather than owning business orchestration. FastAPI owns only HTTP validation, multipart upload adaptation, temporary-file lifecycle, error mapping, OpenAPI, and CORS.

---

# Design Principles

## Deterministic Before AI

Business logic executes before AI reasoning. The LLM explains deterministic conclusions.

## Structured Authority

CandidateProfile owns candidate facts, RequirementProfile owns supplied requirements, and RequirementAssessment owns requirement status and deterministic narrative conclusions.

## Profession Agnostic

Deterministic components contain no profession-specific rules.

## Provider Agnostic

Changing AI providers does not require business logic changes.

## Explainable Decisions

Conclusions are traceable to candidate evidence and supplied requirement data.

## Validation First

AI output is normalized, validated, made consistent, and checked for unsupported claims before presentation.

---

# Current Implementation

Implemented:

- Candidate Profile pipeline
- Generic Requirement pipeline
- Requirement filtering, decomposition, normalization, category preservation, and validation
- Structured evidence collection, scoring, and ranking
- Conservative deterministic semantic matching
- Requirement Assessment authority
- Allowed Claims and unsupported-claims validation
- Prompt construction and provider integration
- Structured output normalization, validation, repair, and consistency processing
- Application Service and composition root
- CLI interface
- FastAPI delivery adapter with health and structured analysis endpoints
- 447 automated tests

---

# Current Limitation

The React frontend is not yet implemented. The backend business behavior is feature frozen and exposes a stable structured API for Sprint 22.

---

# Guiding Principle

Every architectural change must reduce unsupported LLM authority and increase deterministic, explainable reasoning.
