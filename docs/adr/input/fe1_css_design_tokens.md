# FE1 — CSS Design Tokens: Inline-Styles eliminieren

> **Problem:** Das gesamte UI ist mit Inline-Styles gebaut.
> `project_detail.html` allein hat 720 Zeilen, davon ~200 mit `style="..."`.
> Jede Farbe (`#0d1117`, `#6366f1`, `#2d3748`) ist 30–50× dupliziert.
> **Ergebnis:** Theme-Änderungen erfordern grep-replace über 30+ Templates.

---

## FE1.1 — Diagnose: Was ist wo inline

```
FARBEN die überall vorkommen (mind. 20× je):
    #0f1117  → page background
    #1a1d27  → sidebar / card background
    #0d1117  → deep background (cards inner)
    #1e2235  → hover / secondary background
    #2d3148  → border color (primary)
    #2d3748  → border color (variant)
    #6366f1  → primary accent (indigo-500)
    #4f46e5  → primary hover (indigo-600)
    #a5b4fc  → primary light (indigo-300)
    #e2e8f0  → text primary
    #94a3b8  → text muted
    #64748b  → text very muted
    #22c55e  → success (written)
    #f59e0b  → warning (empty chapter)

PATTERN-FEHLER:
    style="background:#0d1117;border-color:#2d3748;"  → 40× in project_detail.html
    style="color:#6366f1;"                            → 25× in project_detail.html
    style="font-size:.7rem;"                          → 60× über alle Templates
```

---

## FE1.2 — Solution: CSS Custom Properties in `base.html`

Ersetze den `<style>`-Block in `base.html`:

