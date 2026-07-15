"""CV analysis logic using the configured AI provider."""

import json
from dataclasses import dataclass
from pathlib import Path
from pydantic import ValidationError

from app.analysis.output_normalizer import normalize_career_analysis_output
from app.assessment.requirement_assessment import RequirementAssessmentEngine
from app.models import CareerAnalysis, RequirementProfile
from app.analysis.consistency_processor import AnalysisConsistencyProcessor
from app.cv_parser import parse_cv
from app.ai.prompt_builder import PromptContext, build_cv_analysis_prompt
from app.candidate_profile.models import CandidateProfile
from app.candidate_profile.extractor import extract_candidate_profile
from app.candidate_profile.normalizer import normalize_candidate_profile
from app.semantic.default_aliases import build_default_skill_alias_registry
from app.semantic.matcher import SkillMatcher
from app.semantic.validator import SkillValidator

from app.ai.ollama_provider import generate


PROMPT_PATH = Path("app/prompts/cv_analysis.txt")

DEBUG_ARTIFACT_PATH = Path("debug/last_failed_analysis.json")

CAREER_ANALYSIS_ROOT_KEYS = {
    "overall_match_score",
    "professional_summary",
    "strengths",
    "missing_skills",
    "career_gap_analysis",
    "recommendations",
    "learning_roadmap",
}


class CareerAnalysisGenerationError(RuntimeError):
    """Raised when the provider cannot produce a valid CareerAnalysis response."""

    def __init__(
        self,
        original_error: ValidationError | str,
        repair_error: ValidationError | None = None,
        original_response: str | None = None,
        repaired_response: str | None = None,
    ) -> None:
        if isinstance(original_error, str):
            self.original_error = None
            self.repair_error = None
            self.original_response = None
            self.repaired_response = None
            super().__init__(original_error)
            return

        if repair_error is None or original_response is None or repaired_response is None:
            raise TypeError("Detailed validation failures require both errors and responses.")

        self.original_error = original_error
        self.repair_error = repair_error
        self.original_response = original_response
        self.repaired_response = repaired_response

        message = (
            "CareerAnalysis schema validation failed after one repair attempt.\n\n"
            "Original Validation Errors:\n"
            f"{_format_validation_errors(original_error)}\n\n"
            "Repaired Validation Errors:\n"
            f"{_format_validation_errors(repair_error)}\n\n"
            "Original Response:\n"
            f"{original_response}\n\n"
            "Repaired Response:\n"
            f"{repaired_response}"
        )
        super().__init__(message)


@dataclass(frozen=True)
class AnalysisResult:
    candidate_profile: CandidateProfile
    analysis: dict


def extract_json(text: str) -> str:
    """Extract JSON from an AI response."""

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:].strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    return text


def _career_analysis_schema() -> str:
    return json.dumps(
        CareerAnalysis.model_json_schema(),
        indent=2,
        ensure_ascii=False,
    )


def _format_validation_errors(validation_error: ValidationError) -> str:
    return json.dumps(
        validation_error.errors(),
        indent=2,
        ensure_ascii=False,
        default=str,
    )


