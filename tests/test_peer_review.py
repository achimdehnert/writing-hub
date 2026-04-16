"""
Tests for the Scientific Peer Review feature.

Tests:
  - Service: is_peer_review_eligible, _parse_findings, _parse_verdict
  - Models: PeerReviewSession, PeerReviewFinding
  - Views: Dashboard, Start (mocked LLM), Session Detail
"""
import pytest
from django.contrib.auth.models import User
from django.test import Client

from apps.projects.models import (
    BookProject,
    ContentTypeLookup,
    GenreLookup,
    OutlineNode,
    OutlineVersion,
    PeerReviewFinding,
    PeerReviewSession,
)
from apps.projects.services.peer_review_service import (
    PEER_REVIEW_AGENTS,
    SCIENTIFIC_CONTENT_TYPES,
    _parse_findings,
    _parse_verdict,
    is_peer_review_eligible,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db):
    return User.objects.create_user(username="pr_testuser", password="pass123")


@pytest.fixture
def auth_client(user):
    c = Client()
    c.login(username="pr_testuser", password="pass123")
    return c


@pytest.fixture
def scientific_project(db, user):
    ct, _ = ContentTypeLookup.objects.get_or_create(
        slug="paper", defaults={"name": "Paper", "order": 10}
    )
    genre, _ = GenreLookup.objects.get_or_create(
        name="Wissenschaft", defaults={"order": 10}
    )
    return BookProject.objects.create(
        title="Test Scientific Paper",
        owner=user,
        content_type="scientific",
        content_type_lookup=ct,
        genre_lookup=genre,
        target_word_count=10000,
    )


@pytest.fixture
def novel_project(db, user):
    ct, _ = ContentTypeLookup.objects.get_or_create(
        slug="roman", defaults={"name": "Roman", "order": 1}
    )
    genre, _ = GenreLookup.objects.get_or_create(
        name="Fantasy", defaults={"order": 1}
    )
    return BookProject.objects.create(
        title="Test Novel",
        owner=user,
        content_type="novel",
        content_type_lookup=ct,
        genre_lookup=genre,
        target_word_count=80000,
    )


@pytest.fixture
def outline_with_chapters(scientific_project):
    version = OutlineVersion.objects.create(
        project=scientific_project,
        name="v1",
    )
    chapters = []
    for i, title in enumerate(["Einleitung", "Methodik", "Ergebnisse", "Diskussion"], 1):
        ch = OutlineNode.objects.create(
            outline_version=version,
            title=title,
            beat_type="chapter",
            order=i,
            content=f"Inhalt von {title}. " * 50,
        )
        chapters.append(ch)
    return version, chapters


# ---------------------------------------------------------------------------
# Service: Eligibility
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPeerReviewEligibility:

    def test_scientific_project_eligible(self, scientific_project):
        assert is_peer_review_eligible(scientific_project) is True

    def test_novel_project_not_eligible(self, novel_project):
        assert is_peer_review_eligible(novel_project) is False

    def test_academic_project_eligible(self, novel_project):
        novel_project.content_type = "academic"
        novel_project.save(update_fields=["content_type"])
        assert is_peer_review_eligible(novel_project) is True

    def test_essay_project_eligible(self, novel_project):
        novel_project.content_type = "essay"
        novel_project.save(update_fields=["content_type"])
        assert is_peer_review_eligible(novel_project) is True

    def test_scientific_content_types_constant(self):
        assert "scientific" in SCIENTIFIC_CONTENT_TYPES
        assert "academic" in SCIENTIFIC_CONTENT_TYPES
        assert "essay" in SCIENTIFIC_CONTENT_TYPES
        assert "novel" not in SCIENTIFIC_CONTENT_TYPES


# ---------------------------------------------------------------------------
# Service: Parsing
# ---------------------------------------------------------------------------

class TestParseFunctions:

    def test_parse_findings_valid(self):
        raw = """Here is the analysis:
        [{"type": "weakness", "category": "validity", "severity": "major",
          "feedback": "Stichprobe zu klein", "text_ref": "n=5"},
         {"type": "strength", "category": "design", "severity": "minor",
          "feedback": "Gutes Forschungsdesign", "text_ref": ""}]
        """
        result = _parse_findings(raw)
        assert len(result) == 2
        assert result[0]["feedback"] == "Stichprobe zu klein"
        assert result[1]["type"] == "strength"

    def test_parse_findings_empty_feedback_filtered(self):
        raw = '[{"type": "weakness", "feedback": ""}, {"type": "strength", "feedback": "Gut"}]'
        result = _parse_findings(raw)
        assert len(result) == 1
        assert result[0]["feedback"] == "Gut"

    def test_parse_findings_invalid_json(self):
        assert _parse_findings("This is not JSON") == []

    def test_parse_findings_no_array(self):
        assert _parse_findings('{"key": "value"}') == []

    def test_parse_verdict_valid(self):
        raw = """
        {"verdict": "minor_revisions", "summary": "Solide Arbeit",
         "strengths": ["Gute Methodik"], "main_issues": ["Quellen fehlen"],
         "recommendations": ["Mehr Literatur"], "scores": {"originality": 7}}
        """
        result = _parse_verdict(raw)
        assert result is not None
        assert result["verdict"] == "minor_revisions"
        assert result["scores"]["originality"] == 7

    def test_parse_verdict_invalid(self):
        assert _parse_verdict("No JSON here") is None

    def test_parse_verdict_array_returns_none(self):
        assert _parse_verdict("[1, 2, 3]") is None


