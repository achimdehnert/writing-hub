# FE2 — HTMX: Partielle Updates & Live-Generation

> **Problem:** Alle Interaktionen sind entweder Full-Page-Reloads oder
> handgeschriebenes vanilla JS fetch() mit polling per `setInterval`.
> Kein HTMX in requirements.txt — aber kein Grund, es nicht zu nutzen.
> **Konsequenz:** Filter-Formulare laden die ganze Seite neu.
> Generation-Status braucht eigenen Polling-Loop mit 5 fetch-Calls.

---

## FE2.1 — HTMX einbinden (CDN, kein pip nötig)

In `base.html` vor `</head>`:

```html
<!-- HTMX 2.x — kein pip, kein Build-Step -->
<script src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.3/dist/htmx.min.js"
        integrity="sha384-..."
        crossorigin="anonymous"></script>
<!-- HTMX SSE Extension für Live-Generation -->
<script src="https://cdn.jsdelivr.net/npm/htmx-ext-sse@2.2.2/sse.js"></script>

<!-- CSRF für HTMX-POST -->
<script>
  document.addEventListener('htmx:configRequest', (e) => {
    e.detail.headers['X-CSRFToken'] = '{{ csrf_token }}';
  });
</script>
```

---

## FE2.2 — Quick Win: Filter-Bar ohne Reload (`project_list.html`)

**Vorher:** Filter-Formular → POST → Full Page Reload

```html
<!-- VORHER -->
<form method="get" class="mb-4">
    ...filter fields...
    <button type="submit" class="btn btn-primary btn-sm">
        <i class="bi bi-funnel"></i>
    </button>
</form>
<div id="projects-grid">
    {% for p in projects %}...{% endfor %}
</div>
```

**Nachher:** Filter → HTMX GET → nur `#projects-grid` austauschen

```html
<!-- NACHHER -->
<form method="get"
      hx-get="{% url 'projects:list' %}"
      hx-target="#projects-grid"
      hx-push-url="true"
      hx-trigger="change from:select, input delay:400ms from:[name='q']"
      class="mb-4">
    ...filter fields...
</form>

<div id="projects-grid"
     hx-get="{% url 'projects:list' %}"
     hx-trigger="revealed"
     hx-swap="outerHTML">
    {% include "projects/_project_grid.html" %}
</div>
```

**Neue Partial-View in `apps/projects/views_html.py`:**

```python
def project_list_partial(request):
    """Gibt nur das Projekt-Grid zurück (für HTMX-Requests)."""
    projects = _filter_projects(request)
    if request.htmx:  # pip install django-htmx
        return render(request, "projects/_project_grid.html",
                      {"projects": projects})
    return render(request, "projects/project_list.html",
                  {"projects": projects, ...})
```

---

## FE2.3 — KI-Generation: HTMX Polling statt setInterval

**Vorher:** `chapter_writer.html` hat ~80 Zeilen JS für Generation-Polling:
```javascript
// 80 Zeilen vanilla JS
function startGeneration(chapterId) {
    fetch('/api/v1/...write/', {method: 'POST', ...})
    .then(r => r.json())
    .then(data => {
        const jobId = data.job_id;
        const pollInterval = setInterval(() => {
            fetch(`/api/v1/.../jobs/${jobId}/status/`)...
        }, 1500);
    });
}
```

**Nachher:** HTMX Polling — 10 Zeilen HTML:

```html
<!-- Generation-Trigger Button -->
<button class="btn btn-accent btn-sm"
        hx-post="{% url 'projects:node_generate' node.id %}"
        hx-target="#gen-result"
        hx-indicator="#gen-spinner"
        hx-disabled-elt="this">
    <i class="bi bi-stars me-1"></i>
    <span class="htmx-indicator">
        <span class="spinner-border spinner-border-sm"></span>
    </span>
    Mit KI generieren
</button>

<!-- Generation Result Container -->
<div id="gen-result"
     hx-get="{% url 'projects:node_status' node.id %}"
     hx-trigger="every 2s [isGenerating]"
     hx-swap="innerHTML">
</div>
```

**View:**
```python
# apps/projects/views_html.py
def node_generate(request, node_id):
    """Startet KI-Generierung, gibt sofort Polling-Fragment zurück."""
    node = get_object_or_404(OutlineNode, id=node_id)
    job = kick_off_generation(node)  # Celery Task
    return render(request, "projects/_gen_status.html",
                  {"job_id": job.id, "node": node})


def node_status(request, node_id):
    """Gibt aktuellen Job-Status zurück (HTMX polling target)."""
    # prüft Job-Status, gibt Fragment zurück
    job = get_latest_job(node_id)
    if job.status == "done":
        return render(request, "projects/_gen_done.html",
                      {"node": job.node, "content": job.result})
    return render(request, "projects/_gen_progress.html",
                  {"job": job, "step": job.progress_step})
```

