# UC-002: Neues Projekt erstellen

**Akteur:** Eingeloggter Autor
**Ziel:** Ein neues Buchprojekt anlegen, damit der Autor mit dem Schreiben beginnen kann.

## Vorbedingung
Der Autor ist eingeloggt.

## Hauptszenario
1. Autor klickt auf "Neues Projekt" in der Projektliste
2. System zeigt das Formular "Neues Schreibprojekt"
3. Autor wählt einen Inhaltstyp (Roman, Sachbuch, Kurzgeschichte, Drehbuch, Essay, Novelle, Graphic Novel, Akademische Arbeit, Wissenschaftliches Paper)
4. Autor gibt einen Arbeitstitel ein
5. Autor wählt ein Genre aus 15 Optionen (Fantasy, Science-Fiction, Thriller, Krimi, Romantik, Horror, Historischer Roman, Literarische Fiktion, Young Adult, Kinderbuch, Autobiografie, Sachbuch, Reisebericht, Humor, Mystery)
6. Autor füllt optionale Felder aus (Beschreibung, Zielgruppe, Ziel-Wortanzahl)
7. Autor klickt "Projekt erstellen"

## Fehlerfälle
- Falls der Titel leer ist, zeigt das System eine Fehlermeldung und das Formular bleibt offen.
- Falls der Autor nicht eingeloggt ist, wird er zur Login-Seite umgeleitet (302/403).

## Akzeptanzkriterien
- AK-1: Formular lädt mit HTTP 200 und zeigt "Neues Schreibprojekt"
- AK-2: Unauthentifizierter Zugriff wird mit 301/302/403 abgelehnt
- AK-3: Alle 9 Inhaltstypen sind als Auswahl vorhanden (Roman, Sachbuch, Kurzgeschichte, Drehbuch, Essay, Novelle, Graphic Novel, Akademische Arbeit, Wissenschaftliches Paper)
- AK-4: Arbeitstitel-Feld ist vorhanden
- AK-5: Alle 15 Genres sind vorhanden (Fantasy, Science-Fiction, Thriller, Krimi, Romantik, Horror, Historischer Roman, Literarische Fiktion, Young Adult, Kinderbuch, Autobiografie, Sachbuch, Reisebericht, Humor, Mystery)
- AK-6: Kurzbeschreibung/Prämisse Feld vorhanden
- AK-7: Zielgruppen-Dropdown mit "Erwachsene" Option vorhanden
- AK-8: Ziel-Wortanzahl Feld mit Default 50000 vorhanden
- AK-9: "Projekt erstellen" Submit-Button vorhanden
- AK-10: "Abbrechen" Link führt zurück zu /projekte/
- AK-11: Autoren/Schreibstile Sektion ist sichtbar
- AK-12: Leerer Titel wird abgelehnt (Formular bleibt offen)
- AK-13: Gültige Daten → Projekt wird erstellt (Redirect)

## Scope
Nicht enthalten: Projekt-Import, Bulk-Erstellung, Template-basierte Projekte.
