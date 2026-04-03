"""
ChapterWriterHandler — writing-hub (ADR-083 Phase 3)

Portiert aus bfagent.writing_hub.handlers.chapter_writer_handler.
Aenderungen:
  - FK-Quellen: bfagent.BookProjects -> projects.BookProject (UUID)
  - FK-Quellen: bfagent.Characters   -> worlds.WorldCharacter
  - FK-Quellen: bfagent.Worlds       -> worlds.World
  - LLM: aifw.service.sync_completion (statt deprecated aifw.generate_text)
  - Event Bus: entfernt (nicht in writing-hub)
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from aifw.service import sync_completion
from aifw.schema import LLMResult

logger = logging.getLogger(__name__)


@dataclass
class ChapterContext:
    """Kontext fuer Kapitel-Generierung — alle relevanten Projektdaten."""

    project_id: str
    chapter_ref: str
    title: str = ""
    genre: str = ""
    premise: str = ""
    target_audience: str = ""
    content_type: str = "novel"
    citation_style: str = "APA"
    chapter_number: int = 1
    chapter_title: str = ""
    chapter_outline: str = ""
    chapter_beat: str = ""
    emotional_arc: str = ""
    target_word_count: int = 2000
    existing_content: str = ""
    prev_chapter_summary: str = ""
    next_chapter_outline: str = ""
    research_notes: str = ""
    characters: list[dict] = field(default_factory=list)
    worlds: list[dict] = field(default_factory=list)
    all_chapters_outline: list[dict] = field(default_factory=list)
    style_dna: dict | None = None

    @property
    def is_academic(self) -> bool:
        return self.content_type in ("academic", "scientific", "essay")

    def to_prompt_context(self) -> str:
        """Baut Kontext-String fuer LLM-Prompt."""
        parts = []

        if self.is_academic:
            return self._to_academic_context()

        parts.append("=" * 50)
        parts.append("BUCH-INFORMATIONEN")
        parts.append("=" * 50)
        parts.append(f"Titel: {self.title}")
        parts.append(f"Genre: {self.genre}")
        if self.premise:
            parts.append(f"Premise: {self.premise}")
        if self.target_audience:
            parts.append(f"Zielgruppe: {self.target_audience}")

        parts.append("")
        parts.append("=" * 50)
        parts.append(f"ZU SCHREIBENDES KAPITEL: {self.chapter_number} - {self.chapter_title}")
        parts.append("=" * 50)

        if self.chapter_outline:
            parts.append("\nKAPITEL-OUTLINE (WAS PASSIEREN SOLL):")
            parts.append(self.chapter_outline)
        else:
            parts.append("\nKein Outline vorhanden")

        if self.chapter_beat:
            parts.append(f"\nStory-Beat: {self.chapter_beat}")
        if self.emotional_arc:
            parts.append(f"Emotionaler Bogen: {self.emotional_arc}")
        parts.append(f"Ziel-Wortanzahl: ca. {self.target_word_count} Woerter")

        if self.prev_chapter_summary:
            parts.append("")
            parts.append("WAS BISHER GESCHAH:")
            parts.append(self.prev_chapter_summary[:600])

        if self.next_chapter_outline:
            parts.append("")
            parts.append("VORSCHAU NAECHSTES KAPITEL:")
            parts.append(self.next_chapter_outline[:200])

        if self.characters:
            parts.append("")
            parts.append("=" * 50)
            parts.append("CHARAKTERE")
            parts.append("=" * 50)
            for char in self.characters[:5]:
                name = char.get("name") or "Unbekannt"
                role = char.get("role") or "Nebenrolle"
                desc = (char.get("description") or "")[:200]
                motivation = (char.get("motivation") or "")[:150]
                parts.append(f"\n{name} ({role})")
                if desc:
                    parts.append(f"  Beschreibung: {desc}")
                if motivation:
                    parts.append(f"  Motivation: {motivation}")

        if self.worlds:
            parts.append("")
            parts.append("=" * 50)
            parts.append("SETTING & WELT")
            parts.append("=" * 50)
            for world in self.worlds[:2]:
                name = world.get("name") or "Unbekannt"
                desc = (world.get("description") or "")[:300]
                parts.append(f"\n{name}")
                if desc:
                    parts.append(f"  {desc}")

        if self.style_dna:
            parts.append("")
            parts.append("=" * 50)
            parts.append("AUTHOR STYLE DNA")
            parts.append("=" * 50)
            dna = self.style_dna
            if dna.get("name"):
                parts.append(f"Stilprofil: {dna['name']}")
            if dna.get("signature_moves"):
                parts.append("\nSignature Moves:")
                for move in dna["signature_moves"][:5]:
                    parts.append(f"  - {move}")
            if dna.get("do_list"):
                parts.append("\nDO:")
                for item in dna["do_list"][:8]:
                    parts.append(f"  - {item}")
            if dna.get("dont_list"):
                parts.append("\nDONT:")
                for item in dna["dont_list"][:5]:
                    parts.append(f"  - {item}")
            if dna.get("taboo_list"):
                parts.append("\nTABU-WOERTER:")
                parts.append(f"  {', '.join(dna['taboo_list'][:10])}")

        parts.append("")
        parts.append("=" * 50)
        return "\n".join(parts)

    def _to_academic_context(self) -> str:
        """Akademischer/wissenschaftlicher Kontext — kein Fiction-Vokabular."""
        parts = []
        parts.append("=" * 50)
        parts.append("AUFSATZ-INFORMATIONEN")
        parts.append("=" * 50)
        parts.append(f"Titel: {self.title}")
        if self.premise:
            parts.append(f"Forschungsfrage / These: {self.premise}")
        if self.target_audience:
            parts.append(f"Zielgruppe: {self.target_audience}")
        parts.append(f"Zitierstil: {self.citation_style}")

        parts.append("")
        parts.append("=" * 50)
        parts.append(f"ZU SCHREIBENDES KAPITEL: {self.chapter_number} - {self.chapter_title}")
        parts.append("=" * 50)

        if self.chapter_outline:
            parts.append("\nKAPITEL-INHALT (WAS BEHANDELT WERDEN SOLL):")
            parts.append(self.chapter_outline)
        else:
            parts.append("\nKein Outline vorhanden")

        if self.chapter_beat:
            parts.append(f"\nStruktur-Funktion: {self.chapter_beat}")
        parts.append(f"Ziel-Wortanzahl: ca. {self.target_word_count} Woerter")

        if self.prev_chapter_summary:
            parts.append("")
            parts.append("VORHERIGES KAPITEL (ZUSAMMENFASSUNG):")
            parts.append(self.prev_chapter_summary[:600])

        if self.research_notes:
            parts.append("")
            parts.append("=" * 50)
            parts.append("RECHERCHE-ERGEBNISSE & QUELLEN")
            parts.append("=" * 50)
            parts.append(self.research_notes[:3000])

        if self.style_dna:
            parts.append("")
            parts.append("=" * 50)
            parts.append("SCHREIBSTIL-VORGABEN")
            parts.append("=" * 50)
            dna = self.style_dna
            if dna.get("do_list"):
                parts.append("\nDO:")
                for item in dna["do_list"][:8]:
                    parts.append(f"  - {item}")
            if dna.get("dont_list"):
                parts.append("\nDONT:")
                for item in dna["dont_list"][:5]:
                    parts.append(f"  - {item}")

        parts.append("")
        parts.append("=" * 50)
        return "\n".join(parts)

    @classmethod
    def from_project(cls, project_id: str, chapter_ref: str) -> "ChapterContext":
        """
        Erstellt ChapterContext aus writing-hub Modellen.
        Charaktere und Welten kommen aus worlds.WorldCharacter / worlds.World.
        """
        from apps.projects.models import BookProject

        try:
            project = BookProject.objects.get(pk=project_id)
        except BookProject.DoesNotExist:
            return cls(project_id=project_id, chapter_ref=chapter_ref)

        characters: list = []
        worlds: list = []
        try:
            from apps.worlds.models import ProjectCharacterLink, ProjectWorldLink
            for link in ProjectWorldLink.objects.filter(project=project)[:3]:
                w = link.get_world()
                if w:
                    worlds.append({"name": getattr(w, "name", ""), "description": getattr(w, "description", "")})
            for link in ProjectCharacterLink.objects.filter(project=project)[:10]:
                c = link.get_character()
                if c:
                    characters.append({"name": getattr(c, "name", ""), "role": link.narrative_role or ""})
        except Exception as exc:
            logger.debug("World/character context not available: %s", exc)

        style_dna = None
        try:
            from apps.authoring.models import AuthorStyleDNA
            dna_obj = AuthorStyleDNA.objects.filter(
                author=project.owner, is_primary=True
            ).first()
            if dna_obj:
                style_dna = {
                    "name": dna_obj.name,
                    "signature_moves": dna_obj.signature_moves or [],
                    "do_list": dna_obj.do_list or [],
                    "dont_list": dna_obj.dont_list or [],
                    "taboo_list": dna_obj.taboo_list or [],
                }
        except Exception as exc:
            logger.warning("Could not load Style DNA: %s", exc)

        return cls(
            project_id=project_id,
            chapter_ref=chapter_ref,
            title=project.title or "",
            genre=project.genre or "",
            premise=getattr(project, "premise", "") or "",
            target_audience=project.target_audience or "",
            characters=characters,
            worlds=worlds,
            style_dna=style_dna,
        )


SYSTEM_WRITE = """Du bist ein preisgekroenter Romanautor, spezialisiert auf fesselnde Erzaehlungen.

