# AI Career Coach — Project State

> This document is the primary source of truth for the current state of the AI Career Coach project.
> All development conversations should begin by reviewing this file.

Last Updated: 2026-07-10

---

# Current Sprint

Sprint 13 — Analysis Quality and Semantic Gap Validation

Status:
Not Started

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
Prompt Builder
↓
LLM
↓
Structured JSON
↓
Pydantic Validation

---

# Completed Sprints

- ✅ Sprint 1 — Project Setup
- ✅ Sprint 2 — Git Workflow
- ✅ Sprint 3 — PDF Reader
- ✅ Sprint 4 — Text Cleaner
- ✅ Sprint 5 — CV Parser
- ✅ Sprint 6 — Ollama Integration
- ✅ Sprint 7 — Structured JSON Output
- ✅ Sprint 8 — Pydantic Validation
- ✅ Sprint 9 — Role Profiles
- ✅ Sprint 10 — Prompt Improvements
- ✅ Sprint 11 — Prompt Architecture
- ✅ Sprint 12 — Generic Candidate Profile Extraction

---

# Current Work

Working on:

- Semantic skill matching
- Missing skill validation
- Analysis consistency
- Candidate Profile presentation in CLI

---

# Next Tasks

- Semantic skill graph
- Evidence-based gap analysis
- Candidate Profile CLI output
- Multi-CV testing
- Improve language extraction
- Improve parser robustness for additional CV layouts

---

# Active ADRs

- ADR-001 — Layered Architecture
- ADR-002 — Structured AI Responses
- ADR-003 — AI as a Component
- ADR-004 — Role Profiles
- ADR-005 — Structured CV Parsing
- ADR-006 — Generic Candidate Profile Extraction

---

# Known Issues

- Experience parser should support additional CV layouts.
- Education parser should support more education formats.
- Semantic skill normalization is still limited.
- LLM may underestimate demonstrated proficiency.
- Semantically equivalent skills may still be reported as missing.
- Candidate Profile is not yet displayed in the CLI.

---

# Design Principles

- No CV-specific logic
- No company-specific rules
- No university-specific rules
- Generic parsing first
- Semantic normalization second
- Prompt Builder never contains business logic
- Analyzer only orchestrates components
- Deterministic extraction before AI reasoning
- Normalize data before analysis