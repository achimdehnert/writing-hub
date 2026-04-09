# Universal Writing Prompt Framework

> Themenagnostisches, formatübergreifendes Prompt-Framework für jede Art von Textarbeit.  
> Unterstützte Formate: Roman · Kurzgeschichte · Essay · Wissenschaftlicher Aufsatz · Seminararbeit · Dissertation · Paper · Sachbuch · Bericht · Handbuch

---

## Architektur

```
Schritt 0  →  Format-Profil wählen
Schritt 1  →  Kontext-Initialisierung (einmalig)
Schritt 2  →  Outline generieren / prüfen
Schritt 3  →  Abschnitt für Abschnitt schreiben
Schritt 4  →  Review & Kohärenzprüfung
```

---

## Schritt 0 — Format-Profil

Wähle ein Profil und speichere es als `{{format_profil}}`.

---

### Profil A: Roman / Kurzgeschichte

```
FORMAT_PROFIL = {
  "typ":            "Roman | Kurzgeschichte",
  "struktur":       "Akt | Kapitel | Szene",
  "pflicht_meta":   ["genre", "pov", "zeitform", "ton", "hauptfigur", "antagonist",
                     "setting", "kernthema", "zielgruppe"],
  "abschnitts_ziel":"dramaturgische Funktion + emotionaler Ton",
  "qualitaet":      "show-don't-tell, subtext, sensorische Details",
  "zitation":       "keine",
  "outline_logik":  "Drei-Akt | Heldenreise | Fünf-Akt | Snowflake"
}
```

---

### Profil B: Essay (akademisch / literarisch)

```
FORMAT_PROFIL = {
  "typ":            "Essay",
  "struktur":       "Einleitung | Hauptteil (Argumente) | Schluss",
  "pflicht_meta":   ["these", "zielgruppe", "ton", "sprache", "zitationsstil"],
  "abschnitts_ziel":"These entfalten und belegen",
  "qualitaet":      "argumentative Dichte, Originalität, Stilsicherheit",
  "zitation":       "optional (akademisch: Pflicht)",
  "outline_logik":  "These → Argument → Gegenargument → Synthese"
}
```

---

### Profil C: Wissenschaftlicher Aufsatz / Paper

```
FORMAT_PROFIL = {
  "typ":            "Wissenschaftlicher Aufsatz | Journal Paper",
  "struktur":       "IMRaD | Einleitung–Theorie–Methode–Ergebnis–Diskussion–Fazit",
  "pflicht_meta":   ["forschungsfrage", "methode", "fachgebiet", "zielgruppe",
                     "zitationsstil", "wortlimit", "keywords"],
  "abschnitts_ziel":"wissenschaftlicher Beitrag zur Forschungsfrage",
  "qualitaet":      "Präzision, Replizierbarkeit, Belegpflicht, Objektivität",
  "zitation":       "Pflicht (APA 7 | IEEE | Chicago | Vancouver)",
  "outline_logik":  "Forschungsfrage → Lücke → Methode → Befund → Implikation"
}
```

---

### Profil D: Seminararbeit / Hausarbeit

```
FORMAT_PROFIL = {
  "typ":            "Seminararbeit | Hausarbeit",
  "struktur":       "Einleitung | Hauptteil (2–4 Kapitel) | Fazit | Literatur",
  "pflicht_meta":   ["thema", "forschungsfrage", "fachgebiet", "hochschule",
                     "betreuer", "seitenzahl", "zitationsstil"],
  "abschnitts_ziel":"Auseinandersetzung mit Forschungsstand + eigene Analyse",
  "qualitaet":      "formale Korrektheit, nachvollziehbare Argumentation",
  "zitation":       "Pflicht",
  "outline_logik":  "Problemstellung → Theorie → Analyse → Ergebnis"
}
```

---

### Profil E: Dissertation / Monographie

```
FORMAT_PROFIL = {
  "typ":            "Dissertation | Monographie",
  "struktur":       "Kapitel (typ. 5–8) + Anhang + Literaturverzeichnis",
  "pflicht_meta":   ["forschungsfrage", "forschungsluecke", "methode", "fachgebiet",
                     "betreuer", "universitaet", "zitationsstil", "sprache",
                     "umfang_seiten", "keywords"],
  "abschnitts_ziel":"originärer wissenschaftlicher Beitrag",
  "qualitaet":      "methodische Strenge, theoretische Tiefe, empirische Fundierung",
  "zitation":       "Pflicht (konsistentes System)",
  "outline_logik":  "Forschungslücke → Theorierahmen → Methodik → Empirie → Diskussion"
}
```

