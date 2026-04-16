"""
Prompt Utilities — promptfw Integration (ADR-083, ADR-146)

Resolution order (ADR-146):
  1. DB: promptfw.contrib.django.render_prompt() (cached, SandboxedEnvironment)
  2. File: .jinja2 frontmatter files in templates/prompts/
  3. Error: PromptRenderError

Usage:
    from apps.core.prompt_utils import render_prompt

    messages = render_prompt(
        "idea_import/brainstorm_ideas",
        inspiration="...",
        genre="Thriller",
        count=5,
    )
    result = router.completion(action_code="outline_generate", messages=messages)
"""

import logging
from pathlib import Path
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

# Prompt templates directory (file fallback)
PROMPTS_DIR = Path(settings.BASE_DIR) / "templates" / "prompts"


class PromptRenderError(RuntimeError):
    """Raised when a prompt template cannot be found or rendered."""


def render_prompt(template_name: str, **context: Any) -> list[dict]:
    """
    Render a prompt template to messages list.

    Args:
        template_name: Template path without extension
            e.g. "idea_import/brainstorm_ideas" (legacy)
            or action_code "writing-hub.idea-import.brainstorm-ideas" (new)
        **context: Variables to pass to the template

    Returns:
        List of message dicts: [{"role": "system", "content": "..."}, ...]

    Resolution: DB (ADR-146) → File (.jinja2) → Error
    """
    # Convert legacy path format to action_code
    # "idea_import/brainstorm_ideas" → "writing-hub.idea-import.brainstorm-ideas"
    action_code = _to_action_code(template_name)

    # 1. Try DB-backed resolution (promptfw.contrib.django)
    try:
        from promptfw.contrib.django import PromptNotFoundError, PromptValidationError
        from promptfw.contrib.django import render_prompt as db_render_prompt

        return db_render_prompt(action_code, **context)
    except PromptNotFoundError:
        logger.debug("DB prompt not found for '%s', trying file fallback", action_code)
    except PromptValidationError as exc:
        raise PromptRenderError(
            f"Prompt validation failed for '{action_code}': {exc}"
        ) from exc
    except Exception as exc:
        logger.warning("DB render failed for '%s': %s", action_code, exc)

    # 2. File fallback (legacy .jinja2 frontmatter)
    return _render_from_file(template_name, context)


def _to_action_code(template_name: str) -> str:
    """Convert legacy path to action_code.

    "idea_import/brainstorm_ideas" → "writing-hub.idea-import.brainstorm-ideas"
    "writing-hub.idea-import.brainstorm-ideas" → unchanged
    """
    if "." in template_name and "/" not in template_name:
        return template_name  # already action_code format
    parts = template_name.replace("/", ".").replace("_", "-")
    return f"writing-hub.{parts}"


def _render_from_file(template_name: str, context: dict) -> list[dict]:
    """Render from .jinja2 frontmatter file (legacy fallback)."""
    import yaml
    from jinja2 import Template as _Jinja2Template

    template_path = PROMPTS_DIR / f"{template_name}.jinja2"

    if not template_path.exists():
        raise PromptRenderError(f"Prompt template not found: {template_path}")

    try:
        raw_tpl = template_path.read_text()
        # Strip leading Jinja2 comments ({# ... #}) before frontmatter
        tpl_lines = raw_tpl.split("\n")
        while tpl_lines and tpl_lines[0].strip().startswith("{#"):
            tpl_lines.pop(0)
        raw_tpl = "\n".join(tpl_lines)

        if not raw_tpl.strip().startswith("---"):
            raise ValueError("Template must start with YAML frontmatter (---)")

        # Split on all --- delimiters and merge YAML blocks
        parts = raw_tpl.split("---")
        # parts[0] is empty (before first ---), rest are YAML sections
        yaml_sections = [p for p in parts[1:] if p.strip()]
        if not yaml_sections:
            raise ValueError("Invalid frontmatter: expected --- ... --- format")

        frontmatter: dict = {}
        for section in yaml_sections:
            parsed = yaml.safe_load(section)
            if isinstance(parsed, dict):
                frontmatter.update(parsed)

        if not frontmatter:
            raise ValueError(
                "Frontmatter must contain at least one YAML dict section"
            )

        messages: list[dict[str, str]] = []
        for role in ("system", "user", "assistant"):
            if role in frontmatter:
                tpl = _Jinja2Template(str(frontmatter[role]))
                rendered = tpl.render(**context).strip()
                if rendered:
                    messages.append({"role": role, "content": rendered})

        if not messages:
            raise PromptRenderError(
                f"promptfw returned empty messages for '{template_name}'"
            )
        return messages
    except PromptRenderError:
        raise
    except Exception as exc:
        raise PromptRenderError(
            f"promptfw render failed for '{template_name}': {exc}"
        ) from exc


def prompt_exists(template_name: str) -> bool:
    """Check if a prompt template exists (DB or file)."""
    action_code = _to_action_code(template_name)
    try:
        from promptfw.contrib.django.models import PromptTemplate

        if PromptTemplate.objects.filter(
            action_code=action_code, is_active=True, deleted_at__isnull=True
        ).exists():
            return True
    except Exception:
        pass
    template_path = PROMPTS_DIR / f"{template_name}.jinja2"
    return template_path.exists()
