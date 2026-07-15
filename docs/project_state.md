# AI Career Coach — Project State

> This document is the primary source of truth for the current state of the AI Career Coach project.
> All development conversations should begin by reviewing this file.

Last Updated: 2026-07-15

---

# Current Sprint

Sprint 14 — Generic Requirement Processing Pipeline

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
                         Requirement Normalizer
                         ↓
                         Requirement Validator
                         ↓
                         RequirementProfile
CandidateProfile
        +
RequirementProfile
↓
Candidate Evidence Collector
↓
Skill Matcher
↓
Skill Validator
↓
Validated Skill Matches
↓
Requirement Assessment Engine
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

---

# Sprint 14 Deliverables

* ✅ Generic `RequirementSource` model
* ✅ Pasted job-description source support
* ✅ TXT requirement source support
* ✅ Requirement Source Loader
* ✅ Generic Requirement Extractor
* ✅ Common job-description section heading support
* ✅ Bulleted requirement extraction
* ✅ Non-bulleted requirement extraction
* ✅ Responsibility section exclusion
* ✅ Requirement Profile Normalizer
* ✅ Duplicate requirement removal
* ✅ Requirement Profile Validator
* ✅ Empty requirement profile rejection
* ✅ Unsupported priority validation
* ✅ Requirement Pipeline orchestration
* ✅ Dependency-injected pipeline components
* ✅ Analyzer integration with `RequirementProfile`
* ✅ Static role-profile loading removed from Analyzer
* ✅ CLI requirement source selection
* ✅ Multiline pasted job-description input
* ✅ Deterministic Requirement Assessment Engine
* ✅ Overall coverage calculation
* ✅ Required, preferred, and optional coverage calculation
* ✅ Deterministic missing requirement grouping
* ✅ Requirement Assessment prompt context
* ✅ Requirement terminology cleanup in Prompt Builder
* ✅ Real-world job-description CLI validation
* ✅ 135 automated tests passing

---

# Sprint 14 Validation Result

Verified with:

* Pasted job descriptions
* TXT requirement sources
* Generic requirement source loading
* Common job-description headings
* Bulleted and non-bulleted requirement lines
* Requirement normalization
* Requirement validation
* Requirement pipeline orchestration
* Analyzer consumption of `RequirementProfile`
* Candidate evidence collection
* Exact and alias-based skill matching
* Skill validation
* Deterministic requirement assessment
* Structured LLM response generation
* Output normalization
* Pydantic validation
* Validation repair
* Deterministic consistency processing
* CLI presentation
* A real AI Engineer job description

Latest test result:

```text
135 passed in 0.88s
```

---

# Current Work

Sprint 14 implementation is complete.

Remaining closure tasks:

* Review staged Sprint 14 files
* Exclude local development automation files from the commit
* Update architecture documentation
* Update architectural decisions
* Run the final complete test suite
* Commit Sprint 14 changes
* Push Sprint 14 to origin

Local-only development automation files must not be committed:

```text
AGENTS.md
run_codex.ps1
tasks/
```

---

# Next Sprint

Sprint 15 — Evidence Intelligence and Requirement Decomposition

Proposed scope:

* Requirement decomposition into atomic skills
* Evidence quality scoring
* Evidence ranking
* Experience-source weighting
* Seniority-safe professional summaries
* Unsupported summary claim prevention
* Stronger evidence-based strength selection
* Improved recommendation action quality
* Improved learning roadmap task quality

---

# Known Issues

* Requirement extraction currently preserves complete requirement sentences instead of decomposing them into atomic skills.
* Compound requirement lines may contain multiple technologies or concepts in one requirement.
* Evidence quality is not scored.
* Skills listed in the CV and skills demonstrated through experience are not yet weighted differently.
* Professional summaries may contain unsupported seniority or research claims from the LLM.
* Strength selection may prioritize weakly relevant skills over stronger evidence.
* Overall coverage is deterministic but depends on the granularity of extracted requirements.
* Experience parsing supports a limited number of CV layouts.
* Education parsing supports a limited number of formats.
* Candidate Profile summary extraction is not implemented.
* Language extraction may include proficiency-label fragments.
* Semantic alias coverage is limited.
* Partial skill matching is not implemented.
* Recommendation fallback wording can be generic.
* Learning roadmap fallback tasks can be generic.
* Detected CV section previews are truncated in CLI output.

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
* Score and rank candidate evidence.
* Produce explainable conclusions supported by candidate evidence.
* Prevent unsupported seniority and experience claims.
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
* Requirement validation before assessment
* Prompts do not own business logic
* Prompt Builder only assembles context
* Analyzer only orchestrates components
* LLM generates explanations and presentation
* Deterministic components establish facts
* Requirement Assessment owns coverage calculations
* Output normalization repairs structure, not analysis
* Pydantic models define response contracts
* Unsupported candidate claims must not be introduced
* Demonstrated skills must not be reported as missing
* Missing skills must be traceable to validated requirement data
* Every architectural change should reduce LLM responsibility
