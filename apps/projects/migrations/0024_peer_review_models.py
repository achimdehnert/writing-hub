# Generated manually — PeerReviewSession + PeerReviewFinding

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0023_add_academic_scientific_content_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='PeerReviewSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', 'Ausstehend'), ('running', 'Läuft'), ('done', 'Abgeschlossen'), ('error', 'Fehler')], default='pending', max_length=20)),
                ('verdict', models.CharField(blank=True, choices=[('accept', 'Accept'), ('minor_revisions', 'Minor Revisions'), ('major_revisions', 'Major Revisions'), ('reject', 'Reject')], default='', max_length=20)),
                ('summary', models.TextField(blank=True, default='')),
                ('strengths', models.JSONField(default=list)),
                ('main_issues', models.JSONField(default=list)),
                ('recommendations', models.JSONField(default=list)),
                ('scores', models.JSONField(default=dict, help_text='Dimension scores: originality, methodology, argumentation, sources, structure (1-10)')),
                ('agents_used', models.JSONField(default=list)),
                ('chapter_count', models.PositiveSmallIntegerField(default=0)),
                ('finding_count', models.PositiveSmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='peer_reviews', to='projects.bookproject')),
            ],
            options={
                'verbose_name': 'Peer Review Session',
                'verbose_name_plural': 'Peer Review Sessions',
                'db_table': 'wh_peer_review_sessions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PeerReviewFinding',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('agent', models.CharField(choices=[('methodology', 'Methodik-Prüfer'), ('argumentation', 'Argumentations-Prüfer'), ('sources', 'Quellen-Prüfer'), ('structure', 'Struktur-Prüfer')], max_length=30)),
                ('finding_type', models.CharField(choices=[('strength', 'Stärke'), ('weakness', 'Schwäche'), ('suggestion', 'Vorschlag'), ('concern', 'Bedenken')], default='suggestion', max_length=20)),
                ('category', models.CharField(blank=True, default='', max_length=50)),
                ('severity', models.CharField(choices=[('minor', 'Minor'), ('major', 'Major'), ('critical', 'Critical')], default='minor', max_length=10)),
                ('feedback', models.TextField()),
                ('text_reference', models.TextField(blank=True, default='')),
                ('is_resolved', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='peer_findings', to='projects.outlinenode')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='findings', to='projects.peerreviewsession')),
            ],
            options={
                'verbose_name': 'Peer Review Finding',
                'verbose_name_plural': 'Peer Review Findings',
                'db_table': 'wh_peer_review_findings',
                'ordering': ['session', 'node__order', '-severity', 'agent'],
            },
        ),
    ]