```html
<!-- templates/base.html — <style> Block ersetzen -->
<style>
  /* ── Design Tokens ─────────────────────────────────────────────────── */
  :root {
    /* Backgrounds */
    --bg-page:       #0f1117;
    --bg-sidebar:    #1a1d27;
    --bg-card:       #0d1117;
    --bg-card-inner: #131929;
    --bg-hover:      #1e2235;
    --bg-header:     #1e2235;

    /* Borders */
    --border:        #2d3148;
    --border-alt:    #2d3748;
    --border-form:   #475569;

    /* Primary (Indigo) */
    --primary:       #6366f1;
    --primary-hover: #4f46e5;
    --primary-light: #a5b4fc;
    --primary-dark:  #1e1b4b;
    --primary-mid:   #3730a3;

    /* Text */
    --text:          #e2e8f0;
    --text-muted:    #94a3b8;
    --text-faint:    #64748b;

    /* Semantic */
    --success:       #22c55e;
    --warning:       #f59e0b;
    --danger:        #ef4444;
    --info:          #38bdf8;

    /* Sizing */
    --sidebar-w:     240px;
    --radius:        .75rem;
    --radius-sm:     .375rem;
  }

  /* ── Base ──────────────────────────────────────────────────────────── */
  body {
    background: var(--bg-page);
    color: var(--text);
    font-family: 'Inter', system-ui, sans-serif;
  }

  /* ── Sidebar ───────────────────────────────────────────────────────── */
  .sidebar {
    background: var(--bg-sidebar);
    border-right: 1px solid var(--border);
    min-height: 100vh;
    width: var(--sidebar-w);
    position: fixed; top: 0; left: 0; z-index: 100;
  }
  .sidebar .nav-link { color: var(--text-muted); padding: .5rem 1.25rem; border-radius: var(--radius-sm); margin: .125rem .5rem; }
  .sidebar .nav-link:hover,
  .sidebar .nav-link.active { color: #fff; background: var(--bg-hover); }
  .sidebar .nav-link i { margin-right: .5rem; }

  /* ── Layout ────────────────────────────────────────────────────────── */
  .main-content { margin-left: var(--sidebar-w); padding: 2rem; }
  .topbar {
    background: var(--bg-sidebar);
    border-bottom: 1px solid var(--border);
    padding: .75rem 2rem;
    margin-left: var(--sidebar-w);
    position: sticky; top: 0; z-index: 99;
  }

  /* ── Cards ─────────────────────────────────────────────────────────── */
  .card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); }
  .card-header { background: var(--bg-header); border-bottom: 1px solid var(--border); }
  .card-inner { background: var(--bg-card-inner); }

  /* ── Buttons ───────────────────────────────────────────────────────── */
  .btn-primary { background: var(--primary); border-color: var(--primary); }
  .btn-primary:hover { background: var(--primary-hover); border-color: var(--primary-hover); }
  .btn-accent {
    background: var(--primary-dark);
    color: var(--primary-light);
    border: 1px solid var(--primary-mid);
  }
  .btn-accent:hover { background: var(--primary-mid); color: #fff; }

  /* ── Forms ─────────────────────────────────────────────────────────── */
  .form-control, .form-select {
    background: var(--bg-card-inner) !important;
    color: var(--text) !important;
    border: 1px solid var(--border-form) !important;
    border-radius: var(--radius-sm);
  }
  .form-control::placeholder { color: var(--text-faint) !important; }
  .form-control:focus, .form-select:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,.25) !important;
  }
  .form-select option { background: var(--bg-hover); color: var(--text); }
  .form-label { color: var(--text-muted); font-weight: 500; }
  .form-text { color: var(--text-faint) !important; }

  /* ── Text Utilities ─────────────────────────────────────────────────── */
  .text-muted  { color: var(--text-muted) !important; }
  .text-faint  { color: var(--text-faint) !important; }
  .text-primary { color: var(--primary) !important; }
  .text-success { color: var(--success) !important; }
  .text-warning { color: var(--warning) !important; }

  /* ── Typography Utilities ───────────────────────────────────────────── */
  .fs-tiny  { font-size: .65rem; }
  .fs-xs    { font-size: .72rem; }
  .fs-sm    { font-size: .8rem; }
  .fs-label { font-size: .7rem; text-transform: uppercase; letter-spacing: .06em; }

  /* ── Stat Card ─────────────────────────────────────────────────────── */
  .stat-card { background: var(--bg-card-inner); border: 1px solid var(--border-alt); border-radius: var(--radius-sm); }
  .stat-val   { font-size: 1.75rem; font-weight: 800; color: var(--primary); line-height: 1; }
  .stat-label { font-size: .7rem; color: var(--text-faint); margin-top: .2rem; }

  /* ── Brand ─────────────────────────────────────────────────────────── */
  .brand { font-size: 1.1rem; font-weight: 700; color: var(--primary); letter-spacing: -.02em; padding: 1.25rem 1.5rem .75rem; }
</style>
```

---

## FE1.3 — Template-Refactor Beispiel

**Vorher** (`project_detail.html`, 40× wiederholt):
```html
<div class="card text-center py-3" style="background:#0d1117;border-color:#2d3748;">
    <div class="fw-bold fs-4" style="color:#6366f1;">{{ stat_words }}</div>
    <div class="text-muted" style="font-size:.7rem;">Wörter</div>
</div>
```

**Nachher:**
```html
<div class="stat-card text-center py-3">
    <div class="stat-val">{{ stat_words }}</div>
    <div class="stat-label">Wörter</div>
</div>
```

**Vorher** (KI-Button, 15× wiederholt):
```html
<button style="background:#1e1b4b;color:#a5b4fc;border:1px solid #3730a3;">
    <i class="bi bi-stars me-1"></i>KI
</button>
```

**Nachher:**
```html
<button class="btn btn-accent btn-sm">
    <i class="bi bi-stars me-1"></i>KI
</button>
```

---

## FE1.4 — Neue Template-Partials Struktur

