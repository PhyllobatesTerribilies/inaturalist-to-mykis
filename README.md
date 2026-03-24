# inat-to-mykis

Konvertiert iNaturalist-Exporte (CSV/XLS(X)) in ein MykIS-kompatibles Format.

## Features
- Robust: liest Excel oder CSV (`;`/`,`), Fallback auf Standard-CSV.
- Mapping: iNat-Felder → MykIS-Spalten.
- Validierung: meldet fehlende Felder und Formatprobleme.
- GUI: einfache Bedienung ohne Kommandozeile.
- Zusätzliche Spalten:
  - **Taxon** als `Gattung` und `Art` (Epithet)
  - **Koordinaten** zusätzlich in DMS (`geol*`/`geob*` 1 & 2)

## Installation (lokal)

Voraussetzung: Python 3.10+

```bash
pip install pandas openpyxl
# optional fürs Packaging:
pip install pyinstaller
```

> Windows-Nutzer: Start der GUI per Doppelklick auf `inat_to_mykis_gui.py` (wenn `.py` mit Python verknüpft ist) oder:
>
> ```bash
> python inat_to_mykis_gui.py
> ```

## Verwendung

### GUI
1. Eingabedatei wählen (`.csv`, `.xlsx`, `.xls`)
2. Ausgabedatei wählen (`.xlsx` oder `.csv`)
3. Optional „Nur Pilze (Fungi)“ aktivieren
4. „Konvertieren“ klicken

Im Protokoll erscheinen Header, Hinweise/Fehler, und am Ende eine Zusammenfassung.


## Eingabefelder (iNat)
- **Taxon (Pflicht):** `scientific_name` **oder** `taxon_name` **oder** `species_guess`
- **Datum (Pflicht):** `observed_on` **oder** `observed_on_string`
- **Optional:** `latitude`, `longitude`, `place_guess`, `user_name`/`user_login`, `image_url`/`sound_url`, `taxon_id`

## Ausgabeschema (MykIS)
- **Gattung**, **Art** (Art = Epithet; voller Name wird nicht mehr ausgegeben)
- **Datum** (TT.MM.JJJJ), **Uhrzeit** (HH:MM:SS, falls vorhanden)
- **Breite**, **Länge** (Dezimalgrad)
- **DMS-Koordinaten**:  
  `geolgrad1, geolminute1, geolsekunde1, geobgrad1, geobminute1, geobsekunde1, geolgrad2, geolminute2, geolsekunde2, geobgrad2, geobminute2, geobsekunde2`
- **Ort**, **Fundkommentar**, **Quelle**, **Sammler**, **Bestimmer**, **MedienURL**, **Genauigkeit_m**, **Taxon_ID**, **iNat_URL**

## Validierung
- **Datum:** leer oder falsches Format (soll **TT.MM.JJJJ** sein)
- **Art:** leer (d. h. Epithet fehlt)
- **Ort:** leer
- **Nur Gattung:** wird berichtet (Gattung gesetzt, Art leer)

## Entwicklung

### Versionierung
- Versionen in `version.py` pflegen:
  ```python
  __version__ = "0.2.0"
  __date__    = "2025-09-30"
  ```

### Changelog
- Änderungen in `CHANGELOG.md` dokumentieren (Abschnitt **[Unreleased]** → neue Version).

### Git-Workflow (Beispiel)

```bash
git init
git add .
git commit -m "feat: initial GUI + mapping updates"
# Release 0.2.0
# 1) version.py auf 0.2.0 setzen, 2) CHANGELOG.md aktualisieren
git commit -am "chore(release): 0.2.0"
git tag -a v0.2.0 -m "inat-to-mykis 0.2.0"
git push --tags
```

### Optional: EXE bauen (Windows)

```bash
pyinstaller --onefile --noconsole --name inat-to-mykis-gui inat_to_mykis_gui.py
# Ergebnis unter dist/inat-to-mykis-gui.exe
```

## Lizenz
MIT (oder passend zu deinem Projekt)
