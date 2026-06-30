"""CV analysis logic using the configured AI provider."""

from app.ai.ollama_provider import generate


def analyze_cv(cv_text: str, target_role: str) -> str:
    """Analyze CV text for a target career role."""
    prompt = f"""
You are an AI Career Coach.

Analyze the CV for this target role: {target_role}

Return a concise analysis with these sections:
1. Overall Match Score
2. Strengths
3. Missing Skills
4. Career Gap Analysis
5. Recommendations
6. Learning Roadmap

CV:
{cv_text[:4000]}
"""
    return generate(prompt)