"""
ChapterWriterHandler — writing-hub (ADR-083 Phase 3)

Portiert aus bfagent.writing_hub.handlers.chapter_writer_handler.
Aenderungen:
  - FK-Quellen: bfagent.BookProjects -> projects.BookProject (UUID)
  - FK-Quellen: bfagent.Characters   -> worlds.WorldCharacter
  - FK-Quellen: bfagent.Worlds       -> worlds.World
  - LLM: LLMRouter (aifw-basiert, ADR-095) — kein direkter aifw-Zugriff
  - Event Bus: entfernt (nicht in writing-hub)
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from apps.authoring.defaults import (
    CHAR_DESC_MAX_CHARS,
    CHAR_MOTIVATION_MAX_CHARS,
    CHUNK_CONTEXT_WINDOW,
    CHUNK_MAX_CONTINUATIONS,
    CHUNK_TARGET_RATIO,
    DEFAULT_CITATION_STYLE,
    DEFAULT_CONTENT_TYPE,
    DEFAULT_TARGET_WORD_COUNT,
    MAX_CHARACTERS_IN_PROMPT,
    MAX_STYLE_DO_ITEMS,
    MAX_STYLE_DONT_ITEMS,
    MAX_STYLE_SIGNATURE_MOVES,
    MAX_STYLE_TABOO_ITEMS,
    MAX_TOKENS_REFINE,
    MAX_TOKENS_WRITE,
    MAX_WORLDS_IN_PROMPT,
    MIN_TOKENS_WRITE,
    NEXT_CHAPTER_OUTLINE_MAX_CHARS,
    PREV_CHAPTER_SUMMARY_MAX_CHARS,
    RESEARCH_NOTES_MAX_CHARS,
    STYLE_PROMPT_MAX_CHARS,
    WORLD_ATMOSPHERE_MAX_CHARS,
    WORLD_DESC_MAX_CHARS,
)
from apps.core.prompt_utils import render_prompt
from apps.authoring.services.chapter_production_service import _strip_chapter_heading
from apps.authoring.services.llm_router import LLMRouter, LLMRoutingError

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
    content_type: str = DEFAULT_CONTENT_TYPE
    citation_style: str = DEFAULT_CITATION_STYLE
    chapter_number: int = 1
    chapter_title: str = ""
    chapter_outline: str = ""
    chapter_beat: str = ""
    emotional_arc: str = ""
    target_word_count: int = DEFAULT_TARGET_WORD_COUNT
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
            parts.append(self.prev_chapter_summary[:PREV_CHAPTER_SUMMARY_MAX_CHARS])

        if self.next_chapter_outline:
            parts.append("")
            parts.append("VORSCHAU NAECHSTES KAPITEL:")
            parts.append(self.next_chapter_outline[:NEXT_CHAPTER_OUTLINE_MAX_CHARS])

        if self.characters:
            parts.append("")
            parts.append("=" * 50)
            parts.append("CHARAKTERE")
            parts.append("=" * 50)
            for char in self.characters[:MAX_CHARACTERS_IN_PROMPT]:
                name = char.get("name") or "Unbekannt"
                role = char.get("role") or "Nebenrolle"
                desc = (char.get("description") or "")[:CHAR_DESC_MAX_CHARS]
                motivation = (char.get("motivation") or "")[:CHAR_MOTIVATION_MAX_CHARS]
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
            for world in self.worlds[:MAX_WORLDS_IN_PROMPT]:
                name = world.get("name") or "Unbekannt"
                desc = (world.get("description") or "")[:WORLD_DESC_MAX_CHARS]
                atmosphere = (world.get("atmosphere") or "")[:WORLD_ATMOSPHERE_MAX_CHARS]
                parts.append(f"\n{name}")
                if desc:
                    parts.append(f"  {desc}")
                if atmosphere:
                    parts.append(f"  Atmosphaere: {atmosphere}")

        if self.style_dna:
            parts.append("")
            parts.append("=" * 50)
            parts.append("AUTHOR STYLE DNA")
            parts.append("=" * 50)
            dna = self.style_dna
            if dna.get("name"):
                parts.append(f"Stilprofil: {dna['name']}")
            if dna.get("style_prompt"):
                parts.append(f"\nStil-Anweisungen:\n{dna['style_prompt'][:STYLE_PROMPT_MAX_CHARS]}")
            if dna.get("signature_moves"):
                parts.append("\nSignature Moves:")
                for move in dna["signature_moves"][:MAX_STYLE_SIGNATURE_MOVES]:
                    parts.append(f"  - {move}")
            if dna.get("do_list"):
                parts.append("\nDO:")
                for item in dna["do_list"][:MAX_STYLE_DO_ITEMS]:
                    parts.append(f"  - {item}")
            if dna.get("dont_list"):
                parts.append("\nDONT:")
                for item in dna["dont_list"][:MAX_STYLE_DONT_ITEMS]:
                    parts.append(f"  - {item}")
            if dna.get("taboo_list"):
                parts.append("\nTABU-WOERTER:")
                parts.append(f"  {', '.join(dna['taboo_list'][:MAX_STYLE_TABOO_ITEMS])}")

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
            parts.append(self.prev_chapter_summary[:PREV_CHAPTER_SUMMARY_MAX_CHARS])

        if self.research_notes:
            parts.append("")
            parts.append("=" * 50)
            parts.append("RECHERCHE-ERGEBNISSE & QUELLEN")
            parts.append("=" * 50)
            parts.append(self.research_notes[:RESEARCH_NOTES_MAX_CHARS])

        if self.style_dna:
            parts.append("")
            parts.append("=" * 50)
            parts.append("SCHREIBSTIL-VORGABEN")
            parts.append("=" * 50)
            dna = self.style_dna
            if dna.get("style_prompt"):
                parts.append(f"\nStil-Anweisungen:\n{dna['style_prompt'][:STYLE_PROMPT_MAX_CHARS]}")
            if dna.get("do_list"):
                parts.append("\nDO:")
                for item in dna["do_list"][:MAX_STYLE_DO_ITEMS]:
                    parts.append(f"  - {item}")
            if dna.get("dont_list"):
                parts.append("\nDONT:")
                for item in dna["dont_list"][:MAX_STYLE_DONT_ITEMS]:
                    parts.append(f"  - {item}")
            if dna.get("taboo_list"):
                parts.append("\nTABU-WOERTER:")
                parts.append(f"  {', '.join(dna['taboo_list'][:MAX_STYLE_TABOO_ITEMS])}")

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
                    worlds.append({
                        "name": getattr(w, "name", ""),
                        "description": getattr(w, "description", ""),
                        "atmosphere": getattr(w, "atmosphere", ""),
                    })
            for link in ProjectCharacterLink.objects.filter(project=project)[:10]:
                c = link.get_character()
                if c:
                    characters.append({
                        "name": getattr(c, "name", ""),
                        "role": link.narrative_role or getattr(c, "role", ""),
                        "description": getattr(c, "description", "") or getattr(c, "backstory", ""),
                        "motivation": getattr(c, "motivation", ""),
                    })
        except Exception as exc:
            logger.debug("World/character context not available: %s", exc)

        # WritingStyle vom Projekt (primaer) -> AuthorStyleDNA (fallback)
        style_dna = None
        try:
            ws = project.writing_style
            if ws:
                style_dna = {
                    "name": ws.name,
                    "signature_moves": ws.signature_moves or [],
                    "do_list": ws.do_list or [],
                    "dont_list": ws.dont_list or [],
                    "taboo_list": ws.taboo_list or [],
                }
                if ws.style_prompt:
                    style_dna["style_prompt"] = ws.style_prompt
        except Exception:
            pass

        if not style_dna:
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


_TPL_REFINE = "authoring/chapter_refine"
_TPL_CONTINUE = "authoring/chapter_continue"
_TPL_SUMMARY = "authoring/chapter_summary"
_DEFAULT_WRITE_TPL = "authoring/chapter_write_default"


class ChapterWriterHandler:
    """
    Handler fuer Kapitel-Generierung via LLM.

    Methoden:
      write_chapter(context)              — einzelnes Kapitel
      refine_chapter(context, instruction) — Kapitel verfeinern
      continue_chapter(context)           — Kapitel fortsetzen
      generate_summary(content)           — Zusammenfassung
    """

    MAX_TOKENS = MAX_TOKENS_WRITE

    def write_chapter(self, context: ChapterContext) -> dict[str, Any]:
        """Schreibt ein vollstaendiges Kapitel."""
        words_per_chunk = int(self.MAX_TOKENS / 1.5)
        if context.target_word_count > words_per_chunk:
            return self._write_chunked(context)
        return self._write_single(context)

    def _write_template(self, context: ChapterContext) -> str:
        """Convention: chapter_write_{content_type}, fallback to default."""
        from apps.core.prompt_utils import prompt_exists
        ct_tpl = f"authoring/chapter_write_{context.content_type}"
        if prompt_exists(ct_tpl):
            return ct_tpl
        return _DEFAULT_WRITE_TPL

    def _render_write_messages(self, context: ChapterContext) -> list[dict]:
        """Render write messages via convention-based template (unified interface)."""
        from authoringfw import get_content_type_config
        ct_config = get_content_type_config(context.content_type)
        style_block = "\n".join(f"- {c}" for c in ct_config.style_profile.to_constraints())
        tpl = self._write_template(context)
        return render_prompt(
            tpl,
            ctx_block=context.to_prompt_context(),
            style_block=style_block,
            brief=context.chapter_outline or "",
            target_words=context.target_word_count,
        )

    def _write_single(self, context: ChapterContext) -> dict[str, Any]:
        estimated_tokens = int(context.target_word_count * 1.5)
        max_tokens = min(max(estimated_tokens, MIN_TOKENS_WRITE), self.MAX_TOKENS)

        messages = self._render_write_messages(context)
        try:
            router = LLMRouter()
            raw = router.completion(
                "chapter_generation", messages, max_tokens=max_tokens
            )
        except (LLMRoutingError, Exception) as exc:
            logger.error("_write_single failed: %s", exc)
            return {"success": False, "error": str(exc)}

        content = _strip_chapter_heading(raw.strip())
        return {
            "success": True,
            "content": content,
            "word_count": len(content.split()),
        }

    def _write_chunked(self, context: ChapterContext) -> dict[str, Any]:
        from authoringfw import get_content_type_config

        words_per_chunk = int(self.MAX_TOKENS / 1.5) - 200
        num_chunks = (context.target_word_count // words_per_chunk) + 1
        context_str = context.to_prompt_context()
        all_content: list[str] = []

        ct_config = get_content_type_config(context.content_type)
        vocab = ct_config.chunk_vocab

        write_msgs = self._render_write_messages(context)
        sys_prompt = write_msgs[0]["content"] if write_msgs else "Schreibe ein Kapitel."

        for chunk_num in range(num_chunks):
            is_first = chunk_num == 0
            is_last = chunk_num == num_chunks - 1

            if is_first:
                chunk_prompt = (
                    f"{context_str}\n\nSchreibe etwa {words_per_chunk} Woerter "
                    f"(Teil 1/{num_chunks}). Beginne mit einer "
                    f"{vocab['opening']}. ENDE NICHT — das Kapitel wird fortgesetzt."
                )
            elif is_last:
                prev = "\n\n".join(all_content[-2:])[-CHUNK_CONTEXT_WINDOW:]
                chunk_prompt = (
                    f"BISHERIGER INHALT (Auszug):\n{prev}\n\n"
                    f"Schreibe das ENDE des Kapitels (~{words_per_chunk} Woerter, "
                    f"Teil {chunk_num + 1}/{num_chunks}). "
                    "Schliesse das Kapitel ab."
                )
            else:
                prev = "\n\n".join(all_content[-2:])[-CHUNK_CONTEXT_WINDOW:]
                chunk_prompt = (
                    f"BISHERIGER INHALT (Auszug):\n{prev}\n\n"
                    f"{vocab['mid']} (~{words_per_chunk} Woerter, "
                    f"Teil {chunk_num + 1}/{num_chunks}). "
                    f"{vocab['mid_detail']}. ENDE NICHT."
                )

            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": chunk_prompt},
            ]
            try:
                router = LLMRouter()
                chunk_content = router.completion(
                    "chapter_generation", messages, max_tokens=self.MAX_TOKENS
                )
            except (LLMRoutingError, Exception) as exc:
                logger.error("Chunk %d error: %s", chunk_num + 1, exc)
                if all_content:
                    partial = "\n\n".join(all_content)
                    return {
                        "success": True,
                        "content": partial + f"\n\n[Abgebrochen nach Teil {chunk_num}: {exc}]",
                        "word_count": len(partial.split()),
                    }
                return {"success": False, "error": str(exc)}

            all_content.append(chunk_content.strip())

        full_content = _strip_chapter_heading("\n\n".join(all_content))
        current_words = len(full_content.split())
        min_words = int(context.target_word_count * CHUNK_TARGET_RATIO)

        continuations = 0
        while current_words < min_words and continuations < CHUNK_MAX_CONTINUATIONS:
            continuations += 1
            remaining = context.target_word_count - current_words
            prev = full_content[-CHUNK_CONTEXT_WINDOW:]
            cont_prompt = (
                f"BISHERIGER INHALT (Auszug):\n{prev}\n\n"
                f"Das Kapitel hat erst {current_words} von {context.target_word_count} Woertern. "
                f"Schreibe ~{remaining} weitere Woerter, um das Kapitel fortzusetzen. "
                f"Wiederhole KEINEN bestehenden Inhalt."
            )
            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": cont_prompt},
            ]
            try:
                router = LLMRouter()
                continuation = router.completion(
                    "chapter_generation", messages, max_tokens=self.MAX_TOKENS
                )
                full_content = full_content.rstrip() + "\n\n" + continuation.strip()
                current_words = len(full_content.split())
                logger.info(
                    "Continuation %d: %d/%d words",
                    continuations, current_words, context.target_word_count,
                )
            except (LLMRoutingError, Exception) as exc:
                logger.warning("Continuation %d failed: %s", continuations, exc)
                break

        return {
            "success": True,
            "content": full_content,
            "word_count": len(full_content.split()),
        }

    def refine_chapter(self, context: ChapterContext, instruction: str) -> dict[str, Any]:
        """Verfeinert bestehenden Kapiteltext."""
        if not context.existing_content:
            return {"success": False, "error": "Kein bestehender Inhalt zum Verfeinern"}

        messages = render_prompt(
            _TPL_REFINE,
            context=context.to_prompt_context(),
            existing_content=context.existing_content,
            instruction=instruction,
        )
        try:
            router = LLMRouter()
            raw = router.completion("chapter_generation", messages, max_tokens=MAX_TOKENS_REFINE)
        except (LLMRoutingError, Exception) as exc:
            return {"success": False, "error": str(exc)}

        content = raw.strip()
        return {
            "success": True,
            "content": content,
            "word_count": len(content.split()),
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
        messages = render_prompt(
            _TPL_CONTINUE,
            context=context.to_prompt_context(),
            existing_content=context.existing_content,
            remaining_words=remaining,
        )
        try:
            router = LLMRouter()
            raw = router.completion(
                "chapter_generation",
                messages,
                max_tokens=min(max(int(remaining * 1.5), 1000), self.MAX_TOKENS),
            )
        except (LLMRoutingError, Exception) as exc:
            return {"success": False, "error": str(exc)}

        continuation = raw.strip()
        full_content = context.existing_content + "\n\n" + continuation
        return {
            "success": True,
            "content": full_content,
            "word_count": len(full_content.split()),
        }

    def generate_summary(self, content: str) -> str:
        """Generiert eine kurze Zusammenfassung fuer Kontinuitaets-Kontext."""
        if not content or len(content) < 100:
            return ""

        messages = render_prompt(_TPL_SUMMARY, content=content)
        try:
            router = LLMRouter()
            return router.completion("chapter_generation", messages, max_tokens=200).strip()
        except (LLMRoutingError, Exception) as exc:
            logger.warning("Summary generation failed: %s", exc)

        return content[:200] + "..."


chapter_writer_handler = ChapterWriterHandler()
