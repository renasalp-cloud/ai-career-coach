# Architecture Decision Records (ADR)

This document records the most important architectural decisions made during the development of **AI Career Coach**.

The purpose of this document is to explain **why** a decision was made, not only **what** was implemented.

---

# ADR-001 — Layered Architecture

**Date:** 2026-07-06

**Status:** Accepted

## Context

The project started as a simple command-line application. As new features were added (PDF extraction, AI analysis, validation, parsing), keeping everything in a single flow became difficult.

## Decision

Adopt a layered architecture where each component has a single responsibility.

Current layers:

- PDF Reader
- Text Cleaner
- CV Parser
- Role Profiles
- AI Provider
- Presentation Layer

## Alternatives Considered

- Keep all logic inside `main.py`
- Place all AI-related logic inside `analyzer.py`

## Consequences

### Positive

- Easier maintenance
- Easier testing
- Better scalability
- Lower coupling

### Negative

- More files
- Slightly higher initial complexity

---

# ADR-002 — Structured AI Responses

**Date:** 2026-07-06

**Status:** Accepted

## Context

Free-text AI responses were difficult to validate and frequently changed format.

## Decision

Require every AI response to follow a predefined JSON schema.

Responses are validated before being shown to the user.

## Alternatives Considered

- Plain text responses
- Markdown responses

## Consequences

### Positive

- Predictable output
- Easier formatting
- Strong validation using Pydantic
- Better integration with future UI

### Negative

- Prompt engineering becomes more important

---

# ADR-003 — AI as a Component

**Date:** 2026-07-06

**Status:** Accepted

## Context

The first implementation relied almost entirely on the LLM.

This made the application difficult to control and extend.

## Decision

Treat the LLM as one component of the system.

Business logic must remain outside the AI provider.

The AI provider is responsible only for reasoning.

## Alternatives Considered

- LLM-centric architecture

## Consequences

### Positive

- Easier provider replacement
- Better separation of responsibilities
- More deterministic application behavior

### Negative

- More application logic must be implemented outside the LLM

---

# ADR-004 — Role Profiles

**Date:** 2026-07-06

> Superseded in Sprint 14 by the Generic Requirement Pipeline.
> Static role profiles are no longer the primary requirement source.

Status:
Superseded by ADR-011

## Context

The same candidate should be evaluated differently depending on the target role.

Different careers require different skills and evaluation criteria.

## Decision

Introduce role profiles describing expected skills for each supported role.

Examples:

- AI Engineer
- Backend Developer
- Marketing Specialist
- Data Analyst

## Alternatives Considered

- Let the LLM infer role requirements automatically

## Consequences

### Positive

- More consistent evaluations
- Reduced hallucinations
- Easier customization
- Better prompt quality

### Negative

- Role profiles require maintenance

---

# ADR-005 — Structured CV Parsing

**Date:** 2026-07-06

**Status:** Accepted

## Context

Passing the entire CV directly to the LLM reduced analysis quality and made prompts harder to control.

## Decision

Extract structured sections from the CV before AI analysis.

Current sections include:

- Education
- Experience
- Skills
- Languages

The parser will continue to evolve as support for more CV formats is added.

## Alternatives Considered

- Send raw PDF text directly to the LLM

## Consequences

### Positive

- Cleaner prompts
- Better AI reasoning
- Improved maintainability
- Easier future integrations

### Negative

- Parser maintenance is required

---

# ADR-006 — Generic Candidate Profile Extraction

**Date:** 2026-07-10

**Status:** Accepted

## Context

The first implementation of Candidate Profile Extraction gradually evolved into a CV-specific solution.

The extractor began recognizing particular companies, universities, degree names, and candidate details in order to improve the analysis of a single test CV.

Although this increased the quality of one example, it violated one of the project's main architectural goals: **the system must work for any candidate, not only for the current one.**

## Decision

Candidate Profile Extraction must remain completely generic.

The extraction layer is responsible only for extracting structured information from a parsed CV.

It must never contain knowledge about specific candidates, companies, universities, degrees, or projects.

Semantic normalization is considered a separate responsibility.

The architecture is therefore divided into two independent steps:

