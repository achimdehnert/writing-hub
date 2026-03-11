# WeltenHub-Integration

Welten, Charaktere, Orte und Szenen werden im **WeltenHub** verwaltet.
Das Writing Hub verknüpft Buchprojekte mit WeltenHub-Entitäten.

## Grundprinzip (SSoT)

> **Single Source of Truth:** Alle Weltdaten liegen in WeltenHub.
> Writing Hub speichert nur die Verknüpfung (UUID-Referenz).

## WeltenHub öffnen

In der Sidebar: **WeltenHub ↗** — öffnet [weltenhub.iil.pet](https://weltenhub.iil.pet) in neuem Tab.

## Welt mit Projekt verknüpfen

1. Im Projekt → **Welten**
2. Klicke **Welt generieren** (KI erstellt Welt + speichert in WeltenHub)
3. Oder: bestehende WeltenHub-UUID manuell eintragen

## Welt generieren (KI)

Die KI generiert auf Basis von Titel + Genre eine vollständige Welt:
- Name, Beschreibung, Geographie
- Kulturen, Bewohner, Magie-System
- Technologie-Level, Politik, Geschichte

Die Welt wird **direkt in WeltenHub gespeichert** und mit deinem Projekt verknüpft.

## Charaktere

Unter **Welt-Detail** → **Charaktere generieren**:

- Anzahl wählen (Standard: 5)
- Anforderungen eingeben (z.B. "Protagonistin, weiblich, 30er Jahre")
- KI generiert Charaktere mit Persönlichkeit, Hintergrund, Zielen, Ängsten
- Charaktere werden in WeltenHub gespeichert und mit dem Projekt verknüpft

## Orte

Unter **Welt-Detail** → **Orte generieren**:

- Orte mit Atmosphäre und Bedeutung für die Geschichte
- Werden als `LocationCreateInput` in WeltenHub gespeichert
