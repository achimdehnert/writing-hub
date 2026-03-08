"""
ChapterWriterHandler — writing-hub (ADR-083 Phase 3)

Portiert aus bfagent.writing_hub.handlers.chapter_writer_handler.
Änderungen:
  - FK-Quellen: bfagent.BookProjects → projects.BookProject (UUID)
  - FK-Quellen: bfagent.Characters   → worlds.WorldCharacter
  - FK-Quellen: bfagent.Worlds       → worlds.World
  - LLM: bfagent.services.llm_client → aifw direkt (Action Code: chapter_generation)
  - Event Bus: entfernt (nicht in writing-hub)
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ChapterContext:
    """Kontext für Kapitel-Generierung — alle relevanten Projektdaten."""

    project_id: str
    chapter_ref: str
    title: str = ""
    genre: str = ""
    premise: str = ""
    target_audience: str = ""
    chapter_number: int = 1
    chapter_title: str = ""
    chapter_outline: str = ""
    chapter_beat: str = ""
    emotional_arc: str = ""
    target_word_count: int = 2000
    existing_content: str = ""
    prev_chapter_summary: str = ""
    next_chapter_outline: str = ""
    characters: list[dict] = field(default_factory=list)
    worlds: list[dict] = field(default_factory=list)
    all_chapters_outline: list[dict] = field(default_factory=list)
    style_dna: dict | None = None

    def to_prompt_context(self) -> str:
        """Baut Kontext-String für LLM-Prompt."""
        parts = []

        parts.append("=" * 50)
        parts.append("📚 BUCH-INFORMATIONEN")
        parts.append("=" * 50)
        parts.append(f"**Titel:** {self.title}")
        parts.append(f"**Genre:** {self.genre}")
        if self.premise:
            parts.append(f"**Premise:** {self.premise}")
        if self.target_audience:
            parts.append(f"**Zielgruppe:** {self.target_audience}")

        parts.append("")
        parts.append("=" * 50)
        parts.append(f"📖 ZU SCHREIBENDES KAPITEL: {self.chapter_number} - {self.chapter_title}")
        parts.append("=" * 50)

        if self.chapter_outline:
            parts.append("\n🎯 **KAPITEL-OUTLINE (WAS PASSIEREN SOLL):**")
            parts.append(self.chapter_outline)
        else:
            parts.append("\n⚠️ Kein Outline vorhanden")

        if self.chapter_beat:
            parts.append(f"\n**Story-Beat:** {self.chapter_beat}")
        if self.emotional_arc:
            parts.append(f"**Emotionaler Bogen:** {self.emotional_arc}")
        parts.append(f"**Ziel-Wortanzahl:** ca. {self.target_word_count} Wörter")

        if self.prev_chapter_summary:
            parts.append("")
            parts.append("📝 **WAS BISHER GESCHAH:**")
            parts.append(self.prev_chapter_summary[:600])

        if self.next_chapter_outline:
            parts.append("")
            parts.append("➡️ **VORSCHAU NÄCHSTES KAPITEL:**")
            parts.append(self.next_chapter_outline[:200])

        if self.characters:
            parts.append("")
            parts.append("=" * 50)
            parts.append("👥 CHARAKTERE")
            parts.append("=" * 50)
            for char in self.characters[:5]:
                name = char.get("name") or "Unbekannt"
                role = char.get("role") or "Nebenrolle"
                desc = (char.get("description") or "")[:200]
                motivation = (char.get("motivation") or "")[:150]
                parts.append(f"\n**{name}** ({role})")
                if desc:
                    parts.append(f"  Beschreibung: {desc}")
                if motivation:
                    parts.append(f"  Motivation: {motivation}")

        if self.worlds:
            parts.append("")
            parts.append("=" * 50)
            parts.append("🌍 SETTING & WELT")
            parts.append("=" * 50)
            for world in self.worlds[:2]:
                name = world.get("name") or "Unbekannt"
                desc = (world.get("description") or "")[:300]
                parts.append(f"\n**{name}**")
                if desc:
                    parts.append(f"  {desc}")

        if self.style_dna:
            parts.append("")
            parts.append("=" * 50)
            parts.append("✨ AUTHOR STYLE DNA (WICHTIG!)")
            parts.append("=" * 50)
            dna = self.style_dna
            if dna.get("name"):
                parts.append(f"**Stilprofil:** {dna['name']}")
            if dna.get("signature_moves"):
                parts.append("\n🎯 **Signature Moves:**")
                for move in dna["signature_moves"][:5]:
                    parts.append(f"  • {move}")
            if dna.get("do_list"):
                parts.append("\n✅ **DO:**")
                for item in dna["do_list"][:8]:
                    parts.append(f"  • {item}")
            if dna.get("dont_list"):
                parts.append("\n❌ **DON'T:**")
                for item in dna["dont_list"][:5]:
                    parts.append(f"  • {item}")
            if dna.get("taboo_list"):
                parts.append("\n🚫 **TABU-WÖRTER:**")
                parts.append(f"  {', '.join(dna['taboo_list'][:10])}")

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
        from apps.worlds.models import World, WorldCharacter

        try:
            project = BookProject.objects.get(pk=project_id)
        except BookProject.DoesNotExist:
            return cls(project_id=project_id, chapter_ref=chapter_ref)

        characters = list(
            WorldCharacter.objects.filter(
                world__project_worlds__project=project
            ).values("name", "role", "description", "motivation", "personality")[:10]
        )

        worlds = list(
            World.objects.filter(
                project_worlds__project=project
            ).values("name", "description", "setting_era", "culture")[:3]
        )

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
            premise=project.premise or "",
            target_audience=project.target_audience or "",
            characters=characters,
            worlds=worlds,
            style_dna=style_dna,
        )


SYSTEM_WRITE = """Du bist ein preisgekrönter Romanautor, spezialisiert auf fesselnde Erzählungen.

