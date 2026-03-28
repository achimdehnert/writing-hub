# FE3 — Drama-Dashboard: Spannungskurve & Emotionsbogen

> **Neu:** Nach Prio-1 haben OutlineNodes `tension_numeric` und
> `emotion_start/end`. Diese Daten brauchen eine Visualisierung —
> die Spannungskurve als interaktives Chart direkt im Projekt-Detail.

---

## FE3.1 — Was visualisiert wird

```
SPANNUNGSKURVE:
    X-Achse: Kapitel (1–N)
    Y-Achse: tension_numeric (1–10)
    Farbe: Outcome-Typ (grün=yes, rot=no, gelb=yes_but, orange=no_and)
    Markierung: Wendepunkte (ProjectTurningPoint)

EMOTIONS-DELTA-ÜBERSICHT:
    Pro Kapitel: emotion_start → emotion_end
    Farbe: positiver Delta = grün, negativer = rot

FORESHADOWING-STATUS:
    Liste aller ForeshadowingEntry mit Setup/Payoff-Status
```

---

## FE3.2 — Chart.js einbinden (CDN)

In `base.html` oder nur in Drama-Dashboard-Template:

```html
{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
{% endblock %}
```

---

## FE3.3 — View: Drama-Dashboard-Daten

```python
# apps/projects/views_html.py
def project_drama_dashboard(request, pk):
    """Drama-Dashboard — Spannungskurve, Emotionsbogen, Foreshadowing."""
    project = get_object_or_404(BookProject, pk=pk, owner=request.user)
    active_version = OutlineVersion.objects.filter(
        project=project, is_active=True
    ).first()

    nodes = []
    if active_version:
        nodes = list(
            OutlineNode.objects
            .filter(outline_version=active_version)
            .select_related("outcome", "tension_level")
            .order_by("order")
        )

    # Spannungskurven-Daten für Chart.js
    tension_data = [
        {
            "order": n.order,
            "title": n.title[:30],
            "tension": n.tension_numeric or 0,
            "outcome": n.outcome.code if n.outcome else "",
            "emotion_start": n.emotion_start,
            "emotion_end": n.emotion_end,
            "beat": n.outlinefw_beat_name or n.beat_phase,
        }
        for n in nodes
    ]

    turning_points = []
    if hasattr(project, "turning_points"):
        turning_points = list(
            project.turning_points
            .select_related("turning_point_type")
            .order_by("position_percent")
        )

    foreshadowing = []
    if hasattr(project, "foreshadowing_entries"):
        foreshadowing = list(project.foreshadowing_entries.all())

    return render(request, "projects/drama_dashboard.html", {
        "project": project,
        "tension_data_json": json.dumps(tension_data, ensure_ascii=False),
        "turning_points": turning_points,
        "foreshadowing": foreshadowing,
        "nodes": nodes,
    })
```

---

## FE3.4 — Template: `templates/projects/drama_dashboard.html`