---

### Profil F: Sachbuch / Ratgeber

```
FORMAT_PROFIL = {
  "typ":            "Sachbuch | Ratgeber | Handbuch",
  "struktur":       "Kapitel | Unterkapitel | Praxisboxen",
  "pflicht_meta":   ["thema", "zielgruppe", "ton", "kernbotschaft", "usp",
                     "kapitelanzahl", "zitationsstil"],
  "abschnitts_ziel":"Wissen vermitteln + Leser zur Handlung befähigen",
  "qualitaet":      "Zugänglichkeit, Praxisrelevanz, klare Sprache",
  "zitation":       "optional (Quellenangaben empfohlen)",
  "outline_logik":  "Problem → Lösung → Praxis → Vertiefung"
}
```

---

### Profil G: Bericht / Gutachten

```
FORMAT_PROFIL = {
  "typ":            "Bericht | Gutachten | Technischer Bericht",
  "struktur":       "Executive Summary | Befunde | Empfehlungen | Anhang",
  "pflicht_meta":   ["auftraggeber", "fragestellung", "methode", "zeitraum",
                     "zielgruppe", "format", "zitationsstil"],
  "abschnitts_ziel":"objektive Befunddarstellung + handlungsorientierte Empfehlung",
  "qualitaet":      "Neutralität, Nachvollziehbarkeit, Prägnanz",
  "zitation":       "je nach Auftraggeber",
  "outline_logik":  "Auftrag → Methode → Befund → Bewertung → Empfehlung"
}
```

---

## Schritt 1 — Kontext-Initialisierung (einmalig)

```
# Einmalig ausführen – JSON-Ausgabe als {{werk_kontext}} speichern

Du bist ein professioneller Autor / wissenschaftlicher Schreiber.
Format-Profil: {{format_profil}}

Erstelle das Werk-Profil als JSON. Pflichtfelder laut Profil:
{{format_profil.pflicht_meta}}

Zusätzlich immer:
{
  "titel":          "{{arbeitstitel}}",
  "sprache":        "{{sprache}}",
  "umfang":         "{{zielumfang}}",   // Wörter oder Seiten
  "deadline":       "{{deadline}}",      // optional
  "besonderheiten": "{{besonderheiten}}" // Stilregeln, Formvorgaben, etc.
}

Gib ausschließlich valides JSON zurück. Keine Erklärungen.
```

---

## Schritt 2 — Outline generieren

### 2a — Outline erstellen (wenn noch kein Outline vorhanden)

```
Kontext: {{werk_kontext}}

Erstelle ein vollständiges Outline für {{werk_kontext.titel}}.

Outline-Logik für dieses Format: {{format_profil.outline_logik}}

Für jeden Abschnitt / jedes Kapitel:
- Nummer und Titel
- Funktion im Gesamtwerk (1 Satz)
- Kerninhalt (2–3 Stichpunkte)
- Geschätzter Umfang (Wörter / Seiten)
{{#if format == Roman}}
- Emotionaler Ton
- Dramaturgische Funktion (Exposition | Konflikt | Wendepunkt | Klimax | Auflösung)
{{/if}}
{{#if format == wissenschaftlich}}
- Forschungsbezug (wie trägt dieser Abschnitt zur Forschungsfrage bei?)
- Schlüsselquellen (vorläufig)
{{/if}}

Ausgabe: nummerierte Liste, kein Fließtext.
```

### 2b — Bestehendes Outline prüfen und verbessern

```
Kontext: {{werk_kontext}}

Analysiere das folgende Outline auf:
1. Logische Konsistenz und Vollständigkeit
2. Abdeckung der {{format_profil.outline_logik}}
3. Fehlende Abschnitte oder Redundanzen
4. Proportionalität (Umfang je Abschnitt sinnvoll?)
{{#if wissenschaftlich}}
5. Ist die Forschungsfrage in jedem Abschnitt verankert?
6. Gibt es eine explizite Forschungslücke?
{{/if}}
{{#if Roman}}
5. Ist die emotionale Kurve dramaturgisch tragfähig?
6. Haben Haupt- und Nebenfiguren ausreichend Entwicklung?
{{/if}}

Outline:
---
{{bestehendes_outline}}
---

Ausgabe: Befund + konkrete Verbesserungsvorschläge.
```

---

## Schritt 3 — Abschnitt schreiben

