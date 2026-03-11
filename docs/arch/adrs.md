# Architecture Decision Records (ADRs)

## ADR-001: WeltenHub als SSoT fuer Weltendaten

**Status:** Accepted

**Kontext:**
Writing Hub benoetigt Zugriff auf Welten, Charaktere, Orte und Szenen.
Diese Daten werden auch in WeltenHub verwaltet.

**Entscheidung:**
Writing Hub speichert **keine Kopien** von WeltenHub-Entitaeten.
Stattdessen werden nur UUID-Referenzen in Link-Modellen gespeichert.
Alle Lesezugriffe gehen direkt an die WeltenHub-API via `iil-weltenfw`.

**Konsequenzen:**
- (+) Keine Datensynchronisation noetig
- (+) Aenderungen in WeltenHub sofort sichtbar
- (-) Abhaengigkeit von WeltenHub-Verfuegbarkeit
- (-) Latenz bei Seitenaufrufen mit vielen WeltenHub-Calls

---

## ADR-002: iil-aifw als LLM-Abstraktionsschicht

**Status:** Accepted

**Kontext:**
LLM-Aufrufe werden in mehreren Apps benoetigt.
Direkte OpenAI-SDK-Nutzung erzeugt Vendor Lock-in.

**Entscheidung:**
Alle LLM-Aufrufe gehen ueber `iil-aifw.LLMRouter`.
Kein direkter Import von `openai` in App-Code.

**Konsequenzen:**
- (+) LLM-Backend austauschbar ohne App-Aenderungen
- (+) Zentrales Logging aller LLM-Calls via `action_code`
- (-) Abhaengigkeit von iil-aifw-Package

---

## ADR-003: JSONField fuer Style-Lab-Listen

**Status:** Accepted

**Kontext:**
`WritingStyle` benoetigt Listen fuer DO/DONT/Taboo/Signature Moves.
`ArrayField` von `django.contrib.postgres` ist SQLite-inkompatibel.

**Entscheidung:**
`JSONField` statt `ArrayField` fuer alle Listen in `WritingStyle`.

**Konsequenzen:**
- (+) SQLite-kompatibel fuer lokale Entwicklung
- (+) Kein Django-Contrib-Postgres-Dependency noetig
- (-) Kein DB-Level Array-Querying

---

## ADR-004: Separate Link-Tabellen fuer WeltenHub-Referenzen

**Status:** Accepted

**Kontext:**
Ein Projekt kann mit einer Welt, mehreren Charakteren, Orten und Szenen
verknüpft sein.

**Entscheidung:**
Jeder Entitaetstyp bekommt eine eigene Link-Tabelle:
`ProjectWorldLink`, `ProjectCharacterLink`, `ProjectLocationLink`, `ProjectSceneLink`.

**Konsequenzen:**
- (+) Klare Trennung, einfach erweiterbar
- (+) `unique_together` verhindert Duplikate pro Entitaetstyp
- (-) 4 statt 1 Tabellen

---

## ADR-005: promptfw mit Fallback

**Status:** Accepted

**Kontext:**
`iil-promptfw` ist optional und Templates koennen fehlen.

**Entscheidung:**
Immer `has_template()` pruefen und Inline-Fallback implementieren.
Kein Fehler wenn Template nicht verfuegbar.

**Konsequenzen:**
- (+) Robustheit gegenueber fehlenden Templates
- (+) Einfaches Testen ohne promptfw-Templates
- (-) Doppelter Code (Template + Fallback)

---

## ADR-006: UUID als Primary Key

**Status:** Accepted

**Kontext:**
Sequentielle Integer-PKs in URLs sind ein Sicherheitsrisiko (IDOR).

**Entscheidung:**
Alle Hauptmodelle verwenden `UUIDField(primary_key=True, default=uuid.uuid4)`.

**Konsequenzen:**
- (+) Kein Enumeration-Angriff moeglich
- (+) Konsistent mit WeltenHub-IDs
- (-) Groessere URLs
