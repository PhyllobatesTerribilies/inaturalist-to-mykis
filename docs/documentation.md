# Dokumentation – inaturalist-to-mykis

**Version:** 0.8.0  
**Datum:** 2026-03-26

---

## 1. Einleitung

Das Programm inaturalist-to-mykis konvertiert Pilzbeobachtungen von iNaturalist in ein Format, das direkt in MykIS importiert werden kann. Dabei werden vordefinierte Spalten einer exportierten iNaturalist-Datei in das kompatible MykIS-Dateiformat überführt.

### Details zum Dateiformat

Referenzformat: mykdaten.xls
Layout: Die verwendete Vorlage für das Programm findet man unter [2026-02-07_layout_mykdaten.xls](https://github.com/PhyllobatesTerribilies/inaturalist-to-mykis/tree/master/assets).

### Konvertierung

1. Einfach - Dateierstellung: \
   Es wird nur die exportierte iNaturalist Datei verwendet und das Programm erstellt eine neue Datei mit den neunen Datensätzen
2. Anhängen an bestehende Datei \
   Es wird die exportierte iNaturalist Datei verwendet und eine bestehende mykdaten.xls Datei. Bei der Konvertierung werden die neuen Datensätze an die mykdaten.xls Datei angehängt. Zu beachten ist das es eine Datei ist mit den selben Spalten wie mykdaten.xls.
3. Fundortzuordnung \
   Hierbei werden neue Fundorte bestehende Fundorten zugeordnet. Hierfür muss dem Programm eine entsprechende Fundort-Datei bereitgestellt werden.

Weitere Informationen findet man weiter un in der Dokumentation.

### Unterstützte Formate:

- **Eingabe:** CSV, XLSX, XLS
- **Ausgabe:** XLS, XLSX, CSV

## 2. Start

### 2.1 Programmstart

![alt text](C:\workspace\INaturlist_Mykis_Konvertierung%20_github\docs\medien_docs\image.png)

```
Doppelklick auf: inaturalist-to-mykis.exe
```

### 2.2 Hauptfenster

Nach dem ausführen des Programms öffnet sich folgendes Fenster:

![](C:\Users\Julian%20Grausgruber\AppData\Roaming\marktext\images\2026-03-15-18-02-35-image.png)**Legende:**

- GRÜN **Eingabefeld:** iNaturalist-Exportdatei
- ROT **Ausgabefeld:** Konvertierte Datei bzw bestehende Datei (mykdate.xls)
- ROSA **Fundort Zuordnungs Liste:** Liste bestehender Fundort zur Fundortzurodnung bei neuen Datensätzen
- GELB **Optionen:** Auswahloption, ob die neuen Datensätze an einen bestehende Datei angehängt werden soll
- BLAU **Protokoll:** Live-Status und Meldungen

## 3. Bedienung

### 3.1 Einfache Konvertierung (Neue Datei)

**Schritt 1:** Eingabedatei wählen

- Klick auf **Durchsuchen…** (bei Eingabedatei)
- Wähle iNaturalist-Export (z.B. `observations-527425.csv`)

**Schritt 2:** Ausgabedatei

- Nach dem eine Eingabedatei gewählt wurde, wird eine Automatischer Datei Vorschlag vom Programm erzeugt, im selben Ordner wie die Eingabedatei.
  Beispiel: `observations-527425_mykis.xls`
- Dateiort und Name kann jederzeit geändert werden.

**Schritt 3:** Konvertieren

- Klick auf **Konvertieren**
- Weitere Information zur Konvertierung findet man in der Protokoll Ausgabe

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

### 3.2 Anhängen an bestehende Datei

**Schritt 1:** Eingabedatei wählen

- Klick auf **Durchsuchen…** (bei Eingabedatei)
- Wähle iNaturalist-Export (z.B. `observations-527425.csv`)

**Schritt 2:** Anhänge-Modus aktivieren

- Checkbox aktivieren: **"An bestehende Mykis-Datei anhängen"**
- Bei der Auswahl der Ausgabedatei ändert sich der Button zu: **"Datei zum Anhängen wählen…"**
  ![alt text](C:\workspace\INaturlist_Mykis_Konvertierung%20_github\docs\medien_docs\image-2.png)

**Schritt 3:** Bestehende Datei wählen

- Klick auf **Datei zum Anhängen wählen…**
- Wähle bestehende Mykis-Datei (z.B. `mykdaten.xls`)

**Schritt 4:** Konvertieren

- Neue Daten werden **unten an** die bestehende Datei angehängt
- Zur Sicherheit soll vor der Konvertierung ein Backup, von der bestehenden Datei, erzeugt werden.

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

**Spalten-Kompatibilitätsprüfung**

Beim Konvertieren prüft das Programm automatisch die Spaltenübereinstimmung. Es ist eine Referenz mykdaten.xls hinterlegt, mit der die bestehende Datei beim Anhängen überprüft wird ob alle Spalten vorhanden sind.

Szenario: Spalten stimmen NICHT überein:

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

### 3.3 Fundortzurodnung

**Schritt 1:** Eingabedatei und Ausgabedatei wählen 

- Die beiden Datein wie in den vorheringen Punkten auswählen, je nach dem ob man einen Datei erstellen oder an einen bestehende Datei anhängen möchte

**Schritt 2:** Fundort Referenzliste auswählen

- Die Referenz Fundortliste auswählen.

**Schritt 3:** Konvertieren

- Die neuen Datensätze werden jetzt mit der Referenz Fundortliste überprüft. Bei Übereinstimmung mit den 16tel Quadranten, werden vordefinierte Spalten des Refernzdatensatzes auf den neuen Datensatz kopiert.
- Mehr Information zu der Fundortzurordnung findest man hier. [Fundortzurordnung](#44-fundort-zurodnung)

## 4. Spalten-Mapping: iNaturalist → Mykis

### 4.1 Übersicht der Spalten

Diese soll ein Überblick bieten über die Feldzuweisung bzw. Berarbeitung der von iNaturalist zu Mykis Spalten.
Für manche Mykis Spalten werden mehrere iNaturalist Felder verwendet, da nicht immer alle eingetragen sind. So wie die Reihung im iNaturalist Feld in der folgenden Tabelle ist, so wird auch die Priorität gewertet.\
Beispiel: Mykis: Gattung --> iNaturalist: scientific_name \ species_guess --> Das bedeutet solange im Feld scientific_name etwas vorhanden ist, wird das verwendet.

| Mykis Spalte    | iNaturalist Feld                          | Beschreibung                                                                                                                            |
| --------------- | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Gattung         | scientific_name \ species_guess           | 1. Wort wird verwendet z.b: Amanita muscaria --> "Amanita"                                                                              |
| ART             | scientific_name \ species_guess           | Alle Wörter nach dem 1. wird verwendet z.b: Amanita muscaria --> "muscaria"                                                             |
| BASIS_datum1    | observed_on \ observed_on_string          | Datum Format wird extrahiert (JJJJ-MM-DD) und als TT.MM.JJJJ ausgegeben                                                                 |
| datum2          | observed_on \ observed_on_string          | Datum Format wird extrahiert (JJJJ-MM-DD) und als TT.MM.JJJJ ausgegeben                                                                 |
| erfasser        | user_name \ user_login                    | 1. Wort wird als Vorname verwendet und die Restlichen als Nachname - Formatausgabe: Nachname, Vorname z.b: Maren Kamke --> Kamke, Maren |
| sammler         | field:mykis-leg. \ user_name \ user_login | 1. Wort wird als Vorname verwendet und die Restlichen als Nachname - Formatausgabe: Nachname, Vorname z.b: Maren Kamke --> Kamke, Maren |
| bestimmer       | field:mykis-det. \ user_name \ user_login | 1. Wort wird als Vorname verwendet und die Restlichen als Nachname - Formatausgabe: Nachname, Vorname z.b: Maren Kamke --> Kamke, Maren |
| nachweisquelle  | -                                         | "iNaturalist" wird fix hinterlegt                                                                                                       |
| nordwert2       | latitude                                  | Ortskoordinaten                                                                                                                         |
| ostwert2        | longitude                                 | Ortskoordinaten                                                                                                                         |
| Foto_Zeichnung  | -                                         | "D" wird fix hinterlegt                                                                                                                 |
| art_bemerkung   | url                                       | Link zur iNaturalist-Beobachtung                                                                                                        |
| organ_substrat  | field:mykis-substrat_organ                |                                                                                                                                         |
| substratzustand | field:mykis-substrat_zustand              |                                                                                                                                         |
| substrat_text   | description                               |                                                                                                                                         |
| wuchsstelle     | field:mykis-wuchsstelle                   |                                                                                                                                         |
| stadium         | field:mykis-stadium                       |                                                                                                                                         |
| sonderstandort  | field:mykis-pflanzengesellschaft          |                                                                                                                                         |
| Wirt            | field:mykis-substrat/-wirt                |                                                                                                                                         |
| name_staat      | place_country_name / place_guess          | Land                                                                                                                                    |
| name_provinz    | place_state_name / place_guess            | Bundesland                                                                                                                              |
| BASIS_ort       | place_guess                               | Ort                                                                                                                                     |
| BASIS_ortslage  | -                                         | "iNaturalist" wird fix hinterlegt                                                                                                       |
| MTB             | -                                         | MTB-Q64 wird berechnet aus nordwert2 und ostwert2                                                                                       |

### 4.2 Ortsdaten

Das Programm nutzt die iNaturlist Felder  `place_country_name`, `place_state_name`,sowie `place_guess`.

Wenn die Felder `place_country_name`, `place_state_name` nicht verfürgbar sind bzw. nicht mit exportiert werden, wird stattdessen das Feld `place_guess` verwendet

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

### 4.3 iNaturalist Daten Filterung

Die Daten von iNaturalist werden bei der Konvertierung gefiltert und aussortiert.
Wenn das Feld "field:mykis-erfassung" in der Datei vorhanden ist,  wird jede Zeile dieser Spalte auf diese Wörter überprüft.

| Wörter |
| ------ |
| yes    |
| ja     |
|        |

## 4.4 Fundort Zurodnung

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

Die originalen Geokoordianten des neuen Fundortes werden auch gelöscht.

## 5. Log

Das Programm erzeugt bei jeder Konvertierung ein Log Datei mit einem Datum, diese kann verwendet werden um noch genauere Details über die Fundortzurodnung zu bekommen.
Es wird Details über die Referenz Fundort Datei ausgegeben wie z.b: Anzahl an Refernz Datensätze oder auch die "mtb" Spalte gefunden wurde oder auch wie viele verschiede 16tel Quadranten es gibt. 
Es wird in der Datei auch jede Fundortzuordnung aufgelistet.

z.b: Fundort-Zuordnung:[0] --> Das bedeutet der Index 0 in der iNaturalist Datei wurde wie angegeben verwändert.
'BASIS_ortslage: 'iNaturalist' → 'OT Hasseldieksdamm Hofholz'
Das heißt die BASIS_ortslage wurde auf OT Hasseldieksdamm Hofholz geändert.

Bei jeder Konvertierung erstellt das Programm automatisch eine Log-Datei mit Zeitstempel. Diese Datei dient der Qualitätssicherung und liefert detaillierte Informationen darüber, wie die Fundortdaten verarbeitet und zugeordnet wurden.

### Inhalte der Log-Datei

Das Protokoll gibt Aufschluss über folgende Punkte:

- Anzahl der geladenen Referenz-Datensätze.
- Bestätigung, ob die benötigte MTB-Spalte (Messtischblatt) gefunden wurde.
- Statistiken über die geografische Abdeckung (z. B. Anzahl der verschiedenen 16tel-Quadranten).
- Status der geladenen Shapefiles für die geografische Validierung.
- Detaillierte Fundort-Zuordnung

#### Detaillierte Fundort-Zuordnung

Ein Eintrag wie `Fundort-Zuordnung:[0]` bedeutet, dass der Datensatz mit dem Index 0 (Der Index muss immer +2 gerechnet werden für die exakte Excel Zeile) aus der iNaturalist-Quelldatei verarbeitet wurde. Die Pfeile (`→`) zeigen dabei die Transformation der Daten an:

> **Beispiel:** `BASIS_ortslage: 'iNaturalist' → 'OT Hasseldieksdamm Hofholz'`  
> Hier wurde der Name `iNaturalist` durch die Ortsbezeichnung aus der Referenzdatei ersetzt.

**Beispiel Log**

```
Start inat to mykis convertation
Info: Referenzdatei ausgewählt C:\workspace\INaturlist_Mykis_Konvertierung\Testdaten\MTB\fundorte_sh.xlsx
Info: Referenzdatei geladen: 5808 Spalten
Info: MTB-Spalte gefunden als 'mtb'
Lade Shapefile: C:\workspace\INaturlist_Mykis_Konvertierung _github\dist\inaturalist-to-mykis\_internal\assets\b25_utm32s\b25_utm32s.shp
Shapefile geladen: 2980 MTB-Blätter
Referenz Datei Einträge: 5808
Referenz Datei verschiedene 16tel Quadranten: 1778
Fundort-Zuordnung:[0] --> 1626,342 ' → ' 1626.342', 'BASIS_ortslage: 'iNaturalist' → 'OT Hasseldieksdamm Hofholz', BASIS_ort: 'Kiel' → 'Kiel', name_staat: 'Deutschland' → 'Deutschland', name_provinz: '' → 'Schleswig-Holstein', name_kreis: 'nan' → 'Kiel', hoehenstufe: 'nan' → 'planar (unter 100mNN)', ozeanitaet: 'nan' → 'subozeanisch', zonalitaet: 'nan' → 'temperat'
Fundort-Zuordnung:[1] --> 1626,432 ' → ' 1626.432', 'BASIS_ortslage: 'iNaturalist' → 'Zentrum Südfriedhof', BASIS_ort: 'Schützenwall/Boiestraße - Kiel' → 'Kiel', name_staat: 'Deutschland' → 'Deutschland', name_provinz: '' → 'Schleswig-Holstein', name_kreis: 'nan' → 'Kiel', hoehenstufe: 'nan' → 'planar (unter 100mNN)', ozeanitaet: 'nan' → 'subozeanisch', zonalitaet: 'nan' → 'temperat'
Fundort-Zuordnung:[2] --> 1626,431 ' → ' 1626.431', 'BASIS_ortslage: 'iNaturalist' → 'OT Hasseldieksdamm Uhlenkrug-Tierheim', BASIS_ort: 'Kiel' → 'Kiel', name_staat: 'Deutschland' → 'Deutschland', name_provinz: '' → 'Schleswig-Holstein', name_kreis: 'nan' → 'Kiel', hoehenstufe: 'nan' → 'planar (unter 100mNN)', ozeanitaet: 'nan' → 'subozeanisch', zonalitaet: 'nan' → 'temperat'
```

## 6. Best Practices

### 6.1 Vorbereitung in iNaturalist Expot

[Beobachtungen exportieren · iNaturalist](https://www.inaturalist.org/observations/export?projects%5B%5D=mykis-kartierung) 

![](C:\Users\Julian%20Grausgruber\AppData\Roaming\marktext\images\2026-02-16-18-21-04-image.png)Bei der Standardauswahl werden die Mykis Felder nicht mitexportiert. Als Empehlung alle Mykis Felder mitexportieren:
Zurzeit werden folgeden Felder in der Konvertierung verwendet:

- field:mykis-leg.
- field:mykis-det.
- field:mykis-stadium
- field:mykis-substrat_zustand
- field:mykis-substrat/-wirt
- field:mykis-substrat_organ
- field:mykis-wuchsstelle

Folgende Felder sind auch noch wichtig um eine bessere Ortbeschreibung bzw eine konsistentere Ausgabe zu haben:

- place_country_name
- place_state_name

Am besten einfach bei Geo alle aktiveren:

![](C:\Users\Julian%20Grausgruber\AppData\Roaming\marktext\images\2026-02-16-18-20-42-image.png)

### 6.2 Backup-Strategie

Vor jedem Anhängen, ein Backup (Eine Kopie) von der Original Datei machen.

## 7. Fehlerbehebung

#### Spalten stimmen nicht überein

**Problem:** Beim Anhängen unterschiedliche Spalten

**Ursache:**

- Alte Datei mit veraltetem Format

**Lösung:**

1. Prüfe Protokoll welche Spalten fehlen
2. Entscheide ob fortfahren (neue Spalten werden hinzugefügt)
3. Optional: Alte Datei mit neuem Template re-konvertieren

---

## 8 Versions-Historie

#### v0.8.0 (2026-03-26)

- Namen und Kommentare Änderung

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
