# UC-001: Projektliste anzeigen

**Akteur:** Eingeloggter Autor
**Ziel:** Alle eigenen Buchprojekte auf einen Blick sehen, damit der Autor den Überblick über seine laufenden Manuskripte behält.

## Vorbedingung
Der Autor ist eingeloggt und hat mindestens ein Projekt angelegt.

## Hauptszenario
1. Autor navigiert zur Projektliste (/projekte/)
2. System zeigt die Überschrift "Meine Projekte"
3. System zeigt alle Projekte des Autors als Karten an
4. Jede Karte zeigt Titel, Wortanzahl und einen "Öffnen"-Link
5. Navigation enthält Links zu allen Hauptbereichen (Projekte, Outlines, Serien, Ideen, Autoren)

## Fehlerfälle
- Falls keine Projekte vorhanden sind, zeigt das System eine leere Zustandsmeldung.
- Falls der Autor nicht eingeloggt ist, wird er zur Login-Seite umgeleitet (302).

## Akzeptanzkriterien
- AK-1: Seite lädt mit HTTP 200 und enthält "Meine Projekte"
- AK-2: Navigation enthält Links zu /projekte/, /projekte/quick/, /ideen/studio/, /outlines/, /autoren/, /serien/, /ideen/
- AK-3: "Neues Projekt" Button ist sichtbar und verlinkt auf /projekte/new/
- AK-4: Suchfeld "Titel suchen" ist vorhanden
- AK-5: Inhaltstyp-Filter enthält Roman, Sachbuch, Kurzgeschichte, Essay
- AK-6: Genre-Filter enthält Fantasy, Science-Fiction, Thriller, Krimi
- AK-7: Projekt-Cards zeigen Wortanzahl ("Wörter")
- AK-8: "Quick Project" Link auf /projekte/quick/ vorhanden
- AK-9: "Importieren" Link auf /projekte/import/ vorhanden
- AK-10: "Abmelden" Link auf /accounts/logout/ vorhanden

## Scope
Nicht enthalten: Volltextsuche über Projektinhalte, Bulk-Operationen.
