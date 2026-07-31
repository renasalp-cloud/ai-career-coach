from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from statistics import median

from pypdf import PdfReader


@dataclass(frozen=True)
class _TextFragment:
    text: str
    x: float
    y: float
    top_down: bool


_LINE_TOLERANCE = 4.0
_MIN_COLUMN_GAP = 72.0


def clean_text(text: str) -> str:
    """
    Cleans extracted PDF text while preserving line breaks.
    """
    lines = []

    for line in text.splitlines():
        cleaned_line = _remove_artificial_character_spacing(line.strip())
        cleaned_line = " ".join(cleaned_line.split())

        if cleaned_line:
            lines.append(cleaned_line)

    return "\n".join(lines)


def _remove_artificial_character_spacing(line: str) -> str:
    """Collapse glyph spacing only when most alphanumeric tokens are singletons."""

    tokens = line.split()
    alphanumeric_tokens = [
        token for token in tokens if any(character.isalnum() for character in token)
    ]
    if (
        len(alphanumeric_tokens) < 4
        or sum(len(token.strip(".,:;()[]/-")) <= 1 for token in alphanumeric_tokens)
        / len(alphanumeric_tokens)
        < 0.75
    ):
        return line

    words = line.split("  ")
    if len(words) == 1:
        words = [line]
    return " ".join(word.replace(" ", "") for word in words)


def _positioned_page_text(page: object) -> str:
    """Reconstruct a page from positioned fragments, preserving visual columns."""

    fragments: list[_TextFragment] = []

    def collect(
        text: str,
        cm: list[float],
        tm: list[float],
        _font: object,
        _font_size: float,
    ) -> None:
        if not text.strip() or len(cm) < 6 or len(tm) < 6:
            return
        horizontal_scale = hypot(cm[0], cm[1]) or 1.0
        vertical_scale = hypot(cm[2], cm[3]) or 1.0
        x = (tm[4] * cm[0] + tm[5] * cm[2] + cm[4]) / horizontal_scale
        y = (tm[4] * cm[1] + tm[5] * cm[3] + cm[5]) / vertical_scale
        vertical_direction = tm[2] * cm[1] + tm[3] * cm[3]
        fragments.append(
            _TextFragment(text.strip(), x, y, vertical_direction < 0)
        )

    page.extract_text(visitor_text=collect)
    fragments = _deduplicate_fragments(fragments)
    if len(fragments) < 2:
        return ""

    columns = _split_columns(fragments, _page_width(page))
    return "\n".join(
        line
        for column in columns
        for line in _ordered_lines(column)
    )


def _deduplicate_fragments(
    fragments: list[_TextFragment],
) -> list[_TextFragment]:
    """Discard exact duplicate drawing operations without losing repeated content."""

    unique: list[_TextFragment] = []
    seen: set[tuple[str, int, int]] = set()
    for fragment in fragments:
        key = (fragment.text, round(fragment.x), round(fragment.y))
        if key not in seen:
            seen.add(key)
            unique.append(fragment)
    return unique


def _page_width(page: object) -> float:
    try:
        return float(page.mediabox.width)
    except (AttributeError, TypeError, ValueError):
        return 0.0


def _split_columns(
    fragments: list[_TextFragment],
    page_width: float,
) -> list[list[_TextFragment]]:
    """Split on confident broad horizontal gaps; otherwise retain one column."""

    ordered = sorted(fragments, key=lambda fragment: fragment.x)
    gaps = [
        (ordered[index + 1].x - ordered[index].x, index)
        for index in range(len(ordered) - 1)
    ]
    if not gaps:
        return [ordered]

    gap, split_index = max(gaps)
    threshold = max(_MIN_COLUMN_GAP, page_width * 0.12)
    left = ordered[: split_index + 1]
    right = ordered[split_index + 1 :]
    if gap < threshold or len(left) < 2 or len(right) < 2:
        return [ordered]

    return [left, right]


def _ordered_lines(fragments: list[_TextFragment]) -> list[str]:
    """Group nearby baselines and order each visual line left-to-right."""

    top_down = sum(fragment.top_down for fragment in fragments) > len(fragments) / 2
    vertical = sorted(
        fragments,
        key=lambda fragment: fragment.y,
        reverse=not top_down,
    )
    lines: list[list[_TextFragment]] = []
    baselines: list[float] = []

    for fragment in vertical:
        matching_line = next(
            (
                index
                for index, baseline in enumerate(baselines)
                if abs(fragment.y - baseline) <= _LINE_TOLERANCE
            ),
            None,
        )
        if matching_line is None:
            lines.append([fragment])
            baselines.append(fragment.y)
        else:
            lines[matching_line].append(fragment)
            baselines[matching_line] = median(
                item.y for item in lines[matching_line]
            )

    return [
        " ".join(item.text for item in sorted(line, key=lambda item: item.x))
        for line in lines
    ]


def extract_text(pdf_path: str) -> str:
    """
    Reads a PDF file and returns cleaned extracted text.
    """
    reader = PdfReader(pdf_path)

    pages: list[str] = []

    for page in reader.pages:
        standard_text = page.extract_text() or ""
        try:
            positioned_text = _positioned_page_text(page)
        except Exception:
            positioned_text = ""

        page_text = positioned_text or standard_text
        cleaned_page = clean_text(page_text)
        if cleaned_page:
            pages.append(cleaned_page)

    return "\n\n".join(pages)
