# Betriebsanleitung – inat-to-mykis

**Version:** 0.3.0  
**Datum:** 2026-02-16

---

## 1. Einleitung

Das Programm **inat-to-mykis** konvertiert Pilzbeobachtungen aus **iNaturalist** in ein Format, das in **MykIS** (Mykologisches Informationssystem) importiert werden kann. 

### Unterstützte Formate:

- **Eingabe:** CSV, XLSX, XLS
- **Ausgabe:** XLS, XLSX, CSV

---

## 2. Installation & Start

### 2.1 Programmstart

**Option 1: Ausführbare Datei (empfohlen)**

```
Doppelklick auf: inat-to-mykis.exe
```

### 2.2 Hauptfenster

Nach dem Start öffnet sich das Hauptfenster:

![](C:\Users\Julian%20Grausgruber\AppData\Roaming\marktext\images\2026-03-15-18-02-35-image.png)**Legende:**

- GRÜN **Eingabefeld:** iNaturalist-Exportdatei
- ROT **Ausgabefeld:** Ziel für konvertierte Datei
- ROSA **Fundort Zuordnungs Liste:** Live-Status und Meldungen
- GELB **Optionen:** Anhängen an bestehende Datei
- BLAU **Protokoll:** Live-Status und Meldungen

---

## 3. Bedienung

### 3.1 Einfache Konvertierung (Neue Datei)

**Schritt 1:** Eingabedatei wählen

- Klick auf **Durchsuchen…** (bei Eingabedatei)
- Wähle iNaturalist-Export (z.B. `observations-527425.csv`)

**Schritt 2:** Ausgabedatei prüfen

- Automatischer Vorschlag: `observations-527425_mykis.xls`
- Optional: Klick auf **Ziel wählen…** zum Ändern

**Schritt 3:** Konvertieren

- Klick auf **Konvertieren**
- Fortschritt im Protokollfenster verfolgen

**Protokoll-Ausgabe (Beispiel):**

```
📂 Lese observations-527425.csv...
INFO: Tabelle eingelesen
- Zeilen:  216
- Spalten: 58

🔄 Konvertiere nach Mykis-Format...
✅ Mapping abgeschlossen: 216 Zeilen

💾 Speichere observations-527425_mykis.xls...

==================================================
✅ Konvertierung erfolgreich!
==================================================
Zeilen: 216
Datei: C:\...\observations-527425_mykis.xls
==================================================
```

---

### 3.2 Anhängen an bestehende Datei

**Schritt 1:** Eingabedatei wählen

- Neue iNaturalist-Beobachtungen laden

**Schritt 2:** Anhänge-Modus aktivieren

- Checkbox aktivieren: **"An bestehende Mykis-Datei anhängen"**
- Button ändert sich zu: **"Datei zum Anhängen wählen…"**

**Schritt 3:** Bestehende Datei wählen

- Klick auf **Datei zum Anhängen wählen…**
- Wähle bestehende Mykis-Datei (z.B. `mykdaten.xls`)

**Schritt 4:** Konvertieren

- Neue Daten werden **unten an** die bestehende Datei angehängt
- Die ausgewählte Datei wird **überschrieben** (Backup empfohlen!)

**Protokoll-Ausgabe (Beispiel):**

```
📂 Lese observations-week2.csv...
INFO: Tabelle eingelesen
- Zeilen:  30

🔄 Konvertiere nach Mykis-Format...
✅ Mapping abgeschlossen: 30 Zeilen

📎 Anhänge-Modus: Lade bestehende Datei 2026-02_mykdaten.xls
   📊 Bestehende Datei: 150 Zeilen, 45 Spalten
   ✅ Erfolgreich angehängt
   📊 Vorher: 150 Zeilen
   📊 Hinzugefügt: 30 Zeilen
   📊 Gesamt: 180 Zeilen

💾 Speichere 2026-02_mykdaten.xls...

==================================================
✅ Konvertierung erfolgreich!
==================================================
```

---

### 3.3 Spalten-Kompatibilitätsprüfung

Beim Anhängen prüft das Programm automatisch die Spaltenübereinstimmung. Es ist eine Referenz mykdaten.xls hinterlegt, mit der die bestehende Datei beim Anhängen überprüft wird ob alle Spalten vorhanden sind.

