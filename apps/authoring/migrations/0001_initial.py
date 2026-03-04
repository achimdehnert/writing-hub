import uuid

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("projects", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="QualityDimension",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("code", models.CharField(db_index=True, max_length=50, unique=True)),
                ("name_de", models.CharField(max_length=100)),
                ("name_en", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("weight", models.DecimalField(decimal_places=2, default=1.0, max_digits=3)),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_quality_dimensions", "ordering": ["sort_order", "code"]},
        ),
        migrations.CreateModel(
            name="GateDecisionType",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("code", models.CharField(db_index=True, max_length=30, unique=True)),
                ("name_de", models.CharField(max_length=100)),
                ("name_en", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("color", models.CharField(default="secondary", max_length=20)),
                ("icon", models.CharField(default="bi-question-circle", max_length=50)),
                ("allows_commit", models.BooleanField(default=False)),
                ("sort_order", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_gate_decision_types", "ordering": ["sort_order"]},
        ),
        migrations.CreateModel(
            name="AuthorStyleDNA",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="style_dnas", to=settings.AUTH_USER_MODEL)),
                ("name", models.CharField(max_length=200)),
                ("is_primary", models.BooleanField(default=False)),
                ("signature_moves", models.JSONField(default=list)),
                ("do_list", models.JSONField(default=list)),
                ("dont_list", models.JSONField(default=list)),
                ("taboo_list", models.JSONField(default=list)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_author_style_dnas"},
        ),
        migrations.CreateModel(
            name="AuthoringSession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="authoring_sessions", to="projects.bookproject")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="authoring_sessions", to=settings.AUTH_USER_MODEL)),
                ("current_node_id", models.CharField(blank=True, max_length=100)),
                ("context_window", models.JSONField(default=list)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_authoring_sessions", "ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="ProjectPhaseExecution",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="phase_executions", to="projects.bookproject")),
                ("phase_key", models.CharField(db_index=True, max_length=100)),
                ("step_key", models.CharField(blank=True, max_length=100)),
                ("status", models.CharField(choices=[("pending", "Ausstehend"), ("active", "Aktiv"), ("waiting", "Wartet auf Gate-Freigabe"), ("completed", "Abgeschlossen"), ("skipped", "Übersprungen")], default="pending", max_length=15)),
                ("gate_approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="approved_phase_executions", to=settings.AUTH_USER_MODEL)),
                ("gate_approved_at", models.DateTimeField(blank=True, null=True)),
                ("gate_notes", models.TextField(blank=True)),
                ("context", models.JSONField(default=dict)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "wh_project_phase_executions"},
        ),
        migrations.CreateModel(
            name="ProjectQualityConfig",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("project", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="quality_config", to="projects.bookproject")),
                ("min_overall_score", models.DecimalField(decimal_places=2, default="7.50", max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)])),
                ("auto_approve_threshold", models.DecimalField(decimal_places=2, default="8.50", max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)])),
                ("auto_reject_threshold", models.DecimalField(decimal_places=2, default="5.00", max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)])),
                ("require_manual_approval", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_project_quality_configs"},
        ),
        migrations.CreateModel(
            name="ChapterQualityScore",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("chapter_ref", models.CharField(db_index=True, max_length=100)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quality_scores", to="projects.bookproject")),
                ("scored_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="chapter_scores", to=settings.AUTH_USER_MODEL)),
                ("scored_at", models.DateTimeField(auto_now_add=True)),
                ("gate_decision", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="chapter_scores", to="authoring.gatedecisiontype")),
                ("overall_score", models.DecimalField(decimal_places=2, max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)])),
                ("findings", models.JSONField(blank=True, default=dict)),
                ("notes", models.TextField(blank=True)),
            ],
            options={"db_table": "wh_chapter_quality_scores", "ordering": ["-scored_at"]},
        ),
        migrations.CreateModel(
            name="ChapterDimensionScore",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("quality_score", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="dimension_scores", to="authoring.chapterqualityscore")),
                ("dimension", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="chapter_scores", to="authoring.qualitydimension")),
                ("score", models.DecimalField(decimal_places=2, max_digits=4, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)])),
                ("notes", models.TextField(blank=True)),
            ],
            options={"db_table": "wh_chapter_dimension_scores"},
        ),
        migrations.CreateModel(
            name="ChapterWriteJob",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chapter_write_jobs", to="projects.bookproject")),
                ("chapter_ref", models.CharField(db_index=True, max_length=100)),
                ("requested_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="chapter_write_jobs", to=settings.AUTH_USER_MODEL)),
                ("status", models.CharField(choices=[("pending", "Ausstehend"), ("running", "Läuft"), ("done", "Fertig"), ("failed", "Fehlgeschlagen")], db_index=True, default="pending", max_length=10)),
                ("content", models.TextField(blank=True)),
                ("word_count", models.PositiveIntegerField(default=0)),
                ("error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "wh_chapter_write_jobs", "ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="authorstyledna",
            constraint=models.UniqueConstraint(fields=["author", "name"], name="unique_author_style_dna"),
        ),
        migrations.AddConstraint(
            model_name="projectphaseexecution",
            constraint=models.UniqueConstraint(fields=["project", "phase_key", "step_key"], name="unique_project_phase_step"),
        ),
        migrations.AddConstraint(
            model_name="chapterdimensionscore",
            constraint=models.UniqueConstraint(fields=["quality_score", "dimension"], name="unique_quality_score_dimension"),
        ),
        migrations.AddIndex(
            model_name="chapterwritejob",
            index=models.Index(fields=["chapter_ref", "status"], name="wh_chapter_write_jobs_ref_status"),
        ),
    ]
