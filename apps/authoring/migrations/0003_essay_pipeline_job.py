import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authoring', '0002_batch_write_job'),
        ('projects', '0016_text_analysis_snapshot'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EssayPipelineJob',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(
                    choices=[('pending', 'Ausstehend'), ('running', 'Läuft'), ('done', 'Fertig'), ('failed', 'Fehlgeschlagen'), ('canceled', 'Abgebrochen')],
                    db_index=True, default='pending', max_length=10,
                )),
                ('current_step', models.CharField(
                    choices=[
                        ('created', 'Projekt erstellt'),
                        ('outline', 'Outline wird generiert'),
                        ('research', 'Literaturrecherche'),
                        ('writing', 'Kapitel werden geschrieben'),
                        ('review', 'Peer Review'),
                        ('done', 'Fertig'),
                        ('failed', 'Fehlgeschlagen'),
                    ],
                    default='created', max_length=20,
                )),
                ('framework', models.CharField(default='academic_essay', max_length=50)),
                ('do_research', models.BooleanField(default=False)),
                ('do_review', models.BooleanField(default=False)),
                ('total_chapters', models.PositiveSmallIntegerField(default=0)),
                ('completed_chapters', models.PositiveSmallIntegerField(default=0)),
                ('current_chapter_title', models.CharField(blank=True, default='', max_length=300)),
                ('log_messages', models.JSONField(default=list)),
                ('error', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='essay_pipeline_jobs',
                    to='projects.bookproject',
                )),
                ('requested_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='essay_pipeline_jobs',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Essay-Pipeline-Job',
                'verbose_name_plural': 'Essay-Pipeline-Jobs',
                'db_table': 'wh_essay_pipeline_jobs',
                'ordering': ['-created_at'],
            },
        ),
    ]