### 3a — Standard-Abschnitts-Prompt (alle Formate)

```
Kontext: {{werk_kontext}}
Abschnitt: {{abschnitt_nummer}} — {{abschnitt_titel}}
Funktion: {{abschnitt_funktion}}
Umfang: ~{{abschnitt_worte}} Wörter

Vorheriger Abschnitt (Kurzfassung): {{vorheriger_abschnitt_summary}}
Nächster Abschnitt (geplant):       {{naechster_abschnitt_titel}}

Inhaltliche Anforderungen:
{{abschnitt_inhalt_stichpunkte}}

Qualitätskriterien für dieses Format: {{format_profil.qualitaet}}

Schluss des Abschnitts: Überleitung zu "{{naechster_abschnitt_titel}}"
```

### 3b — Wissenschaftlicher Abschnitt (Profil C / D / E)

```
Kontext: {{werk_kontext}}
Abschnitt: {{abschnitt_nummer}} — {{abschnitt_titel}}
Umfang: ~{{abschnitt_worte}} Wörter

Forschungsbezug: {{abschnitt_forschungsbezug}}
Schlüsselquellen: {{abschnitt_quellen}}

Pflichtstruktur:
1. Eröffnung: Bezug zur Forschungsfrage / These
2. Hauptinhalt: {{abschnitt_inhalt_stichpunkte}}
3. Kritische Würdigung / Einordnung
4. Überleitung zu {{naechster_abschnitt_titel}}

Zitation: {{werk_kontext.zitationsstil}}
Stil: sachlich, präzise, belegpflichtig.
Keine Wertungen ohne Beleg.
```

### 3c — Erzählerischer Abschnitt / Kapitel (Profil A)

```
Kontext: {{werk_kontext}}
Kapitel: {{kapitel_nummer}} — {{kapitel_titel}}
Emotionaler Ton: {{kapitel_ton}}
Dramaturgische Funktion: {{kapitel_funktion}}
POV: {{werk_kontext.pov}}
Zeitform: {{werk_kontext.zeitform}}

Szenenstruktur:
- Eröffnung (Hook): {{kapitel_hook}}
- Entwicklung: {{kapitel_kernszene}}
- Abschluss: {{kapitel_ausklang}}

Stilregeln:
- Show, don't tell
- Sensorische Details für Ton: {{kapitel_ton}}
- Subtext in Dialogen
- Letzter Satz als Micro-Cliffhanger oder emotionaler Widerhall

Übergang zu Kapitel {{naechstes_kapitel}}: {{uebergangs_hinweis}}
```

### 3d — Argumentativer Abschnitt (Profil B / C)

```
Kontext: {{werk_kontext}}
Abschnitt: {{abschnitt_nummer}} — {{abschnitt_titel}}
These dieses Abschnitts: "{{abschnitts_these}}"
Verhältnis zum Gesamtargument: {{verhaeltnis}}  // vertiefend | kontrastierend | ergänzend

Struktur:
1. These entfalten (2–3 Sätze)
2. Beleg 1: {{beleg_1}}
3. Beleg 2: {{beleg_2}}
4. Gegenargument + Entkräftung: {{gegenargument}}
5. Synthese: Beitrag zur Gesamtthese
6. Überleitung

Stil: argumentativ, differenziert, sprachlich klar.
```

---

## Schritt 4 — Review & Kohärenz

### 4a — Abschnitts-Review

```
Kontext: {{werk_kontext}}

Reviewe den folgenden Abschnitt anhand dieser Kriterien:

Allgemein:
- [ ] Erfüllt der Abschnitt seine Funktion im Gesamtwerk?
- [ ] Ist der Umfang proportional?
- [ ] Ist die Überleitung zum nächsten Abschnitt vorhanden?

Format-spezifisch ({{format_profil.typ}}):
{{#if wissenschaftlich}}
- [ ] Alle Behauptungen belegt?
- [ ] Forschungsfrage im Blick?
- [ ] Zitationsstil konsistent?
- [ ] Keine undefinierten Fachbegriffe?
{{/if}}
{{#if Roman}}
- [ ] Show-don't-tell eingehalten?
- [ ] Emotionaler Ton konsistent?
- [ ] Figurenstimme authentisch?
- [ ] Keine Logikbrüche zur Figurenbiografie?
{{/if}}
{{#if Essay}}
- [ ] These klar erkennbar?
- [ ] Argumentation lückenlos?
- [ ] Gegenposition berücksichtigt?
{{/if}}

Text:
---
{{abschnitts_text}}
---

Ausgabe: Checklistenergebnis + priorisierte Verbesserungsvorschläge.
```

