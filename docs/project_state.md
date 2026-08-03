# AI Career Coach — Project State

> This document is the primary source of truth for the current state of the AI Career Coach project.
> All development conversations should begin by reviewing this file.

Last Updated: 2026-08-03

---

# Current Sprint

Sprint 21 — FastAPI Delivery Layer

Status:

Completed

The backend is feature frozen and ready for frontend integration.

---

# Current Architecture

```text
Candidate CV
↓
PDF Reader
↓
Text Cleaner
↓
CV Parser
↓
Candidate Profile Extractor
↓
Candidate Profile Normalizer
↓
CandidateProfile

Requirement Source
↓
Requirement Loader
↓
Requirement Extractor
↓
Deterministic Requirement Filter
↓
Requirement Decomposer
↓
Requirement Normalizer
↓
Requirement Category Classifier
↓
Requirement Validator
↓
RequirementProfile

CandidateProfile + RequirementProfile
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
↓
Application Service
↓
CLI / FastAPI Delivery Layer
```

Composition Root:

```text
app/bootstrap.py
```

Application Layer:

```text
app/application/
```

Delivery adapters depend on the Application Service and do not own business orchestration.

---

# Completed Sprints

* ✅ Sprint 1 — Project Setup
* ✅ Sprint 2 — Git Workflow
* ✅ Sprint 3 — PDF Reader
* ✅ Sprint 4 — Text Cleaner
* ✅ Sprint 5 — CV Parser
* ✅ Sprint 6 — Ollama Integration
* ✅ Sprint 7 — Structured JSON Output
* ✅ Sprint 8 — Pydantic Validation
* ✅ Sprint 9 — Role Profiles
* ✅ Sprint 10 — Prompt Improvements
* ✅ Sprint 11 — Prompt Architecture
* ✅ Sprint 12 — Generic Candidate Profile Extraction
* ✅ Sprint 13 — Analysis Quality and Semantic Gap Validation
* ✅ Sprint 14 — Generic Requirement Processing Pipeline
* ✅ Sprint 15 — Evidence Intelligence and Requirement Decomposition
* ✅ Sprint 16 — Application Service and Application Layer
* ✅ Sprint 17 — Unsupported Claims and Analysis Authority
* ✅ Sprint 18 — Requirement Filtering and Logical Requirement Preservation
* ✅ Sprint 19 — Requirement Semantics and Deterministic Consistency
* ✅ Sprint 20 — Robust Candidate Extraction and Analysis Quality
* ✅ Sprint 21 — FastAPI Delivery Layer

Static role profiles are no longer production analysis authority.

---

# Sprint 19 Summary

Sprint 19 improved analysis quality while preserving profession-independent and provider-independent behavior.

Completed work:

* ✅ Deterministic requirement category preservation
* ✅ Conservative false-gap reduction
* ✅ Modifier-aware matching
* ✅ Explicit language matching
* ✅ Related-field education matching
* ✅ Shared-suffix requirement decomposition
* ✅ Deterministic requirement assessment
* ✅ Deterministic narrative consistency processing
* ✅ Demonstrated requirements excluded from gaps, recommendations, and roadmap items
* ✅ Missing requirements preserved by category and priority
* ✅ End-to-end validation across multiple CV and requirement formats

Latest confirmed automated test result:

```text
303 passed in 1.26s
```

---

# Analysis Authority

Production analysis authority is:

```text
Supplied Candidate CV
+
Supplied Job Description
```

The following are not analysis authority:

```text
Target-role title
Static role profiles
Prompt examples
Codex task examples
General profession assumptions
```

`target_role` provides presentation and contextual information only.

Requirements originate from the user-supplied requirement source and pass through the validated Requirement Pipeline.

RequirementAssessment is authoritative for demonstrated and missing requirements and for deterministic strengths, gaps, recommendations, and roadmap generation.

---

# LLM Responsibility

The LLM may:

* Understand supplied requirement language
* Explain deterministic assessment results
* Connect requirement data with candidate evidence
* Improve narrative clarity

The LLM must not:

* Generate requirements from the target-role title
* Override RequirementAssessment
* Convert demonstrated requirements into missing requirements
* Convert missing requirements into demonstrated requirements
* Invent candidate facts or evidence
* Treat every alternative requirement as independently mandatory
* Treat salary, benefits, culture, or application instructions as requirements
* Introduce unsupported claims

---

# Known Limitations

* Partial requirement satisfaction is not yet supported.
* Recommendation generation is deterministic but remains template-based.
* The learning roadmap is deterministic but not yet personalized beyond validated requirement gaps and priority.
* Semantic alias coverage remains limited.
* The FastAPI delivery layer currently exposes health and structured analysis endpoints; the frontend delivery layer is not implemented.

