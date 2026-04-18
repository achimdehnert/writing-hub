# Writing-Hub — Priorisierte Use-Case-Liste für Verlage

> **Ziel**: Writing-Hub als strategisches Verlagsprodukt von der Idee bis zum
> druckfertigen Manuskript einsetzen.
>
> **Stand**: 2026-04-18 — basierend auf Codebase-Analyse
>
> **Zielgruppe**: Kleiner Verlag (1–5 Personen), bei dem eine Person oft
> mehrere Rollen gleichzeitig übernimmt: **Autor = Lektor = Verleger**.
> Die Use Cases sind so priorisiert, dass Writing-Hub auch als
> Ein-Personen-Verlagstool sofort Wert liefert.

---

## Legende

| Spalte | Bedeutung |
|--------|-----------|
| **Prio** | P0 = Blocker für MVP, P1 = Kernwert, P2 = Differenzierung, P3 = Nice-to-have |
| **Status** | ✅ vorhanden, 🔶 teilweise, ❌ fehlt |
| **Aufwand** | S = ≤3 Tage, M = 1–2 Wochen, L = 3–6 Wochen, XL = >6 Wochen |

---

## Phase 1: Konzept & Planung

| # | Use Case | Prio | Status | Aufwand | Details |
|---|----------|------|--------|---------|---------|
| 1.1 | **Ideen-Import & Ideenentwicklung** — Rohe Buchideen erfassen, mit KI strukturieren, zur Prämisse verdichten | P1 | ✅ | — | `apps/idea_import/` — Ideen-Studio, Ideen-Import, Prämissen-Generator vorhanden |
| 1.2 | **Projektanlage mit Inhaltstyp-Steuerung** — Roman, Sachbuch, Kurzgeschichte, akademisch anlegen mit typ-spezifischen Workflows | P0 | ✅ | — | `BookProject.content_type` + `ContentTypeLookup` + Quick Project. Sachbuch/Nonfiction gerade frisch implementiert |
| 1.3 | **Framework-basierte Outline-Generierung** — KI-Outline aus 15+ Frameworks (3-Akt, Sachbuch, IMRaD, Dissertation etc.) | P0 | ✅ | — | `OutlineFramework` + `OutlineGeneratorService`, KI-Generator Modal |
| 1.4 | **Kapitelstruktur manuell bearbeiten** — Drag & Drop, Reihenfolge, Beschreibungen, Beats | P0 | ✅ | — | `OutlineVersion` + `OutlineNode` mit CRUD |
| 1.5 | **Verlagsseitige Projekt-Templates** — vordefinierte Buchstrukturen (z.B. "Ratgeber 200 Seiten", "Krimi 80k Wörter") als Vorlage | P1 | ❌ | M | Neue Entity `ProjectTemplate` mit vorgefüllten Werten (Framework, Wortziel, Genre, Zielgruppe). Admin-UI + Template-Picker beim Erstellen |
| 1.6 | **Serien-Management** — Mehrere Bücher einer Reihe verwalten, übergreifende Kontinuität | P2 | ✅ | — | `apps/series/` mit `BookSeries`, `SeriesArc` |

---

## Phase 2: Recherche & Weltenbau

| # | Use Case | Prio | Status | Aufwand | Details |
|---|----------|------|--------|---------|---------|
| 2.1 | **KI-Literaturrecherche** — Brave, Semantic Scholar, arXiv, PubMed, OpenAlex durchsuchen, Quellen übernehmen | P0 | ✅ | — | `citation_service.py` + `views_citations.py`. Sachbuch: Web-Suche. Akademisch: Paper-Suche |
| 2.2 | **DOI/ISBN-Lookup** — Einzelquellen via DOI oder ISBN nachschlagen | P1 | ✅ | — | CrossRef API + OpenLibrary API |
| 2.3 | **BibTeX-Import** — Bestehende Literaturlisten importieren | P1 | ✅ | — | BibTeX-Parser im Citations-Dashboard |
| 2.4 | **Weltenbau** — Orte, Szenen, Welten für Fiktion erstellen und verwalten | P2 | ✅ | — | `apps/worlds/` — Welten, Orte, Szenen mit KI-Generierung |
| 2.5 | **Charakter-Entwicklung** — Figuren mit Profil, Beziehungen, Entwicklungsbogen | P2 | ✅ | — | `apps/worlds/` — CharacterService mit KI |
| 2.6 | **Faktencheck-Service** — KI-gestützte Faktenprüfung für Sachbücher (Behauptungen gegen Quellen abgleichen) | P1 | ❌ | L | Neuer Service: Behauptungen extrahieren → gegen Citation-DB + Web prüfen → Konfidenz-Score. Kritisch für Sachbuch-Verlage |
| 2.7 | **Kapitel-spezifische Recherche** — Pro Kapitel gezielt recherchieren, Ergebnisse dem Kapitel zuordnen | P1 | 🔶 | S | `outline_research` + `node_research` Endpoints existieren, aber Zuordnung Quelle→Kapitel fehlt |