```text
Raw CV Sections
        │
        ▼
Candidate Profile Extractor
        │
        ▼
Candidate Profile Normalizer
        │
        ▼
Verified Candidate Profile
```

### Candidate Profile Extractor responsibilities

- Parse generic document structure
- Extract education
- Extract experience
- Extract skills
- Extract languages
- Extract certifications
- Extract projects
- Detect date ranges
- Preserve factual information only

### Candidate Profile Normalizer responsibilities

- Normalize equivalent skill names
- Map related technical concepts
- Remove duplicates
- Produce a consistent domain model
- Perform generic semantic enrichment

## The extraction layer MUST NOT

- Check for company names (e.g. Accenture)
- Check for university names
- Check for specific degree names
- Check for candidate names
- Insert hardcoded dates
- Contain logic written to make a single CV pass

### Acceptable generic normalization

```python
if skill == "Image Classification":
    normalized_skill = "Computer Vision"
```

### Unacceptable candidate-specific logic

```python
if "Accenture" in experience_text:
    add_bootcamp_experience()
```

## Alternatives Considered

- Keep all extraction logic inside the LLM
- Continue adding candidate-specific parsing rules
- Merge extraction and normalization into a single component

## Consequences

### Positive

- Supports different CV formats
- Generalizes to different candidates
- Easier unit testing
- Lower maintenance cost
- Clear separation of responsibilities
- Better long-term scalability

### Negative

- Generic parsing is more difficult
- Additional normalization rules will be required over time
- More components increase architectural complexity

---

# Future ADRs

Future architectural decisions will also be documented here.

Potential future ADRs include:

- Candidate Assessment Engine
- Job Description Parser
- ATS Compatibility Analysis
- Multi-LLM Support
- Report Generation Pipeline
- Web Application Architecture
- Retrieval-Augmented Generation (RAG)

# ADR-007 — Candidate Profile Pipeline

Date: 2026-07-10

Status:
Accepted

## Context

Previously the analyzer consumed parsed CV sections directly.

This tightly coupled prompt generation with the CV parser and made semantic normalization difficult.

## Decision

Introduce a Candidate Profile pipeline.

Pipeline:

PDF
→ Text Cleaner
→ CV Parser
→ Candidate Profile Extractor
→ Candidate Profile Normalizer
→ Prompt Builder
→ LLM

The Prompt Builder and Analyzer now consume CandidateProfile instead of raw CV sections.

## Consequences

Advantages

- Better separation of concerns
- Easier testing
- Reusable CandidateProfile
- Better semantic normalization
- Easier support for multiple CV formats

Trade-offs

- Additional extraction layer
- Slightly larger pipeline

# ADR-008 — Requirement-Based Semantic Matching

**Date:** 2026-07-13

**Status:** Accepted

## Context

Earlier versions relied primarily on AI reasoning to determine whether a candidate satisfied role requirements.

This made matching inconsistent and difficult to verify.

## Decision

Introduce a deterministic semantic matching pipeline before AI analysis.

Pipeline:

Requirement Profile
↓

Evidence Collector
↓

Skill Matcher
↓

Skill Validator
↓

Validated Skill Matches

The LLM receives validated skill matches instead of deciding skill presence itself.

## Alternatives Considered

- Let the LLM determine all matching
- Keyword-only matching

## Consequences

### Positive

- Deterministic skill validation
- Better explainability
- Reduced hallucinations
- Easier testing
- Better provider independence

### Negative

- Additional preprocessing layer
- Alias maintenance over time

# ADR-009 — Output Normalization Before Validation

**Date:** 2026-07-13

**Status:** Accepted

## Context

Small language models occasionally returned valid analysis with incorrect field names or slightly different structures.

Although the content was correct, schema validation failed.

## Decision

Introduce an Output Normalizer between JSON extraction and Pydantic validation.

Pipeline:

LLM
↓

JSON Extraction
↓

Output Normalizer
↓

Pydantic Validation

The normalizer repairs structural inconsistencies only.

It must never modify analytical conclusions.

## Alternatives Considered

- Larger prompts
- Multiple repair prompts
- Relaxing the schema

## Consequences

### Positive

- Higher validation success
- Better provider compatibility
- More robust pipeline

### Negative

- Additional maintenance

# ADR-010 — Deterministic Post-Processing

