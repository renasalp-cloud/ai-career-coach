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
- Application Service orchestration with CLI and FastAPI delivery

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

Current version: **Backend MVP (CLI and FastAPI)**

Sprint 20 is complete, and the backend business logic is feature frozen. Sprint 21, the FastAPI delivery layer, is complete. The latest verified automated test result is **447 passed**. Sprint 22, the React frontend, is next.

The REST API exposes `GET /health` and `POST /analyses`. The analysis route accepts multipart fields `cv_file` (PDF), `target_role`, and `job_description`, delegates to the Application Service, and returns a structured response. The React frontend is not implemented yet.

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

## API Documentation

Run the local development server:

```powershell
python -m uvicorn app.api.app:app --reload
```

Interactive API documentation: http://localhost:8000/docs

OpenAPI schema: http://localhost:8000/openapi.json

### Local API configuration

The API reads the following optional environment variables:

- `API_TITLE` (default: `AI Career Coach API`)
- `API_VERSION` (default: `0.1.0`)
- `API_DESCRIPTION` (default: the documented career-analysis description)
- `API_CORS_ORIGINS` (default: `http://localhost:5173`)

`API_CORS_ORIGINS` is a comma-separated list of explicit browser origins. Whitespace,
empty entries, and duplicates are removed. For example:

```powershell
$env:API_CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
python -m uvicorn app.api.app:app --reload
```

Only configured origins are allowed. The default supports local React development;
production deployments must set their actual frontend origin. Wildcard origins are
not enabled, credentials are disabled, and CORS permits only `GET`, `POST`, and
preflight `OPTIONS` requests.

### React integration preview

The future React application should configure its API base URL independently:

```text
VITE_API_BASE_URL=http://localhost:8000
```

Submit `POST /analyses` as `multipart/form-data` with `cv_file`, `target_role`, and
`job_description`. Use browser `FormData` and do not set the `Content-Type` header
manually; the browser must generate the multipart boundary. The successful response
is structured `AnalysisResponse` JSON and does not require CLI parsing or knowledge
of the configured LLM provider.
