# AI Career Coach - Response Schema

## Purpose

This document defines the structured JSON response returned by the AI analysis engine.

The same response will be used by:
- CLI output
- Web interface
- PDF report generation
- Future user dashboard

## Schema v0.1

```json
{
  "overall_match_score": 0,
  "professional_summary": "",
  "strengths": [
    {
      "title": "",
      "evidence": ""
    }
  ],
  "missing_skills": {
    "critical": [
      {
        "skill": "",
        "reason": ""
      }
    ],
    "important": [
      {
        "skill": "",
        "reason": ""
      }
    ],
    "optional": [
      {
        "skill": "",
        "reason": ""
      }
    ]
  },
  "career_gap_analysis": "",
  "recommendations": [
    {
      "priority": "",
      "title": "",
      "reason": "",
      "action": ""
    }
  ],
  "learning_roadmap": [
    {
      "week": 1,
      "goal": "",
      "topics": [],
      "practical_task": "",
      "expected_outcome": ""
    }
  ]
}
```

## Notes

- `overall_match_score` must be between 0 and 100.
- `strengths` must include evidence from the CV.
- `missing_skills` must be grouped by priority.
- `recommendations` must be actionable.
- `learning_roadmap` must contain a 4-week plan.