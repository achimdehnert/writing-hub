# FE4 — Essay: Argument-Tree UI

> Nach O3 hat der Hub `EssayOutline` + `ArgumentNode` als DB-Struktur.
> Ein Essay braucht eine andere UI als ein Roman —
> keinen linearen Outline-Tree, sondern einen **Argumentationsbaum**.

---

## FE4.1 — View

```python
# apps/projects/views_html.py
def essay_outline_view(request, pk):
    project = get_object_or_404(BookProject, pk=pk, owner=request.user)
    essay = getattr(project, "essay_outline", None)
    nodes = []
    if essay:
        nodes = list(
            essay.argument_nodes
            .select_related("node_type", "parent")
            .order_by("order")
        )
    return render(request, "projects/essay_outline.html", {
        "project": project,
        "essay": essay,
        "root_nodes": [n for n in nodes if not n.parent_id],
        "all_nodes": nodes,
    })
```

---

## FE4.2 — Template: `templates/projects/essay_outline.html`

```html
{% extends "base.html" %}
{% block title %}Argumentationsstruktur — {{ project.title }}{% endblock %}

{% block content %}
<div style="max-width:960px;margin:0 auto;">

    <!-- Header + These -->
    {% if essay %}
    <div class="card mb-4">
        <div class="card-body p-4">
            <div class="d-flex justify-content-between align-items-start mb-3">
                <h5 class="fw-bold mb-0" style="color:var(--text);">
                    <i class="bi bi-lightbulb me-2 text-primary"></i>These
                </h5>
                <button class="btn btn-accent btn-sm"
                        hx-post="{% url 'projects:essay_generate' project.pk %}"
                        hx-target="#argument-tree"
                        hx-indicator="#gen-spinner">
                    <i class="bi bi-stars me-1"></i>KI generieren
                    <span class="htmx-indicator ms-1">
                        <span class="spinner-border spinner-border-sm" id="gen-spinner"></span>
                    </span>
                </button>
            </div>

            <!-- These / Gegenthese / Synthese -->
            <div class="row g-3">
                <div class="col-md-4">
                    <div class="p-3 rounded" style="background:#1e3a2f;border:1px solid #166534;">
                        <div class="fs-label mb-1" style="color:#4ade80;">THESE</div>
                        <div class="fs-sm">{{ essay.thesis }}</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="p-3 rounded" style="background:#3b1e1e;border:1px solid #991b1b;">
                        <div class="fs-label mb-1" style="color:#f87171;">GEGENTHESE</div>
                        <div class="fs-sm">{{ essay.antithesis|default:"—" }}</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="p-3 rounded" style="background:#1e2a3a;border:1px solid #1d4ed8;">
                        <div class="fs-label mb-1" style="color:#60a5fa;">SYNTHESE</div>
                        <div class="fs-sm">{{ essay.synthesis|default:"—" }}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    <!-- Argument-Tree -->
    <div id="argument-tree">
        {% include "projects/_argument_tree.html" with nodes=root_nodes depth=0 %}
    </div>

</div>
{% endblock %}
```

---

## FE4.3 — Partial: `templates/projects/_argument_tree.html`

