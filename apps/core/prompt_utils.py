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
# We import yaml/jinja2 directly to avoid a parameter name collision
# in render_frontmatter_string (its first param is named 'content',
# which collides with template variables named 'content').
try:
    import yaml
    from jinja2 import Template as _Jinja2Template
    _PROMPTFW_AVAILABLE = True
except ImportError:
    _PROMPTFW_AVAILABLE = False


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
            raw_tpl = template_path.read_text()
            # Strip leading Jinja2 comments ({# ... #}) before frontmatter
            tpl_lines = raw_tpl.split("\n")
            while tpl_lines and tpl_lines[0].strip().startswith("{#"):
                tpl_lines.pop(0)
            raw_tpl = "\n".join(tpl_lines)
            messages = _render_frontmatter(raw_tpl, context)
        except Exception as exc:
            raise PromptRenderError(
                f"promptfw render failed for '{template_name}': {exc}"
            ) from exc
        if not messages:
            raise PromptRenderError(
                f"promptfw returned empty messages for '{template_name}'"
            )
        return messages

    # yaml/jinja2 not available — should not happen (Django deps)
    raise PromptRenderError(
        f"yaml/jinja2 not installed — cannot render '{template_name}'"
    )


def _render_frontmatter(template_str: str, ctx: dict) -> list[dict]:
    """Render YAML-frontmatter template to messages.

    Same logic as promptfw.frontmatter.render_frontmatter_string but accepts
    context as a dict to avoid the 'content' parameter name collision.
    """
    if not template_str.strip().startswith("---"):
        raise ValueError("Template must start with YAML frontmatter (---)")

    parts = template_str.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Invalid frontmatter: expected --- ... --- format")

    frontmatter = yaml.safe_load(parts[1])
    if not isinstance(frontmatter, dict):
        raise ValueError(
            f"Frontmatter must be a YAML dict, got {type(frontmatter).__name__}"
        )

    messages: list[dict[str, str]] = []
    for role in ("system", "user", "assistant"):
        if role in frontmatter:
            tpl = _Jinja2Template(str(frontmatter[role]))
            rendered = tpl.render(**ctx).strip()
            if rendered:
                messages.append({"role": role, "content": rendered})
    return messages


def prompt_exists(template_name: str) -> bool:
    """Check if a prompt template exists."""
    template_path = PROMPTS_DIR / f"{template_name}.jinja2"
    return template_path.exists()
