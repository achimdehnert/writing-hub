"""
Authors — Markdown-Import Service für Schreibstile.

Parst eine strukturierte Markdown-Datei und extrahiert:
  - Name, Beschreibung
  - DO / DONT / Taboo / Signature Moves (Listen)
  - style_prompt, source_text
  - Optional: LLM-Fallback fuer freiformatierte MDs

Erwartetes MD-Format (Sektionen per ## Heading):
  # <Stilname>
  ## Beschreibung | ## Description
  ## DO | ## Erlaubt
  ## DON'T | ## DONT | ## Vermeiden
  ## Taboo | ## Tabu | ## Taboo-Woerter
  ## Signature Moves | ## Stilmittel
  ## Stil-Prompt | ## Style Prompt
  ## Quelltext | ## Source Text | ## Beispieltext
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import WritingStyle

logger = logging.getLogger(__name__)

# Section heading aliases (case-insensitive)
_SECTION_MAP: dict[str, list[str]] = {
    "description": [
        "beschreibung", "description", "desc", "ueber", "about",
    ],
    "do_list": [
        "do", "erlaubt", "empfohlen", "dos", "do-liste", "regeln do",
    ],
    "dont_list": [
        "don't", "dont", "don'ts", "donts", "vermeiden", "nicht",
        "don't-liste", "dont-liste",
    ],
    "taboo_list": [
        "taboo", "tabu", "taboo-woerter", "tabu-woerter",
        "taboo-liste", "tabu-liste", "verboten",
    ],
    "signature_moves": [
        "signature moves", "signature-moves", "stilmittel",
        "charakteristisch", "besonderheiten", "merkmale",
    ],
    "style_prompt": [
        "stil-prompt", "style prompt", "style-prompt",
        "schreibanweisung", "prompt", "anweisung",
    ],
    "source_text": [
        "quelltext", "source text", "source", "beispieltext",
        "textprobe", "originaltext", "referenztext",
    ],
}

# Reverse lookup: alias -> field_name
_ALIAS_TO_FIELD: dict[str, str] = {}
for _field_name, _aliases in _SECTION_MAP.items():
    for _alias in _aliases:
        _ALIAS_TO_FIELD[_alias] = _field_name


@dataclass
class StyleImportResult:
    """Ergebnis eines MD-Imports."""
    name: str = ""
    description: str = ""
    do_list: list[str] = field(default_factory=list)
    dont_list: list[str] = field(default_factory=list)
    taboo_list: list[str] = field(default_factory=list)
    signature_moves: list[str] = field(default_factory=list)
    style_prompt: str = ""
    source_text: str = ""
    raw_markdown: str = ""
    sections_found: list[str] = field(default_factory=list)

    @property
    def has_structured_data(self) -> bool:
        return bool(
            self.do_list or self.dont_list
            or self.taboo_list or self.signature_moves
        )


# Regex: match ## heading (with optional trailing colon or dash)
_HEADING_RE = re.compile(
    r"^#{1,3}\s+(.+?)[\s:—-]*$",
    re.MULTILINE,
)

# List item patterns: "- item", "* item", "• item", "1. item"
_LIST_ITEM_RE = re.compile(
    r"^\s*(?:[-*•◦]|\d+[.)]\s)\s*(.+)$",
    re.MULTILINE,
)


def parse_style_markdown(markdown_text: str) -> StyleImportResult:
    """
    Parst eine Markdown-Datei und extrahiert Schreibstil-Daten.

    Erkennt bekannte Sektionen (DO/DONT/Taboo etc.) und extrahiert
    deren Inhalte als Listen oder Freitext.
    """
    result = StyleImportResult(raw_markdown=markdown_text)

    if not markdown_text or not markdown_text.strip():
        return result

    text = markdown_text.strip()

    # Extract title from first H1 heading
    h1_match = re.match(r"^#\s+(.+?)[\s:—-]*$", text, re.MULTILINE)
    if h1_match:
        result.name = h1_match.group(1).strip()

    # Split into sections by ## headings
    sections = _split_into_sections(text)

    for heading, content in sections.items():
        heading_lower = heading.lower().strip()
        field_name = _match_heading_to_field(heading_lower)

        if not field_name:
            logger.debug("Unknown section heading: %r", heading)
            continue

        result.sections_found.append(field_name)

        if field_name in ("do_list", "dont_list", "taboo_list", "signature_moves"):
            items = _extract_list_items(content)
            setattr(result, field_name, items)
        elif field_name == "description":
            result.description = content.strip()
        elif field_name == "style_prompt":
            result.style_prompt = content.strip()
        elif field_name == "source_text":
            result.source_text = content.strip()

    return result


def _split_into_sections(text: str) -> dict[str, str]:
    """Splits markdown into {heading: content} dict by ## headings."""
    sections: dict[str, str] = {}
    headings = list(_HEADING_RE.finditer(text))

    if not headings:
        return sections

    for i, match in enumerate(headings):
        heading = match.group(1).strip()
        start = match.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        content = text[start:end].strip()
        if content:
            sections[heading] = content

    return sections


def _match_heading_to_field(heading: str) -> str | None:
    """Match a heading string to a known field name."""
    # Direct alias match
    if heading in _ALIAS_TO_FIELD:
        return _ALIAS_TO_FIELD[heading]

    # Fuzzy match: check if any alias is contained in heading
    for alias, field_name in _ALIAS_TO_FIELD.items():
        if alias in heading:
            return field_name

    return None


def _extract_list_items(content: str) -> list[str]:
    """Extract list items from markdown content."""
    items = []
    matches = _LIST_ITEM_RE.findall(content)

    if matches:
        for item in matches:
            cleaned = item.strip().rstrip(".").strip()
            if cleaned:
                items.append(cleaned)
    else:
        # Fallback: treat non-empty lines as items
        for line in content.splitlines():
            line = line.strip().rstrip(".").strip()
            if line and not line.startswith("#"):
                items.append(line)

    return items


def import_style_from_markdown(
    author,
    markdown_text: str,
    *,
    auto_analyze: bool = True,
    name_override: str = "",
) -> tuple["WritingStyle", StyleImportResult]:
    """
    Erstellt einen WritingStyle aus einer Markdown-Datei.

    Args:
        author: Author-Instanz
        markdown_text: Inhalt der MD-Datei
        auto_analyze: LLM-Analyse starten wenn wenig strukturierte Daten
        name_override: Optionaler Name (ueberschreibt MD-Titel)

    Returns:
        (WritingStyle, StyleImportResult)
    """
    from .models import WritingStyle

    parsed = parse_style_markdown(markdown_text)

    name = name_override or parsed.name or "Importierter Stil"
    description = parsed.description

    style = WritingStyle.objects.create(
        author=author,
        name=name,
        description=description,
        source_text=parsed.source_text or parsed.raw_markdown,
        style_prompt=parsed.style_prompt,
        do_list=parsed.do_list,
        dont_list=parsed.dont_list,
        taboo_list=parsed.taboo_list,
        signature_moves=parsed.signature_moves,
        status=WritingStyle.Status.DRAFT,
    )

    logger.info(
        "Imported WritingStyle %s from MD: sections=%s, has_structured=%s",
        style.pk, parsed.sections_found, parsed.has_structured_data,
    )

    return style, parsed
