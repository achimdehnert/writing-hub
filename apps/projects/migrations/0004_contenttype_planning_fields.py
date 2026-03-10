"""
Migration 0004: Add DB-driven planning configuration fields to ContentTypeLookup.

Same pattern as bfagent Migration 0050. Allows any content type configured
in the DB to define its own aifw action_code and promptfw template prefix
for planning calls (premise/themes/logline) — no code changes needed when
adding new formats (screenplay, lyric, comic_script, etc.).
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0003_outlinenode_content"),
    ]

    operations = [
        migrations.AddField(
            model_name="contenttypelookup",
            name="planning_action_code",
            field=models.CharField(
                blank=True,
                default="",
                max_length=100,
                help_text=(
                    "aifw action_code for planning calls (premise/themes/logline). "
                    "e.g. 'planning_novel', 'planning_screenplay'. "
                    "Falls back to 'planning_novel' if empty."
                ),
            ),
        ),
        migrations.AddField(
            model_name="contenttypelookup",
            name="planning_prompt_template",
            field=models.CharField(
                blank=True,
                default="",
                max_length=128,
                help_text=(
                    "promptfw template key prefix for planning, e.g. 'roman' -> renders "
                    "'roman.system.planning' + 'roman.task.planning'. "
                    "Falls back to slug if empty, then to 'roman' if no match found."
                ),
            ),
        ),
        migrations.AddField(
            model_name="contenttypelookup",
            name="planning_system_prompt",
            field=models.TextField(
                blank=True,
                default="",
                help_text=(
                    "Custom system prompt for planning LLM calls. "
                    "Overrides promptfw template system prompt when set."
                ),
            ),
        ),
        migrations.AddField(
            model_name="contenttypelookup",
            name="planning_user_template",
            field=models.TextField(
                blank=True,
                default="",
                help_text=(
                    "Custom user prompt template for planning. "
                    "Variables: {title}, {genre}, {description}, {context}. "
                    "Overrides promptfw template when set."
                ),
            ),
        ),
    ]