def _write_failed_analysis_debug_artifact(
    original_response: str,
    original_error: ValidationError,
    repaired_response: str,
    repair_error: ValidationError,
) -> None:
    artifact = {
        "original_response": original_response,
        "original_errors": original_error.errors(),
        "repaired_response": repaired_response,
        "repaired_errors": repair_error.errors(),
    }
    DEBUG_ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEBUG_ARTIFACT_PATH.write_text(
        json.dumps(artifact, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def _build_repair_prompt(
    original_prompt: str,
    invalid_json: str,
    validation_error: ValidationError,
) -> str:
    return f"""
The previous CareerAnalysis response did not match the required JSON schema.

Repair formatting and structure only. Preserve the facts and analysis in the
previous response. Do not regenerate the analysis or create a new candidate profile.

Return ONLY one valid CareerAnalysis JSON object.

Do not return input structures such as:
- candidate_profile
- role_profile
- validated_skill_matches
- requirement_assessment

Do not use markdown.
Do not use code fences.
Do not add explanations.
Do not omit any required key.
Do not invent unsupported facts.

Original analysis request:
<ORIGINAL_REQUEST>
{original_prompt}
</ORIGINAL_REQUEST>

Previous invalid response:
<INVALID_RESPONSE>
{invalid_json}
</INVALID_RESPONSE>

Validation errors:
{json.dumps(validation_error.errors(), indent=2, ensure_ascii=False, default=str)}

Required schema:
{_career_analysis_schema()}
"""


def _has_required_root_keys(json_text: str) -> bool:
    try:
        response = json.loads(json_text)
    except (json.JSONDecodeError, TypeError):
        return False

    return isinstance(response, dict) and CAREER_ANALYSIS_ROOT_KEYS.issubset(response)


def _validate_or_repair_analysis(
    json_text: str,
    original_prompt: str,
) -> CareerAnalysis:
    try:
        parsed_data = json.loads(json_text)
        normalized_data = normalize_career_analysis_output(parsed_data)

        return CareerAnalysis.model_validate(normalized_data)

    except (json.JSONDecodeError, ValidationError) as original_error:
        if isinstance(original_error, json.JSONDecodeError):
            raise CareerAnalysisGenerationError(
                f"LLM response was not valid JSON: {original_error}"
            ) from original_error

        repair_prompt = _build_repair_prompt(
            original_prompt=original_prompt,
            invalid_json=json_text,
            validation_error=original_error,
        )
        repaired_response_text = generate(repair_prompt)
        repaired_json_text = extract_json(repaired_response_text)

        try:
            repaired_data = json.loads(repaired_json_text)
            normalized_repaired_data = normalize_career_analysis_output(
                repaired_data
            )

            return CareerAnalysis.model_validate(
                normalized_repaired_data
            )

        except (json.JSONDecodeError, ValidationError) as repair_error:
            if isinstance(repair_error, json.JSONDecodeError):
                raise CareerAnalysisGenerationError(
                    f"Repaired LLM response was not valid JSON: {repair_error}"
                ) from repair_error

            _write_failed_analysis_debug_artifact(
                original_response=json_text,
                original_error=original_error,
                repaired_response=repaired_json_text,
                repair_error=repair_error,
            )
            raise CareerAnalysisGenerationError(
                original_error=original_error,
                repair_error=repair_error,
                original_response=json_text,
                repaired_response=repaired_json_text,
            ) from repair_error


def _validate_analysis_response(
    json_text: str,
    original_prompt: str,
) -> CareerAnalysis:
    if not _has_required_root_keys(json_text):
        retry_response_text = generate(original_prompt)
        json_text = extract_json(retry_response_text)

        if not _has_required_root_keys(json_text):
            raise CareerAnalysisGenerationError(
                "LLM response did not contain the required CareerAnalysis root keys "
                "after one retry."
            )

    return _validate_or_repair_analysis(
        json_text=json_text,
        original_prompt=original_prompt,
    )


def analyze_cv(
    cv_text: str,
    requirement_profile: RequirementProfile,
    cv_sections: dict[str, str] | None = None,
) -> AnalysisResult:
    """Analyze a CV against an already-built requirement profile."""

    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")

    if cv_sections is None:
        cv_sections = parse_cv(cv_text)

    candidate_profile = extract_candidate_profile(cv_sections)
    candidate_profile = normalize_candidate_profile(candidate_profile)

    skill_matcher = SkillMatcher(
        alias_registry=build_default_skill_alias_registry(),
    )
    skill_matches = skill_matcher.match(candidate_profile, requirement_profile)
    validated_skill_matches = SkillValidator().validate(skill_matches)
    requirement_assessment = RequirementAssessmentEngine().assess(
        requirement_profile,
        validated_skill_matches,
    )
    prompt_context = PromptContext(
        template=prompt_template,
        requirement_profile=requirement_profile,
        candidate_profile=candidate_profile,
        validated_skill_matches=validated_skill_matches,
        requirement_assessment=requirement_assessment,
    )

    prompt = build_cv_analysis_prompt(prompt_context)

    response_text = generate(prompt)
    json_text = extract_json(response_text)

    analysis = _validate_analysis_response(
        json_text=json_text,
        original_prompt=prompt,
    )
    analysis = AnalysisConsistencyProcessor().process(
        analysis,
        candidate_profile,
        requirement_profile,
        validated_skill_matches,
    )

    return AnalysisResult(
        candidate_profile=candidate_profile,
        analysis=analysis.model_dump(),
    )
