# AI Career Coach — Project State

> This document is the primary source of truth for the current state of the AI Career Coach project.
> All development conversations should begin by reviewing this file.

Last Updated: 2026-07-13

---

# Current Sprint

Sprint 13 — Analysis Quality and Semantic Gap Validation

Status:
Completed

---

# Current Architecture

PDF
↓
Text Cleaner
↓
CV Parser
↓
Candidate Profile Extractor
↓
Candidate Profile Normalizer
↓
Requirement Profile Extractor
↓
Evidence Collector
↓
Skill Matcher
↓
Skill Validator
↓
Prompt Builder
↓
LLM
↓
Structured JSON
↓
Output Normalizer
↓
Pydantic Validation
↓
Deterministic Consistency Processing
↓
CLI Output

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

---

# Sprint 13 Deliverables

* ✅ Generic RequirementProfile extraction
* ✅ CandidateEvidenceCollector
* ✅ Configurable SkillAliasRegistry
* ✅ Default skill alias provider
* ✅ Deterministic SkillMatcher
* ✅ SkillValidator
* ✅ Action-based practical experience matching
* ✅ Deterministic missing skill grouping
* ✅ Evidence-based strength validation
* ✅ Demonstrated skill removal from missing skills
* ✅ Profession-agnostic analysis prompt
* ✅ Provider-agnostic prompt structure
* ✅ Structured JSON schema guidance
* ✅ CareerAnalysis output normalization
* ✅ CareerAnalysis validation repair flow
* ✅ Deterministic consistency processing
* ✅ Recommendation prioritization
* ✅ Four-week learning roadmap enforcement
* ✅ Duplicate roadmap focus prevention
* ✅ Candidate Profile CLI presentation
* ✅ 68 automated tests passing

---

# Sprint 13 Validation Result

Verified with:

* Candidate profile extraction
* Requirement extraction
* Evidence collection
* Exact and alias-based skill matching
* Missing skill classification
* Structured LLM response generation
* Output normalization
* Pydantic validation
* Validation repair
* Deterministic consistency processing
* CLI presentation

Latest test result:

```text
68 passed in 0.70s
```

---

# Current Work

Sprint 13 implementation is complete.

Remaining closure tasks:

* Update architectural decisions
* Commit Sprint 13 changes
* Push local commits to origin
* Define Sprint 14 scope

---

# Next Tasks

Potential Sprint 14 tasks:

* Introduce partial skill matching
* Improve semantic alias coverage
* Improve evidence quality scoring
* Improve professional summary quality
* Improve recommendation wording
* Improve learning roadmap action quality
* Improve language extraction
* Improve parser robustness for additional CV layouts
* Add multi-role tests
* Add multi-CV tests
* Replace static role profiles with generic requirement sources

---

# Active ADRs

* ADR-001 — Layered Architecture
* ADR-002 — Structured AI Responses
* ADR-003 — AI as a Component
* ADR-004 — Role Profiles
* ADR-005 — Structured CV Parsing
* ADR-006 — Generic Candidate Profile Extraction

---

# Known Issues

* Experience parsing supports a limited number of CV layouts.
* Education parsing supports a limited number of formats.
* Candidate Profile summary extraction is not implemented.
* Language extraction may include proficiency-label fragments.
* Semantic alias coverage is limited.
* Partial skill matching is not implemented.
* Detected CV section previews are truncated in CLI output.
* Recommendation wording can become generic after deterministic fallback.
* Learning roadmap fallback tasks can be generic.
* Static role profile files are not suitable as the final multi-role requirement source.

---

# Long-Term Vision

AI Career Coach is intended to become a profession-agnostic career analysis platform.

The system should:

* Analyze any profession, not only technology-related roles.
* Accept different requirement sources such as job descriptions, competency frameworks, and role databases.
* Perform deterministic extraction before AI reasoning.
* Keep business logic outside prompts.
* Minimize LLM responsibility through deterministic pipelines.
* Use semantic matching instead of simple keyword matching.
* Produce explainable conclusions supported by candidate evidence.
* Remain provider agnostic.
* Remain modular and easily extensible.

---

# Design Principles

* No profession-specific business logic
* No CV-specific business logic
* No company-specific rules
* No university-specific rules
* Generic extraction first
* Deterministic processing before AI reasoning
* Semantic normalization before matching
* Prompts do not own business logic
* Prompt Builder only assembles context
* Analyzer only orchestrates components
* LLM generates explanations and presentation
* Deterministic components establish facts
* Output normalization repairs structure, not analysis
* Pydantic models define the response contract
* Unsupported candidate claims must not be introduced
* Demonstrated skills must not be reported as missing
