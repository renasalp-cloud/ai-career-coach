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

# Future ADRs

Future architectural decisions will also be documented here.

Examples:

- Assessment Engine
- Candidate Profile domain model
- Job Description Parser
- ATS Analysis
- Multi-LLM support
- Web Architecture 