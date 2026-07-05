# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden hier festgehalten.
Format angelehnt an [Keep a Changelog](https://keepachangelog.com/de/).

## [0.13.0] – 2026-07-04

### Neu
- **Wirt-Übersetzungstabelle auslagerbar** – die Zuordnung „iNaturalist-Wirtsname → Mykis-Bezeichnung"
  liegt jetzt in `assets/wirt_uebersetzungen.csv` und lässt sich in Excel bearbeiten/erweitern,
  **ohne das Programm zu ändern**. Fehlt oder ist die Datei fehlerhaft, greifen eingebaute Standardwerte.
- **Änderungs-Protokolle als CSV** – zusätzlich zum `.log` entstehen pro Konvertierung strukturierte,
  in Excel auswertbare CSV-Dateien (Zeitstempel im Namen):
  - `..._changes.csv` – alle Feldänderungen der Fundort-/MTB-Zuordnung (je Feld alt → neu).
  - `..._namen.csv` – jede ersetzte Erfasser-Zeile mit `id`, `user_id`, `user_login`, `user_name`,
    `erfasser_alt`, `erfasser_neu`.
  - `..._namen_unique.csv` – jeder Name nur einmal, mit Spalte `anzahl` (wie oft er vorkam).
- **Spalten-Vorschau im Protokoll** – beim Auswählen der Namens- oder Fundort-Referenzliste werden
  deren Spalten sofort im Protokoll angezeigt; zusätzlich eine klare Warnung, wenn die Namensliste
  nicht die Pflichtspalten `user_login`/`mykis-name` hat.
- **Fenster- und Taskleisten-Icon**.

### Geändert
- **GUI modernisiert** – ruhiges, flaches Design; klarere Beschriftungen mit erklärenden Hinweistexten;
  vergrößertes Protokollfeld.
- **Feld „Ungenauigkeit"** wird mit deutschem Dezimalkomma geschrieben (`3.5` → `3,5`).
- **MTB-Zuordnung deutlich schneller** – Punkt-in-Blatt-Suche über einen räumlichen Index (R-Tree)
  statt eines Vollscans über alle TK25-Blätter (bei gleichem Ergebnis).
- **Referenz-Log entschlackt** – Einträge ohne Geokoordinaten werden als Summenzeile statt einer Zeile
  pro Eintrag gemeldet; Einträge ohne Quadrant erzeugen eine Sammel-Warnung.
- Interne Umbenennungen für konsistente Namensgebung (englische Verben, deutsche Fachbegriffe).

### Behoben
- **GUI-Einfrieren/-Abstürze behoben** – Protokoll- und Dialog-Ausgaben aus dem Hintergrund-Thread
  werden jetzt thread-sicher in den Hauptthread geleitet (Tkinter ist nicht thread-safe).
- **„CSV UTF-8"-Dateien (mit BOM)** werden korrekt gelesen – zuvor wurde die erste Spalte nicht erkannt,
  wodurch die Namenskonvertierung still fehlschlug.
- **Kleine Referenzlisten** (z. B. eine 2-spaltige Namensliste) wurden je nach Trennzeichen falsch
  eingelesen – behoben.
- **Absturz bei negativen/ganzzahligen Koordinaten** (z. B. Längengrad `-3`) in der
  Koordinaten-Umwandlung behoben.
- **Namensreihung** mehrteiliger Namen korrigiert: „Hans Peter Müller" → „Müller, Hans Peter".
- **Log-Datei** wird an vorhersehbarer Stelle (neben der `.exe` bzw. in der Projektwurzel) angelegt
  und einmal geöffnet statt bei jeder Zeile.
- Fehlt der Referenzdatei eine Koordinatenspalte (`ostwert2`/`nordwert2`), wird das gemeldet statt
  mitten in der Konvertierung abzustürzen.
- Warnungen zu fehlenden **optionalen** Spalten fluten das Protokoll nicht mehr (nur noch Debug-Log).

### Entwicklung
- **Automatische Tests eingeführt** (pytest, 39 Tests) für die Kernlogik: Rastermathematik der
  MTB-Quadranten, Referenz-Index, Koordinaten-Parsing, Ortsfeld-Extraktion und Namenskonvertierung.
- **Abhängigkeiten deklariert** in `pyproject.toml` (`[project]` + optionale Dev-Werkzeuge); dadurch
  reproduzierbar installierbar.
- Die große MTB-Zuordnungsfunktion in kleine, einzeln testbare Funktionen zerlegt.
- Codebasis durchgängig `black`- und `mypy --strict`-konform.

## [0.12.0] – 2026-07-01

- Stand vor dieser Sitzung (Basis für 0.13.0).