---

## Phase 3: Schreiben & Produktion

| # | Use Case | Prio | Status | Aufwand | Details |
|---|----------|------|--------|---------|---------|
| 3.1 | **KI-Kapitelproduktion** — Brief→Write→Analyze→Gate→Revise Pipeline pro Kapitel | P0 | ✅ | — | `ChapterProductionService` mit 6-stufiger Pipeline, Quality Gate, automatischer Revision |
| 3.2 | **Batch-Schreiben** — Alle/mehrere Kapitel in einem Durchlauf generieren | P0 | ✅ | — | `views_analysis.ProjectBatchView` |
| 3.3 | **Schreibstil-Profile** — Autorenstile definieren und beim Schreiben anwenden | P1 | ✅ | — | `apps/authors/` — WritingStyle + StyleProfile, pro Projekt zuweisbar |
| 3.4 | **Manuskript-Ansicht** — Komplettes Buch als Lese-Ansicht | P0 | ✅ | — | `views_manuscript.py` — Hero-Header, Statistiken, TOC, Kapitel |
| 3.5 | **Drama-Dashboard** — Spannungskurve, Wendepunkte, Pacing visualisieren | P2 | ✅ | — | `DramaDashboardView` + `DramaService` |
| 3.6 | **Inline-Editor für Kapitel** — Kapiteltext direkt im Browser bearbeiten (nicht nur KI) | P0 | 🔶 | M | `ChapterContentView` existiert. Fehlt: Rich-Text-Editor (Markdown/WYSIWYG), Autosave, Versionierung auf Kapitel-Ebene |
| 3.7 | **Co-Authoring / Mehrbenutzerbetrieb** — Mehrere Autoren/Lektoren arbeiten am selben Projekt | P1 | ❌ | XL | Aktuell: `owner`-basiert (Single-User). Benötigt: Rollen (Autor, Lektor, Redakteur, Verleger), Berechtigungen, Kommentar-Threads, Activity-Log |
| 3.8 | **Versionierung & Snapshots** — Manuskript-Stände einfrieren, vergleichen, wiederherstellen | P1 | ✅ | — | `views_versions.py` — Snapshot Create/Detail/Delete |
| 3.9 | **Budget & Kostentracking** — KI-Kosten pro Projekt/Kapitel transparent machen | P2 | ✅ | — | `views_analysis.ProjectBudgetView` |

---

## Phase 4: Review & Qualitätssicherung