**Szenario: Spalten stimmen NICHT überein**

```
⚠️  WARNUNG: Spalten stimmen nicht überein!
   Fehlen in bestehender Datei (2):
      - sammler
      - BASIS_datum1

   Fehlen in neuen Daten (1):
      - alte_spalte

┌────────────────────────────────────────────┐
│ Spalten unterschiedlich                    │
├────────────────────────────────────────────┤
│ Die Spalten stimmen nicht überein!         │
│                                            │
│ Bestehende Datei: 45 Spalten               │
│ Neue Daten: 46 Spalten                     │
│ Fehlende Spalten: 3                        │
│                                            │
│ Trotzdem fortfahren?                       │
│ (Details siehe Protokoll)                  │
│                                            │
│         [Ja]           [Nein]              │
└────────────────────────────────────────────┘
```

**Was passiert bei "Ja"?**

- Fehlende Spalten in neuen Daten: bleiben leer in neuen Zeilen
- Zusätzliche Spalten in neuen Daten: werden zur Datei hinzugefügt
- Alte Zeilen: neue Spalten bleiben leer

---

## 4. Spalten-Mapping: iNaturalist → Mykis

### 4.1 Übersicht der Hauptspalten

| iNaturalist Feld                                | Mykis Spalte              | Beschreibung                                                       |
| ----------------------------------------------- | ------------------------- | ------------------------------------------------------------------ |
| `scientific_name`                               | `GATTUNG` + `ART`         | Wird aufgetrennt (z.B. "Amanita muscaria" → "Amanita", "muscaria") |
| `observed_on`                                   | `BASIS_datum1` + `datum2` | Datum im Format TT.MM.JJJJ                                         |
| `user_name` / `user_login`                      | `erfasser`                | iNaturalist-Benutzername                                           |
| `url`                                           | `nachweisquelle`          | Link zur iNaturalist-Beobachtung                                   |
| `image_url`                                     | `Foto_Zeichnung`          | Link zum Foto                                                      |
| `latitude`                                      | `nordwert2`               | Breitengrad (Y-Koordinate)                                         |
| `longitude`                                     | `ostwert2`                | Längengrad (X-Koordinate)                                          |
| `description`                                   | `substrat_text`           | Beobachtungsnotizen                                                |
| `field:mykis-leg.` / `user_name` / `user_login` | `sammler`                 | Sammler / Finder                                                   |
| `field:mykis-det.` / `user_name` / `user_login` | `bestimmer`               | Bestimmer                                                          |
|                                                 |                           |                                                                    |

### 4.2 Ortsdaten

Das Programm nutzt die iNaturlist Felder  `place_country_name`, `place_state_name`,sowie `place_guess`.

Wenn die Felder `place_country_name`, `place_state_name` nicht verfürgbar sind bzw. nicht mit exportiert werden, wird stattdessen das Feld `place_guess`

strukturierte iNaturalist-Felder mit automatischem Fallback auf `place_guess`

#### Land (name_staat)

```
Primär:   place_country_name → "Germany"
          ↓ Normalisierung
          "Deutschland"

Fallback: place_guess (letzter Teil bei 2+ Teilen)
          "Berlin, Deutschland" → "Deutschland"
          "Wald, Bayern, DE" → "DE" → "Deutschland"

Minimum:  2 Teile erforderlich
          "Kiel" → "" (zu wenig Information)
```

Die Land Namen Germany, de, deu, deutschland werden alle umgewandelt in den Namen Deutschland (Norminalisierung)

#### Bundesland (name_provinz)

```
Primär:   place_state_name
          "Bayern", "Schleswig-Holstein"

Fallback: place_guess (vorletzter Teil bei 3+ Teilen)
          "Berlin, Brandenburg, Deutschland" → "Brandenburg"
          "Wald, Erlangen, Bayern, DE" → "Bayern"

Minimum:  3 Teile erforderlich
```

#### Fundort (BASIS_ort)

```
Adaptive Logik basierend auf Anzahl der Teile in place_guess:

1-3 Teile: Erster Teil
  "Kiel" → "Kiel"
  "Bosau, Deutschland" → "Bosau"
  "Berlin, Brandenburg, Deutschland" → "Berlin"

4+ Teile: Zweiter Teil
  "Meilwald, Erlangen, Bayern, DE" → "Erlangen"
```