DEINE AUFGABE: Schreibe ein vollstaendiges Kapitel basierend auf dem gegebenen Outline und Kontext.

WICHTIG:
- Schreibe das Kapitel KOMPLETT NEU basierend auf dem Outline
- Verwende die Charaktere und das Setting aus dem Kontext
- Schreibe auf Deutsch, lebendig und literarisch hochwertig
- KEINE Metakommentare — NUR den Romantext!"""

SYSTEM_WRITE_ACADEMIC = """Du bist ein erfahrener Wissenschaftler und Fachautor.

DEINE AUFGABE: Schreibe ein vollstaendiges Kapitel eines wissenschaftlichen Aufsatzes.

WICHTIG:
- Schreibe in einem sachlichen, praezisen und wissenschaftlichen Stil
- KEINE fiktiven Charaktere, Dialoge oder narrativen Elemente
- Verwende Fachterminologie angemessen fuer die Zielgruppe
- Zitiere relevante Quellen im angegebenen Zitierstil (z.B. APA: (Autor, Jahr))
- Gliedere mit Zwischenueberschriften wo sinnvoll
- Argumentiere logisch und belege Aussagen mit Quellen
- KEINE Metakommentare — NUR den Fachtext!"""

USER_WRITE = """# KAPITEL SCHREIBEN

