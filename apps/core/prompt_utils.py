"""
Prompt Utilities — promptfw Integration (ADR-083)

Zentraler Helper für PromptStack.render_to_messages() mit Fallback.

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

# Try to import promptfw
try:
    from promptfw import PromptStack
    _PROMPTFW_AVAILABLE = True
except ImportError:
    _PROMPTFW_AVAILABLE = False
    PromptStack = None


def render_prompt(template_name: str, **context: Any) -> list[dict]:
    """
    Render a prompt template to messages list.

    Args:
        template_name: Template path without extension (e.g. "idea_import/brainstorm_ideas")
        **context: Variables to pass to the template

    Returns:
        List of message dicts: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]

    Falls back to inline prompt if template not found or promptfw not available.
    """
    template_path = PROMPTS_DIR / f"{template_name}.jinja2"

    if not _PROMPTFW_AVAILABLE:
        logger.debug("promptfw not available, using fallback for %s", template_name)
        return _fallback_render(template_path, context)

    if not template_path.exists():
        logger.warning("Prompt template not found: %s", template_path)
        return _fallback_render(template_path, context)

    try:
        stack = PromptStack.from_file(str(template_path))
        return stack.render_to_messages(**context)
    except Exception as exc:
        logger.warning("PromptStack render failed for %s: %s", template_name, exc)
        return _fallback_render(template_path, context)


def _fallback_render(template_path: Path, context: dict) -> list[dict]:
    """
    Fallback: Parse YAML frontmatter manually if promptfw not available.
    """
    if not template_path.exists():
        # Return empty messages - caller should handle this
        return []

    try:
        import yaml
        from jinja2 import Template

        content = template_path.read_text()

        # Parse YAML frontmatter (between --- markers)
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                # Render system and user with Jinja2
                messages = []
                if "system" in frontmatter:
                    system_tpl = Template(frontmatter["system"])
                    messages.append({
                        "role": "system",
                        "content": system_tpl.render(**context).strip()
                    })
                if "user" in frontmatter:
                    user_tpl = Template(frontmatter["user"])
                    messages.append({
                        "role": "user",
                        "content": user_tpl.render(**context).strip()
                    })
                return messages

        return []
    except Exception as exc:
        logger.warning("Fallback render failed for %s: %s", template_path, exc)
        return []


def prompt_exists(template_name: str) -> bool:
    """Check if a prompt template exists."""
    template_path = PROMPTS_DIR / f"{template_name}.jinja2"
    return template_path.exists()