#### Standortbeschreibung (BASIS_ortslage)

```
Quelle:   place_guess (erster Teil bei 4+ Teilen)
          "Meilwald mit Eisgrube, Erlangen, Bayern, DE" 
          → "Meilwald mit Eisgrube"
```

### 4.3 Mykis Custom Fields

Diese Spalten werden aus iNaturalist Custom Fields übernommen:

| iNaturalist Custom Field       | Mykis Spalte      | Beschreibung                                            |
| ------------------------------ | ----------------- | ------------------------------------------------------- |
| `field:mykis-leg.`             | `sammler`         | Sammler (mit Fallback auf `user_name` / `user_login`)   |
| `field:mykis-det.`             | `bestimmer`       | Bestimmer (mit Fallback auf `user_name` / `user_login`) |
| `field:mykis-substrat_organ`   | `organ_substrat`  | Substrat-Organ                                          |
| `field:mykis-substrat_zustand` | `substratzustand` | Zustand des Substrats                                   |
| `field:mykis-wuchsstelle`      | `wuchsstelle`     | Wuchsstelle                                             |
| `field:mykis-stadium`          | `stadium`         | Stadium                                                 |
| `ield:mykis-substrat/-wirt`    | `Wirt`            | Wirt                                                    |

### 4.4 iNaturalist Daten Filterung

Die Daten von iNaturalist werden bei der Konvertierung gefiltert und aussortiert.
Wenn das Feld "field:mykis-erfassung" in der Datei vorhanden wird, jede Zeile dieser Spalte ob die Wörter 

| yes |
| --- |
| ja  |
|     |
|     |
|     |

## 

## 4.5 Fundort Zurodnung

Die Fundort Zurodnung ist nur aktiv, solange eine Datei als Fundort Zuodrnungs Liste hinterlegt ist.


Wenn ein Fundort im gleichen 16tel Quadranten liegt, wie ein bestehendert Fundort in der Fundort Zurodnungs Liste, dann werden diese Daten auf den Neunen übertragen.
Wenn es mehrere bestehende Fundort in der Fundort Zuordnungs Liste vorhanden sind, werden die Daten des Nähesten auf den neuen Fundort übertragen.


Folgende Daten werden übertrage:

- BASIS_ort

- BASIS_ortslage

- name_staat

- name_provinz

- MTB

- name_kreis

- hoehenstufe

- ozeanitaet

- zonalitaet



Die originalen Geokoordianten des neuen Fundortes werden gelöscht

## 5. Best Practices

### 5.1 Vorbereitung in iNaturalist Expot

