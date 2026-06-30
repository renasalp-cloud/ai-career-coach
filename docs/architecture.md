# AI Career Coach - Architecture

## Current Architecture

The application currently works as a command-line tool.

## Data Flow

```text
User
  ↓
app/main.py
  ↓
app/pdf_reader.py
  ↓
Extracted CV Text
  ↓
app/ai_analyzer.py
  ↓
AI Career Feedback
```

## Components

### main.py

Starts the application and handles user input.

### pdf_reader.py

Handles PDF text extraction and basic text cleaning.

### ai_analyzer.py

Will handle AI-based CV analysis.

Planned responsibilities:
- Receive extracted CV text
- Receive target career role
- Generate strengths
- Generate weaknesses
- Generate improvement suggestions
- Return structured feedback

## AI Provider Strategy

The project should avoid being tightly coupled to a single AI provider.

The first implementation may use OpenAI API, but the architecture should allow future support for other providers such as local models or other AI APIs.