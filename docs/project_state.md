# AI Career Coach — Project State

> This document is the primary source of truth for the current state of the AI Career Coach project.
> All development conversations should begin by reviewing this file.

Last Updated: 2026-07-26

---

# Current Sprint

Sprint 17 — Application Layer & Delivery Architecture

Status:
Completed

---

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
Requirement Pipeline
↓
Requirement Assessment
↓
Prompt Builder
↓
LLM
↓
Structured JSON
↓
Pydantic Validation
↓
Application Service
↓
CLI / Future FastAPI
```

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
* ✅ Sprint 16 — Claim Safety and Analysis Reliability
* ✅ Sprint 17 — Application Layer & Delivery Architecture


---

# Sprint 15 Deliverables

## Requirement Decomposition

* ✅ Deterministic atomic requirement decomposition
* ✅ Compound requirement splitting
* ✅ Comma-separated requirement decomposition
* ✅ Semicolon-separated requirement decomposition
* ✅ Safe conjunction decomposition
* ✅ Spaced slash-separated requirement decomposition
* ✅ Generic wrapper removal
* ✅ Requirement priority preservation
* ✅ Requirement Profile metadata preservation
* ✅ Duplicate atomic requirement removal
* ✅ Input profile immutability
* ✅ Protected phrase preservation
* ✅ Protected phrase preservation inside larger requirement lists
* ✅ Ambiguous verb-phrase protection
* ✅ Requirement Decomposer pipeline integration
* ✅ Dependency-injected decomposer support

## Structured Candidate Evidence

* ✅ Generic `CandidateEvidence` model
* ✅ Validated evidence source types
* ✅ Work-experience evidence collection
* ✅ Project evidence collection
* ✅ Education evidence collection
* ✅ Certification evidence collection
* ✅ Skills-section evidence collection
* ✅ Candidate-summary evidence support
* ✅ Other candidate-section evidence support
* ✅ Deterministic evidence ordering
* ✅ Exact duplicate evidence removal
* ✅ Distinct same-skill evidence preservation
* ✅ Candidate Profile immutability
* ✅ Source-label encoding cleanup

## Evidence Quality Scoring

* ✅ Validated `ScoredCandidateEvidence` model
* ✅ Deterministic evidence quality scoring
* ✅ Generic evidence source weighting
* ✅ Action-signal detection
* ✅ Practical activity evidence weighting
* ✅ Conservative skills-declaration scoring
* ✅ Explainable quality factors
* ✅ Score boundary validation
* ✅ Deterministic batch scoring
* ✅ Input order preservation
* ✅ Evidence immutability

## Evidence Ranking

* ✅ Deterministic evidence ranking
* ✅ Quality-score descending ordering
* ✅ Stable equal-score ordering
* ✅ Case-insensitive skill grouping
* ✅ First-seen group-order preservation
* ✅ Ranking within evidence groups
* ✅ Bounded top-evidence selection
* ✅ Invalid selection-limit rejection
* ✅ Distinct evidence preservation
* ✅ Input collection immutability

## Semantic Integration

* ✅ Structured evidence integration into Skill Matcher
* ✅ Evidence scoring before final selection
* ✅ Evidence ranking before final selection
* ✅ Relevant-evidence filtering
* ✅ Strongest-evidence-first output
* ✅ Configurable evidence limit
* ✅ Dependency-injected evidence scorer
* ✅ Dependency-injected evidence ranker
* ✅ Final-boundary legacy evidence conversion
* ✅ Existing exact matching preservation
* ✅ Existing alias matching preservation
* ✅ Existing practical-experience matching preservation
* ✅ Existing action-evidence rules preservation
* ✅ Requirement-order preservation
* ✅ Deterministic repeated matching

## Evidence-Aware Requirement Assessment

* ✅ Evidence-strength classification
* ✅ Strong evidence classification
* ✅ Moderate evidence classification
* ✅ Weak evidence classification
* ✅ Missing-evidence classification
* ✅ Strongest selected evidence determines strength
* ✅ Duplicate evidence does not inflate strength
* ✅ Existing demonstrated and missing statuses preserved
* ✅ Existing coverage calculations preserved
* ✅ Required coverage preservation
* ✅ Preferred coverage preservation
* ✅ Optional coverage preservation
* ✅ Missing requirement grouping preservation
* ✅ Assessment input immutability
* ✅ Prompt Builder compatibility
* ✅ Analyzer and CLI compatibility

## Generic Validation Improvements

* ✅ Requirement section-heading leakage prevention
* ✅ `Preferred` heading filtering
* ✅ `Requirements` heading filtering
* ✅ `Responsibilities` heading filtering
* ✅ Written and verbal communication preservation
* ✅ Malformed adjective-fragment prevention
* ✅ Existing `Problem solving` skill matching correction
* ✅ Clean recommendation requirement inputs
* ✅ Clean learning-roadmap requirement inputs
* ✅ Non-technical role validation

---

# Sprint 15 Validation Result

Verified with:

* Compound requirement sentences
* Atomic requirement decomposition
* Protected phrases
* Ambiguous verb conjunctions
* Structured evidence from candidate-profile sections
* Evidence source typing
* Evidence quality scoring
* Evidence quality explanations
* Stable evidence ranking
* Grouped evidence ranking
* Top-evidence selection
* Structured evidence integration into semantic matching
* Exact skill matching
* Alias-based skill matching
* Practical-experience matching
* Action-evidence matching
* Evidence-aware requirement assessment
* Strong, moderate, weak, and missing evidence classifications
* Existing deterministic coverage calculations
* Generic section-heading filtering
* AI Engineer job descriptions
* Office Administrator job descriptions
* Profession-agnostic CLI analysis
* Structured LLM response generation
* Output normalization
* Pydantic validation
* Validation repair
* Deterministic consistency processing
* CLI presentation

Latest confirmed automated test result:

```text
195 passed in 1.00s
```

Real-world validation confirmed that the same analysis pipeline can process both technical and non-technical target roles without relying on a static role catalog.

---

# Sprint 16 Deliverables

## Allowed Claims Model

* ✅ Generic `AllowedClaim` model
* ✅ Generic `AllowedClaims` collection
* ✅ Structured claim categorization
* ✅ Claim source preservation
* ✅ Claim confidence support
* ✅ Generic claim metadata
* ✅ Pydantic validation
* ✅ Input immutability
* ✅ Prompt Builder compatibility
* ✅ Analyzer compatibility

## Allowed Claims Builder

* ✅ Deterministic allowed-claim construction
* ✅ Candidate Profile integration
* ✅ Requirement Assessment integration
* ✅ Ranked Candidate Evidence integration
* ✅ Demonstrated requirement filtering
* ✅ Evidence-backed claim generation
* ✅ Unsupported requirement exclusion
* ✅ Duplicate claim removal
* ✅ Stable deterministic ordering
* ✅ Dependency injection support
* ✅ Builder output validation
* ✅ Existing pipeline compatibility

## Prompt Context Improvements

* ✅ Allowed Claims integration into Prompt Builder
* ✅ Explicit claim-boundary context
* ✅ Deterministic requirement-status context
* ✅ Evidence-strength exposure
* ✅ Structured claim serialization
* ✅ Prompt size optimization
* ✅ Existing prompt compatibility
* ✅ Provider-independent prompt structure

## Unsupported Claims Validation

* ✅ Generic Unsupported Claims Validator
* ✅ Claim-to-evidence verification
* ✅ Unsupported strength detection
* ✅ Unsupported recommendation detection
* ✅ Unsupported summary detection
* ✅ Unsupported experience detection
* ✅ Requirement-status verification
* ✅ Safe validation failure handling
* ✅ Analyzer integration
* ✅ Existing validation compatibility

## CareerAnalysis Reliability

* ✅ Explicit CareerAnalysis schema contract
* ✅ Integer score enforcement
* ✅ Structured object enforcement
* ✅ Nested collection validation
* ✅ Required collection validation
* ✅ Learning roadmap minimum-size enforcement
* ✅ Improved validation repair instructions
* ✅ Complete JSON regeneration during repair
* ✅ Single repair-attempt preservation

## Deterministic Requirement Authority

* ✅ Requirement Assessment designated as authoritative
* ✅ Demonstrated requirements protected from reinterpretation
* ✅ Missing requirements protected from reinterpretation
* ✅ Requirement priority preservation
* ✅ Deterministic assessment exposed to the LLM
* ✅ Prompt-level authority rules
* ✅ Repair-prompt authority rules

## Evidence Preservation

* ✅ Exact evidence preservation
* ✅ Near-verbatim evidence support
* ✅ Unsupported evidence rejection
* ✅ Prevention of fabricated experience
* ✅ Prevention of fabricated projects
* ✅ Prevention of fabricated employers
* ✅ Prevention of fabricated responsibilities
* ✅ Prevention of fabricated seniority
* ✅ Prevention of fabricated production experience

## Prompt Repair Improvements

* ✅ Full schema supplied during repair
* ✅ Validation errors included
* ✅ Allowed Claims included
* ✅ Requirement Assessment included
* ✅ Requirement-authority rules included
* ✅ Evidence-preservation rules included
* ✅ Complete response regeneration
* ✅ Patch-style responses prohibited

## End-to-End Integration

* ✅ Analyzer integration
* ✅ Prompt Builder integration
* ✅ Validation pipeline compatibility
* ✅ Output Normalizer compatibility
* ✅ Unsupported Claims Validator compatibility
* ✅ Deterministic Consistency Processor compatibility
* ✅ CLI compatibility
* ✅ Provider-independent architecture preservation

## Analyzer Integration

* ✅ Allowed Claims Builder orchestration
* ✅ Unsupported Claims Validator orchestration
* ✅ Existing analyzer flow preservation
* ✅ Single repair-attempt preservation
* ✅ End-to-end deterministic pipeline compatibility

## Real-World Validation

* ✅ Real AI Engineer job description validation
* ✅ Real project CV validation
* ✅ End-to-end CLI execution
* ✅ Schema-valid CareerAnalysis generation
* ✅ Validation repair verification
* ✅ Unsupported Claims validation verification

# Sprint 16 Validation Result

Verified with:

* Allowed Claims generation
* Allowed Claims Builder
* Evidence-backed claim construction
* Prompt Builder integration
* CareerAnalysis schema enforcement
* Integer score validation
* Structured strengths validation
* Structured recommendations validation
* Structured career-gap validation
* Learning-roadmap minimum-length validation
* Validation repair prompt improvements
* Complete JSON regeneration during repair
* Unsupported Claims validation
* Requirement Assessment authority
* Evidence-preservation rules
* Prompt-level deterministic guidance
* Analyzer integration
* Output normalization
* Pydantic validation
* Validation repair
* Deterministic consistency processing
* Real AI Engineer job description
* Real project CV
* Profession-agnostic CLI analysis
* Real Office Administrator job description

Latest confirmed automated test result:

```text
235 passed in 1.13s
```

Real-world validation confirmed that the complete analysis pipeline successfully processes real candidate CVs and real job descriptions while preserving deterministic requirement assessment, structured evidence, claim safety, and schema reliability.

The analyzer now successfully completes:

* Candidate Profile extraction
* Requirement extraction
* Evidence collection
* Evidence scoring
* Evidence ranking
* Semantic matching
* Requirement assessment
* Allowed Claims generation
* Prompt generation
* Structured JSON generation
* Output normalization
* Pydantic validation
* Validation repair
* Unsupported Claims validation
* Deterministic consistency processing
* CLI presentation

---

# Current Work

Sprint 16 implementation and real-world validation are complete.

Remaining closure tasks:

* Review all Sprint 16 changed files
* Update architecture documentation
* Update architectural decisions
* Update project state documentation
* Run the final complete test suite
* Stage Sprint 16 project files
* Commit Sprint 16 changes
* Push Sprint 16 to origin


---

# Next Sprint

Sprint 17 — Application Service and REST API

Proposed scope:

* Application Service layer
* Separation of application orchestration from CLI
* Analysis request model
* Analysis response model
* FastAPI integration
* REST API endpoints
* CV upload endpoint
* Requirement-text endpoint
* TXT requirement endpoint
* API validation
* API error handling
* OpenAPI / Swagger support
* Frontend-ready backend architecture
* Preservation of local Ollama support
* Provider-independent application boundary

---

# Known Issues

* Requirement extraction may classify benefit sections as requirements.
* Composite degree requirements may be decomposed too aggressively.
* Partial semantic skill matching remains conservative for related competencies.
* Semantic alias coverage is still limited.
* Related but non-equivalent technologies may require additional aliases.
* Evidence-source weighting may require future calibration.
* Candidate Profile summary extraction is not implemented.
* Experience parsing supports a limited number of CV layouts.
* Education parsing supports a limited number of formats.
* Language extraction may include proficiency-label fragments.
* Recommendation quality depends on validated requirement extraction.
* Some roadmap recommendations remain generic.
* Detected CV section previews are truncated in CLI output.
* Application logic is still invoked through the CLI rather than a reusable Application Service.
* REST API is not yet implemented.
* Frontend is not yet implemented.
* Requirement assessment may conservatively classify demonstrated skills as missing when semantic equivalence is not yet recognized.

---
# Active ADRs

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

Superseded:

* ADR-004 — Role Profiles

  Superseded by ADR-011. Static role profiles are no longer the primary requirement source.

---

# Long-Term Vision

AI Career Coach is intended to become a profession-agnostic career assessment platform.

The system should:

* Analyze any profession, not only technology-related roles.
* Accept different requirement sources such as job descriptions, competency frameworks, role databases, and external integrations.
* Perform deterministic extraction before AI reasoning.
* Decompose complex requirements into testable atomic concepts.
* Keep business logic outside prompts.
* Minimize LLM responsibility through deterministic pipelines.
* Use semantic matching instead of simple keyword matching.
* Collect structured candidate evidence.
* Score candidate evidence deterministically.
* Rank evidence before matching and assessment.
* Distinguish demonstrated evidence from skills-section declarations.
* Expose evidence strength in requirement assessment.
* Produce explainable conclusions supported by candidate evidence.
* Prevent unsupported candidate claims.
* Restrict generated conclusions to deterministic evidence.
* Preserve deterministic requirement assessment authority.
* Provide a reusable Application Service.
* Expose analysis through a validated REST API.
* Support a modern frontend.
* Preserve local and open-source model support.
* Remain provider-agnostic.
* Remain modular and easily extensible.
* Improve deterministic semantic equivalence across related technologies and educational backgrounds.

---

# Design Principles

* No profession-specific business logic
* No CV-specific business logic
* No company-specific rules
* No university-specific rules
* No static role catalog dependency

* Generic extraction first
* Deterministic processing before AI reasoning

* Requirement decomposition before normalization
* Requirement validation before assessment

* Semantic normalization before matching

* Evidence collection remains independent from requirements
* Evidence scoring remains independent from target roles
* Evidence ranking remains independent from semantic matching
* Evidence relevance is established before final evidence selection

* Prompt Builder only assembles context
* Analyzer only orchestrates components
* Prompts do not own business logic

* LLM generates explanations and presentation
* Deterministic components establish facts

* Requirement Assessment owns coverage calculations
* Requirement Assessment is the authoritative source for requirement status
* Requirement Assessment exposes evidence strength
* Demonstrated requirements must never be reinterpreted as missing
* Missing requirements must never be reinterpreted as demonstrated

* Allowed Claims define the maximum claim boundary
* Every generated claim must be supported by deterministic evidence
* Unsupported candidate claims must not be introduced
* Unsupported claims must be rejected before final output

* Evidence attached to matches must be relevant
* Stronger relevant evidence must be preferred over weaker evidence
* Evidence volume must not inflate evidence strength
* Evidence must remain traceable to deterministic sources

* Output normalization repairs structure, not analysis
* Validation repair preserves the complete response contract
* Pydantic models define response contracts

* Prompt engineering supports deterministic business logic but never replaces it

* Application interfaces must not depend on a specific AI provider

* Every architectural change should reduce LLM responsibility
* Business logic owns factual decisions.
* The LLM explains deterministic decisions but does not redefine them.

---

# Current Project Status

Completed:

- Generic candidate profile extraction
- Generic requirement processing pipeline
- Requirement assessment engine
- Evidence collection
- Application layer
- Composition root
- Thin CLI adapter
- End-to-end deterministic analysis pipeline

Known Issues:

- Requirement filtering still includes non-requirement sections (Benefits, salary, etc.).
- Degree alternatives are decomposed too aggressively.
- Semantic matching for equivalent skills requires improvement.
- Language equivalence matching is limited.
- Composite requirement parsing (AND/OR) needs refinement.