```html
{# Rekursiver Argument-Tree #}
{% for node in nodes %}
<div class="argument-node mb-2"
     style="margin-left:{{ depth|add:0 }}rem;">

    <!-- Node Card -->
    <div class="d-flex gap-2 align-items-start p-3 rounded"
         style="background:var(--bg-hover);border:1px solid var(--border);
                border-left:3px solid {% if node.is_counterargument %}var(--danger){% elif node.node_type.code == 'thesis' %}var(--primary){% elif node.node_type.code == 'synthesis' %}#60a5fa{% else %}var(--border){% endif %};">

        <!-- Typ-Badge -->
        <div class="flex-shrink-0">
            <span class="badge fs-tiny"
                  style="background:var(--bg-card);color:var(--text-muted);">
                {{ node.node_type.label|default:"?" }}
            </span>
            <!-- Stärke-Indikator -->
            <div class="mt-1 d-flex gap-1">
                {% for i in "12345"|make_list %}
                <div style="width:6px;height:6px;border-radius:50%;
                            background:{% if forloop.counter <= node.argument_strength|divisibleby:2 %}var(--primary){% else %}var(--border){% endif %};"></div>
                {% endfor %}
            </div>
        </div>

        <!-- Inhalt -->
        <div style="flex:1;min-width:0;">
            <div class="fs-sm fw-semibold mb-1">{{ node.claim }}</div>
            {% if node.supporting_evidence %}
            <div class="text-muted fs-xs">
                <i class="bi bi-journal-text me-1"></i>{{ node.supporting_evidence|truncatechars:120 }}
            </div>
            {% endif %}
            {% if node.is_counterargument and node.is_refuted %}
            <span class="badge fs-tiny mt-1" style="background:#166534;color:#4ade80;">
                ✓ widerlegt
            </span>
            {% elif node.is_counterargument %}
            <span class="badge fs-tiny mt-1" style="background:#991b1b;color:#f87171;">
                ⚠ Widerlegung fehlt
            </span>
            {% endif %}
        </div>

        <!-- Wortanzahl + Edit -->
        <div class="flex-shrink-0 text-end">
            {% if node.target_words %}
            <div class="fs-tiny text-muted">~{{ node.target_words }}W</div>
            {% endif %}
            {% if node.word_count %}
            <div class="fs-tiny" style="color:var(--success);">{{ node.word_count }}W</div>
            {% endif %}
        </div>
    </div>

    <!-- Kinder-Nodes -->
    {% if node.children.all %}
    <div class="mt-1 ps-3" style="border-left:1px solid var(--border);">
        {% include "projects/_argument_tree.html" with nodes=node.children.all depth=depth|add:1 %}
    </div>
    {% endif %}

</div>
{% endfor %}
```

---

## FE4.4 — URL

```python
path("<uuid:pk>/essay/", views_html.essay_outline_view, name="essay_outline"),
```

In `project_detail.html` — conditional je nach content_type:
```html
{% if project.content_type in 'essay,nonfiction' %}
<a href="{% url 'projects:essay_outline' project.pk %}"
   class="btn btn-accent btn-sm">
    <i class="bi bi-list-nested me-1"></i>Argumentation
</a>
{% endif %}
```

---
---

# FE5 — Serie: Arc-Dashboard

> `BookSeries` nach O2 hat `SeriesArc`, `SeriesVolumeRole`, `SeriesCharacterContinuity`.
> Das bestehende `series/list.html` und `series/detail.html` zeigen nur Titel + Bände.
> Diese UI macht den Serien-Arc sichtbar.

---

## FE5.1 — View

```python
# apps/series/views_html.py (ergänzen)
def series_arc_dashboard(request, pk):
    series = get_object_or_404(BookSeries, pk=pk, owner=request.user)
    volumes = list(
        series.volumes
        .select_related("project", "role")
        .order_by("volume_number")
    )
    arc = getattr(series, "arc", None)
    continuities = {}
    for v in volumes:
        conts = list(
            SeriesCharacterContinuity.objects
            .filter(series=series, volume=v)
            .order_by("character_name")
        )
        continuities[v.pk] = conts

    return render(request, "series/arc_dashboard.html", {
        "series": series,
        "arc": arc,
        "volumes": volumes,
        "continuities": continuities,
    })
```

---

## FE5.2 — Template: `templates/series/arc_dashboard.html`

