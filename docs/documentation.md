# Dokumentation – inaturalist-to-mykis

**Version:** 0.10.0  
**Datum:** 2026-05-18

---

## 1. Einleitung

Das Programm inaturalist-to-mykis konvertiert Pilzbeobachtungen von iNaturalist in ein Format, das direkt in MykIS importiert werden kann. Dabei werden vordefinierte Spalten einer exportierten iNaturalist-Datei in das kompatible MykIS-Dateiformat überführt.

Funktionen:

- Konvertierung der Daten
- Erfassung Filter (field:mykis-erfassung)
- Standort Filter (geoprivacy = obscured)
- Koordinaten --> MTB 16tel
- Namenszuordnung
- Referenzfundor Zuordnung
- Log Datei
- 

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

![](C:\Users\Julian%20Grausgruber\AppData\Roaming\marktext\images\2026-07-07-20-55-10-image.png)**Legende:**

- GRÜN **Eingabefeld:** iNaturalist-Exportdatei
- ROT **Ausgabefeld:** Konvertierte Datei bzw bestehende Datei (mykdate.xls)
- ROSA **Fundortrefernz Liste:** Liste bestehender Fundort zur Fundortzurodnung bei neuen Datensätzen
- SCHWARZ **Namenszurodnungs Liste:** List mit user_login und Mykisnamen
- GELB **Optionen:** Auswahloption,
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

### 3.3 Fundortzuordnung

**Schritt 1:** Eingabedatei und Ausgabedatei wählen 

- Die beiden Datein wie in den vorheringen Punkten auswählen, je nach dem ob man einen Datei erstellen oder an einen bestehende Datei anhängen möchte

**Schritt 2:** Fundort Referenzliste auswählen

- Die Referenz Fundortliste auswählen.

**Schritt 3:** Konvertieren

