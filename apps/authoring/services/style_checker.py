"""
StyleChecker — regelbasierte Stilprüfung ohne LLM.

Portiert aus bfagent.writing_hub.services.style_checker (ADR-083).
Keine Django-Abhängigkeiten außer Decimal.
PATTERNS sind unveränderliche linguistische Regeln (Regex-Antipattern).
"""

import re
from decimal import Decimal


class StyleChecker:
    """
    Regelbasierter StyleChecker ohne LLM.

    Prüft Text gegen Regex-Antipattern pro book_type_name.
    Gibt dimension_scores zurück für QualityGateService.evaluate().
    """

    PATTERNS: dict[str, list[tuple[str, str, str]]] = {
        "novel": [
            (r"\b(irgendwie|sozusagen|eigentlich|quasi)\b", "Fuellwort", "minor"),
            (r"\b\w+end\s+sagte\b", "Adverb bei Dialogverb", "major"),
            (r"\bwurde\b.{1,40}\bvon\b", "Passiv-Konstruktion", "suggestion"),
            (r"(?<=[.!?])\s+[A-Z][^.!?]{0,30}(sagte|fragte|rief|fluesterte)\b", "Dialogverb nach Satz", "minor"),
        ],
        "essay": [
            (r"\b(ich|wir)\b", "Ich/Wir-Verwendung in Essay", "major"),
            (r"Es ist klar,?\s+dass", "Unbelegte Behauptung", "major"),
            (r"\boffensichtlich\b", "Subjektiver Ausdruck", "minor"),
        ],
        "scientific": [
            (r"\b(immer|niemals|stets|grundsaetzlich|grundsätzlich)\b", "Absolute Aussage", "major"),
            (r"\bbeweist\s+definitiv\b", "Overclaiming", "major"),
            (r"\b(klar|offensichtlich|eindeutig)\b", "Unpräziser Ausdruck", "minor"),
        ],
        "nonfiction": [
            (r"\b(irgendwie|sozusagen|quasi)\b", "Fuellwort", "minor"),
            (r"\bman\s+(sollte|muss|kann)\b", "Unpersönliche Formulierung", "suggestion"),
        ],
        "academic": [
            (r"\b(immer|niemals|stets)\b", "Absolute Aussage", "major"),
            (r"\b(ich|wir)\b", "Ich/Wir-Verwendung", "major"),
            (r"\bbeweist\b", "Overclaiming ohne Modalität", "minor"),
        ],
    }

    def check(self, text: str, book_type_name: str) -> dict[str, Decimal]:
        """
        Prüft text gegen Patterns für book_type_name.

        Args:
            text: Zu prüfender Text
            book_type_name: Buchtyp-Name (z.B. "novel", "essay")

        Returns:
            Dict mit {dimension_code: score} für QualityGateService.
        """
        type_key = book_type_name.lower().strip()
        patterns = self.PATTERNS.get(type_key, [])
        if not patterns or not text:
            return {}

        hits = sum(1 for pat, _, _ in patterns if re.search(pat, text, re.IGNORECASE))
        score = max(
            Decimal("0.00"),
            Decimal("10.00") - Decimal(str(hits)) * Decimal("1.50"),
        )
        return {f"style_regex_{type_key}": score}

    def get_findings(self, text: str, book_type_name: str) -> list[dict]:
        """
        Detaillierte Findings (für UI-Anzeige).

        Returns:
            Liste von Dicts: pattern, label, severity, match_count, examples
        """
        type_key = book_type_name.lower().strip()
        patterns = self.PATTERNS.get(type_key, [])
        findings = []
        for pat, label, severity in patterns:
            matches = re.findall(pat, text or "", re.IGNORECASE)
            if matches:
                findings.append(
                    {
                        "pattern": pat,
                        "label": label,
                        "severity": severity,
                        "match_count": len(matches),
                        "examples": matches[:3],
                    }
                )
        return findings