### 4b — Gesamtwerk-Kohärenzprüfung

```
Kontext: {{werk_kontext}}

Prüfe die Kohärenz des Gesamtwerks anhand der Abschnitts-Summaries.

Prüfpunkte:
1. Roter Faden: Ist die {{#if wissenschaftlich}}Forschungsfrage{{/if}}{{#if Roman}}Hauptfiguren-Entwicklung{{/if}}{{#if Essay}}These{{/if}} durchgängig sichtbar?
2. Widersprüche zwischen Abschnitten?
3. Informationswiederholungen / Redundanzen?
4. Fehlende Übergänge oder Brüche?
5. Proportionalität: Welche Abschnitte sind unter-/überdimensioniert?

Abschnitts-Summaries:
---
{{alle_summaries}}
---

Ausgabe: Befund je Prüfpunkt + Handlungsempfehlungen.
```

### 4c — Sprachliches Lektorat

```
Kontext: {{werk_kontext}}

Lektoriere den folgenden Text für Format "{{format_profil.typ}}".

Fokus:
{{#if wissenschaftlich}}
- Präzision: Vage Formulierungen identifizieren und schärfen
- Nominalstil auflösen wo möglich
- Passiv-Konstruktionen prüfen (wann sinnvoll, wann vermeiden?)
- Fremdwörter: definiert oder ersetzbar?
{{/if}}
{{#if Roman}}
- Lesefluss: Satzrhythmus, Absatzlänge
- Adverbien und Adjektive reduzieren
- Dialoge auf Authentizität prüfen
- Perspektivbrüche markieren
{{/if}}
{{#if Essay}}
- Argumentationsklarheit
- Übergänge zwischen Gedanken
- Stilistische Konsistenz
{{/if}}

Text:
---
{{text}}
---

Ausgabe: Annotierter Text mit [KOMMENTAR]-Tags + Zusammenfassung der Hauptprobleme.
```

---

## Spezial-Prompts

### SP-1 — Abstract / Klappentext generieren

```
Kontext: {{werk_kontext}}

Schreibe einen {{#if wissenschaftlich}}Abstract (150–250 Wörter, strukturiert:
Hintergrund – Methode – Ergebnis – Schlussfolgerung){{/if}}
{{#if Roman}}Klappentext (150–200 Wörter, Hook – Figur – Konflikt – Cliffhanger, 
kein Spoiler){{/if}}
{{#if Sachbuch}}Buchbeschreibung (200–250 Wörter, Problem – Lösung – USP – CTA){{/if}}

Basis: folgende Zusammenfassung des Werks:
{{werk_zusammenfassung}}
```

### SP-2 — Kapitel-/Abschnittstitel generieren

```
Kontext: {{werk_kontext}}

Generiere 5 Titeloptionen für Abschnitt {{abschnitt_nummer}}.
Funktion dieses Abschnitts: {{abschnitt_funktion}}
Kerninhalt: {{abschnitt_inhalt_stichpunkte}}

Anforderungen je nach Format:
{{#if wissenschaftlich}} Präzise, informativ, kein Clickbait {{/if}}
{{#if Roman}} Atmosphärisch, andeutend, keine Spoiler {{/if}}
{{#if Sachbuch}} Nutzenorientiert, klar, ggf. mit Zahl oder Versprechen {{/if}}

Gib 5 Optionen mit je 1 Satz Begründung.
```

### SP-3 — Forschungslücke identifizieren (Profil C / D / E)

```
Kontext: {{werk_kontext}}

Analysiere den folgenden Forschungsstand und identifiziere:
1. Die dominante Forschungsperspektive
2. Methodische Lücken (was wurde nicht untersucht?)
3. Theoretische Lücken (was wurde nicht erklärt?)
4. Empirische Lücken (welche Daten fehlen?)
5. Die spezifischste und argumentierbarste Forschungslücke für diesen Aufsatz

Forschungsstand-Text:
---
{{forschungsstand_text}}
---

Ausgabe: Strukturierte Analyse + 1 formulierter Lückensatz für die Einleitung.
```

### SP-4 — Figurenprofil (Profil A)