| # | Use Case | Prio | Status | Aufwand | Details |
|---|----------|------|--------|---------|---------|
| 4.1 | **KI-Lektorat** — Automatische Prüfung auf Konsistenz, Logik, Stil, Timeline, Pacing | P0 | ✅ | — | `views_lektorat.py` — Session-basiert, Issue-Tracking, KI-Korrekturvorschläge |
| 4.2 | **KI-Review mit Agenten** — Story Editor, Lektor, Beta-Leser, Genre-Experte, Dramaturg | P0 | ✅ | — | `views_review.py` — 5 KI-Agenten, Kapitel-Review, Feedback-Typen |
| 4.3 | **Redaktion / Editing** — KI-gestütztes Lektorat mit konkreten Textvorschlägen | P1 | ✅ | — | `views_review.py` — `ProjectEditingView`, `ChapterAIEditingView` |
| 4.4 | **Beta-Leser-Simulation** — KI simuliert verschiedene Lesertypen | P2 | ✅ | — | `views_knowledge.BetaReaderDashboardView` |
| 4.5 | **Peer Review** — Wissenschaftliche Multi-Agenten-Begutachtung (Methodik, Argumentation, Quellen, Struktur) | P2 | ✅ | — | `views_peer_review.py` — 4 Agenten, nur für academic/scientific/essay |
| 4.6 | **Menschliches Lektorat-Interface** — Lektor gibt Anmerkungen, Autor bearbeitet, Status-Tracking | P0 | 🔶 | M | Review-Add existiert (manuelles Feedback). Fehlt: dediziertes Lektor-UI mit Margin-Kommentaren, Annotationen am Text, Änderungsverfolgung |
| 4.7 | **Qualitäts-Health-Score** — Aggregierter Qualitätswert pro Projekt/Kapitel | P1 | ✅ | — | `views_health.py` — Health-Dashboard, Partial-Updates |
| 4.8 | **Plagiatsprüfung** — Text gegen externe Quellen auf Plagiate prüfen | P1 | ❌ | L | Neuer Service: Paragraphen-Hashing + externe API (Copyscape, Turnitin) oder eigener Embedding-Vergleich |

---

## Phase 5: Publikation & Export

| # | Use Case | Prio | Status | Aufwand | Details |
|---|----------|------|--------|---------|---------|
| 5.1 | **Multi-Format-Export** — Markdown, Text, HTML, PDF (weasyprint), EPUB (ebooklib) | P0 | ✅ | — | `views_export.py` — 5 Formate, Titelseite, Outline-Toggle |
| 5.2 | **Publishing-Profil** — ISBN, Verlagsname, Copyright, Sprache, Altersfreigabe, BISAC-Kategorien | P0 | ✅ | — | `PublishingProfile` + Tab-Navigation (Metadaten, Cover, Front/Backmatter) |
| 5.3 | **Pitch-Paket** — Logline, Exposé, Query Letter, Comparable Titles automatisch generieren | P1 | ✅ | — | `PitchDashboardView` + `GeneratePitchView` — LLM-generiert |
| 5.4 | **KI-Keywords** — Automatische Keyword-Generierung für Metadaten/SEO | P1 | ✅ | — | `PublishingKeywordsAIView` |
| 5.5 | **Druckfertiges PDF** — Professionelle Typografie, Satzspiegel, Schriftauswahl, Seitenzahlen, Kopfzeilen | P0 | 🔶 | L | weasyprint-Export existiert, aber: keine Satzspiegel-Kontrolle, keine Schrift-Auswahl, kein Inhaltsverzeichnis, keine Kolumnentitel. Benötigt: CSS-Print-Stylesheets oder LaTeX-Backend |
| 5.6 | **EPUB-Qualität** — Valides EPUB 3 mit Metadaten, Cover, TOC, CSS-Styles | P1 | 🔶 | M | Basis-EPUB funktioniert. Fehlt: Cover-Bild, EPUB-Validierung, Custom CSS, Schrift-Embedding |
| 5.7 | **Cover-Integration** — Cover-Bild hochladen/generieren, in Export einbetten | P2 | ❌ | M | `PublishingProfile` hat Tab "Cover" aber kein Upload/Generator. Benötigt: Bild-Upload + EPUB/PDF-Integration |
| 5.8 | **Inhaltsverzeichnis** — Automatisch generiertes TOC in Export-Formaten | P1 | 🔶 | S | EPUB hat TOC. PDF/HTML fehlt es |
| 5.9 | **Amazon KDP / Tolino / BoD-Kompatibilität** — Export-Presets für Self-Publishing-Plattformen | P2 | ❌ | L | Format-Validierung, Metadaten-Mapping, Trim-Size-Presets (6x9, A5 etc.) |

---

## Phase 6: Verlag & Zusammenarbeit

> **Kleiner Verlag**: Bei 1–3 Personen ist eine Person oft Autor, Lektor und
> Verleger gleichzeitig. Die Prioritäten berücksichtigen dieses Modell:
> Multi-User ist **kein Blocker** für den MVP — stattdessen braucht der
> Solo-Verleger einen **Rollenwechsel-Workflow**: gleicher User, aber
> unterschiedliche "Hüte" (Schreiben → Lektorieren → Publizieren).

