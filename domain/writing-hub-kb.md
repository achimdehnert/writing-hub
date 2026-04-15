# Domain KB: writing-hub (Creative Writing)

## Glossar

| Begriff | Definition |
|---------|-----------|
| **BookProject** | Zentrales Entity — ein Schreibprojekt eines Autors (Roman, Sachbuch, Essay etc.) |
| **ContentType** | Inhaltstyp eines Projekts: Roman, Sachbuch, Kurzgeschichte, Drehbuch, Essay, Akademische Arbeit, Wissenschaftliches Paper |
| **Genre** | Literarische Gattung: Fantasy, Sci-Fi, Thriller, Krimi, Romantik, Horror etc. (15 Optionen) |
| **Audience** | Zielgruppe: Erwachsene, Young Adult, Kinderbuch etc. |
| **Author** | Autor-Profil mit Name und Bio (1 User → N Authors, Pen-Names möglich) |
| **WritingStyle** | Schreibstil eines Autors mit DO/DONT/Taboo-Regeln (Style Lab) |
| **OutlineFramework** | Strukturierte Gliederungs-Methode (Three Act, Hero's Journey, Save the Cat etc.) |
| **BookSeries** | Container für mehrteilige Werke (z.B. Trilogie) |
| **IdeaImportDraft** | Staging-Tabelle für KI-extrahierte Buchideen (pending_review → committed/discarded) |
| **Ideen-Studio** | Werkzeug zum Brainstormen und Verfeinern von Buchideen |
| **Quick Project** | Schnellerstellung eines Projekts mit Minimal-Daten |

## Pflichtfelder

- **BookProject**: title (str), content_type (Choices), owner (User FK)
- **Author**: name (str), owner (User FK)
- **WritingStyle**: name (str), author (Author FK)
- **BookSeries**: title (str), owner (User FK)

## Invarianten

1. Ein BookProject gehört IMMER genau einem Owner (User)
2. ContentType ist ein enum mit 7 festen Werten (novel, nonfiction, short_story, screenplay, essay, academic, scientific)
3. Genre und Audience sind Lookup-Tabellen (dynamisch erweiterbar)
4. target_word_count hat einen Default von 50.000
5. Projektliste zeigt NUR Projekte des eingeloggten Users (owner-Filter)
6. Unauthentifizierter Zugriff auf /projekte/ → Redirect 302 zu Login
7. Unauthentifizierter Zugriff auf /projekte/new/ → Redirect 302 zu Login

## Scope-Grenzen

- **Nicht enthalten**: Collaboration (Mehrautoren-Projekte)
- **Nicht enthalten**: Bulk-Upload von Projekten
- **Nicht enthalten**: Volltextsuche über Projektinhalte
- **Nicht enthalten**: Projekt-Export als PDF/EPUB (in der Projektliste)

## Navigation (Hauptbereiche)

| URL-Prefix | Bereich | Namespace |
|------------|---------|-----------|
| `/projekte/` | Buchprojekte + Neues Projekt | projects |
| `/projekte/quick/` | Quick Project | projects |
| `/projekte/import/` | Import | projects |
| `/outlines/` | Gliederungen | outlines |
| `/serien/` | Buchserien | series_html |
| `/ideen/` | Ideen | ideas |
| `/ideen/studio/` | Ideen-Studio | ideas |
| `/autoren/` | Autoren & Schreibstile | authors |
| `/welten/` | Welten | worlds_html |

## UI-Pattern

- Projektliste: Card-basiertes Layout mit Titel, Genre, Status, Wortanzahl
- Filter: Suchfeld (Titel), Dropdown (ContentType), Dropdown (Genre)
- Formular: Radio-Buttons für ContentType und Genre, Input für Titel, Textarea für Beschreibung
- HTMX: Partials für Filter-Updates (kein hx-boost — verboten per ADR-048)
