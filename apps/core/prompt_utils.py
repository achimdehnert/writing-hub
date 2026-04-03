"""
Prompt Utilities — promptfw Integration (ADR-083)

Thin wrapper around promptfw.frontmatter (SSoT) for rendering
.jinja2 YAML-frontmatter templates to OpenAI-format messages.

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

# Prompt templates directory
PROMPTS_DIR = Path(settings.BASE_DIR) / "templates" / "prompts"


class PromptRenderError(RuntimeError):
    """Raised when a prompt template cannot be found or rendered."""

# promptfw.frontmatter is the SSoT for YAML-frontmatter rendering.
# Fallback only if promptfw is not installed (should not happen in production).
try:
    from promptfw.frontmatter import render_frontmatter_string
    _PROMPTFW_AVAILABLE = True
except ImportError:
    _PROMPTFW_AVAILABLE = False
    render_frontmatter_string = None


def render_prompt(template_name: str, **context: Any) -> list[dict]:
    """
    Render a prompt template to messages list.

    Args:
        template_name: Template path without extension (e.g. "idea_import/brainstorm_ideas")
        **context: Variables to pass to the template

    Returns:
        List of message dicts: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]

    Delegates to promptfw.frontmatter.render_frontmatter_file() (SSoT).
    """
    template_path = PROMPTS_DIR / f"{template_name}.jinja2"

    if not template_path.exists():
        raise PromptRenderError(
            f"Prompt template not found: {template_path}"
        )

    if _PROMPTFW_AVAILABLE:
        try:
            content = template_path.read_text()
            # Strip leading Jinja2 comments ({# ... #}) before frontmatter
            lines = content.split("\n")
            while lines and lines[0].strip().startswith("{#"):
                lines.pop(0)
            content = "\n".join(lines)
            messages = render_frontmatter_string(content, **context)
        except Exception as exc:
            raise PromptRenderError(
                f"promptfw render failed for '{template_name}': {exc}"
            ) from exc
        if not messages:
            raise PromptRenderError(
                f"promptfw returned empty messages for '{template_name}'"
            )
        return messages

    # CI / dev without promptfw — try minimal YAML fallback
    messages = _fallback_render(template_path, context)
    if not messages:
        raise PromptRenderError(
            f"Fallback render produced no messages for '{template_name}'"
        )
    return messages


def _fallback_render(template_path: Path, context: dict) -> list[dict]:
    """Minimal fallback if promptfw is not installed (dev/CI only)."""
    try:
        import yaml
        from jinja2 import Template

        content = template_path.read_text()
        if not content.startswith("---"):
            return []
        parts = content.split("---", 2)
        if len(parts) < 3:
            return []
        frontmatter = yaml.safe_load(parts[1])
        messages = []
        for role in ("system", "user"):
            if role in frontmatter:
                tpl = Template(str(frontmatter[role]))
                rendered = tpl.render(**context).strip()
                if rendered:
                    messages.append({"role": role, "content": rendered})
        return messages
    except Exception as exc:
        logger.warning("Fallback render failed for %s: %s", template_path, exc)
        return []


def prompt_exists(template_name: str) -> bool:
    """Check if a prompt template exists."""
    template_path = PROMPTS_DIR / f"{template_name}.jinja2"
    return template_path.exists()