```html
{% extends "base.html" %}
{% block title %}Drama-Dashboard — {{ project.title }}{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
{% endblock %}

{% block content %}
<div style="max-width:1200px;margin:0 auto;">

    <!-- Header -->
    <div class="d-flex align-items-center justify-content-between mb-4">
        <h4 class="fw-bold mb-0" style="color:var(--text);">
            <i class="bi bi-activity me-2 text-primary"></i>Drama-Dashboard
        </h4>
        <a href="{% url 'projects:detail' project.pk %}"
           class="btn btn-outline-secondary btn-sm">
            <i class="bi bi-arrow-left me-1"></i>Projekt
        </a>
    </div>

    <!-- Spannungskurve -->
    <div class="card mb-4">
        <div class="card-header d-flex justify-content-between align-items-center py-2 px-3">
            <span class="fw-semibold fs-sm">
                <i class="bi bi-graph-up me-2 text-primary"></i>Spannungskurve
            </span>
            <div class="d-flex gap-2">
                <span class="badge fs-tiny" style="background:var(--bg-hover);color:var(--success);">● YES</span>
                <span class="badge fs-tiny" style="background:var(--bg-hover);color:var(--danger);">● NO</span>
                <span class="badge fs-tiny" style="background:var(--bg-hover);color:var(--warning);">● YES/BUT</span>
                <span class="badge fs-tiny" style="background:var(--bg-hover);color:#fb923c;">● NO/AND</span>
            </div>
        </div>
        <div class="card-body p-3">
            <canvas id="tensionChart" height="100"></canvas>
        </div>
    </div>

    <!-- Wendepunkte + Emotionsbogen -->
    <div class="row g-3 mb-4">

        <!-- Wendepunkte -->
        <div class="col-md-5">
            <div class="card h-100">
                <div class="card-header py-2 px-3">
                    <span class="fw-semibold fs-sm">
                        <i class="bi bi-sign-turn-right me-2 text-primary"></i>Wendepunkte
                    </span>
                </div>
                <div class="card-body p-0">
                    {% for tp in turning_points %}
                    <div class="d-flex align-items-center gap-3 px-3 py-2"
                         style="border-bottom:1px solid var(--border);">
                        <div class="text-center" style="min-width:2.5rem;">
                            <div class="fw-bold" style="color:var(--primary);font-size:.9rem;">
                                {{ tp.position_percent }}%
                            </div>
                        </div>
                        <div style="flex:1;min-width:0;">
                            <div class="fs-sm fw-semibold">
                                {{ tp.turning_point_type.label|default:"-" }}
                            </div>
                            {% if tp.what_happens %}
                            <div class="text-muted fs-xs text-truncate">
                                {{ tp.what_happens }}
                            </div>
                            {% endif %}
                        </div>
                        {% if tp.node %}
                        <span class="badge fs-tiny"
                              style="background:var(--bg-hover);color:var(--text-muted);">
                            Kap. {{ tp.node.order }}
                        </span>
                        {% else %}
                        <span class="badge fs-tiny"
                              style="background:var(--bg-hover);color:var(--warning);">
                            ⚠ kein Kapitel
                        </span>
                        {% endif %}
                    </div>
                    {% empty %}
                    <div class="p-3 text-muted fs-sm text-center">
                        Noch keine Wendepunkte generiert.
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- Emotions-Delta -->
        <div class="col-md-7">
            <div class="card h-100">
                <div class="card-header py-2 px-3">
                    <span class="fw-semibold fs-sm">
                        <i class="bi bi-arrow-left-right me-2 text-primary"></i>Emotionsbogen
                    </span>
                </div>
                <div class="card-body p-0" style="max-height:320px;overflow-y:auto;">
                    {% for n in nodes %}
                    {% if n.emotion_start or n.emotion_end %}
                    <div class="d-flex align-items-center gap-2 px-3 py-2"
                         style="border-bottom:1px solid var(--border);">
                        <span class="text-muted fs-xs" style="min-width:1.5rem;">
                            {{ n.order }}.
                        </span>
                        <span class="fs-xs text-truncate" style="flex:1;max-width:140px;">
                            {{ n.title|truncatechars:20 }}
                        </span>
                        <span class="fs-xs px-2 py-1 rounded"
                              style="background:var(--bg-hover);color:var(--text-muted);">
                            {{ n.emotion_start|default:"—" }}
                        </span>
                        <i class="bi bi-arrow-right fs-xs text-muted"></i>
                        <span class="fs-xs px-2 py-1 rounded"
                              style="{% if n.emotion_end and n.emotion_start != n.emotion_end %}background:#1e3a2f;color:var(--success){% else %}background:var(--bg-hover);color:var(--text-muted){% endif %}">
                            {{ n.emotion_end|default:"—" }}
                        </span>
                        {% if n.outcome %}
                        <span class="fs-tiny badge"
                              style="background:var(--bg-hover);color:{% if n.outcome.code == 'yes' %}var(--success){% elif n.outcome.code == 'no' %}var(--danger){% elif n.outcome.code == 'yes_but' %}var(--warning){% else %}#fb923c{% endif %}">
                            {{ n.outcome.label }}
                        </span>
                        {% endif %}
                    </div>
                    {% endif %}
                    {% empty %}
                    <div class="p-3 text-muted fs-sm text-center">
                        Emotions-Felder noch nicht befüllt.
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>

    <!-- Foreshadowing -->
    <div class="card mb-4">
        <div class="card-header d-flex justify-content-between align-items-center py-2 px-3">
            <span class="fw-semibold fs-sm">
                <i class="bi bi-eye me-2 text-primary"></i>Foreshadowing
            </span>
            <a href="{% url 'projects:foreshadowing' project.pk %}"
               class="btn btn-outline-secondary btn-sm fs-xs">
                <i class="bi bi-plus-lg me-1"></i>Neu
            </a>
        </div>
        <div class="card-body p-0">
            {% for fs in foreshadowing %}
            <div class="d-flex align-items-center gap-3 px-3 py-2"
                 style="border-bottom:1px solid var(--border);">
                <!-- Status-Icon -->
                <div style="font-size:1rem;">
                    {% if fs.is_paid_off %}
                    <i class="bi bi-check-circle-fill" style="color:var(--success);" title="Vollständig"></i>
                    {% elif fs.is_planted %}
                    <i class="bi bi-hourglass-split" style="color:var(--warning);" title="Setup gesetzt, Payoff fehlt"></i>
                    {% else %}
                    <i class="bi bi-circle" style="color:var(--text-faint);" title="Noch nicht gesetzt"></i>
                    {% endif %}
                </div>
                <div style="flex:1;min-width:0;">
                    <div class="fs-sm fw-semibold">{{ fs.label }}</div>
                    <div class="text-muted fs-xs">
                        {% if fs.foreshadow_type %}{{ fs.foreshadow_type.label }}{% endif %}
                        {% if fs.setup_node %} · Setup: Kap. {{ fs.setup_node.order }}{% endif %}
                        {% if fs.payoff_node %} · Payoff: Kap. {{ fs.payoff_node.order }}{% endif %}
                    </div>
                </div>
                {% if fs.gap_warning %}
                <span class="badge fs-tiny" style="background:#3b1e1e;color:var(--danger);">
                    ⚠ Payoff fehlt
                </span>
                {% endif %}
            </div>
            {% empty %}
            <div class="p-3 text-muted fs-sm text-center">
                Noch kein Foreshadowing geplant.
            </div>
            {% endfor %}
        </div>
    </div>

</div>

<!-- Chart.js Script -->
<script>
(function() {
  const raw = {{ tension_data_json|safe }};
  if (!raw.length) return;

  const OUTCOME_COLORS = {
    yes:     '#22c55e',
    no:      '#ef4444',
    yes_but: '#f59e0b',
    no_and:  '#fb923c',
    '':      '#6366f1',
  };

  const ctx = document.getElementById('tensionChart');
  if (!ctx) return;

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: raw.map(d => `${d.order}. ${d.title}`),
      datasets: [{
        label: 'Spannung',
        data: raw.map(d => d.tension),
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99,102,241,.15)',
        tension: 0.35,
        fill: true,
        pointBackgroundColor: raw.map(d => OUTCOME_COLORS[d.outcome] || '#6366f1'),
        pointRadius: 6,
        pointHoverRadius: 8,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const d = raw[ctx.dataIndex];
              return [
                `Spannung: ${d.tension}/10`,
                d.outcome ? `Outcome: ${d.outcome}` : '',
                d.emotion_start ? `${d.emotion_start} → ${d.emotion_end}` : '',
              ].filter(Boolean);
            }
          }
        }
      },
      scales: {
        y: {
          min: 0, max: 10,
          grid: { color: '#1e2235' },
          ticks: { color: '#94a3b8', stepSize: 2 }
        },
        x: {
          grid: { color: '#1e2235' },
          ticks: {
            color: '#94a3b8',
            maxRotation: 35,
            font: { size: 10 }
          }
        }
      }
    }
  });
})();
</script>
{% endblock %}
```

---

## FE3.5 — URL + Navigation

```python
# apps/projects/urls_html.py
path("<uuid:pk>/drama/", views_html.project_drama_dashboard,
     name="drama_dashboard"),
```

In `project_detail.html` Quick-Action-Badges ergänzen:
```html
<a href="{% url 'projects:drama_dashboard' project.pk %}"
   class="btn btn-accent btn-sm">
    <i class="bi bi-activity me-1"></i>Drama
</a>
```

---

*writing-hub · FE3 · Drama-Dashboard*
*Chart.js CDN, kein Build-Step · Neue Route: /projects/{pk}/drama/*
