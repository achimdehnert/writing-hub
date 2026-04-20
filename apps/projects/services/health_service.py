"""
DramaturgicHealthScore — ADR-157 Rev.1

Misst die VOLLSTÄNDIGKEIT DER PLANUNG, nicht die Qualität des Textes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from apps.authoring.defaults import DEFAULT_CONTENT_TYPE


@dataclass
class HealthCheck:
    label: str
    passed: bool
    message: str
    weight: int = 1


@dataclass
class DramaturgicHealthResult:
    score: int
    checks: list[HealthCheck] = field(default_factory=list)
    mvn_complete: bool = False

    @property
    def level(self) -> str:
        if self.score >= 80:
            return "solid"  # Struktur vollständig
        if self.score >= 50:
            return "developing"  # Kernstruktur vorhanden
        return "skeleton"  # Grundriss, MVN noch unvollständig

    @property
    def top_issues(self) -> list[HealthCheck]:
        return sorted(
            [c for c in self.checks if not c.passed],
            key=lambda c: -c.weight,
        )[:3]


NON_DRAMATIC_TYPES = ("essay", "nonfiction", "sachbuch")


def compute_dramaturgic_health(project) -> DramaturgicHealthResult:
    """
    Berechnet DramaturgicHealthScore für ein BookProject.

    score = Vollständigkeit der Planung (0–100).
    Für Essays/Sachbücher wird _compute_nondramatic_health() gerufen.
    """
    content_type = getattr(project, "content_type", DEFAULT_CONTENT_TYPE)
    if content_type in NON_DRAMATIC_TYPES:
        return _compute_nondramatic_health(project, content_type)

    checks: list[HealthCheck] = []

    # --- MVN-PFLICHTFELDER (Gewicht 3) ---
    checks.append(
        HealthCheck(
            label="Äußere Geschichte definiert",
            passed=bool(getattr(project, "outer_story", "").strip()),
            message="outer_story ist leer — Was passiert im Roman?",
            weight=3,
        )
    )
    checks.append(
        HealthCheck(
            label="Innere Geschichte definiert",
            passed=bool(getattr(project, "inner_story", "").strip()),
            message="inner_story ist leer — Was verändert sich in der Figur?",
            weight=3,
        )
    )
    checks.append(
        HealthCheck(
            label="Arc-Richtung gesetzt",
            passed=bool(getattr(project, "arc_direction", "")),
            message="arc_direction fehlt — positiv / negativ / flach?",
            weight=3,
        )
    )

    # --- PROTAGONIST (Gewicht 3) ---
    protagonists = list(project.character_links.filter(narrative_role="protagonist"))
    checks.append(
        HealthCheck(
            label="Protagonist definiert",
            passed=len(protagonists) >= 1,
            message="Kein Protagonist — narrative_role=protagonist nicht gesetzt.",
            weight=3,
        )
    )
    checks.append(
        HealthCheck(
            label="Protagonist-Anzahl plausibel",
            passed=len(protagonists) <= 2,
            message=f"{len(protagonists)} Protagonisten definiert — max. 2 (Dual-POV).",
            weight=1,
        )
    )

    protagonist = protagonists[0] if protagonists else None
    if protagonist:
        checks.append(
            HealthCheck(
                label="Protagonist: Want",
                passed=bool(protagonist.want.strip()),
                message="Protagonist.want leer — äußeres Ziel fehlt.",
                weight=3,
            )
        )
        checks.append(
            HealthCheck(
                label="Protagonist: Need",
                passed=bool(protagonist.need.strip()),
                message="Protagonist.need leer — innere Wahrheit fehlt.",
                weight=3,
            )
        )
        checks.append(
            HealthCheck(
                label="Protagonist: Flaw",
                passed=bool(protagonist.flaw.strip()),
                message="Protagonist.flaw leer — ohne Fehler kein Arc.",
                weight=3,
            )
        )
        if protagonist.want.strip() and protagonist.need.strip():
            checks.append(
                HealthCheck(
                    label="Want ≠ Need",
                    passed=protagonist.want.strip() != protagonist.need.strip(),
                    message="Want == Need — kein dramaturgischer Arc möglich.",
                    weight=3,
                )
            )

    # --- ANTAGONIST (Gewicht 2) ---
    antagonists = list(project.character_links.filter(narrative_role="antagonist"))
    checks.append(
        HealthCheck(
            label="Antagonist definiert",
            passed=len(antagonists) >= 1,
            message="Kein Antagonist — ohne Gegenkraft kein Konflikt.",
            weight=2,
        )
    )
    antagonist = antagonists[0] if antagonists else None
    if antagonist:
        checks.append(
            HealthCheck(
                label="Antagonisten-Logik",
                passed=bool(antagonist.antagonist_logic.strip()),
                message="antagonist_logic leer — warum glaubt er, das Richtige zu tun?",
                weight=2,
            )
        )
        checks.append(
            HealthCheck(
                label="Spiegel-Beziehung",
                passed=bool(antagonist.mirror_to_protagonist.strip()),
                message="mirror_to_protagonist leer — ohne Spiegel ist der Antagonist flach.",
                weight=2,
            )
        )
        if antagonist.antagonist_type not in ("inner_self", ""):
            checks.append(
                HealthCheck(
                    label="Informationsvorsprung",
                    passed=bool(antagonist.information_advantage.strip()),
                    message="information_advantage leer — Asymmetrie erzeugt Spannung.",
                    weight=1,
                )
            )

    # --- MAKROSTRUKTUR (Gewicht 2) ---
    checks.append(
        HealthCheck(
            label="Wendepunkte definiert",
            passed=project.turning_points.exists() if hasattr(project, "turning_points") else False,
            message="Keine ProjectTurningPoints — Makrostruktur fehlt.",
            weight=2,
        )
    )

    # --- THEMA (Gewicht 2) ---
    checks.append(
        HealthCheck(
            label="Thema definiert",
            passed=bool(getattr(project, "theme", None)),
            message="ProjectTheme fehlt — ohne Thema fehlt dem Roman Bedeutung.",
            weight=2,
        )
    )

    # --- B-STORY (Gewicht 1) ---
    checks.append(
        HealthCheck(
            label="B-Story definiert",
            passed=project.subplot_arcs.filter(story_label="b_story").exists()
            if hasattr(project, "subplot_arcs")
            else False,
            message="Keine B-Story — thematischer Spiegel fehlt.",
            weight=1,
        )
    )

    # --- ERZÄHLSTIMME (Gewicht 1) ---
    checks.append(
        HealthCheck(
            label="Erzählstimme definiert",
            passed=bool(getattr(project, "narrative_voice", None)),
            message="NarrativeVoice fehlt.",
            weight=1,
        )
    )

    # --- COMPARABLE TITLES / COMPS (ADR-159, Gewicht 1) ---
    try:
        comp_count = project.comparable_titles.count()
        checks.append(
            HealthCheck(
                label="Comparable Titles",
                passed=comp_count >= 2,
                message="Weniger als 2 Comps — für Verlagsanfrage unzureichend.",
                weight=1,
            )
        )
        if comp_count > 0:
            comps = list(project.comparable_titles.all())
            checks.append(
                HealthCheck(
                    label="Comps aktuell (< 5 Jahre)",
                    passed=not any(c.age_warning for c in comps),
                    message="Mindestens ein Comp ist älter als 5 Jahre — verlegerisch problematisch.",
                    weight=1,
                )
            )
    except Exception:
        pass

    # --- OFFENE RECHERCHE-FRAGEN (ADR-160, Gewicht 1) ---
    try:
        open_questions = project.research_notes.filter(is_open_question=True).count()
        checks.append(
            HealthCheck(
                label="Offene Recherche-Fragen",
                passed=open_questions == 0,
                message=f"{open_questions} offene Recherche-Fragen — vor Fertigstellung klären.",
                weight=1,
            )
        )
    except Exception:
        pass

    # --- GENRE-KONVENTIONEN (ADR-160, Gewicht 2 für 'required') ---
    try:
        from apps.projects.services.genre_service import check_genre_conventions

        for gc in check_genre_conventions(project):
            if gc["weight"] == "required":
                checks.append(
                    HealthCheck(
                        label=f"Genre-Konvention: {gc['label']}",
                        passed=gc["passed"],
                        message=gc["description"],
                        weight=2,
                    )
                )
    except Exception:
        pass

    total_weight = sum(c.weight for c in checks)
    earned_weight = sum(c.weight for c in checks if c.passed)
    score = int((earned_weight / total_weight) * 100) if total_weight else 0
    mvn_complete = all(c.passed for c in checks if c.weight == 3)

    return DramaturgicHealthResult(score=score, checks=checks, mvn_complete=mvn_complete)


def _compute_nondramatic_health(project, content_type: str) -> DramaturgicHealthResult:
    """Separater Health-Pfad für Essays und Sachbücher."""
    checks: list[HealthCheck] = []
    checks.append(
        HealthCheck(
            label="Kernthese / Äußere Geschichte",
            passed=bool(getattr(project, "outer_story", "").strip()),
            message="outer_story / Kernthese leer.",
            weight=3,
        )
    )
    checks.append(
        HealthCheck(
            label="Erzählstimme / Stil definiert",
            passed=bool(getattr(project, "narrative_voice", None)),
            message="NarrativeVoice fehlt.",
            weight=2,
        )
    )
    checks.append(
        HealthCheck(
            label="Outline vorhanden",
            passed=project.outline_versions.filter(is_active=True).exists(),
            message="Keine aktive Outline.",
            weight=2,
        )
    )
    total = sum(c.weight for c in checks)
    earned = sum(c.weight for c in checks if c.passed)
    score = int((earned / total) * 100) if total else 0
    return DramaturgicHealthResult(score=score, checks=checks, mvn_complete=True)