| # | Use Case | Prio | Status | Aufwand | Details |
|---|----------|------|--------|---------|---------|
| 6.1a | **Rollenwechsel-Workflow (Solo)** — Ein User durchläuft Phasen als Autor→Lektor→Verleger mit phasenspezifischer UI | P0 | 🔶 | M | `ProjectPhaseExecution` existiert bereits. Benötigt: aktive Rolle pro Phase anzeigen, phasenspezifische Sidebar/Aktionen, "Hut wechseln"-Button. **Kein Multi-User nötig** |
| 6.1b | **Multi-User mit Rollen (Team)** — Mehrere Personen mit Autor/Lektor/Verleger-Rolle am selben Projekt | P2 | ❌ | L | Team-Model, Einladungs-Link, rollenbasierte Berechtigungen. Erst relevant ab 3+ Personen im Verlag |
| 6.2 | **Verlags-Dashboard** — Überblick über alle Projekte mit Status, Phase, Fortschritt, nächste Aktion | P0 | 🔶 | M | Projektliste existiert. Benötigt: Phasen-Status-Spalte, Fortschrittsbalken, Filter nach Phase/Typ, "Nächster Schritt"-Anzeige. Für Solo-Verleger: Kanban-Board (Idee→Schreiben→Lektorat→Produktion→Fertig) |
| 6.3 | **Deadline & Meilenstein-Tracking** — Abgabetermine, Phasen-Deadlines, Erinnerungen | P1 | ❌ | M | Neues Model: `ProjectMilestone` (Phase, Deadline, Status). Kalender-View, E-Mail-Reminder |
| 6.4 | **Phasen-Checkliste & Gate-Freigabe** — Pro Phase: Checkliste abarbeiten, dann nächste Phase freischalten | P1 | 🔶 | M | `ProjectPhaseExecution` + `gate_approved_by` existiert. Für kleinen Verlag: einfache Checkliste statt komplexer Workflow-Engine. Selbst-Freigabe mit Bestätigungs-Dialog |
| 6.5 | **Notiz-System pro Kapitel** — Eigene Notizen, KI-Feedback und Lektorats-Anmerkungen an einem Ort | P1 | 🔶 | S | ChapterReview existiert. Für Solo: Notizen = Selbst-Kommentare beim Rollenwechsel ("als Lektor notiert: ..."). Inline-Annotationen und @mentions erst für Team-Modus (6.1b) |
| 6.6 | **Aktivitäts-Log / Audit-Trail** — Wer hat wann was geändert | P2 | ❌ | M | Benötigt: Django-Signals oder Middleware für Change-Tracking |
| 6.7 | **API für externe Systeme** — REST/GraphQL für Integration mit Verlagssystemen (ERP, Warenwirtschaft) | P2 | 🔶 | L | Basis-REST existiert (`views.py`). Benötigt: vollständige API, Auth (API-Keys/OAuth), Dokumentation |
| 6.8 | **White-Label / Mandantenfähigkeit** — Mehrere Verlage auf einer Instanz | P3 | ❌ | XL | Django-Tenants oder Schema-basierte Trennung. Branding pro Verlag |
| 6.9 | **Verlagsprofil & Imprint** — Verlagsname, Logo, Standard-Copyright, Standard-Metadaten als Voreinstellung für alle Projekte | P1 | ❌ | S | Neues Model `PublisherProfile` (Name, Logo, Default-Copyright, BISAC-Präferenzen). Wird in `PublishingProfile` als Default übernommen. Spart Eingabe-Zeit bei jedem neuen Buch |

---

## Empfohlene Reihenfolge — Kleiner Verlag (1–3 Personen)

> **Kernidee**: Der Solo-Verleger braucht kein Multi-User-System.
> Er braucht einen **durchgängigen Workflow**, der ihn durch alle Phasen führt —
> vom leeren Projekt bis zur ISBN-fertigen Datei.

### Sprint 1 — "Ein Buch komplett durchbringen" (4–5 Wochen)

*Ziel: Ein Sachbuch oder Roman von der Idee bis zum druckfertigen PDF in Writing-Hub erstellen.*