```html
{% extends "base.html" %}
{% block title %}Serien-Arc — {{ series.title }}{% endblock %}

{% block content %}
<div style="max-width:1100px;margin:0 auto;">

    <!-- Serien-Arc Header -->
    {% if arc %}
    <div class="card mb-4">
        <div class="card-header py-2 px-3">
            <span class="fw-semibold fs-sm">
                <i class="bi bi-diagram-3 me-2 text-primary"></i>Serien-Arc
                <span class="badge ms-2 fs-tiny"
                      style="background:var(--bg-hover);color:var(--text-muted);">
                    {{ arc.arc_type.label|default:"Arc-Typ" }}
                </span>
            </span>
        </div>
        <div class="card-body p-3">
            <div class="row g-3">
                <div class="col-md-6">
                    <div class="fs-label mb-1 text-muted">SERIEN-WANT</div>
                    <div class="fs-sm">{{ arc.series_want|default:"—" }}</div>
                </div>
                <div class="col-md-6">
                    <div class="fs-label mb-1 text-muted">SERIEN-NEED</div>
                    <div class="fs-sm">{{ arc.series_need|default:"—" }}</div>
                </div>
                <div class="col-md-6">
                    <div class="fs-label mb-1" style="color:var(--danger);">FALSCHE ÜBERZEUGUNG (ANFANG)</div>
                    <div class="fs-sm">{{ arc.series_false_belief|default:"—" }}</div>
                </div>
                <div class="col-md-6">
                    <div class="fs-label mb-1" style="color:var(--success);">WAHRE ERKENNTNIS (ENDE)</div>
                    <div class="fs-sm">{{ arc.series_true_belief|default:"—" }}</div>
                </div>
                {% if arc.series_theme_question %}
                <div class="col-12">
                    <div class="fs-label mb-1 text-muted">SERIEN-THEMA-FRAGE</div>
                    <div class="fs-sm fst-italic"
                         style="color:var(--primary-light);">
                        „{{ arc.series_theme_question }}"
                    </div>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    {% endif %}

    <!-- Band-Timeline -->
    <div class="card mb-4">
        <div class="card-header py-2 px-3">
            <span class="fw-semibold fs-sm">
                <i class="bi bi-collection me-2 text-primary"></i>Bände
            </span>
        </div>
        <div class="card-body p-3">
            <div class="d-flex gap-3" style="overflow-x:auto;padding-bottom:.5rem;">
                {% for v in volumes %}
                <div class="flex-shrink-0"
                     style="width:220px;background:var(--bg-hover);
                            border:1px solid var(--border);border-radius:var(--radius-sm);
                            padding:1rem;">

                    <!-- Band-Header -->
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="fw-bold" style="color:var(--primary);">Band {{ v.volume_number }}</span>
                        {% if v.role %}
                        <span class="badge fs-tiny"
                              style="background:var(--bg-card);color:var(--text-muted);">
                            {{ v.role.get_arc_position_display }}
                        </span>
                        {% endif %}
                    </div>

                    <div class="fs-sm fw-semibold mb-2">{{ v.project.title }}</div>

                    <!-- Fortschritt -->
                    {% with proj=v.project %}
                    {% if proj.target_word_count %}
                    <div class="mb-2">
                        <div class="d-flex justify-content-between fs-tiny text-muted mb-1">
                            <span>Fortschritt</span>
                        </div>
                        <div class="progress" style="height:4px;background:var(--bg-card);">
                            <div class="progress-bar"
                                 style="width:{% widthratio proj.outline_versions.first.nodes.filter.word_count 1 proj.target_word_count %}%;
                                        background:var(--primary);">
                            </div>
                        </div>
                    </div>
                    {% endif %}
                    {% endwith %}

                    <!-- Cliffhanger -->
                    {% if v.role and v.role.cliffhanger_type != 'none' %}
                    <div class="fs-xs mt-2 p-2 rounded"
                         style="background:var(--bg-card);border:1px solid var(--warning);">
                        <span style="color:var(--warning);">
                            <i class="bi bi-exclamation-triangle-fill me-1"></i>
                        </span>
                        <span class="text-muted">{{ v.role.get_cliffhanger_type_display }}</span>
                    </div>
                    {% endif %}

                    <!-- Versprechen -->
                    {% if v.role and v.role.promise_to_reader %}
                    <div class="fs-xs mt-2 text-muted">
                        <i class="bi bi-arrow-right-circle me-1"></i>
                        {{ v.role.promise_to_reader|truncatechars:60 }}
                    </div>
                    {% endif %}

                    <a href="{% url 'projects:detail' v.project.pk %}"
                       class="btn btn-outline-secondary btn-sm w-100 mt-3 fs-xs">
                        Zum Projekt
                    </a>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- Figur-Kontinuität -->
    {% for v in volumes %}
    {% if continuities|get_item:v.pk %}
    <div class="card mb-3">
        <div class="card-header py-2 px-3">
            <span class="fw-semibold fs-sm text-muted">
                Band {{ v.volume_number }} — Figur-Zustand am Ende
            </span>
        </div>
        <div class="card-body p-0">
            {% for c in continuities|get_item:v.pk %}
            <div class="px-3 py-2 d-flex gap-3"
                 style="border-bottom:1px solid var(--border);">
                <div style="min-width:140px;">
                    <div class="fs-sm fw-semibold">{{ c.character_name }}</div>
                </div>
                <div class="row g-2 flex-grow-1">
                    {% if c.emotional_state %}
                    <div class="col-md-4">
                        <div class="fs-label text-muted mb-1">EMOTIONAL</div>
                        <div class="fs-xs">{{ c.emotional_state|truncatechars:80 }}</div>
                    </div>
                    {% endif %}
                    {% if c.arc_progress %}
                    <div class="col-md-4">
                        <div class="fs-label text-muted mb-1">ARC-STAND</div>
                        <div class="fs-xs">{{ c.arc_progress|truncatechars:80 }}</div>
                    </div>
                    {% endif %}
                    {% if c.unresolved_threads %}
                    <div class="col-md-4">
                        <div class="fs-label mb-1" style="color:var(--warning);">OFFENE FÄDEN</div>
                        <ul class="list-unstyled mb-0">
                            {% for t in c.unresolved_threads %}
                            <li class="fs-xs text-muted">· {{ t }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}
    {% endfor %}

</div>
{% endblock %}
```