## STORY-KONTEXT:
{context}

## DEINE AUFGABE:
Schreibe das vollstaendige Kapitel ({target_words} Woerter).

BEGINNE JETZT MIT DEM KAPITELTEXT:"""

USER_WRITE_ACADEMIC = """# KAPITEL SCHREIBEN

## AUFSATZ-KONTEXT:
{context}

## DEINE AUFGABE:
Schreibe das vollstaendige Kapitel ({target_words} Woerter).
- Verwende einen wissenschaftlichen Schreibstil
- Zitiere die angegebenen Quellen im Text
- Verwende KEINE fiktiven Personen, Dialoge oder Erzaehlungen
- Gib konkrete Fakten, Definitionen und Argumente

BEGINNE JETZT MIT DEM KAPITELTEXT:"""


class ChapterWriterHandler:
    """
    Handler fuer Kapitel-Generierung via LLM.

    Methoden:
      write_chapter(context)              — einzelnes Kapitel
      refine_chapter(context, instruction) — Kapitel verfeinern
      continue_chapter(context)           — Kapitel fortsetzen
      generate_summary(content)           — Zusammenfassung
    """

    MAX_TOKENS = 4096

    def write_chapter(self, context: ChapterContext) -> dict[str, Any]:
        """Schreibt ein vollstaendiges Kapitel."""
        words_per_chunk = int(self.MAX_TOKENS / 1.5)
        if context.target_word_count > words_per_chunk:
            return self._write_chunked(context)
        return self._write_single(context)

    def _select_prompts(self, context: ChapterContext) -> tuple[str, str]:
        """Select system/user prompts based on content type."""
        if context.is_academic:
            return SYSTEM_WRITE_ACADEMIC, USER_WRITE_ACADEMIC
        return SYSTEM_WRITE, USER_WRITE

    def _write_single(self, context: ChapterContext) -> dict[str, Any]:
        context_str = context.to_prompt_context()
        estimated_tokens = int(context.target_word_count * 1.5)
        max_tokens = min(max(estimated_tokens, 2000), self.MAX_TOKENS)
        sys_prompt, usr_prompt = self._select_prompts(context)

        messages = [
            {"role": "system", "content": sys_prompt},
            {
                "role": "user",
                "content": usr_prompt.format(
                    context=context_str,
                    target_words=context.target_word_count,
                ),
            },
        ]
        try:
            result: LLMResult = sync_completion(
                "chapter_generation", messages, max_tokens=max_tokens
            )
        except Exception as exc:
            logger.error("_write_single failed: %s", exc)
            return {"success": False, "error": str(exc)}

        if not result.success:
            return {"success": False, "error": result.error}

        content = result.content.strip()
        return {
            "success": True,
            "content": content,
            "word_count": len(content.split()),
            "latency_ms": result.latency_ms,
        }

    def _write_chunked(self, context: ChapterContext) -> dict[str, Any]:
        words_per_chunk = int(self.MAX_TOKENS / 1.5) - 200
        num_chunks = (context.target_word_count // words_per_chunk) + 1
        context_str = context.to_prompt_context()
        all_content: list[str] = []
        total_latency = 0

        sys_prompt, _ = self._select_prompts(context)

        for chunk_num in range(num_chunks):
            is_first = chunk_num == 0
            is_last = chunk_num == num_chunks - 1

            if is_first:
                chunk_prompt = (
                    f"Schreibe den ANFANG von Kapitel {context.chapter_number}.\n\n"
                    f"{context_str}\n\nSchreibe etwa {words_per_chunk} Woerter. "
                    f"Teil 1 von {num_chunks}. ENDE NICHT mit dem Kapitel."
                )
            elif is_last:
                prev = "\n\n".join(all_content[-2:])[-3000:]
                chunk_prompt = (
                    f"Schreibe das ENDE von Kapitel {context.chapter_number}.\n\n"
                    f"BISHERIGER INHALT:\n{prev}\n\nSchreibe etwa {words_per_chunk} Woerter. "
                    f"Letzter Teil ({chunk_num + 1} von {num_chunks})."
                )
            else:
                prev = "\n\n".join(all_content[-2:])[-3000:]
                chunk_prompt = (
                    f"Setze Kapitel {context.chapter_number} fort.\n\n"
                    f"BISHERIGER INHALT:\n{prev}\n\nSchreibe etwa {words_per_chunk} Woerter. "
                    f"Teil {chunk_num + 1} von {num_chunks}. ENDE NICHT."
                )

            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": chunk_prompt},
            ]
            try:
                result: LLMResult = sync_completion(
                    "chapter_generation", messages, max_tokens=self.MAX_TOKENS
                )
            except Exception as exc:
                logger.error("Chunk %d error: %s", chunk_num + 1, exc)
                if all_content:
                    partial = "\n\n".join(all_content)
                    return {
                        "success": True,
                        "content": partial + f"\n\n[Abgebrochen nach Teil {chunk_num}: {exc}]",
                        "word_count": len(partial.split()),
                        "latency_ms": total_latency,
                    }
                return {"success": False, "error": str(exc)}

            if not result.success:
                if all_content:
                    partial = "\n\n".join(all_content)
                    return {
                        "success": True,
                        "content": partial + "\n\n[Abgebrochen]",
                        "word_count": len(partial.split()),
                        "latency_ms": total_latency,
                    }
                return {"success": False, "error": result.error}

            all_content.append(result.content.strip())
            total_latency += result.latency_ms or 0

        full_content = "\n\n".join(all_content)
        return {
            "success": True,
            "content": full_content,
            "word_count": len(full_content.split()),
            "latency_ms": total_latency,
        }

    def refine_chapter(self, context: ChapterContext, instruction: str) -> dict[str, Any]:
        """Verfeinert bestehenden Kapiteltext."""
        if not context.existing_content:
            return {"success": False, "error": "Kein bestehender Inhalt zum Verfeinern"}

        messages = [
            {
                "role": "system",
                "content": "Du bist ein erfahrener Lektor. Verbessere den Text gemaess der Anweisung. NUR den Text ausgeben.",
            },
            {
                "role": "user",
                "content": (
                    f"## KONTEXT:\n{context.to_prompt_context()}\n\n"
                    f"## AKTUELLER TEXT:\n{context.existing_content}\n\n"
                    f"## AUFTRAG:\n{instruction}\n\nVERBESSERTER TEXT:"
                ),
            },
        ]
        try:
            result: LLMResult = sync_completion("chapter_generation", messages, max_tokens=8000)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

        if not result.success:
            return {"success": False, "error": result.error}

        content = result.content.strip()
        return {
            "success": True,
            "content": content,
            "word_count": len(content.split()),
            "latency_ms": result.latency_ms,
        }

    def continue_chapter(self, context: ChapterContext) -> dict[str, Any]:
        """Setzt ein unvollstaendiges Kapitel fort."""
        if not context.existing_content:
            return self.write_chapter(context)

        current_words = len(context.existing_content.split())
        if current_words >= context.target_word_count * 0.9:
            return {
                "success": True,
                "content": context.existing_content,
                "word_count": current_words,
                "message": "Kapitel bereits vollstaendig",
            }

        remaining = context.target_word_count - current_words
        messages = [
            {
                "role": "system",
                "content": "Du setzt einen begonnenen Text nahtlos fort. NUR die Fortsetzung ausgeben.",
            },
            {
                "role": "user",
                "content": (
                    f"## KONTEXT:\n{context.to_prompt_context()}\n\n"
                    f"## BISHERIGER TEXT:\n{context.existing_content}\n\n"
                    f"Setze NAHTLOS fort ({remaining} Woerter):\nFORTSETZUNG:"
                ),
            },
        ]
        try:
            result: LLMResult = sync_completion(
                "chapter_generation",
                messages,
                max_tokens=min(max(int(remaining * 1.5), 1000), self.MAX_TOKENS),
            )
        except Exception as exc:
            return {"success": False, "error": str(exc)}

        if not result.success:
            return {"success": False, "error": result.error}

        continuation = result.content.strip()
        full_content = context.existing_content + "\n\n" + continuation
        return {
            "success": True,
            "content": full_content,
            "word_count": len(full_content.split()),
            "latency_ms": result.latency_ms,
        }

    def generate_summary(self, content: str) -> str:
        """Generiert eine kurze Zusammenfassung fuer Kontinuitaets-Kontext."""
        if not content or len(content) < 100:
            return ""

        messages = [
            {
                "role": "system",
                "content": "Fasse den Text in 2-3 Saetzen zusammen. NUR die Zusammenfassung.",
            },
            {"role": "user", "content": content[:3000] + "\n\nZUSAMMENFASSUNG:"},
        ]
        try:
            result: LLMResult = sync_completion("chapter_generation", messages, max_tokens=200)
            if result.success:
                return result.content.strip()
        except Exception as exc:
            logger.warning("Summary generation failed: %s", exc)

        return content[:200] + "..."


chapter_writer_handler = ChapterWriterHandler()