```
Erstelle ein vollständiges Figurenprofil für {{figur_name}}.

Pflichtfelder:
- Äußeres (nur das Wesentliche, das die Figur charakterisiert)
- Innerer Kernkonflikt (1 Satz)
- Wunsch (was will die Figur bewusst?)
- Bedürfnis (was braucht die Figur wirklich?)
- Wunde (prägendes Erlebnis der Vergangenheit)
- Fehlglaube (falsche Überzeugung über sich/die Welt)
- Stimme (Sprachmuster, Wortwahl, Rhythmus)
- Verhältnis zur Hauptfigur: {{verhaeltnis_zur_hauptfigur}}
- Entwicklungsbogen über das Werk

Werk-Kontext: {{werk_kontext}}
```

### SP-5 — Literaturrecherche-Prompt (Profil C / D / E)

```
Kontext: {{werk_kontext}}

Erstelle eine strukturierte Recherche-Anfrage für Abschnitt "{{abschnitt_titel}}".

Gesuchte Quellentypen:
- Grundlagenwerke (Monographien/Lehrbücher)
- Aktuelle empirische Studien ({{recherche_zeitraum}})
- Reviews / Meta-Analysen
- Kontroverse Positionen / Gegenargumente

Suchbegriffe (Deutsch + Englisch):
{{suchbegriffe}}

Bewertungskriterien für Quellen:
- Peer-reviewed bevorzugt
- Impact Factor / Zitationshäufigkeit
- Aktualität vs. Klassiker abwägen
- Primär- vor Sekundärquellen

Ausgabe: Bewertete Quellenliste mit Kurz-Annotation je Quelle.
```

---

## Variablen-Gesamtübersicht

### Universal (alle Formate)

| Variable | Beschreibung |
|---|---|
| `{{format_profil}}` | Gewähltes Profil (A–G) |
| `{{werk_kontext}}` | JSON aus Schritt 1 |
| `{{arbeitstitel}}` | Arbeitstitel des Werks |
| `{{sprache}}` | Deutsch / Englisch / … |
| `{{zielumfang}}` | Wörter oder Seiten |
| `{{abschnitt_nummer}}` | z.B. §3 oder Kapitel 5 |
| `{{abschnitt_titel}}` | Titel des Abschnitts |
| `{{abschnitt_funktion}}` | Funktion im Gesamtwerk |
| `{{abschnitt_worte}}` | Ziel-Wörter dieses Abschnitts |
| `{{vorheriger_abschnitt_summary}}` | 3–5 Sätze Kurzfassung |
| `{{naechster_abschnitt_titel}}` | Für Überleitung |

### Wissenschaftlich (C / D / E)

| Variable | Beschreibung |
|---|---|
| `{{forschungsfrage}}` | 1 präziser Fragesatz |
| `{{forschungsluecke}}` | Explizit benannte Lücke |
| `{{methode}}` | Qualitativ / quantitativ / Mixed |
| `{{zitationsstil}}` | APA 7 / IEEE / Chicago / … |
| `{{schluessel_quellen}}` | Min. 3 Quellen mit Jahr |
| `{{abschnitts_these}}` | These dieses Abschnitts |
| `{{gegenargument}}` | Einwand + Entkräftung |

### Narrativ (A)

| Variable | Beschreibung |
|---|---|
| `{{genre}}` | z.B. Psychothriller, Fantasy |
| `{{pov}}` | Ich / 3. Person nah / auktorial |
| `{{zeitform}}` | Präteritum / Präsens |
| `{{kapitel_ton}}` | Emotionaler Ton |
| `{{kapitel_funktion}}` | Exposition / Konflikt / Klimax / … |
| `{{kapitel_hook}}` | Eröffnungsszene |
| `{{kapitel_kernszene}}` | Hauptszene |
| `{{figur_name}}` | Name der Figur (für SP-4) |

---

## Nutzungsreihenfolge

```
1. Schritt 0   → Format-Profil (A–G) wählen und speichern
2. Schritt 1   → Kontext-Init ausführen → {{werk_kontext}} speichern
3. Schritt 2a  → Outline erstellen ODER
   Schritt 2b  → Bestehendes Outline prüfen
4. Schritt 3   → Je Abschnitt den passenden Sub-Prompt wählen:
                 3a (universal) | 3b (wissenschaftlich) |
                 3c (narrativ)  | 3d (argumentativ)
5. Schritt 4a  → Jeden Abschnitt reviewen
6. Schritt 4b  → Gesamtwerk-Kohärenz prüfen
7. Schritt 4c  → Lektorat
8. SP-1        → Abstract / Klappentext
```