---

## FE5.3 — URL + Navigation

```python
# apps/series/urls_html.py
path("<uuid:pk>/arc/", views_html.series_arc_dashboard, name="arc_dashboard"),
```

In `base.html` Sidebar — Series-Link bleibt, Arc-Dashboard über Series-Detail erreichbar.

---

## FE5.4 — Custom Template Filter für `continuities`

```python
# apps/core/templatetags/wh_extras.py
from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    """{{ dict|get_item:key }}"""
    return dictionary.get(key, [])
```

---
---

# Zusammenfassung: Alle FE-Optimierungen

| Schritt | Was | Aufwand | Impact |
|---------|-----|---------|--------|
| FE1 | CSS Custom Properties — Inline-Styles eliminieren | 2h | ~60% weniger Duplizierung |
| FE2 | HTMX — Filter, Generation, Inline-Edit | 4h | -150 Zeilen JS, schnelleres UX |
| FE3 | Drama-Dashboard — Spannungskurve, Emotionsbogen | 3h | Neue Route `/drama/` |
| FE4 | Essay Argument-Tree UI | 2h | Format-spezifische UI |
| FE5 | Series Arc Dashboard | 2h | Band-Timeline, Kontinuität sichtbar |

**Empfohlene Reihenfolge:**
```
FE1 → (sofort, kein Breaking Change, pure Gewinn)
FE2 → HTMX Filter + Inline-Save (größter UX-Impact)
FE3 → Drama-Dashboard (nach Prio-1 Deployment sinnvoll)
FE4 → Essay UI (nach O3 Deployment)
FE5 → Series Arc (nach O2 Deployment)
```

---

*writing-hub · FE4–FE5 + Gesamtübersicht · Essay & Series Frontend*