| Use Case | Aufwand | Warum zuerst |
|----------|---------|-------------|
| **6.1a** Rollenwechsel-Workflow | M | Solo-Verleger sieht phasenspezifische UI: Schreiben→Lektorat→Produktion |
| **3.6** Inline-Editor | M | Ohne manuelles Editieren kein Verlag — Autor muss Text anpassen können |
| **5.5** Druckfertiges PDF | M | Das fertige Produkt. Satzspiegel, Schrift, Seitenzahlen, TOC |
| **6.9** Verlagsprofil | S | Einmal einrichten → Copyright/ISBN/Imprint überall vorausgefüllt |
| **5.8** Inhaltsverzeichnis | S | Pflicht für jedes Buch — PDF und EPUB |

### Sprint 2 — "Qualität sichern" (3–4 Wochen)

*Ziel: Lektorats-Workflow so komfortabel, dass er die externe Lektorin ersetzt (oder ergänzt).*

| Use Case | Aufwand | Warum |
|----------|---------|-------|
| **4.6** Lektor-Interface | M | Solo: "Lektor-Hut aufsetzen" → Annotationen, Vorschläge, Accept/Reject |
| **6.4** Phasen-Checkliste | M | Sicherstellen dass nichts vergessen wird (Lektorat✓ Korrekturlesen✓ ISBN✓) |
| **5.6** EPUB-Qualität | M | E-Book als zweites Auslieferungsformat neben Print |
| **6.5** Notiz-System | S | Eigene Lektorats-Notizen sammeln beim Rollenwechsel |
| **1.5** Projekt-Templates | M | "Ratgeber 200 Seiten" oder "Krimi 80k" als Schnellstart |

### Sprint 3 — "Verlag skalieren" (4–6 Wochen)

*Ziel: Vom Solo-Verleger zum kleinen Team — und mehr Bücher gleichzeitig.*

| Use Case | Aufwand | Warum |
|----------|---------|-------|
| **6.2** Verlags-Dashboard / Kanban | M | Bei 5+ parallelen Projekten den Überblick behalten |
| **6.3** Deadline-Tracking | M | Veröffentlichungstermine einhalten |
| **6.1b** Multi-User (Team) | L | Externe Lektorin oder Co-Autorin einladen |
| **5.7** Cover-Integration | M | Komplettes Buchpaket aus einem System |
| **5.9** KDP/Tolino-Export | L | Self-Publishing-Plattformen bedienen |

### Sprint 4 — Differenzierung (4–6 Wochen)

| Use Case | Aufwand | Warum |
|----------|---------|-------|
| **2.6** Faktencheck | L | USP für Sachbuch-Verlage |
| **4.8** Plagiatsprüfung | L | Qualitätssicherung und Risikominimierung |
| **6.6** Audit-Trail | M | Nachvollziehbarkeit bei mehreren Beteiligten |
| **6.7** API | L | Integration mit Distributoren (KDP, Tolino, BoD) |

### Später / Roadmap
| Use Case | Warum später |
|----------|-------------|
| **6.8** White-Label | Erst bei Multi-Verlag-Betrieb |

---

## Bereits vorhandene Stärken (kein Aufwand)

Writing-Hub bringt diese Features **out of the box** mit — kein weiterer Aufwand nötig:

1. ✅ **15 Outline-Frameworks** (Belletristik, Sachbuch, Akademisch)
2. ✅ **KI-Kapitelproduktion** mit Quality Gate und Auto-Revision
3. ✅ **5 KI-Review-Agenten** (Story Editor, Lektor, Beta-Leser, Genre-Experte, Dramaturg)
4. ✅ **Automatisches Lektorat** mit Issue-Tracking und KI-Korrekturvorschlägen
5. ✅ **Multi-Source-Recherche** (Brave, arXiv, Semantic Scholar, PubMed, OpenAlex)
6. ✅ **5 Export-Formate** (Markdown, Text, HTML, PDF, EPUB)
7. ✅ **Pitch-Paket-Generator** (Logline, Exposé, Query Letter)
8. ✅ **Publishing-Profil** (ISBN, BISAC, Copyright, Metadaten)
9. ✅ **Versionierung & Snapshots**
10. ✅ **Budget- & Kostentracking** für KI-Nutzung
11. ✅ **Health-Score** pro Projekt
12. ✅ **Weltenbau & Charakterentwicklung** (Fiktion)
13. ✅ **Serien-Management** mit Story-Arcs
14. ✅ **Peer Review** für wissenschaftliche Texte
15. ✅ **Batch-Schreiben** (alle Kapitel auf einmal)

