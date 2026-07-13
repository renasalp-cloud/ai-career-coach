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

**Status:** Accepted

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