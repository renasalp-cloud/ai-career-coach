import copy

import pytest

from app.evidence.models import CandidateEvidence, ScoredCandidateEvidence
from app.evidence.ranker import EvidenceRanker


def scored(skill: str, score: int, text: str) -> ScoredCandidateEvidence:
    return ScoredCandidateEvidence(
        evidence=CandidateEvidence(
            skill=skill,
            source_type="other",
            source_text=text,
            source_label="Other",
        ),
        quality_score=score,
        quality_factors=["test score"],
    )


def test_rank_orders_scores_descending_and_preserves_equal_score_order() -> None:
    items = [
        scored("First", 30, "first"),
        scored("Second", 80, "second"),
        scored("Third", 80, "third"),
        scored("Fourth", 50, "fourth"),
    ]

    ranked = EvidenceRanker().rank(items)

    assert [item.evidence.source_text for item in ranked] == [
        "second", "third", "fourth", "first"
    ]


def test_rank_does_not_mutate_input_list_or_evidence_objects() -> None:
    items = [scored("Low", 10, "low"), scored("High", 90, "high")]
    original = copy.deepcopy(items)

    ranked = EvidenceRanker().rank(items)

    assert items == original
    assert ranked is not items
    assert all(result is source for result, source in zip(ranked, reversed(items)))


def test_rank_is_repeatable_and_handles_empty_and_single_item_lists() -> None:
    ranker = EvidenceRanker()
    item = scored("Skill", 50, "only")
    items = [scored("Low", 20, "low"), scored("High", 70, "high")]

    assert ranker.rank(items) == ranker.rank(items)
    assert ranker.rank([]) == []
    assert ranker.rank([item]) == [item]


def test_rank_by_skill_normalizes_groups_and_preserves_first_seen_order() -> None:
    items = [
        scored(" Python ", 30, "declaration"),
        scored("Docker", 40, "docker"),
        scored("PYTHON", 80, "work"),
        scored("python", 70, "project"),
    ]

    grouped = EvidenceRanker().rank_by_skill(items)

    assert list(grouped) == ["python", "docker"]
    assert [item.evidence.source_text for item in grouped["python"]] == [
        "work", "project", "declaration"
    ]
    assert grouped["docker"] == [items[1]]


def test_rank_by_skill_preserves_distinct_equal_scored_evidence() -> None:
    first = scored("Skill", 50, "first source")
    second = scored("skill", 50, "second source")

    grouped = EvidenceRanker().rank_by_skill([first, second])

    assert grouped["skill"] == [first, second]


def test_select_top_respects_limit_without_mutating_input() -> None:
    items = [
        scored("Low", 10, "low"),
        scored("High", 90, "high"),
        scored("Middle", 50, "middle"),
    ]
    original = list(items)

    selected = EvidenceRanker().select_top(items, 2)

    assert [item.quality_score for item in selected] == [90, 50]
    assert items == original


def test_select_top_returns_all_items_when_limit_exceeds_available() -> None:
    items = [scored("Low", 10, "low"), scored("High", 90, "high")]

    assert EvidenceRanker().select_top(items, 10) == [items[1], items[0]]


@pytest.mark.parametrize("limit", [0, -1])
def test_select_top_rejects_non_positive_limit(limit: int) -> None:
    with pytest.raises(ValueError, match="limit must be positive"):
        EvidenceRanker().select_top([], limit)