**Date:** 2026-07-13

**Status:** Accepted

## Context

Even after schema validation, LLM responses could contradict validated candidate facts.

Examples included reporting demonstrated skills as missing or generating inconsistent recommendations.

## Decision

Introduce deterministic post-processing after validation.

Responsibilities include:

- Remove demonstrated skills from missing skills
- Validate strengths
- Group missing skills
- Align recommendations
- Align learning roadmap
- Correct unsupported summaries

The post-processing layer improves consistency without regenerating the analysis.

## Alternatives Considered

- Move all logic into prompts
- Trust raw LLM output

## Consequences

### Positive

- Consistent results
- Lower hallucination rate
- Better separation of responsibilities
- Less prompt complexity

### Negative

- Additional processing layer

# ADR-011 — Generic Requirement Pipeline

**Date:** 2026-07-15

**Status:** Accepted

## Context

Earlier versions relied on static role profile files to define role expectations.

This approach required maintaining one role profile for every supported profession and did not scale to real-world job descriptions.

The project goal is to remain profession-agnostic and support arbitrary requirement sources.

## Decision

Introduce a generic Requirement Pipeline.

Pipeline:

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

Requirement Profile

Requirement sources are independent from the analyzer and may include:

- pasted job descriptions
- text files
- future external integrations

The analyzer consumes only a validated RequirementProfile.

It has no knowledge of how the requirements were obtained.

## Alternatives Considered

- Continue using static role profile files
- Let the LLM infer role requirements
- Load role definitions inside the analyzer

## Consequences

### Positive

- Profession-agnostic architecture
- Scalable to arbitrary job descriptions
- Cleaner analyzer responsibilities
- Easier testing
- Better separation of concerns

### Negative

- Requirement extraction becomes a dedicated subsystem
- Additional validation and normalization layers are required

# ADR-012 — Requirement Validation Pipeline

**Date:** 2026-07-15

**Status:** Accepted

## Context

Requirement extraction may produce incomplete or inconsistent RequirementProfile objects.

Allowing invalid requirement data to enter semantic matching would reduce reliability and complicate downstream processing.

## Decision

Introduce a deterministic Requirement Validator.

Responsibilities include:

- validate profile structure
- reject empty requirement sets
- reject duplicate requirements
- reject unsupported priorities
- reject invalid requirement names

The validator performs validation only.

It never repairs or modifies extracted data.

Normalization and validation remain separate responsibilities.

## Alternatives Considered

- Validate inside the analyzer
- Let semantic matching handle invalid profiles
- Automatically repair invalid requirements

## Consequences

### Positive

- Stronger data integrity
- Clear separation of responsibilities
- Easier unit testing
- Earlier failure detection

### Negative

- Additional validation component

# ADR-013 — Deterministic Requirement Assessment

**Date:** 2026-07-15

**Status:** Accepted

## Context

Coverage calculations, missing-skill grouping, and requirement statistics were previously left to the language model.

This reduced consistency and made results provider-dependent.

## Decision

Introduce a deterministic Requirement Assessment Engine.

Pipeline:

Validated Skill Matches
↓

Requirement Assessment

The assessment engine is responsible for:

- overall coverage
- required coverage
- preferred coverage
- optional coverage
- demonstrated skills
- critical missing skills
- preferred missing skills
- optional missing skills

The Prompt Builder receives a RequirementAssessment instead of requiring the LLM to calculate these values.

The LLM explains deterministic assessment results rather than producing them.

## Alternatives Considered

- Let the LLM calculate coverage
- Calculate coverage inside prompts
- Combine assessment with semantic matching

## Consequences

### Positive

- Deterministic coverage calculations
- Reduced hallucinations
- Simpler prompts
- Better explainability
- Greater provider independence

### Negative

- Additional assessment layer

# ADR-014 — Atomic Requirement Decomposition

**Date:** 2026-07-16

**Status:** Accepted

## Context

Requirement extraction originally preserved complete requirement sentences.

Many real-world job descriptions contain compound requirements such as:

* Python, Docker, and cloud deployment
* Planning and stakeholder communication

Treating these as single requirements reduced semantic matching quality and produced inconsistent missing-skill reporting.

## Decision