---

## Persona: Solo-Verleger — Typischer Tagesablauf mit Writing-Hub

```
09:00  ☕ Verlags-Dashboard öffnen → 3 Projekte im Überblick
       → "Sachbuch Homeoffice" ist in Phase "Lektorat"
       → "Krimi Bodensee" braucht noch 2 Kapitel

09:15  🎩 Hut: AUTOR → Krimi Bodensee
       → Kapitel 8 im Inline-Editor schreiben
       → KI-Vorschlag für Dialog-Passage übernehmen

11:00  🎩 Hut: LEKTOR → Sachbuch Homeoffice
       → KI-Lektorat laufen lassen (5 Kapitel, ~2 Min)
       → 12 Findings durchgehen, 3 akzeptieren, 9 als gelöst markieren
       → Eigene Notiz: "Kapitel 4 braucht bessere Überleitung"

12:00  🎩 Hut: VERLEGER → Sachbuch Homeoffice
       → Publishing-Profil prüfen (ISBN, Copyright, BISAC)
       → Druckfertiges PDF exportieren → Trim Size 13,5×21,5 cm
       → EPUB exportieren → an Tolino-Partner senden

14:00  📋 Checkliste "Sachbuch Homeoffice" → alle Punkte grün
       → Phase "Produktion" abschließen → Status: FERTIG ✅

14:30  💡 Neue Idee im Ideen-Studio erfassen
       → KI generiert Prämisse → als neues Projekt anlegen
       → Template "Ratgeber 200 Seiten" wählen → Outline steht
```

---

## Risiken & Abhängigkeiten

| Risiko | Impact | Mitigation |
|--------|--------|------------|
| LLM-Kosten bei hohem Volumen | Hoch | Budget-Tracking vorhanden, Token-Limits pro Projekt einführen |
| LLM-Qualität bei Fachtexten | Mittel | Quality Gate + menschliches Lektorat als Pflichtschritt |
| Datenschutz (Manuskripte bei OpenAI) | Hoch | Self-hosted LLM-Option oder EU-Anbieter (Mistral, Aleph Alpha) |
| Single-Point-of-Failure (1 Server) | Mittel | Docker-basiert, einfach skalierbar, Backup-Strategie vorhanden |
| Solo-Verleger-Burnout | Mittel | KI-Automatisierung reduziert Aufwand pro Buch um ~60% (Recherche, Lektorat, Pitch) |

---

## Vergleich: Aufwand mit vs. ohne Writing-Hub

| Tätigkeit | Ohne Tool | Mit Writing-Hub | Ersparnis |
|-----------|-----------|-----------------|----------|
| Outline erstellen | 2–3 Tage | 30 Sekunden (KI) + 1h Feinschliff | ~90% |
| Recherche (Sachbuch) | 2–4 Wochen | 1–2 Tage (Multi-Source KI) | ~80% |
| Lektorat (1. Durchgang) | 2–3 Wochen (extern, €800–2000) | 5 Min KI + 2h Review | ~85% |
| Exposé / Pitch schreiben | 1–2 Tage | 2 Min (KI-Generator) | ~95% |
| Publishing-Metadaten | 1–2h pro Buch | 10 Min (Verlagsprofil-Defaults) | ~85% |
| PDF-Satz (InDesign) | 1–2 Wochen (extern, €500–1500) | 1 Klick (druckfertiges PDF) | ~95% |
| **Gesamt pro Buch** | **~3 Monate** | **~2–3 Wochen** | **~70%** |

---

*Erstellt aus der Writing-Hub Codebase (12 Django-Apps, 28+ Models, 40+ Views, 10+ Services).
Optimiert für den Solo-Verleger / Kleinverlag mit Mehrfachrollen.*
