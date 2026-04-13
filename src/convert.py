#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iNaturalist → Mykis Konvertierung

Konvertiert iNaturalist CSV-Export in Mykis-kompatibles Format.

Hauptfunktionen:
- Taxon-Extraktion (Gattung/Art)
- Strukturierte Ortsfelder mit intelligenten Fallbacks
- Custom Fields aus Mykis-Projekt
- Koordinaten-Mapping
"""

from __future__ import annotations

import pandas as pd
from typing import Callable, Optional, Any
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path
from typing import Hashable
from src.io_validate import (
    read_any_table,
    inspect_table_header,
)

from src.config import AppConfig

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================


def copy_column(
    df: pd.DataFrame, column: str, default: str = "", raise_on_missing: bool = False
) -> pd.Series:
    """
    Kopiert und bereinigt eine Spalte.

    Args:
        df: Quell-DataFrame
        column: Spaltenname
        default: Wert für leere Zellen
        raise_on_missing: Bei True → Fehler wenn Spalte fehlt

    Returns:
        Bereinigte Serie (stripped, ohne NaN)
    """
    if column not in df.columns:
        if raise_on_missing:
            raise KeyError(f"Spalte '{column}' nicht gefunden")
        print(f"⚠️  WARNUNG: Spalte '{column}' nicht gefunden")
        return pd.Series(default, index=df.index, dtype=str)

    return df[column].fillna(default).astype(str).str.strip().replace("", default)


def copy_numeric_column(df: pd.DataFrame, column: str) -> pd.Series:
    """Kopiert numerische Spalte (z.B. Koordinaten)."""
    if column not in df.columns:
        print(f"⚠️  WARNUNG: Spalte '{column}' nicht gefunden")
        return pd.Series(None, index=df.index, dtype=float)
    return pd.to_numeric(df[column], errors="coerce")


def assign_if_exists(out_df: pd.DataFrame, column: str, series: pd.Series) -> None:
    """Weist Serie einer Spalte zu (nur wenn Spalte im Template existiert)."""
    if column in out_df.columns:
        out_df[column] = series


# ==============================================================================
# EXTRACTION FUNCTIONS (row-by-row via .apply())
# ==============================================================================


def pick_taxon(row: pd.Series[Any]) -> str:
    """Extrahiert Taxon-Namen aus verschiedenen möglichen Spalten."""
    for key in ("scientific_name", "species_guess", "taxon_name"):
        if key in row and pd.notna(row[key]) and str(row[key]).strip():
            return str(row[key]).strip()
    return ""


def pick_date(row: pd.Series[Any]) -> str:
    """Extrahiert und formatiert Datum als DD.MM.YYYY."""
    for key in ("observed_on", "observed_on_string"):
        val = row.get(key, None)
        if pd.notna(val) and str(val).strip():
            dt = pd.to_datetime(str(val), errors="coerce")
            if pd.notna(dt):
                return dt.strftime("%d.%m.%Y")
    return ""


def pick_name(row: pd.Series[Any]) -> str:
    """Extrahiert Benutzernamen."""
    for key in ("user_name", "user_login"):
        v = row.get(key, None)
        if pd.notna(v) and str(v).strip():
            name = str(v).strip()
            if key == "user_name":
                parts = name.split()
                if len(parts) >= 2:
                    first = parts[0]
                    rest = " ".join(parts[1:])
                    return f"{rest}, {first}"

            return name
    return ""


# ==============================================================================
# LOCATION EXTRACTION
# ==============================================================================


def extract_basis_ort(df: pd.DataFrame) -> pd.Series:
    """
    Extrahiert BASIS_ort mit adaptiver Logik.

    Logik:
    - 1-3 Teile: parts[0] (erster Teil)
    - 4+ Teile:  parts[1] (zweiter Teil)

    Beispiele:
    - "Kiel" → "Kiel"
    - "Bosau, Deutschland" → "Bosau"
    - "Berlin, Brandenburg, Deutschland" → "Berlin"
    - "Meilwald, Erlangen, Bayern, DE" → "Erlangen"
    """
    if "place_guess" not in df.columns:
        return pd.Series("", index=df.index, dtype=str)

    def extract_ort(value: Any) -> str:
        if pd.isna(value):
            return ""
        parts = [p.strip() for p in str(value).strip().split(",")]
        if not parts or not parts[0]:
            return ""
        return parts[0] if len(parts) <= 3 else parts[1]

    return df["place_guess"].apply(extract_ort)


def extract_from_place_guess(
    df: pd.DataFrame, position: int = -1, minimum_parts: int = 1
) -> pd.Series:
    """
    Extrahiert Teil aus place_guess (Fallback-Funktion).

    Args:
        df: DataFrame mit place_guess
        position: Index (-1=letzter, -2=vorletzter, 0=erster, etc.)
        minimum_parts: Minimale Anzahl Teile für gültigen Fallback

    Beispiele:
        position=-1, minimum_parts=2: Nur bei 2+ Teilen → letzter Teil
        position=0, minimum_parts=4: Nur bei 4+ Teilen → erster Teil
    """
    if "place_guess" not in df.columns:
        return pd.Series("", index=df.index, dtype=str)

    def extract_part(value: Any) -> str:
        if pd.isna(value):
            return ""
        parts = [p.strip() for p in str(value).strip().split(",")]
        if len(parts) < minimum_parts:
            return ""  # Nicht genug Teile
        try:
            return parts[position] if parts else ""
        except IndexError:
            return ""

    return df["place_guess"].apply(extract_part)


def get_location_with_fallback(
    df: pd.DataFrame,
    primary_column: str,
    fallback_position: int = -1,
    normalize_country: bool = False,
    minimum_parts: int = 1,
) -> pd.Series:
    """
    Ortsdaten mit Fallback-Logik und optionaler Normalisierung.

    Strategie:
    1. Primär: Strukturiertes Feld verwenden
    2. Fallback: Aus place_guess extrahieren (wenn genug Teile)
    3. Optional: Ländernamen normalisieren (Germany → Deutschland)

    Args:
        df: DataFrame
        primary_column: Primäre Spalte (z.B. "place_country_name")
        fallback_position: Position in place_guess (-1, -2, 0, etc.)
        normalize_country: Wenn True → "Germany"/"DE" → "Deutschland"
        minimum_parts: Minimale Teile für Fallback

    Returns:
        Serie mit Werten (primär oder fallback)
    """
    primary = copy_column(df, primary_column, default="")
    fallback = extract_from_place_guess(
        df, position=fallback_position, minimum_parts=minimum_parts
    )
    result = primary.where(primary != "", fallback)

    if normalize_country:
        country_map = {
            "germany": "Deutschland",
            "de": "Deutschland",
            "deu": "Deutschland",
            "deutschland": "Deutschland",
        }
        result = result.str.lower().str.strip().map(country_map).fillna(result)

    return result


def normalize_german_states(series: pd.Series) -> pd.Series:
    """
    Normalisiert NUR deutsche Bundesländer.
    Alle anderen Werte (Österreich, Schweiz, etc.) werden zu "".

    Args:
        series: Serie mit Bundesland-Namen

    Returns:
        Serie mit normalisierten deutschen Bundesländern oder ""
    """
    state_map = {
        # Baden-Württemberg
        "baden-württemberg": "Baden-Württemberg",
        "baden-wurttemberg": "Baden-Württemberg",
        "baden württemberg": "Baden-Württemberg",
        "badenwürttemberg": "Baden-Württemberg",
        "baden": "Baden-Württemberg",
        "württemberg": "Baden-Württemberg",
        "bw": "Baden-Württemberg",
        # Bayern
        "bayern": "Bayern",
        "bayer": "Bayern",
        "by": "Bayern",
        "bavaria": "Bayern",
        # Berlin
        "berlin": "Berlin",
        "be": "Berlin",
        # Brandenburg
        "brandenburg": "Brandenburg",
        "brandenb": "Brandenburg",
        "bb": "Brandenburg",
        # Bremen
        "bremen": "Bremen",
        "hb": "Bremen",
        # Hamburg
        "hamburg": "Hamburg",
        "hh": "Hamburg",
        # Hessen
        "hessen": "Hessen",
        "hesse": "Hessen",
        "he": "Hessen",
        # Mecklenburg-Vorpommern
        "mecklenburg-vorpommern": "Mecklenburg-Vorpommern",
        "mecklenburg vorpommern": "Mecklenburg-Vorpommern",
        "mecklenburgvorpommern": "Mecklenburg-Vorpommern",
        "mecklenburg": "Mecklenburg-Vorpommern",
        "vorpommern": "Mecklenburg-Vorpommern",
        "mv": "Mecklenburg-Vorpommern",
        "m-v": "Mecklenburg-Vorpommern",
        # Niedersachsen
        "niedersachsen": "Niedersachsen",
        "niedersachs": "Niedersachsen",
        "ns": "Niedersachsen",
        "ni": "Niedersachsen",
        # Nordrhein-Westfalen
        "nordrhein-westfalen": "Nordrhein-Westfalen",
        "nordrhein westfalen": "Nordrhein-Westfalen",
        "nordrheinwestfalen": "Nordrhein-Westfalen",
        "nrw": "Nordrhein-Westfalen",
        "nordrhein": "Nordrhein-Westfalen",
        "westfalen": "Nordrhein-Westfalen",
        "nw": "Nordrhein-Westfalen",
        # Rheinland-Pfalz
        "rheinland-pfalz": "Rheinland-Pfalz",
        "rheinland pfalz": "Rheinland-Pfalz",
        "rheinlandpfalz": "Rheinland-Pfalz",
        "rheinland": "Rheinland-Pfalz",
        "pfalz": "Rheinland-Pfalz",
        "rp": "Rheinland-Pfalz",
        "rlp": "Rheinland-Pfalz",
        # Saarland
        "saarland": "Saarland",
        "saar": "Saarland",
        "sl": "Saarland",
        # Sachsen
        "sachsen": "Sachsen",
        "sachs": "Sachsen",
        "sn": "Sachsen",
        "saxony": "Sachsen",
        # Sachsen-Anhalt
        "sachsen-anhalt": "Sachsen-Anhalt",
        "sachsen anhalt": "Sachsen-Anhalt",
        "sachsenanhalt": "Sachsen-Anhalt",
        "anhalt": "Sachsen-Anhalt",
        "st": "Sachsen-Anhalt",
        "lsa": "Sachsen-Anhalt",
        # Schleswig-Holstein
        "schleswig-holstein": "Schleswig-Holstein",
        "schleswig holstein": "Schleswig-Holstein",
        "schleswigholstein": "Schleswig-Holstein",
        "schleswig": "Schleswig-Holstein",
        "holstein": "Schleswig-Holstein",
        "sh": "Schleswig-Holstein",
        # Thüringen
        "thüringen": "Thüringen",
        "thueringen": "Thüringen",
        "thuringen": "Thüringen",
        "th": "Thüringen",
        "thuringia": "Thüringen",
    }

    # Bereinige und normalisiere
    cleaned = series.fillna("").astype(str).str.strip().str.lower()

    # Map anwenden - gibt "" zurück wenn nicht in der Map
    result = cleaned.map(state_map).fillna("")

    return result


def filter_by_erfassung(
    df_in: pd.DataFrame, log_func: Optional[Callable[[str], None]] = None
) -> pd.DataFrame:
    """
    Filtert bereits erfasste Beobachtungen.

    Args:
        df_in: Input DataFrame
        log_func: Logging-Funktion, die einen String nimmt und nichts zurückgibt

    Returns:
        Gefilterter DataFrame (nur leere Erfassung-Zeilen)
    """
    erfassung_column = "field:mykis-erfassung"

    def log(msg: str) -> None:
        if log_func:
            log_func(msg)
        else:
            print(msg)

    if erfassung_column not in df_in.columns:
        log("⚠️  Erfassung-Spalte nicht gefunden - keine Filterung")
        return df_in.copy()

    # Kategorisierung
    series = df_in[erfassung_column].fillna("").astype(str).str.strip().str.lower()
    ja = series.isin(["ja", "yes"]).sum()
    nein = series.isin(["nein", "no"]).sum()
    leer = (series == "").sum()
    sonstiges = len(df_in) - ja - nein - leer

    # Filtere
    df_filtered = df_in[series == ""].copy()

    # Ins Log
    log("")
    log(f"📊 Erfassung-Filter: Von {len(df_in)} Beobachtungen:")
    log(f"   ✅ {leer} noch nicht erfasst → werden verarbeitet")
    if ja > 0:
        log(f"   ❌ {ja} bereits erfasst (Ja) → übersprungen")
    if nein > 0:
        log(f"   ❌ {nein} abgelehnt (Nein) → übersprungen")
    if sonstiges > 0:
        log(f"   ⚠️  {sonstiges} mit sonstigem Text → übersprungen")

    return df_filtered


def convert_location_to_mtbq64(
    df: pd.DataFrame,
    mtb_referenc_df: pd.DataFrame,
    log_file_func: Callable[[str], None],
) -> pd.DataFrame:

    # Shapefile laden
    cfg = AppConfig()
    shapefile_pfad = cfg.resolve_shapefile_path()
    log_file_func(f"Lade Shapefile: {shapefile_pfad}")
    tk25_wgs84 = gpd.read_file(shapefile_pfad).to_crs(epsg=4326)
    log_file_func(f"Shapefile geladen: {len(tk25_wgs84)} MTB-Blätter")

    """
    Konvertiert Koordinaten in das MTB-Q64 Format (8x8 Raster).
    Nutzt das globale GeoDataFrame 'tk25_wgs84'.
    """
    # --- 1. Vorbereitung: Referenzliste für schnellen Abgleich aufbereiten ---
    mtb_col = next(
        (col for col in mtb_referenc_df.columns if col.lower() == "mtb"), None
    )
    referenz_map: dict[str, list[tuple[Hashable, pd.Series]]] = {}
    if not mtb_referenc_df.empty and mtb_col:
        for idx, ref_row in mtb_referenc_df.iterrows():
            # Wir nehmen den Wert so wie er ist (nur Leerzeichen weg)
            val = str(ref_row[mtb_col]).strip().replace(".", ",")

            # Wir splitten am Komma
            teile = val.split(",")

            if len(teile) >= 2:
                # Format mit Komma (z.B. "1000,233"): nimm alles vor Komma + max. 2 Stellen danach
                id_key = f"{teile[0].strip()},{teile[1].strip()[:2]}"
            else:
                # Format ohne Komma (z.B. "1000"): nimm einfach den ganzen Wert
                id_key = teile[0].strip()

            # Jetzt in die Map speichern (auch wenn die ID mehrmals vorkommt)
            if id_key not in referenz_map:
                referenz_map[id_key] = []
            referenz_map[id_key].append((idx, ref_row))

            if pd.isnull(ref_row["ostwert2"]) or pd.isnull(ref_row["nordwert2"]):
                # error
                log_file_func(
                    f"Referenz Fundort[{idx}] hat keinen Geokoordinaten (ostwert2,nordwert2)"
                )



    log_file_func(f"Referenz Datei Einträge: {len(mtb_referenc_df)}")
    log_file_func(f"Referenz Datei verschiedene 16tel Quadranten: {len(referenz_map)}")

    # --- 2. Variablen & Konstanten ---
    QUAD = {(0, 0): 1, (0, 1): 2, (1, 0): 3, (1, 1): 4}
    mbtq16_treffer_count: int = 0

    # --- 3. Hauptschleife über die Daten ---
    for dfRow, row in df.iterrows():
        punkt = Point(row["ostwert2"], row["nordwert2"])

        # Geometrie-Check (nutzt tk25_wgs84 aus dem globalen Scope)
        treffer = tk25_wgs84[tk25_wgs84.geometry.contains(punkt)]

        if treffer.empty:
            log_file_func(
                f"Fundort[{dfRow}] von INaturalist Liste nicht innerhalb der Topographischen Karte Deutschland TK25"
            )
            continue

        if len(treffer) > 1:
            log_file_func(
                f"Warnung: Fundort[{dfRow}] von INaturalist Liste in mehreren Quadranten der Topographischen Karte Deutschland TK25"
            )

        # Blatt-Infos extrahieren
        mtb = treffer.iloc[0]
        xmin, ymin, xmax, ymax = mtb.geometry.bounds

        # Position im 8×8 Raster berechnen (0–7)
        grid_col = min(int((row["ostwert2"] - xmin) / ((xmax - xmin) / 8)), 7)
        grid_row = min(int((ymax - row["nordwert2"]) / ((ymax - ymin) / 8)), 7)

        # Hierarchieebenen d1 (4x4), d2 (2x2), d3 (Einzelzelle) berechnen
        d1 = QUAD[(grid_row // 4, grid_col // 4)]
        d2 = QUAD[((grid_row % 4) // 2, (grid_col % 4) // 2)]
        d3 = QUAD[(grid_row % 2, grid_col % 2)]

        mtbq64 = f"{mtb['id']},{d1}{d2}{d3}"
        mtbq16 = f"{mtb['id']},{d1}{d2}"

        df.at[dfRow, "MTB"] = mtbq64

        # --- 4. Abgleich mit Referenzdaten ---
        if mtbq16 in referenz_map:
            mbtq16_treffer_count = mbtq16_treffer_count + 1
            assert mtb_col is not None
            referenz_treffer: list[tuple[Hashable, pd.Series]] = referenz_map[mtbq16]
            spalten_zu_kopieren = [
                "BASIS_ortslage",
                "BASIS_ort",
                "name_staat",
                "name_provinz",
                "name_kreis",
                "hoehenstufe",
                "ozeanitaet",
                "zonalitaet",
            ]

            if len(referenz_treffer) == 1:
                _, ref_row = referenz_treffer[0]
                # Liste der Spalten, die kopiert werden sollen

                # copy referenz auf in liste
                # df.at[dfRow, "MTB"] = mtbq64
                df.at[dfRow, "ostwert2"] = None
                df.at[dfRow, "nordwert2"] = None
                df.at[dfRow, "MTB"] = ref_row[mtb_col]

                changes = ", ".join(
                    f"{s}: '{df.at[dfRow, s]}' → '{ref_row[s]}'"
                    for s in spalten_zu_kopieren
                    if s in df.columns and s in ref_row.index
                )
                log_file_func(
                    f"Fundort-Zuordnung:[{dfRow}] --> {mtbq64} ' → ' {ref_row[mtb_col]}', '{changes}"
                )

                for spalte in spalten_zu_kopieren:
                    if spalte in df.columns and spalte in ref_row.index:
                        df.at[dfRow, spalte] = ref_row[spalte]

            else:
                min_distanz_series: pd.Series
                min_distanz = float("inf")
                for referenz_idx, ref_row in referenz_treffer:
                    if pd.notnull(ref_row["ostwert2"]) and pd.notnull(
                        ref_row["nordwert2"]
                    ):
                        ref_punkt = Point(ref_row["ostwert2"], ref_row["nordwert2"])
                        distanz = punkt.distance(ref_punkt)
                        if distanz < min_distanz:
                            min_distanz = distanz
                            min_distanz_series = ref_row

                    
                if min_distanz == float("inf"):
                    log_file_func(
                        f"Fundort-Zuordnung:[{dfRow}] --> Error: Keiner der Referenz 16tel Quadranten [{mtbq16}] hat Geokoordinaten (ostwert2,nordwert2)"
                    )
                else:
                    # copy referenz auf in liste
                    # df.at[dfRow, "MTB"] = mtbq64
                    df.at[dfRow, "ostwert2"] = None
                    df.at[dfRow, "nordwert2"] = None

                    df.at[dfRow, "MTB"] = min_distanz_series[mtb_col]
                    changes = ", ".join(
                        f"{s}: '{df.at[dfRow, s]}' → '{min_distanz_series[s]}'"
                        for s in spalten_zu_kopieren
                        if s in df.columns and s in min_distanz_series.index
                    )
                    log_file_func(
                        f"Fundort-Zuordnung:[{dfRow}] --> {mtbq64} ' → ' {min_distanz_series[mtb_col]}', '{changes}"
                    )

                    for spalte in spalten_zu_kopieren:
                        if spalte in df.columns and spalte in min_distanz_series.index:
                            df.at[dfRow, spalte] = min_distanz_series[spalte]

    log_file_func(f"Fundort-Zuordnung: {mbtq16_treffer_count} wurde zugeordnet")

    return df


# ==============================================================================
# MAIN MAPPING FUNCTION
# ==============================================================================


def map_inat_to_mykis(
    df_in: pd.DataFrame,
    log_file_func: Callable[[str], None],
    template_path: str | None = None,
    template_sheet: int = 0,
    mtb_reference_path: str | None = None,
    log_func: Optional[Callable[[str], None]] = None,
) -> pd.DataFrame:
    """
    Konvertiert iNaturalist → Mykis Format.

    Args:
        df_in: iNaturalist Daten
        template_path: Excel-Template mit Spaltendefinition
        template_sheet: Sheet-Index im Template

    Returns:
        DataFrame im Mykis-Format
    """
    log_file_func("Start inat to mykis convertation")

    def log(msg: str) -> None:
        if log_func:
            log_func(msg)
        else:
            print(msg)

    # ========================================================================
    # FILTER: Entferne bereits erfasste Zeilen
    # ========================================================================
    df_in = filter_by_erfassung(df_in, log)

    # Prüfe ob noch Zeilen übrig sind
    if len(df_in) == 0:
        print("❌ FEHLER: Keine Zeilen zum Verarbeiten übrig!")
        print("   Alle Beobachtungen wurden bereits erfasst.\n")
        return pd.DataFrame()

    # Template laden
    template_df = pd.read_excel(template_path, dtype=str, nrows=0)
    columns = template_df.columns.tolist()
    print(f"📋 Template geladen: {len(columns)} Spalten")

    out_df = pd.DataFrame(columns=columns)

    mtb_referenc_df = pd.DataFrame()

    if mtb_reference_path is None:
        log("Info: Keine Referenzdatei ausgewählt.")
        log_file_func("Info: Keine Referenzdatei ausgewählt.")
    elif not Path(mtb_reference_path).is_file():
        log_file_func(f"Warnung: Referenzdatei nicht gefunden: {mtb_reference_path}")
        log(f"Warnung: Referenzdatei nicht gefunden: {mtb_reference_path}")
    else:
        log_file_func(f"Info: Referenzdatei ausgewählt {mtb_reference_path}")
        log(f"Info: Referenzdatei ausgewählt {mtb_reference_path}")
        mtb_referenc_df = read_any_table(Path(mtb_reference_path))
        log_file_func(f"Info: Referenzdatei geladen: {len(mtb_referenc_df)} Spalten")
        log(f"{inspect_table_header(mtb_referenc_df)}")
        mtb_column = next(
            (col for col in mtb_referenc_df.columns if col.lower() == "mtb"), None
        )
        if mtb_column is None:
            log_file_func(
                f"Warnung: Kein 'MTB'-Feld in Datei gefunden: {mtb_reference_path}"
            )
            log(f"Warnung: Kein 'MTB'-Feld in Datei gefunden: {mtb_reference_path}")
            mtb_referenc_df = pd.DataFrame()
        else:
            log_file_func(f"Info: MTB-Spalte gefunden als '{mtb_column}'")
            log(f"Info: MTB-Spalte gefunden als '{mtb_column}'")

    # -------------------------------------------------------------------------
    # TAXONOMIE
    # -------------------------------------------------------------------------
    taxon_names = (
        df_in.apply(pick_taxon, axis=1).astype("string").fillna("").str.strip()
    )

    genus = taxon_names.str.split(r"\s+").str[0].fillna("").str.strip()
    epithet = taxon_names.str.split(r"\s+", n=1).str[1].fillna("").str.strip()

    assign_if_exists(out_df, "GATTUNG", genus)
    assign_if_exists(out_df, "ART", epithet)

    # -------------------------------------------------------------------------
    # DATUM
    # -------------------------------------------------------------------------
    dates = df_in.apply(pick_date, axis=1)
    assign_if_exists(out_df, "BASIS_datum1", dates)
    assign_if_exists(out_df, "datum2", dates)

    # -------------------------------------------------------------------------
    # PERSONEN (Basis - wird durch Custom Fields überschrieben)
    # -------------------------------------------------------------------------
    names_series = df_in.apply(pick_name, axis=1)
    assign_if_exists(out_df, "erfasser", names_series)

    # -------------------------------------------------------------------------
    # NACHWEISQUELLE
    # -------------------------------------------------------------------------
    assign_if_exists(
        out_df, "nachweisquelle", pd.Series("iNaturalist", index=df_in.index)
    )

    # -------------------------------------------------------------------------
    # ORTE (mit intelligenten Fallbacks)
    # -------------------------------------------------------------------------
    # Land (fallback: letzter Teil bei 2+ Teilen)
    name_staat = get_location_with_fallback(
        df_in,
        primary_column="place_country_name",
        fallback_position=-1,
        normalize_country=True,
        minimum_parts=2,
    )
    assign_if_exists(out_df, "name_staat", name_staat)

    # Bundesland (fallback: vorletzter Teil bei 3+ Teilen)
    name_provinz = get_location_with_fallback(
        df_in,
        primary_column="place_state_name",
        fallback_position=-2,
        minimum_parts=3,
    )

    name_provinz = normalize_german_states(name_provinz)
    assign_if_exists(out_df, "name_provinz", name_provinz)

    # Fundort (adaptive Logik: 1-3 Teile→1., 4+→2. Teil)
    basis_ort = extract_basis_ort(df_in)
    assign_if_exists(out_df, "BASIS_ort", basis_ort)

    assign_if_exists(
        out_df, "BASIS_ortslage", pd.Series("iNaturalist", index=df_in.index)
    )



    # -------------------------------------------------------------------------
    # KOORDINATEN (latitude=Nordwert/Y, longitude=Ostwert/X)
    # -------------------------------------------------------------------------
    assign_if_exists(out_df, "nordwert2", copy_numeric_column(df_in, "latitude"))
    assign_if_exists(out_df, "ostwert2", copy_numeric_column(df_in, "longitude"))

    # assign_if_exists(out_df, "Foto_Zeichnung", pd.Series("D", index=df_in.index))
    id_col = copy_column(df_in, "id")      
    if id_col is not None:
        foto_series = "iNNr:" + id_col.astype(str).fillna("")
    else:
        foto_series = pd.Series("iNNr:", index=df_in.index)
    assign_if_exists(out_df, "Foto_Zeichnung", foto_series)

    assign_if_exists(out_df, "art_bemerkung", copy_column(df_in, "field:mykis-bemerkung"))

    assign_if_exists(out_df, "Ungenauigkeit", copy_column(df_in, "positional_accuracy"))

    # -------------------------------------------------------------------------
    # MYKIS CUSTOM FIELDS
    # -------------------------------------------------------------------------
    assign_if_exists(
        out_df, "organ_substrat", copy_column(df_in, "field:mykis-substrat_organ")
    )
    assign_if_exists(
        out_df, "substratzustand", copy_column(df_in, "field:mykis-substrat_zustand")
    )
    assign_if_exists(out_df, "substrat_text", copy_column(df_in, "description"))
    assign_if_exists(
        out_df, "wuchsstelle", copy_column(df_in, "field:mykis-wuchsstelle")
    )
    assign_if_exists(out_df, "stadium", copy_column(df_in, "field:mykis-stadium"))

    assign_if_exists(
        out_df, "sonderstandort", copy_column(df_in, "field:mykis-pflanzengesellschaft")
    )

    assign_if_exists(out_df, "Wirt", copy_column(df_in, "field:mykis-substrat/-wirt"))

    # Sammler/Bestimmer: Custom Fields haben Vorrang vor user_name
    mykis_leg = copy_column(df_in, "field:mykis-leg.")
    mykis_det = copy_column(df_in, "field:mykis-det.")

    sammler_final = mykis_leg.where(mykis_leg != "", names_series)
    bestimmer_final = mykis_det.where(mykis_det != "", names_series)

    assign_if_exists(out_df, "sammler", sammler_final)
    assign_if_exists(out_df, "bestimmer", bestimmer_final)

    out_df = convert_location_to_mtbq64(
        out_df, mtb_referenc_df, log_file_func=log_file_func
    )

    # Bemerkungen
    # assign_if_exists(
    #     out_df, "beobachtung_bemerkungen", copy_column(df_in, "description")
    # )

    # -------------------------------------------------------------------------
    # AUSGABE
    # -------------------------------------------------------------------------
    print(f"✅ Mapping abgeschlossen: {len(out_df)} Zeilen")
    print(out_df.head())

    return out_df