**`templates/projects/_gen_status.html`:**
```html
<div hx-get="{% url 'projects:node_status' node.id %}"
     hx-trigger="every 2s"
     hx-swap="outerHTML"
     class="d-flex align-items-center gap-2 px-3 py-2"
     style="background:var(--bg-hover);border-radius:var(--radius-sm);">
    <div class="spinner-border spinner-border-sm text-primary"></div>
    <span class="fs-sm" style="color:var(--primary-light);">
        Generiere... ({{ job.progress_step }}/2)
    </span>
</div>
```

---

## FE2.4 — Inline-Speichern: HTMX Form

**Vorher:** Manueller Save-Button + fetch() in JS

**Nachher:**

```html
<!-- chapter_writer.html — Content Editor -->
<form id="chapter-form"
      hx-post="{% url 'projects:node_content' node.id %}"
      hx-trigger="keyup delay:2s, change"
      hx-target="#save-indicator"
      hx-swap="innerHTML">
    {% csrf_token %}
    <textarea name="content"
              id="chapter-content"
              class="form-control"
              style="height:calc(100vh - 200px);font-family:'Courier New',monospace;font-size:.9rem;line-height:1.7;"
              >{{ node.content }}</textarea>
</form>

<div id="save-indicator" class="fs-xs text-muted">
    <!-- HTMX tauscht hier den Status aus -->
</div>
```

**`templates/projects/_save_indicator.html`:**
```html
{% if saved %}
<span style="color:var(--success);">
    <i class="bi bi-check-circle me-1"></i>Gespeichert {{ now|time:"H:i" }}
</span>
{% else %}
<span style="color:var(--warning);">
    <i class="bi bi-exclamation-circle me-1"></i>Fehler beim Speichern
</span>
{% endif %}
```

---

## FE2.5 — Outline-Node: Inline Edit ohne Reload

**Neu:** Direkt im Outline-View den Node-Titel editieren:

```html
<!-- templates/outlines/outline_detail.html — Node-Zeile -->
<div class="outline-node" id="node-{{ node.id }}">
    <span class="node-title"
          hx-get="{% url 'projects:node_edit_form' node.id %}"
          hx-target="#node-{{ node.id }}"
          hx-swap="outerHTML"
          style="cursor:pointer;" title="Klicken zum Bearbeiten">
        {{ node.title }}
    </span>
</div>
```

**Edit-Form (returned by `node_edit_form`):**
```html
<div id="node-{{ node.id }}" class="outline-node">
    <form hx-post="{% url 'projects:node_update' node.id %}"
          hx-target="#node-{{ node.id }}"
          hx-swap="outerHTML">
        {% csrf_token %}
        <div class="d-flex gap-2 align-items-center">
            <input type="text" name="title" value="{{ node.title }}"
                   class="form-control form-control-sm" autofocus>
            <button type="submit" class="btn btn-primary btn-sm">
                <i class="bi bi-check-lg"></i>
            </button>
            <button type="button" class="btn btn-outline-secondary btn-sm"
                    hx-get="{% url 'projects:node_row' node.id %}"
                    hx-target="#node-{{ node.id }}"
                    hx-swap="outerHTML">
                <i class="bi bi-x-lg"></i>
            </button>
        </div>
    </form>
</div>
```

---

## FE2.6 — `django-htmx` installieren (optional aber hilfreich)

```bash
pip install django-htmx
```

```python
# settings.py
INSTALLED_APPS += ["django_htmx"]
MIDDLEWARE += ["django_htmx.middleware.HtmxMiddleware"]
```

```python
# In Views:
def my_view(request):
    if request.htmx:
        return render(request, "partials/_fragment.html", ctx)
    return render(request, "full_page.html", ctx)
```

---

## FE2.7 — Zusammenfassung: Was HTMX ersetzt

| Vorher | Nachher | JS-Einsparung |
|--------|---------|---------------|
| ~80 Zeilen Polling-JS | 15 Zeilen HTMX | -65 Zeilen |
| Filter-Form Full Reload | hx-target Partial | 0 Zeilen JS |
| Manual Save-Button + fetch | hx-trigger delay | -20 Zeilen |
| Inline Edit Modal | hx-swap outerHTML | -40 Zeilen |

**Neue Partial-Templates:**
```
templates/projects/
    _project_grid.html      ← Filter-Ergebnis
    _gen_status.html        ← Polling-Fragment
    _gen_done.html          ← Fertig-Fragment
    _gen_progress.html      ← Fortschritt
    _save_indicator.html    ← Speicherstatus
    _node_row.html          ← Node-Zeile (read)
    _node_edit_form.html    ← Node-Zeile (edit)
```

---

*writing-hub · FE2 · HTMX Partielle Updates*
*CDN, kein Build-Step, kein npm*
