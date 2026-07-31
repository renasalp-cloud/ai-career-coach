from pathlib import Path
from unittest.mock import Mock

from app.ai.analyzer import AnalysisResult
from app.analysis.output_normalizer import normalize_career_analysis_output
from app.application import AnalysisRequest, CVSource
from app.bootstrap import create_application_service
from app.candidate_profile.models import CandidateProfile
from app.main import print_analysis
from app.models import CareerAnalysis, RequirementProfile
from app.requirements.source import RequirementSource, RequirementSourceType


def test_normalizes_wrapped_words_lines_punctuation_and_placeholders() -> None:
    result = normalize_career_analysis_output({
        "professional_summary": " Good communication and organizational skil ls.\nWorks well.. ",
        "strengths": [{"title": "Not provided.:", "evidence": "Unknown"}],
        "recommendations": [{
            "priority": "IMPORTANT", "title": "N/A", "reason": "None", "action": "Unknown"
        }],
    })

    assert result["professional_summary"] == (
        "Good communication and organizational skills. Works well."
    )
    assert result["strengths"] == [{"title": "", "evidence": ""}]
    assert result["recommendations"] == [{
        "priority": "medium", "title": "", "reason": "", "action": ""
    }]


def test_renderer_does_not_expose_internal_placeholder_text(capsys) -> None:
    print_analysis({
        "overall_match_score": 0,
        "professional_summary": "Not provided.",
        "strengths": [{"title": "Not provided.:", "evidence": "None"}],
        "missing_skills": {},
        "career_gap_analysis": "Unknown",
        "recommendations": [{
            "priority": "N/A", "title": "None", "reason": "Unknown", "action": "Not provided."
        }],
        "learning_roadmap": [],
    })

    output = capsys.readouterr().out.casefold()
    for placeholder in ("not provided", "none", "n/a", "unknown"):
        assert placeholder not in output


def test_renderer_preserves_strength_evidence_without_placeholder_title(capsys) -> None:
    print_analysis({
        "overall_match_score": 82,
        "professional_summary": "Meaningful candidate summary.",
        "strengths": [{
            "title": "No information available.",
            "evidence": "Solving conflict situations and communicating with patients.",
        }],
        "missing_skills": {},
        "career_gap_analysis": "No validated gaps.",
        "recommendations": [],
        "learning_roadmap": [],
    })

    output = capsys.readouterr().out
    assert "- Solving conflict situations and communicating with patients." in output
    assert "No information available.:" not in output


def test_composition_root_returns_the_same_final_result_rendered_by_cli(
    tmp_path: Path, capsys
) -> None:
    cv_path = tmp_path / "adele.pdf"
    cv_path.touch()
    candidate = CandidateProfile(
        summary="Patient-focused professional with conflict-resolution experience."
    )
    generated = CareerAnalysis(
        overall_match_score=82,
        professional_summary="No information available.",
        strengths=[{
            "title": "No information available.",
            "evidence": "Solving conflict situations and communicating with patients.",
        }],
        missing_skills={
            "critical": [{"skill": "Planning", "reason": "Not demonstrated."}],
            "important": [],
            "optional": [],
        },
        career_gap_analysis="Planning remains a gap.",
        recommendations=[],
        learning_roadmap=[{
            "week": week,
            "goal": "Develop planning",
            "topics": ["Planning"],
            "practical_task": "Complete a planning exercise.",
            "expected_outcome": "Produce a planning work sample.",
        } for week in range(1, 5)],
    )
    service = create_application_service()
    service._pdf_reader = Mock(return_value="CV text")
    service._text_cleaner = Mock(return_value="CV text")
    service._cv_parser = Mock(return_value={"summary": candidate.summary})
    service._candidate_profile_extractor = Mock(return_value=candidate)
    service._candidate_profile_normalizer = Mock(return_value=candidate)
    service._requirement_pipeline = Mock()
    service._requirement_pipeline.build.return_value = RequirementProfile(title="Role")
    service._analyzer = Mock(return_value=AnalysisResult(
        candidate_profile=candidate,
        analysis=generated.model_dump(),
    ))

    response = service.analyze(AnalysisRequest(
        cv_source=CVSource(file_path=cv_path),
        requirement_source=RequirementSource(
            source_type=RequirementSourceType.PASTED_TEXT,
            content="Planning",
        ),
    ))
    print_analysis(response.analysis.model_dump())

    output = capsys.readouterr().out
    assert response.analysis.professional_summary == candidate.summary
    assert response.analysis.overall_match_score == 82
    assert response.analysis.missing_skills.critical[0].skill == "Planning"
    assert f"Professional Summary:\n{candidate.summary}" in output
    assert "Solving conflict situations and communicating with patients." in output
    assert "Professional Summary:\nNo information available." not in output
    assert "No information available.:" not in output
