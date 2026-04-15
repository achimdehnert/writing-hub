# UC-003: Projekt-Detailseite

## Akteur
Authentifizierter Autor

## Ziel
Alle relevanten Informationen und Workflow-Aktionen eines Buchprojekts auf einer Übersichtsseite sehen und nutzen.

## Vorbedingungen
- Autor ist eingeloggt
- Mindestens ein BookProject existiert

## Hauptszenario
1. Autor navigiert zur Projekt-Detailseite `/projekte/<uuid>/`
2. System zeigt Projekt-Header mit Titel, Genre und Typ
3. System zeigt Quick-Action-Buttons: Schreiben, KI-Schreiben, Outline, KI-Outline, Drama, Health, Pitch, Analyse, Batch, Budget, Recherche, Quellen, Beta, Einstellungen
4. System zeigt Statistik-Kästchen: Wörter, Kapitel, Charaktere, Welten, Geschrieben, Fortschritt
5. System zeigt Gesamtfortschritt mit Wort- und Kapitel-Balken
6. System zeigt Workflow-Phasen als klickbare Karten: Konzept, Charaktere, Weltenbau, Outline, Schreiben, Lektorat, Review, Illustration, Publishing, Export
7. Jede Workflow-Karte ist klickbar und navigiert zur jeweiligen Detailseite
8. System zeigt Outline-Detail mit Kapitel-Liste
9. System zeigt Sidebar mit verknüpften Welten und Charakteren

## Fehlerfälle
- E-1: Nicht eingeloggt → Redirect zu Login
- E-2: Projekt-UUID nicht gefunden → 404
- E-3: Projekt gehört anderem User → 404

## Akzeptanzkriterien
- AK-1: Seite lädt mit HTTP 200
- AK-2: Projekt-Titel wird angezeigt
- AK-3: Navigation "Alle Projekte" ist vorhanden
- AK-4: Quick-Action-Button "Schreiben" ist vorhanden
- AK-5: Quick-Action-Button "Health" ist vorhanden
- AK-6: Statistik "Wörter" wird angezeigt
- AK-7: Statistik "Kapitel" wird angezeigt
- AK-8: Gesamtfortschritt-Balken ist vorhanden
- AK-9: Workflow-Phase "Lektorat" ist klickbar (enthält URL /lektorat/)
- AK-10: Workflow-Phase "Review" ist klickbar (enthält URL /review/)
- AK-11: Workflow-Phase "Publishing" ist klickbar (enthält URL /publishing/)
- AK-12: Workflow-Phase "Export" ist klickbar (enthält URL /export/)
- AK-13: Workflow-Phase "Konzept" ist klickbar (enthält URL /edit/)
- AK-14: Bearbeiten-Button ist vorhanden
- AK-15: Outline-Bereich zeigt Kapitel oder Empty-State
- AK-16: Sidebar zeigt Welten- und Charaktere-Bereich
- AK-17: Workflow-Karte "Charaktere" hat onclick-Handler (nicht nur cursor:pointer)
- AK-18: Workflow-Karte "Weltenbau" hat onclick-Handler (nicht nur cursor:pointer)

## Scope
- IN: Projekt-Dashboard, Workflow-Navigation, Statistiken, Outline-Anzeige
- OUT: Kapitel-Schreiben, KI-Generierung, Lektorat-Prüfung (eigene UCs)
