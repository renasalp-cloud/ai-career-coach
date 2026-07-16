# AI Career Coach — Project State

> This document is the primary source of truth for the current state of the AI Career Coach project.
> All development conversations should begin by reviewing this file.

Last Updated: 2026-07-16

---

# Current Sprint

Sprint 15 — Evidence Intelligence and Requirement Decomposition

Status:
Completed

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
Requirement Decomposer
↓
Requirement Normalizer
↓
Requirement Validator
↓
RequirementProfile

CandidateProfile
↓
Candidate Evidence Collector
↓
Structured Candidate Evidence
↓
Evidence Quality Scorer
↓
Scored Candidate Evidence
↓
Evidence Ranker
↓
Ranked Candidate Evidence

CandidateProfile
        +
RequirementProfile
        +
Ranked Candidate Evidence
↓
Skill Matcher
↓
Skill Validator
↓
Validated Skill Matches
↓
Evidence-Aware Requirement Assessment
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
Validation Repair
↓
Deterministic Consistency Processor
↓
CLI Output
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

# Current Work

Sprint 15 implementation and real-world validation are complete.

Remaining closure tasks:

* Review all Sprint 15 changed files
* Exclude local development automation files from the commit
* Update architecture documentation
* Update architectural decisions
* Run the final complete test suite
* Stage Sprint 15 project files
* Commit Sprint 15 changes
* Push Sprint 15 to origin

Local-only development automation and debug files must not be committed:

```text
AGENTS.md
run_codex.ps1
tasks/
debug/
```

---

# Next Sprint

Sprint 16 — Application Service and API Layer

Proposed scope:

* Unsupported candidate-claim prevention
* Deterministic allowed-claims construction
* Application service layer
* Separation of CLI presentation from application orchestration
* Reusable analysis request and response boundary
* FastAPI integration
* CV upload endpoint
* Pasted requirement-text endpoint support
* TXT requirement-source endpoint support
* API validation and error handling
* Frontend-ready backend architecture
* Preservation of local Ollama support
* Provider-independent application boundary

---

# Known Issues

* Professional summaries may still contain unsupported seniority, production, leadership, or research claims generated by the LLM.
* An explicit allowed-claims model has not yet been implemented.
* Partial semantic skill matching is not implemented.
* Semantic alias coverage is limited.
* Related but non-equivalent tools may not match without an explicit alias.
* Evidence `skill` values may use complete source text when a separate concept cannot be extracted deterministically.
* Some ambiguous compound requirements may intentionally remain undecomposed.
* Evidence-source weighting uses initial generic rules and may require future calibration.
* Evidence strength does not currently redefine demonstrated or missing status.
* Experience parsing supports a limited number of CV layouts.
* Education parsing supports a limited number of formats.
* Candidate Profile summary extraction is not implemented.
* Language extraction may include proficiency-label fragments.
* Recommendation fallback wording can be generic.
* Learning roadmap fallback tasks can be generic.
* Detected CV section previews are truncated in CLI output.
* Application logic is still invoked through the CLI rather than a reusable application service.
* A REST API is not yet implemented.
* A frontend is not yet implemented.

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
* Prevent unsupported seniority and experience claims.
* Provide a reusable application service.
* Expose analysis through a validated REST API.
* Support a modern frontend.
* Preserve local and open-source model support.
* Remain provider-agnostic.
* Remain modular and easily extensible.

---

# Design Principles

* No profession-specific business logic
* No CV-specific business logic
* No company-specific rules
* No university-specific rules
* No static role catalog dependency
* Generic extraction first
* Deterministic processing before AI reasoning
* Semantic normalization before matching
* Requirement decomposition before normalization
* Requirement validation before assessment
* Evidence collection remains independent from requirements
* Evidence scoring remains independent from target roles
* Evidence ranking remains independent from semantic matching
* Evidence relevance is established before final evidence selection
* Prompts do not own business logic
* Prompt Builder only assembles context
* Analyzer only orchestrates components
* LLM generates explanations and presentation
* Deterministic components establish facts
* Requirement Assessment owns coverage calculations
* Requirement Assessment exposes evidence strength
* Evidence volume must not inflate evidence strength
* Output normalization repairs structure, not analysis
* Pydantic models define response contracts
* Unsupported candidate claims must not be introduced
* Demonstrated skills must not be reported as missing
* Missing skills must be traceable to validated requirement data
* Evidence attached to matches must be relevant
* Stronger relevant evidence must be preferred over weaker evidence
* Application interfaces must not depend on a specific AI provider
* Every architectural change should reduce LLM responsibility