---

# Sprint 20 Summary

Sprint 20 strengthened the existing backend pipeline without changing its profession-agnostic or provider-independent boundaries.

Completed work:

* ✅ More robust candidate extraction across varied layouts
* ✅ Improved education, experience, and skill-section extraction
* ✅ Parser diagnostics and section-boundary cleanup
* ✅ Multi-column PDF text handling
* ✅ Improved deterministic evidence matching and education assessment
* ✅ Centralized output normalization and placeholder filtering
* ✅ Professional-summary fallback and deterministic strengths normalization
* ✅ Consistent public application flow through the Application Service
* ✅ Backend stabilization and frontend readiness verification

Latest confirmed automated test result:

```text
427 passed
```

The backend is feature-freeze ready. Frontend delivery can consume structured application results without parsing CLI output or owning business logic.

---

# Sprint 21 Summary

Completed work:

Completed work:

* FastAPI application factory
* Import-safe application construction
* Dependency Injection preserved
* Composition Root preserved
* `GET /health`
* Structured `POST /analyses`
* Multipart PDF upload
* Request-scoped temporary-file lifecycle management
* Application Service delegation
* Structured `AnalysisResponse`
* Thread-pool execution for synchronous analysis
* OpenAPI documentation (`/docs` and `/openapi.json`)
* Environment-driven API configuration
* Explicit CORS configuration
* Frontend-ready structured API contract

Task 3 progress:

* OpenAPI application metadata and endpoint tags
* Documented health and multipart analysis contracts
* Documented structured success and safe error responses
* Interactive API documentation and local server instructions


Task 4 progress:

* Environment-driven API metadata and CORS origin configuration
* Explicit local React development origin default
* Controlled CORS methods, headers, and credential policy
* Isolated application-factory settings injection
* Configuration parsing and CORS behavior verification

Task 5 progress:

* Browser-style multipart `FormData` contract verification
* Actual success-response CORS verification for allowed and disallowed origins
* Representative nested `AnalysisResponse` JSON serialization verification
* Predictable `400`, `422`, and `500` frontend error contract verification
* React API base URL and multipart request guidance
* No production contract defect found; production code remains unchanged


Final verified automated test result:

```text
447 passed
```

Sprint 21 is complete. The FastAPI adapter is frontend-ready, the backend business logic remains feature frozen, and Sprint 22 can consume the structured application response without reconstructing business decisions.

---

# Next Sprint

```text
Sprint 22 — React Frontend
```

---

# Active Architectural Decisions

* ADR-001 — Layered Architecture
* ADR-002 — Structured AI Responses
* ADR-003 — AI as a Component
* ADR-005 — Structured CV Parsing
* ADR-006 — Generic Candidate Profile Extraction
* ADR-007 — Candidate Profile Pipeline
* ADR-008 — Requirement-Based Semantic Matching
* ADR-009 — Output Normalization Before Validation
* ADR-010 — Deterministic Post-Processing
* ADR-011 — Generic Requirement Pipeline
* ADR-012 — Requirement Validation Pipeline
* ADR-013 — Deterministic Requirement Assessment
* ADR-014 — Atomic Requirement Decomposition
* ADR-015 — Structured Candidate Evidence
* ADR-016 — Deterministic Evidence Quality Scoring
* ADR-017 — Deterministic Evidence Ranking
* ADR-018 — Evidence-Aware Requirement Assessment
* ADR-019 — Allowed Claims
* ADR-020 — Unsupported Claims Validation
* ADR-021 — Deterministic Requirement Assessment Authority
* ADR-022 — Application Layer and Composition Root
* ADR-023 — Deterministic Requirement Filtering
* ADR-024 — Logical Requirement Preservation
* ADR-025 — Conservative Semantic Matching
* ADR-026 — Candidate Extraction as the Next Quality Priority
* ADR-027 — Backend Feature Freeze Before Frontend Delivery

Superseded:

* ADR-004 — Role Profiles

---

# Design Principles

* No profession-specific, candidate-specific, company-specific, or university-specific business logic
* No target-role-based requirement generation
* Deterministic processing before AI reasoning
* Structured data before free-text reasoning
* CandidateProfile is authoritative for candidate facts
* RequirementProfile is authoritative for supplied requirements
* RequirementAssessment is authoritative for requirement status and deterministic narrative sections
* AllowedClaims define the maximum generated claim boundary
* Prompt Builder assembles context only
* The LLM explains deterministic conclusions
* Output normalization repairs structure only
* Deterministic consistency processing aligns output fields
* Unsupported claims are rejected before presentation
* Application orchestration belongs to the Application Layer
* Dependency construction belongs to the Composition Root
* Provider independence and profession independence must be preserved