# ---------------------------------------------------------------------------
# Service: Agents Configuration
# ---------------------------------------------------------------------------

class TestAgentsConfiguration:

    def test_four_agents_defined(self):
        assert len(PEER_REVIEW_AGENTS) == 4

    def test_agent_keys(self):
        keys = {a["key"] for a in PEER_REVIEW_AGENTS}
        assert keys == {"methodology", "argumentation", "sources", "structure"}

    def test_agents_have_prompt_templates(self):
        for agent in PEER_REVIEW_AGENTS:
            assert "prompt_template" in agent
            assert agent["prompt_template"].startswith("projects/peer_review_")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPeerReviewModels:

    def test_session_creation(self, scientific_project, user):
        session = PeerReviewSession.objects.create(
            project=scientific_project,
            created_by=user,
            status="done",
            verdict="minor_revisions",
            chapter_count=4,
            finding_count=12,
            scores={"originality": 7, "methodology": 8, "argumentation": 6,
                    "sources": 5, "structure": 9},
        )
        assert str(session) == "Peer Review: Test Scientific Paper [Minor Revisions]"
        assert session.avg_score == 7.0

    def test_session_avg_score_empty(self, scientific_project, user):
        session = PeerReviewSession.objects.create(
            project=scientific_project,
            created_by=user,
        )
        assert session.avg_score == 0

    def test_finding_creation(self, scientific_project, user, outline_with_chapters):
        _, chapters = outline_with_chapters
        session = PeerReviewSession.objects.create(
            project=scientific_project,
            created_by=user,
        )
        finding = PeerReviewFinding.objects.create(
            session=session,
            node=chapters[0],
            agent="methodology",
            finding_type="weakness",
            category="validity",
            severity="major",
            feedback="Die Stichprobe ist zu klein für signifikante Aussagen.",
            text_reference="n=5",
        )
        assert finding.get_agent_display() == "Methodik-Prüfer"
        assert finding.get_finding_type_display() == "Schwäche"
        assert not finding.is_resolved

    def test_finding_str(self, scientific_project, user, outline_with_chapters):
        _, chapters = outline_with_chapters
        session = PeerReviewSession.objects.create(
            project=scientific_project, created_by=user,
        )
        finding = PeerReviewFinding.objects.create(
            session=session, node=chapters[0], agent="sources",
            feedback="Quellenarbeit ist hervorragend.",
        )
        assert "[Quellen-Prüfer]" in str(finding)


# ---------------------------------------------------------------------------
# Views: Dashboard
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPeerReviewViews:

    def test_dashboard_200(self, auth_client, scientific_project):
        response = auth_client.get(f"/projekte/{scientific_project.pk}/peer-review/")
        assert response.status_code == 200
        assert "agents" in response.context
        assert response.context["is_eligible"] is True

    def test_dashboard_not_eligible(self, auth_client, novel_project):
        response = auth_client.get(f"/projekte/{novel_project.pk}/peer-review/")
        assert response.status_code == 200
        assert response.context["is_eligible"] is False

    def test_start_no_outline_redirects(self, auth_client, scientific_project):
        response = auth_client.post(
            f"/projekte/{scientific_project.pk}/peer-review/start/"
        )
        assert response.status_code == 302

    def test_start_not_eligible_redirects(self, auth_client, novel_project):
        response = auth_client.post(
            f"/projekte/{novel_project.pk}/peer-review/start/"
        )
        assert response.status_code == 302

    def test_session_detail_200(self, auth_client, scientific_project, user):
        session = PeerReviewSession.objects.create(
            project=scientific_project,
            created_by=user,
            status="done",
            verdict="minor_revisions",
        )
        response = auth_client.get(
            f"/projekte/{scientific_project.pk}/peer-review/{session.pk}/"
        )
        assert response.status_code == 200
        assert "session" in response.context
        assert response.context["session"].verdict == "minor_revisions"

    def test_finding_resolve_toggle(self, auth_client, scientific_project, user, outline_with_chapters):
        _, chapters = outline_with_chapters
        session = PeerReviewSession.objects.create(
            project=scientific_project, created_by=user,
        )
        finding = PeerReviewFinding.objects.create(
            session=session, node=chapters[0], agent="methodology",
            feedback="Test finding",
        )
        response = auth_client.post(
            f"/projekte/{scientific_project.pk}/peer-review/finding/{finding.pk}/resolve/"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["is_resolved"] is True

        response2 = auth_client.post(
            f"/projekte/{scientific_project.pk}/peer-review/finding/{finding.pk}/resolve/"
        )
        data2 = response2.json()
        assert data2["is_resolved"] is False


# ---------------------------------------------------------------------------
# Context Keys
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPeerReviewContextKeys:

    def test_dashboard_context(self, auth_client, scientific_project):
        response = auth_client.get(f"/projekte/{scientific_project.pk}/peer-review/")
        ctx = response.context
        assert "project" in ctx
        assert "sessions" in ctx
        assert "agents" in ctx
        assert "is_eligible" in ctx

    def test_session_context(self, auth_client, scientific_project, user):
        session = PeerReviewSession.objects.create(
            project=scientific_project, created_by=user, status="done",
        )
        response = auth_client.get(
            f"/projekte/{scientific_project.pk}/peer-review/{session.pk}/"
        )
        ctx = response.context
        assert "session" in ctx
        assert "findings" in ctx
        assert "findings_by_agent" in ctx
        assert "critical_count" in ctx
        assert "agent_map" in ctx