```
templates/
    base.html               ← CSS Custom Properties hier
    components/
        _stat_card.html     ← Wiederverwendbare Stat-Karte
        _chapter_badge.html ← Kapitel-Status-Badge
        _btn_ai.html        ← KI-Button
        _card.html          ← Standard-Card-Wrapper
        _breadcrumb.html    ← Zurück-Navigation
```

**`templates/components/_stat_card.html`:**
```html
{# Usage: {% include "components/_stat_card.html" with value=stat_words label="Wörter" %} #}
<div class="stat-card text-center py-3">
    <div class="stat-val">{{ value|default:0 }}</div>
    <div class="stat-label">{{ label }}</div>
</div>
```

**`templates/components/_btn_ai.html`:**
```html
{# Usage: {% include "components/_btn_ai.html" with action="startGeneration('...')" label="KI schreiben" %} #}
<button class="btn btn-accent btn-sm" onclick="{{ action }}">
    <i class="bi bi-stars me-1"></i>{{ label|default:"KI" }}
</button>
```

**`templates/components/_breadcrumb.html`:**
```html
{# Usage: {% include "components/_breadcrumb.html" with url=back_url label="Alle Projekte" %} #}
<a href="{{ url }}" class="btn btn-link text-muted ps-0 mb-3 d-inline-flex align-items-center gap-1">
    <i class="bi bi-arrow-left"></i> {{ label }}
</a>
```

---

## FE1.5 — Migrationsplan: Wie refactorn ohne Regressions?

```
SCHRITT 1 — CSS Custom Properties in base.html einführen (30 min)
    → Neue Klassen (.stat-card, .btn-accent, .stat-val, .stat-label)
    → Alte Inline-Styles bleiben zunächst noch — kein Breaking Change

SCHRITT 2 — project_detail.html (720 Zeilen) refactorn (60 min)
    → Alle stat-cards → .stat-card
    → Alle KI-Buttons → .btn-accent
    → Inline-background:... → CSS Custom Properties

SCHRITT 3 — project_list.html, project_form.html (30 min)
    → Form-Controls bereits über :root geregelt
    → Inline-styles in filter-bar eliminieren

SCHRITT 4 — chapter_writer.html (90 min)
    → Komplexeste Datei — hier lohnt sich auch HTMX (→ FE2)

SCHRITT 5 — Restliche Templates (60 min)
    → authoring/, authors/, series/, worlds/
```

---

## FE1.6 — Quick Win: `project_detail.html` Stat-Row

Ersetze diesen Block komplett in `project_detail.html`:

```html
<!-- VORHER: 48 Zeilen mit inline styles -->
<div class="row g-3 mb-4">
    <div class="col-4 col-md-2">
        <div class="card text-center py-3" style="background:#0d1117;border-color:#2d3748;">
            <div class="fw-bold fs-4" style="color:#6366f1;">{{ stat_words|default:0 }}</div>
            <div class="text-muted" style="font-size:.7rem;">Wörter</div>
        </div>
    </div>
    {# ... 5× wiederholt #}
</div>

<!-- NACHHER: 18 Zeilen, klar und wartbar -->
<div class="row g-3 mb-4">
    {% with stats=stat_list %}
    {% for s in stats %}
    <div class="col-4 col-md-2">
        {% include "components/_stat_card.html" with value=s.value label=s.label %}
    </div>
    {% endfor %}
    {% endwith %}
</div>
```

In der View:
```python
context["stat_list"] = [
    {"value": stat_words, "label": "Wörter"},
    {"value": stat_chapters_total, "label": "Kapitel"},
    {"value": stat_characters, "label": "Charaktere"},
    {"value": stat_worlds, "label": "Welten"},
    {"value": stat_chapters_written, "label": "Geschrieben"},
    {"value": f"{progress_pct}%", "label": "Fortschritt"},
]
```

---

*writing-hub · FE1 · CSS Design Tokens*
*Impact: ~60% weniger Inline-Styles, Theme-Änderungen in 1 Datei*
