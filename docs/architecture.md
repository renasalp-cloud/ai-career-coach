# AI Career Coach Architecture

## Vision

AI Career Coach is an intelligent career assessment platform that evaluates how well a candidate matches a target role.

The system is not designed to be a simple LLM wrapper.

Instead, the LLM is one component inside a larger decision-making pipeline that combines structured data, predefined role requirements, and AI reasoning.

---

# System Goal

Given:

- A candidate CV
- A target role
- (Optional) A job description

The system should produce:

- Overall match score
- Professional summary
- Strengths
- Missing skills
- Career gap analysis
- Personalized recommendations
- Learning roadmap

---

# High-Level Architecture

```text
                   Candidate CV (PDF)
                           │
                           ▼
                     PDF Reader
                           │
                           ▼
                     Text Cleaner
                           │
                           ▼
                      CV Parser
                           │
                           ▼
                  Candidate Profile
                           │
            ┌──────────────┴──────────────┐
            │                             │
            ▼                             ▼
      Role Profile                 Job Description
            │                             │
            └──────────────┬──────────────┘
                           ▼
                  Assessment Engine
                           │
                           ▼
                     AI Reasoning
                           │
                           ▼
                 Structured JSON Report
                           │
                           ▼
              CLI / Web / PDF Presentation
```

---

# Core Components

## 1. PDF Reader

Responsible for:

- Reading PDF files
- Extracting raw text
- Returning plain text

Input:

- PDF file

Output:

- Raw text

---

## 2. Text Cleaner

Responsible for:

- Removing unnecessary whitespace
- Preserving useful formatting
- Preparing text for parsing

Input:

- Raw text

Output:

- Clean text

---

## 3. CV Parser

Responsible for extracting structured information.

Example:

- Education
- Experience
- Projects
- Skills
- Languages
- Certifications

Input:

- Clean text

Output:

- Candidate Profile

---

## 4. Candidate Profile

Represents the candidate as structured data.

Future example:

```python
CandidateProfile(
    education=[],
    experience=[],
    projects=[],
    skills=[],
    certifications=[],
    languages=[]
)
```

The assessment engine should work with structured data rather than raw text whenever possible.

---

## 5. Role Profile

Defines what a specific career role expects.

Examples:

- AI Engineer
- Data Scientist
- Backend Developer
- Frontend Developer
- Marketing Specialist

Each profile defines:

- Critical skills
- Important skills
- Optional skills

Role profiles help reduce hallucinations and improve consistency.

---

## 6. Assessment Engine

The heart of the application.

Responsibilities:

- Compare candidate profile with target role
- Detect strengths
- Detect missing skills
- Calculate match score
- Generate recommendations
- Build learning roadmap

Important:

Business logic belongs here.

The Assessment Engine should remain independent of the AI provider.

---

## 7. AI Provider

Responsible only for reasoning.

Current implementation:

- Ollama
- Qwen 2.5

Future providers:

- OpenAI
- Claude
- Gemini
- Local models

The AI provider should never contain business logic.

---

## 8. Validation Layer

Every AI response must be validated.

Responsibilities:

- JSON validation
- Schema validation
- Type checking

Invalid AI responses should never reach the user.

---

## 9. Presentation Layer

Responsible for presenting the validated report.

Possible outputs:

- CLI
- Web UI
- PDF Report
- REST API

Presentation should never contain business logic.

---

# Design Principles

## Single Responsibility

Each module should have one responsibility.

---

## Structured Data First

Prefer structured objects over raw text whenever possible.

---

## AI as a Component

The AI model is a tool.

It is not the application.

Business logic should remain independent from the LLM.

---

## Validation First

Never trust AI output without validation.

---

## Extensibility

Adding a new role should require only:

- a new Role Profile

Adding a new AI model should require only:

- a new AI Provider

---

## Current MVP

The current implementation includes:

- PDF extraction
- Text cleaning
- CV parsing
- Structured prompts
- Local LLM (Ollama)
- Structured JSON output
- Pydantic validation
- CLI interface

---

# Future Architecture

The long-term architecture will introduce:

- Job Description Parser
- ATS Analysis
- Resume Optimization
- Cover Letter Generator
- Interview Preparation
- Career Dashboard
- Web Application
- User Accounts
- Report History
- Multi-LLM Support

---

# Guiding Principle

Every new feature must answer the following question:

> Does this improve the quality of the career assessment?

If the answer is no, the feature should not be implemented.