Introduce a deterministic Requirement Decomposer between extraction and normalization.

Pipeline:

Requirement Extractor

↓

Requirement Decomposer

↓

Requirement Normalizer

The decomposer is responsible for safely converting compound requirements into atomic concepts while preserving semantic meaning.

Protected phrases and ambiguous verb structures remain intact.

## Alternatives Considered

* Leave decomposition to the LLM
* Split every conjunction blindly
* Perform decomposition during semantic matching

## Consequences

### Positive

* Better requirement granularity
* Improved semantic matching
* Cleaner missing-skill reporting
* Reduced prompt complexity
* Deterministic behavior

### Negative

* Additional preprocessing component
* Continuous refinement of decomposition heuristics

---

# ADR-015 — Structured Candidate Evidence

**Date:** 2026-07-16

**Status:** Accepted

## Context

Earlier versions represented candidate evidence as lightweight text snippets attached directly to skill matches.

This lost information about evidence origin and prevented later deterministic reasoning.

## Decision

Introduce a structured Candidate Evidence model.

Evidence is collected before semantic matching and preserves:

* source type
* originating section
* supporting text
* related skill

The evidence pipeline is independent of matching and assessment.

## Alternatives Considered

* Continue using simple text evidence
* Collect evidence inside the matcher
* Let the LLM infer supporting evidence

## Consequences

### Positive

* Better explainability
* Stronger separation of responsibilities
* Reusable evidence model
* Easier testing
* Foundation for evidence scoring

### Negative

* Additional domain model
* More preprocessing stages

---

# ADR-016 — Deterministic Evidence Quality Scoring

**Date:** 2026-07-16

**Status:** Accepted

## Context

Not every piece of candidate evidence provides the same level of confidence.

Work experience generally provides stronger evidence than a simple skills declaration.

## Decision

Introduce a deterministic Evidence Quality Scorer.

The scorer assigns quality scores using generic, provider-independent rules.

Scoring occurs before semantic matching.

The scorer evaluates evidence quality only.

It never determines whether a requirement is demonstrated.

## Alternatives Considered

* Let the LLM judge evidence quality
* Treat every evidence source equally

## Consequences

### Positive

* Explainable evidence quality
* Deterministic scoring
* Better downstream evidence selection
* Reduced prompt responsibility

### Negative

* Generic weighting rules require future calibration

---

# ADR-017 — Deterministic Evidence Ranking

**Date:** 2026-07-16

**Status:** Accepted

## Context

Semantic matching may collect multiple relevant evidence entries for the same requirement.

Their presentation order should not depend on collection order alone.

## Decision

Introduce an Evidence Ranker after quality scoring.

Evidence is ranked by deterministic quality score while preserving stable ordering for equal scores.

Only the strongest relevant evidence is attached to validated matches.

## Alternatives Considered

* Preserve collection order
* Allow the LLM to choose evidence
* Attach every collected evidence item

## Consequences

### Positive

* Better explainability
* Stronger deterministic behavior
* Cleaner prompts
* Reduced LLM responsibility

### Negative

* Additional processing layer

---

# ADR-018 — Evidence-Aware Requirement Assessment

**Date:** 2026-07-16

**Status:** Accepted

## Context

Requirement Assessment previously distinguished only demonstrated and missing requirements.

It did not indicate how strongly a demonstrated requirement was supported.

## Decision

Extend Requirement Assessment with deterministic evidence-strength classification.

Assessment now categorizes demonstrated requirements using:

* strong
* moderate
* weak
* none

Evidence strength is derived from previously scored and ranked evidence.

Coverage calculations remain unchanged.

## Alternatives Considered

* Let the LLM infer evidence strength
* Recompute evidence quality inside assessment
* Ignore evidence quality completely

## Consequences

### Positive

* More explainable assessments
* Better foundation for future claim validation
* Reduced prompt responsibility
* Preserved deterministic coverage calculations

### Negative

* Assessment now depends on evidence-quality metadata

---

# Future ADRs

Future architectural decisions may include:

* Allowed Claims Builder
* Application Service Layer
* REST API
* Frontend Architecture
* Multi-LLM Support
* Retrieval-Augmented Generation (RAG)
* Report Generation Pipeline
