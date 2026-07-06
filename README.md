# AI Career Coach

An AI powered career assistant that analyzes CVs, identifies skill gaps, and generates personalized career recommendations using a local LLM.

## About

AI Career Coach is an AI-powered application that analyzes CVs and provides personalized career guidance based on a user's target role.

The application extracts text from a PDF CV, organizes it into structured sections, and uses a local Large Language Model (LLM) through Ollama to generate an objective career analysis. The response is validated using structured data models before being presented to the user.

Current features include:

- PDF CV parsing
- Structured CV section extraction
- AI-powered CV analysis
- Target role matching
- Skill gap identification
- Personalized recommendations
- 4-week learning roadmap
- Local AI inference with Ollama
- Structured JSON validation

## Current Architecture

```text
PDF CV
   │
   ▼
PDF Reader
   │
   ▼
Text Cleaning
   │
   ▼
CV Parser
   │
   ▼
Structured CV
   │
   ▼
Ollama (Local LLM)
   │
   ▼
Structured JSON
   │
   ▼
Pydantic Validation
   │
   ▼
CLI Output
```

## Technologies

- Python 3
- Ollama
- Qwen 2.5 (Local LLM)
- Pydantic
- PyPDF
- Git

## Roadmap

### Near Term

- Improve CV parser accuracy
- Improve prompt quality
- Better AI scoring consistency
- Job description analysis

### Future

- ATS compatibility analysis
- Web interface
- PDF report generation
- Career dashboard
- Multi-model AI support

## Status

Current version: **MVP (CLI)**

The project is under active development.

## Getting Started

```bash
git clone <repository-url>

cd ai-career-coach

python -m venv .venv

.venv\Scripts\activate

pip install -r requirements.txt
```

Install Ollama and pull the model:

```bash
ollama pull qwen2.5:7b
```

Run the application:

```bash
python -m app.main
```