DEINE AUFGABE: Schreibe ein vollständiges Kapitel basierend auf dem gegebenen Outline und Kontext.

WICHTIG:
- Schreibe das Kapitel KOMPLETT NEU basierend auf dem Outline
- Verwende die Charaktere und das Setting aus dem Kontext
- Schreibe auf Deutsch, lebendig und literarisch hochwertig
- KEINE Metakommentare — NUR den Romantext!"""

USER_WRITE = """# KAPITEL SCHREIBEN

## STORY-KONTEXT:
{context}

## DEINE AUFGABE:
Schreibe das vollständige Kapitel ({target_words} Wörter).

BEGINNE JETZT MIT DEM KAPITELTEXT:"""


class ChapterWriterHandler:
    """
    Handler für Kapitel-Generierung via LLM.

    Methoden:
      write_chapter(context)              — einzelnes Kapitel
      refine_chapter(context, instruction) — Kapitel verfeinern
      continue_chapter(context)           — Kapitel fortsetzen
      generate_summary(content)           — Zusammenfassung
    """

    MAX_TOKENS = 4096

    def write_chapter(self, context: ChapterContext) -> dict[str, Any]:
        """Schreibt ein vollständiges Kapitel."""
        words_per_chunk = int(self.MAX_TOKENS / 1.5)
        if context.target_word_count > words_per_chunk:
            return self._write_chunked(context)
        return self._write_single(context)

    def _write_single(self, context: ChapterContext) -> dict[str, Any]:
        from aifw import generate_text

        context_str = context.to_prompt_context()
        estimated_tokens = int(context.target_word_count * 1.5)
        max_tokens = min(max(estimated_tokens, 2000), self.MAX_TOKENS)

        try:
            response = generate_text(
                system=SYSTEM_WRITE,
                prompt=USER_WRITE.format(
                    context=context_str,
                    target_words=context.target_word_count,
                ),
                temperature=0.8,
                max_tokens=max_tokens,
                action_code="chapter_generation",
            )
        except Exception as exc:
            logger.error("_write_single failed: %s", exc)
            return {"success": False, "error": str(exc)}

        if not response or not response.get("ok"):
            return {"success": False, "error": (response or {}).get("error", "LLM error")}

        content = response.get("text", "").strip()
        return {
            "success": True,
            "content": content,
            "word_count": len(content.split()),
            "latency_ms": response.get("latency_ms"),
        }

    def _write_chunked(self, context: ChapterContext) -> dict[str, Any]:
        from aifw import generate_text

        words_per_chunk = int(self.MAX_TOKENS / 1.5) - 200
        num_chunks = (context.target_word_count // words_per_chunk) + 1
        context_str = context.to_prompt_context()
        all_content: list[str] = []
        total_latency = 0

        for chunk_num in range(num_chunks):
            is_first = chunk_num == 0
            is_last = chunk_num == num_chunks - 1

            if is_first:
                chunk_prompt = (
                    f"Schreibe den ANFANG von Kapitel {context.chapter_number}.\n\n"
                    f"{context_str}\n\nSchreibe etwa {words_per_chunk} Wörter. "
                    f"Teil 1 von {num_chunks}. ENDE NICHT mit dem Kapitel."
                )
            elif is_last:
                prev = "\n\n".join(all_content[-2:])[-3000:]
                chunk_prompt = (
                    f"Schreibe das ENDE von Kapitel {context.chapter_number}.\n\n"
                    f"BISHERIGER INHALT:\n{prev}\n\nSchreibe etwa {words_per_chunk} Wörter. "
                    f"Letzter Teil ({chunk_num + 1} von {num_chunks})."
                )
            else:
                prev = "\n\n".join(all_content[-2:])[-3000:]
                chunk_prompt = (
                    f"Setze Kapitel {context.chapter_number} fort.\n\n"
                    f"BISHERIGER INHALT:\n{prev}\n\nSchreibe etwa {words_per_chunk} Wörter. "
                    f"Teil {chunk_num + 1} von {num_chunks}. ENDE NICHT."
                )

            try:
                response = generate_text(
                    system=SYSTEM_WRITE,
                    prompt=chunk_prompt,
                    temperature=0.8,
                    max_tokens=self.MAX_TOKENS,
                    action_code="chapter_generation",
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

            if not response or not response.get("ok"):
                if all_content:
                    partial = "\n\n".join(all_content)
                    return {
                        "success": True,
                        "content": partial + "\n\n[Abgebrochen]",
                        "word_count": len(partial.split()),
                        "latency_ms": total_latency,
                    }
                return {"success": False, "error": "LLM error"}

            all_content.append(response.get("text", "").strip())
            total_latency += response.get("latency_ms", 0)

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

        from aifw import generate_text

        try:
            response = generate_text(
                system="Du bist ein erfahrener Lektor. Verbessere den Text gemäß der Anweisung. NUR den Text ausgeben.",
                prompt=(
                    f"## KONTEXT:\n{context.to_prompt_context()}\n\n"
                    f"## AKTUELLER TEXT:\n{context.existing_content}\n\n"
                    f"## AUFTRAG:\n{instruction}\n\nVERBESSERTER TEXT:"
                ),
                temperature=0.7,
                max_tokens=8000,
                action_code="chapter_generation",
            )
        except Exception as exc:
            return {"success": False, "error": str(exc)}

        if not response or not response.get("ok"):
            return {"success": False, "error": (response or {}).get("error", "LLM error")}

        content = response.get("text", "").strip()
        return {
            "success": True,
            "content": content,
            "word_count": len(content.split()),
            "latency_ms": response.get("latency_ms"),
        }

    def continue_chapter(self, context: ChapterContext) -> dict[str, Any]:
        """Setzt ein unvollständiges Kapitel fort."""
        if not context.existing_content:
            return self.write_chapter(context)

        current_words = len(context.existing_content.split())
        if current_words >= context.target_word_count * 0.9:
            return {
                "success": True,
                "content": context.existing_content,
                "word_count": current_words,
                "message": "Kapitel bereits vollständig",
            }

        from aifw import generate_text

        remaining = context.target_word_count - current_words
        try:
            response = generate_text(
                system="Du setzt einen begonnenen Text nahtlos fort. NUR die Fortsetzung ausgeben.",
                prompt=(
                    f"## KONTEXT:\n{context.to_prompt_context()}\n\n"
                    f"## BISHERIGER TEXT:\n{context.existing_content}\n\n"
                    f"Setze NAHTLOS fort ({remaining} Wörter):\nFORTSETZUNG:"
                ),
                temperature=0.8,
                max_tokens=min(max(int(remaining * 1.5), 1000), self.MAX_TOKENS),
                action_code="chapter_generation",
            )
        except Exception as exc:
            return {"success": False, "error": str(exc)}

        if not response or not response.get("ok"):
            return {"success": False, "error": (response or {}).get("error", "LLM error")}

        continuation = response.get("text", "").strip()
        full_content = context.existing_content + "\n\n" + continuation
        return {
            "success": True,
            "content": full_content,
            "word_count": len(full_content.split()),
        }

    def generate_summary(self, content: str) -> str:
        """Generiert eine kurze Zusammenfassung für Kontinuitäts-Kontext."""
        if not content or len(content) < 100:
            return ""

        from aifw import generate_text

        try:
            response = generate_text(
                system="Fasse den Text in 2-3 Sätzen zusammen. NUR die Zusammenfassung.",
                prompt=content[:3000] + "\n\nZUSAMMENFASSUNG:",
                temperature=0.3,
                max_tokens=200,
                action_code="chapter_generation",
            )
            if response and response.get("ok"):
                return response.get("text", "").strip()
        except Exception as exc:
            logger.warning("Summary generation failed: %s", exc)

        return content[:200] + "..."


chapter_writer_handler = ChapterWriterHandler()