[Beobachtungen exportieren · iNaturalist](https://www.inaturalist.org/observations/export?projects%5B%5D=mykis-kartierung) 

![](C:\Users\Julian%20Grausgruber\AppData\Roaming\marktext\images\2026-02-16-18-21-04-image.png)Bei der Standardauswahl sind, werden die Mykis Felder nicht mitexportiert, also entweder alle mykis Felder mitexportieren oder nur die wichtigstern:
Zurzeit werden folgeden Felder in der Konvertierung verwendet:

-  field:mykis-leg.

-  field:mykis-det.

-  field:mykis-stadium

- field:mykis-substrat_zustand

- field:mykis-substrat/-wirt

-  field:mykis-substrat_organ

-  field:mykis-wuchsstelle

Folgende Felder sind auch noch wichtig um eine bessere Ortbeschreibung bzw eine konsistentere Ausgabe zu haben:

- place_country_name

- place_state_name

Am besten einfach bei Geo alle aktiveren:

![](C:\Users\Julian%20Grausgruber\AppData\Roaming\marktext\images\2026-02-16-18-20-42-image.png)

### 5.2 Backup-Strategie

Vor jedem Anhängen, ein Backup (Eine Kopie) von der Original Datei machen.

## 6. Fehlerbehebung

### 6.1 Spalten stimmen nicht überein

**Problem:** Beim Anhängen unterschiedliche Spalten

**Ursache:**

- Alte Datei mit veraltetem Format

**Lösung:**

1. Prüfe Protokoll welche Spalten fehlen
2. Entscheide ob fortfahren (neue Spalten werden hinzugefügt)
3. Optional: Alte Datei mit neuem Template re-konvertieren

---

## 7 Versions-Historie

#### v0.7.0 (2026-03-15)

- Berechnung 64tel Quadrant MTB (1626,232) anstatt 16tel Quadrant MTB (1626,23)

- Fundort Zuordnung mithilfe einer Referenzliste, die man auswählen kann. Nur bei ausgehählter Liste wird die Fundort Zuordnung aktiviert

#### v0.6.0 ( 2026-03-11)

- bugfix: feld von iNaturalist "description" wird nun in das mykdaten Feld "substrat_text" kopiert anstatt 

- bugfix: feld von iNaturalist "field:mykis-substrat/-wirt" wird nun in das mykdaten Feld "Wirt" kopiert anstatt

- Namefeld angepasst: Wenn user_name aus mehreren Teilen besteht (z.b: Max Mustermann), wird der  erste Teil nach hinten geschoben und davor ein Beistrich eingefügt --> Mustermann, Max (Festlegung laut DFGM)

- 16tel Quadrant  MTB Konvertierung hinzugefügt in Feld mykdaten "MTB"

### v0.5.0 (2026-02-23)

- Bugfix: iNaturalist Datei kompatibiltät verbessert: Fehler beim Einlesen gefixed

![](C:\Users\Julian%20Grausgruber\AppData\Roaming\marktext\images\2026-02-23-11-06-26-image.png)

- Bugfix: Fehler beim öffnen der exportierten Datei in Excel 

![](C:\Users\Julian%20Grausgruber\AppData\Roaming\marktext\images\2026-02-23-11-08-34-image.png)

#### v0.4.0 (2026-02-21)

- mykdaten Spalte "Nachweisquelle" --> Ausgabe:  "iNaturalist"

- mykdaten Spalte "Foto_Zeichnung" --> Ausgabe "D"

- mykddaten Spalte "art_bemerkung" --> Ausgabe Spalte "url" von iNaturalist Export

- mykddaten Spalte "sonderstandort" --> Ausgabe Spalte "field:mykis-pflanzengesellschaft" von iNaturalist Export

- mykdaten Spalte "Basis_ortslage" --> Ausgabe: "iNaturalist"

- mykdaten Spalte "name_provinz" --> Ausgabe Bundesländer mit Filterung & Normalisierung

- iNaturalist Datei wird gefilter durch das Feld "field:mykis-erfassung"

#### v0.3.0 (2026-02-16) – Anhänge-Funktion & Ortsdaten-Verbesserungen

**Neue Features:**

- **xls Datei export**

- **Anhängen an bestehende Dateien**
  
  - Neue Checkbox-Option in der GUI
  - Ausgabedatei-Feld dient als Anhänge-Datei im Anhänge-Modus
  - Button-Text passt sich automatisch an ("Datei zum Anhängen wählen…")
  - Intelligente Spalten-Kompatibilitätsprüfung
  - Warnung bei unterschiedlichen Spalten mit Benutzer-Bestätigung
  - Detaillierte Protokoll-Ausgabe (Vorher/Hinzugefügt/Gesamt)

- **Ortsdaten-Extraktion**
  
  - Strukturierte iNaturalist-Felder haben Vorrang
  - Automatischer Fallback auf `place_guess` bei fehlenden Daten
  - Ländernamen-Normalisierung ("Germany" / "DE" → "Deutschland")
  - `name_staat`: Fallback auf letzten Teil bei 2+ Teilen
  - `name_provinz`: Fallback auf vorletzten Teil bei 3+ Teilen
  - `BASIS_ort`: Adaptive Logik (1-3 Teile → 1. Teil, 4+ Teile → 2. Teil)
  - `BASIS_ortslage`: Fallback auf ersten Teil bei 4+ Teilen

---

#### v0.2.0

**Neue Features:**

- Sammler/Bestimmer aus `user_name` / `user_login`
- Output XLSX/CSV
- Input: CSV, XLSX,
- Init Konvertierung iNaturalist → Mykis
- Datum-Formatierung (TT.MM.JJJJ)
- Koordinaten-Export

---

Version 0.3.0 | Stand: 2026-02-16
