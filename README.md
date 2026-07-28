# AI Career Coach

A profession-agnostic career assessment application that compares a candidate CV with user-supplied job requirements.

## About

AI Career Coach extracts a structured CandidateProfile from a PDF CV and a validated RequirementProfile from a supplied job description. Deterministic components collect evidence, match and assess requirements, and keep the final analysis consistent. A local LLM explains those results in a structured CareerAnalysis response.

Current capabilities include:

- PDF text extraction and CV section parsing
- Generic Candidate Profile extraction and normalization
- Requirement extraction, filtering, decomposition, normalization, categorization, and validation
- Structured evidence collection, scoring, and ranking
- Conservative deterministic requirement matching
- Deterministic requirement assessment and narrative consistency
- Allowed-claims and unsupported-claims validation
- Structured JSON normalization and Pydantic validation
- Application Service orchestration and CLI delivery

## Current Architecture

```text
Candidate CV → CandidateProfile
                         ┐
                         ├→ Evidence and deterministic requirement assessment
                         │  → Prompt construction → LLM explanation
Requirement Source       │  → Structured validation
  → RequirementProfile ──┘  → Deterministic consistency and claim validation
                            → CareerAnalysis
```

See [docs/architecture.md](docs/architecture.md) for the component-level architecture.

## Technologies

- Python 3
- Ollama
- Pydantic
- PyPDF
- pytest

The architecture is provider-agnostic; Ollama is the current provider.

## Status

Current version: **MVP (CLI)**

Sprint 19 is complete with 303 passing automated tests. Sprint 20 will focus on robust Candidate Profile extraction across diverse CV layouts, document styles, professions, and wording variations.

REST API and frontend delivery layers are not yet implemented.

## Getting Started

```bash
git clone <repository-url>

cd ai-career-coach

python -m venv .venv

.venv\Scripts\activate

pip install -r requirements.txt
```

Install Ollama and pull a compatible local model:

```bash
ollama pull qwen2.5:7b
```

Run the application:

```bash
python -m app.main
```