- Die neuen Datensätze werden jetzt mit der Referenz Fundortliste überprüft. Bei Übereinstimmung mit den 16tel Quadranten, werden vordefinierte Spalten des Refernzdatensatzes auf den neuen Datensatz kopiert.
- Mehr Information zu der Fundortzuordnung findest man hier. [Fundortzuordnung](#44-fundort-zuordnung)

## 3.4 Namenszuordnung

**Schritt 1:** Eingabedatei und Ausgabedatei wählen

- Die beiden Datein wie in den vorheringen Punkten auswählen, je nach dem ob man einen Datei erstellen oder an einen bestehende Datei anhängen möchte

**Schritt 2:** Namenszurodnungs Liste auswählen

- Achtung Liste muss mindestens die Spalten "user_login" und "mykis-namen" haben. Die Spaltennamen muss exakt sein (Groß & Kleinschreibung ist egal)
  
  ![](C:\Users\Julian%20Grausgruber\AppData\Roaming\marktext\images\2026-05-18-12-10-39-image.png)

**Schritt 2:** Konvertieren

- Die neuen Datensätze werden jetzt mit der Namenszurodnungs Liste überprüft. Bei Übereinstimmung mit einem user_login, wird der Mykis Name in den neuen Datensatz im Feld "Erfasser" eingetragen
- Mehr Information zu der Namenszurordnung findest man hier [Namenzurordnung](#45-namenszuordnung). 

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
| Foto_Zeichnung  | id                                        | "iNNr: id"  z.b:z.b: iNNr:260724269                                                                                                     |
| art_bemerkung   | field:mykis-bemerkung                     |                                                                                                                                         |
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
| Ungenauigkeit   | positional_accuracy                       |                                                                                                                                         |

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

### 4.4 Fundort Zuordnung

Die Fundort-Zuordnung ist nur aktiv, wenn eine Fundort-Referenzliste ausgewählt ist. Diese Liste braucht die Spalten `mtb`, `ostwert2` und `nordwert2`.

**So funktioniert es:** Für jeden neuen Fundort wird aus den Koordinaten der **16tel-Quadrant** bestimmt (z. B. `1626,34`). Liegt in der Referenzliste ein Fundort im selben 16tel-Quadranten, werden dessen Daten übernommen. Passen mehrere, gewinnt der **nächstgelegene** (nach `ostwert2`/`nordwert2`).

> ⚠️ Referenz-Fundorte **ohne** Koordinaten werden nicht verwendet – die Referenzliste sollte immer `ostwert2`/`nordwert2` enthalten.

Fällt eine Beobachtung in einen 16tel-Quadranten, für den es zwar Referenz-Einträge gibt, aber **keiner davon Koordinaten** hat, erscheint in der Log-Datei z. B.:

`Fundort-Zuordnung:[25] --> Error: Keiner der Referenz 16tel Quadranten [3647,24] hat Geokoordinaten (ostwert2,nordwert2)`

Das bedeutet: Für diese Beobachtung (Index 25) konnte im Quadranten `3647,24` kein Referenz-Fundort ausgewählt werden – es wird nichts übertragen.

Folgende Daten werden übertragen:

- BASIS_ort
- BASIS_ortslage
- name_staat
- name_provinz
- MTB
- name_kreis
- hoehenstufe
- ozeanitaet
- zonalitaet

Die originalen Geokoordinaten des neuen Fundortes (`ostwert2`/`nordwert2`) werden dabei gelöscht – der Fundort wird stattdessen über das MTB verortet.

#### MTB-Wert in der Referenzliste

Der `mtb`-Wert muss den Quadranten enthalten – mindestens den 16tel-Quadranten. Ein Wert **ohne Komma** (nur die Blatt-Nummer) wird aktuell **nicht** zugeordnet. Ein Punkt (`.`) zählt wie ein Komma.

| `mtb`                         | Wird zugeordnet? |
| ----------------------------- | ---------------- |
| `1626,342` (64tel-Quadrant)   | ✅ ja             |
| `1626,34` (16tel-Quadrant)    | ✅ ja             |
| `1626.34` (Punkt statt Komma) | ✅ ja             |
| `1626` (ohne Komma)           | ❌ nein           |

### 4.5 Namenszuordnung

Die Namenszurodnung ist nur aktiv, solange eine Datei als Namenszuodrnungs Liste hinterlegt ist.

Folgende Spalten muss in der Datei vorhanden sein:

- user_login

- mykis-name

Die Groß & Kleinschreibung ist egal.

Folgendes Bild zeigt eine Beispiel Datei:

![](C:\Users\Julian%20Grausgruber\AppData\Roaming\marktext\images\2026-05-18-12-10-39-image.png)

Desweiteren kann für die Namenszuordnung noch eine Option ausgewählt werden:

![](C:\Users\Julian%20Grausgruber\AppData\Roaming\marktext\images\2026-05-18-12-15-03-image.png)

Standardmäßig ist die Option ausgeschaltet und dabei wird die automatische Namenskonvertierung auch noch durchgeführt (Name wird erstellt aus dem user_login oder user_name. Jedoch hat die Namenszuordnung immer die höhere Priorität, solange ein Eintrag vorhanden ist, wird dieser für das Feld "Erfasser" gewählt. 

Bei Aktivierung dieser Option, wird in das Feld "Erfasser" der user_login geschrieben, solange kein Eintrag in der Namenszuordnungs - Liste vorhanden ist.

###### 4.5 Wirt

Das Feld **Wirt** wird aus der iNaturalist-Spalte `field:mykis-substrat/-wirt` übernommen. 

Bekannte lateinische Begriffe (Gattungen, Arten, höhere Taxa) werden automatisch in deutsche Bezeichnungen (Mykis) übersetzt – unabhängig von der Groß-/Kleinschreibung im Original. 

Beispiele: `Angiospermae` → `LAUBHOLZ/LAUBBAUM`, `Cervus elaphus` → `Rothirsch`.

 Einträge, die nach der Übersetzung noch immer ein einzelnes Wort ohne Leerzeichen sind (d. h. nur ein Gattungsname, keine Art), erhalten automatisch den Zusatz **` sp.`** (z. B. `Quercus` → `Quercus sp.`). Bereits übersetzte Werte sind davon ausgenommen.

| Lateinisch             | Deutsch                 |
| ---------------------- | ----------------------- |
| Angiospermae           | LAUBHOLZ/LAUBBAUM       |
| Pinopsida              | NADELHOLZ/NADELBAUM     |
| Gliridae               | Bilch                   |
| Harmonia axyridis      | Asiatischer Marienkäfer |
| Capreolus capreolus    | Reh                     |
| Castoridae             | Biber                   |
| Dama dama              | Damwild                 |
| Carnivore              | Fleischfresser          |
| Bos taurus             | Hausrind                |
| Sus scrofa             | Wildschwein             |
| Sus scrofa domestica   | Hausschwein             |
| Capra aegagrus hircus  | Hausziege               |
| Canis lupus familiaris | Hund, Haushund          |
| Coleoptera             | KÄFER                   |
| Coccinellidae          | MARIENKÄFER             |
| Ovis orientalis        | Mufflon                 |
| Equus caballus         | Pferd                   |
| Vulpes vulpes          | Rotfuchs                |
| Cervus elaphus         | Rothirsch               |
| Lepidoptera            | SCHMETTERLINGE          |
| Heteroptera            | WANZEN                  |
| Bubalus arnee          | Wasserbüffel            |
| Oryctolagus cuniculus  | Wildkaninchen           |

###### 4.5 Qualität

Das Feld `field:mykis-qualität` aus dem iNaturalist-Export wird über folgende Tabelle in die Mykis-Qualitäts-ID umgewandelt:

| iNaturalist-Wert            | Mykis-ID |
| --------------------------- | -------- |
| unsicher                    | 1        |
| mikroskopiert               | 2        |
| gesichert                   | 4        |
| plausibel                   | 5        |
| Literaturdaten              | 6        |
| sequenziert                 | 7        |
| mikroskopiert + sequenziert | 8        |

**Fallback:** Ist `field:mykis-qualität` leer, aber `field:mykis-its-sequenz` oder `field:dna barcode its:` gefüllt, wird automatisch ID `7` (sequenziert) gesetzt.

**Unbekannte Werte:** Steht ein nicht gelisteter Text im Feld (z. B. Tippfehler), bleibt die Zelle leer und es wird eine Zeile ins Log geschrieben (`Qualität[idx]: unbekannter Wert '...' wird ignoriert`).

## 5. Log

Bei jeder Konvertierung erstellt das Programm automatisch eine **Log-Datei** mit Zeitstempel (z. B. `inat_to_mykis_2026-07-07_14-05-33.log`) im Ordner `logs/`. Sie dient der Qualitätssicherung und zeigt im Detail, wie die Daten gefiltert, umgewandelt und zugeordnet wurden.

Die Datei enthält:

- **Statistiken** zur Referenzdatei (Anzahl Einträge, gefundene `mtb`-Spalte, Anzahl der 16tel-Quadranten) und zum geladenen Shapefile.
- **Zusammenfassungen** der Filterschritte (z. B. `📊 Erfassung-Filter: Von 216 Beobachtungen: ✅ 200 werden verarbeitet …`).
- **Einzelzeilen** zu jeder Umwandlung und jedem aussortierten oder fehlerhaften Datensatz.

Die meisten Einzelzeilen beginnen mit dem Schritt und dem Datensatz-Index `[idx]`. Der Index bezieht sich auf die iNaturalist-Quelldatei – für die genaue Excel-Zeile gilt: **Excel-Zeile = idx + 2**. Die Pfeile (`→`) zeigen jeweils *alt → neu*.

### Log-Einträge

| Eintrag (Beispiel) | Bedeutung |
| --- | --- |
| `Fundort-Zuordnung:[0] --> … 'BASIS_ortslage: 'iNaturalist' → 'OT …'` | Datensatz 0 wurde einem Referenz-Fundort zugeordnet (je Feld alt → neu). |
| `Fundort[12] Fehler: Koordinate (...) liegt nicht in Deutschland (außerhalb der TK25)` | Die Koordinaten liegen außerhalb der deutschen TK25-Karte – keine MTB-Zuordnung. |
| `Fundort[7] Fehler: keine gültige Koordinate (...)` | Der Datensatz hat keine (gültigen) Koordinaten. |
| `Fundort-Zuordnung:[25] --> Error: Keiner der Referenz 16tel Quadranten [3647,24] hat Geokoordinaten (...)` | Der Quadrant ist in der Referenzliste, aber keiner der Einträge dort hat Koordinaten (siehe 4.4). |
| `Warnung: 2 Referenz-Einträge ohne Quadrant werden keinem Fund zugeordnet (z.B. 1626)` | Referenzeinträge mit MTB ohne Komma/Quadrant werden ignoriert (siehe 4.4). |
| `Erfassungs-Filter (bereits erfasst) [25]: 288123 / Amanita muscaria` | Aussortiert, weil `field:mykis-erfassung` = Ja/Yes ist. |
| `Standort-Filter (obscured) [7]: 4711 / Boletus edulis` | Aussortiert, weil `geoprivacy` = obscured ist (nur wenn die Option aktiv ist). |
| `Wirt-Konvertierung [3]: 'coleoptera' → 'KÄFER'` | Der Wirt-Wert wurde übersetzt bzw. um „ sp." ergänzt. |
| `Namenskonvertierung:[3] user_login 'maxm': 'M, Max' → 'Mustermann, Max'` | Der Erfasser wurde über die Namensliste ersetzt. |
| `Qualität[9]: unbekannter Wert '...' wird ignoriert` | Im Feld `field:mykis-qualität` stand ein nicht gelisteter Wert; die Zelle bleibt leer. |

**Beispiel (Auszug):**

```
Info: Referenzdatei geladen: 5808 Spalten
Info: MTB-Spalte gefunden als 'mtb'
Shapefile geladen: 2980 MTB-Blätter
Referenz Datei Einträge: 5808
Referenz Datei verschiedene 16tel Quadranten: 1778
Fundort-Zuordnung:[0] --> 1626,342 ' → ' 1626.342', 'BASIS_ortslage: 'iNaturalist' → 'OT Hasseldieksdamm Hofholz', BASIS_ort: 'Kiel' → 'Kiel', name_provinz: '' → 'Schleswig-Holstein', name_kreis: 'nan' → 'Kiel', …
```

### Zusätzliche CSV-Dateien

Zusätzlich zur `.log`-Datei erzeugt das Programm – je nach gewählten Listen – strukturierte CSV-Dateien mit demselben Zeitstempel (`;`-getrennt, direkt in Excel zu öffnen).

| Datei | Wird erstellt | Inhalt |
| --- | --- | --- |
| `…_changes.csv` | mit Fundort-Referenzliste | Eine Zeile je zugeordnetem Fundort mit allen Feldänderungen (`MTB_alt`/`MTB_neu` und je Ortsfeld ein `_alt`/`_neu`-Paar). |
| `…_namen.csv` | mit Namensliste | Eine Zeile je ersetztem Erfasser: `id`, `user_id`, `user_login`, `user_name`, `erfasser_alt`, `erfasser_neu`. |
| `…_namen_unique.csv` | mit Namensliste | Wie oben, aber jeder Name nur **einmal**, mit Spalte `anzahl` (wie oft er vorkam). |

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

### v0.12.0 (2026-07-01)

- bugfix: Übersetzung "sus scrofa" : "Wildschwein"
- field:mykis-qualität das Feld gelesen und mit einer Mapping Tabelle umgewandelt (z.b: unsicher --> 1) und auf das Feld Qualität geschrieben

### v0.11.0 (2026-05-21)

- Wirt: Übersetzung taxonomischer Begriffe (z. B. „Angiospermae" → „LAUBHOLZ/LAUBBAUM")

#### v0.10.0 (2026-05-18)

- Auf das Mykis Feld "Qualität" wird jetzt "sequenziert" geschrieben, wenn etwas in den iNaturalist Felder  "field:mykis-its-sequenz" , "field:dna barcode its:" steht

- Namenkonvertierungsdatei: user_login wird konvertiert zu mykis-name

- Option "Erfasser = user_login": Neue Checkbox übernimmt den user_login unverändert als Erfasser. Einträge aus der Namenskonvertierungs-Datei werden weiterhin angewendet.

- Koordinaten-Normalisierung: Ganzzahlige Koordinaten ohne Dezimaltrennzeichen werden automatisch korrekt geparst (z.B. "51232" → 51.232). Erkennung erfolgt automatisch anhand der ersten Ziffer (Deutschland: Breite 47–55°N, Länge 6–15°O).

- Wirtsnamen:  Gattungsnamen werden automatisch mit "sp." ergänzt (z.B. "Quercus" → "Quercus sp.").

#### v0.9.0 (2026-04-13)

- Auf das Mykis -Feld Foto_Zeichnung wird jetzt "iNNr: + INaturlist ID" geschrieben z.b: iNNr:260724269
- Auf das Mykis -Feld art_bemerkung wird jetzt das iNaturalist Feld: field:mykis-bemerkung kopiert
- Auf das Mykis -Feld Ungenauigkeit wird jetzt das iNaturalist Feld: positional_accuracy kopiert
- bugfix log File
  - Fundort ID Anzeige bei Fehler
  - Fundort ID Anzeige, wenn Referenz Fundort keine Geokoordinaten haben
- bugfix Feld ART --> es wurde bisher nur das zweite Wort als Art verwendet 
  - alt: Fuligo    septica rufa --> septica    
  - jetzt: Fuligo    septica rufa --> septica rufa

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
