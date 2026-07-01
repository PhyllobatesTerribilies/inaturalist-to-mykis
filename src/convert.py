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

import logging
from pathlib import Path
from typing import Any, Callable, Hashable, Optional

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from src.config import AppConfig
from src.io_validate import inspect_table_header, make_logger, read_any_table

# ==============================================================================
# KONSTANTEN
# ==============================================================================

# Eingebaute Standard-Übersetzung iNaturalist-Wirtsname → Mykis-Wirtsbezeichnung.
# Zur Laufzeit wird stattdessen assets/wirt_uebersetzungen.csv geladen, falls
# vorhanden (siehe load_wirt_uebersetzungen); diese Werte sind nur der Fallback.
_WIRT_UEBERSETZUNGEN_DEFAULT = {
    "angiospermae": "LAUBHOLZ/LAUBBAUM",
    "pinopsida": "NADELHOLZ/NADELBAUM",
    "gliridae": "Bilch",
    "harmonia axyridis": "Asiatischer Marienkäfer",
    "capreolus capreolus": "Reh",
    "castoridae": "Biber",
    "dama dama": "Damwild",
    "carnivore": "Fleischfresser",
    "bos taurus": "Hausrind",
    "sus scrofa": "Wildschwein",
    "sus scrofa domestica": "Hausschwein",
    "capra aegagrus hircus": "Hausziege",
    "canis lupus familiaris": "Hund, Haushund",
    "coleoptera": "KÄFER",
    "coccinellidae": "MARIENKÄFER",
    "ovis orientalis": "Mufflon",
    "equus caballus": "Pferd",
    "vulpes vulpes": "Rotfuchs",
    "cervus elaphus": "Rothirsch",
    "lepidoptera": "SCHMETTERLINGE",
    "heteroptera": "WANZEN",
    "bubalus arnee": "Wasserbüffel",
    "oryctolagus cuniculus": "Wildkaninchen",
}

# iNaturalist-Qualitätsstufe → Mykis-Qualitäts-ID
QUALITAET_IDS = {
    "unsicher": "1",
    "mikroskopiert": "2",
    "gesichert": "4",
    "plausibel": "5",
    "literaturdaten": "6",
    "sequenziert": "7",
    "mikroskopiert + sequenziert": "8",
}

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================


def load_wirt_uebersetzungen() -> dict[str, str]:
    """
    Lädt die Wirt-Übersetzungstabelle aus assets/wirt_uebersetzungen.csv.

    Format: zwei Spalten mit Kopfzeile (``inaturalist;mykis``). Schlüssel werden
    case-insensitiv verglichen, die Mykis-Werte bleiben unverändert. Neue Wirte
    lassen sich so ohne Code-Änderung ergänzen. Fehlt oder scheitert die Datei,
    greifen die eingebauten Standardwerte.
    """
    path = AppConfig().resolve_wirt_translations_path()
    if not path.is_file():
        return dict(_WIRT_UEBERSETZUNGEN_DEFAULT)

    try:
        df = read_any_table(path)
    except Exception as e:
        logging.warning(
            "Wirt-Übersetzung: '%s' nicht lesbar (%s) – nutze Standardwerte", path, e
        )
        return dict(_WIRT_UEBERSETZUNGEN_DEFAULT)

    # Spalten case-insensitiv und BOM-tolerant zuordnen, sonst die ersten zwei.
    cols = {str(c).replace("﻿", "").strip().lower(): c for c in df.columns}
    src_col = cols.get("inaturalist")
    dst_col = cols.get("mykis")
    if src_col is None or dst_col is None:
        if len(df.columns) < 2:
            logging.warning(
                "Wirt-Übersetzung: '%s' hat keine 2 Spalten – nutze Standardwerte", path
            )
            return dict(_WIRT_UEBERSETZUNGEN_DEFAULT)
        src_col, dst_col = df.columns[0], df.columns[1]

    mapping: dict[str, str] = {}
    for _, row in df.iterrows():
        key = str(row[src_col]).strip().lower()
        value = str(row[dst_col]).strip()
        if key and value and key != "nan" and value != "nan":
            mapping[key] = value
    return mapping or dict(_WIRT_UEBERSETZUNGEN_DEFAULT)


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
        logging.debug(
            "Optionale Spalte '%s' nicht vorhanden – Default wird verwendet", column
        )
        return pd.Series(default, index=df.index, dtype=str)

    return df[column].fillna(default).astype(str).str.strip().replace("", default)


def copy_numeric_column(df: pd.DataFrame, column: str) -> pd.Series:
    """Kopiert numerische Spalte (z.B. Koordinaten)."""
    if column not in df.columns:
        logging.debug(
            "Optionale Spalte '%s' nicht vorhanden – Default wird verwendet", column
        )
        return pd.Series(None, index=df.index, dtype=float)
    return pd.to_numeric(df[column], errors="coerce")


def build_name_lookup(name_ref_df: pd.DataFrame) -> dict[str, str]:
    """
    Erstellt Lookup-Dictionary aus Namenskonvertierungs-Datei.

    Erwartet Spalten: user_login, mykis-name (Groß-/Kleinschreibung egal)

    Returns:
        Dict: user_login → mykis-name
    """
    cols = {c.lower().strip(): c for c in name_ref_df.columns}
    login_col = cols.get("user_login")
    mykis_name_col = cols.get("mykis-name")

    if login_col is None or mykis_name_col is None:
        print(
            "⚠️  WARNUNG: Namenskonvertierungs-Datei braucht Spalten 'user_login' und 'mykis-name'"
        )
        return {}

    lookup: dict[str, str] = {}
    for _, row in name_ref_df.iterrows():
        login = str(row[login_col]).strip()
        mykis_name = str(row[mykis_name_col]).strip()
        if login and mykis_name and login != "nan" and mykis_name != "nan":
            lookup[login] = mykis_name
    return lookup


def assign_if_exists(out_df: pd.DataFrame, column: str, series: pd.Series) -> None:
    """Weist Serie einer Spalte zu (nur wenn Spalte im Template existiert)."""
    if column in out_df.columns:
        out_df[column] = series


# ==============================================================================
# EXTRACTION FUNCTIONS (row-by-row via .apply())
# ==============================================================================


def extract_taxon(row: pd.Series[Any]) -> str:
    """Extrahiert Taxon-Namen aus verschiedenen möglichen Spalten."""
    for key in ("scientific_name", "species_guess", "taxon_name"):
        if key in row and pd.notna(row[key]) and str(row[key]).strip():
            return str(row[key]).strip()
    return ""


def extract_date(row: pd.Series[Any]) -> str:
    """Extrahiert und formatiert Datum als DD.MM.YYYY."""
    for key in ("observed_on", "observed_on_string"):
        val = row.get(key, None)
        if pd.notna(val) and str(val).strip():
            dt = pd.to_datetime(str(val), errors="coerce")
            if pd.notna(dt):
                return dt.strftime("%d.%m.%Y")
    return ""


def extract_name(row: pd.Series[Any]) -> str:
    """Extrahiert Benutzernamen."""
    for key in ("user_name", "user_login"):
        v = row.get(key, None)
        if pd.notna(v) and str(v).strip():
            name = str(v).strip()
            if key == "user_name":
                parts = name.split()
                if len(parts) >= 2:
                    # Konvention: letztes Token = Nachname, Rest = Vorname(n)
                    surname = parts[-1]
                    given = " ".join(parts[:-1])
                    return f"{surname}, {given}"

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


def extract_location_with_fallback(
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

    cleaned = series.fillna("").astype(str).str.strip().str.lower()
    return cleaned.map(state_map).fillna("")


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
    log = make_logger(log_func)

    if erfassung_column not in df_in.columns:
        log("⚠️  Erfassung-Spalte nicht gefunden - keine Filterung")
        return df_in.copy()

    series = df_in[erfassung_column].fillna("").astype(str).str.strip().str.lower()
    yes_count = series.isin(["ja", "yes"]).sum()
    no_count = series.isin(["nein", "no"]).sum()
    empty_count = (series == "").sum()
    other_count = len(df_in) - yes_count - no_count - empty_count

    df_filtered = df_in[series == ""].copy()

    log("")
    log(f"📊 Erfassung-Filter: Von {len(df_in)} Beobachtungen:")
    log(f"   ✅ {empty_count} noch nicht erfasst → werden verarbeitet")
    if yes_count > 0:
        log(f"   ❌ {yes_count} bereits erfasst (Ja) → übersprungen")
    if no_count > 0:
        log(f"   ❌ {no_count} abgelehnt (Nein) → übersprungen")
    if other_count > 0:
        log(f"   ⚠️  {other_count} mit sonstigem Text → übersprungen")

    return df_filtered


# Quadranten-Nummerierung im 2×2-Block: (Zeile, Spalte) → 1..4
_QUAD = {(0, 0): 1, (0, 1): 2, (1, 0): 3, (1, 1): 4}

# Ortsfelder, die bei einem Referenztreffer aus der Referenzzeile übernommen werden
_MTBQ_REFERENCE_COLUMNS = [
    "BASIS_ortslage",
    "BASIS_ort",
    "name_staat",
    "name_provinz",
    "name_kreis",
    "hoehenstufe",
    "ozeanitaet",
    "zonalitaet",
]

# Spaltenkopf der Änderungs-CSV: id + je Feld ein alt/neu-Paar (MTB + Ortsfelder)
CHANGE_LOG_COLUMNS = ["id", "MTB_alt", "MTB_neu"] + [
    f"{col}_{suffix}" for col in _MTBQ_REFERENCE_COLUMNS for suffix in ("alt", "neu")
]


def _load_tk25_shapefile(log_file_func: Callable[[str], None]) -> gpd.GeoDataFrame:
    """Lädt das TK25-Shapefile und projiziert es nach WGS84."""
    shapefile_path = AppConfig().resolve_shapefile_path()
    log_file_func(f"Lade Shapefile: {shapefile_path}")
    tk25 = gpd.read_file(shapefile_path).to_crs(epsg=4326)
    log_file_func(f"Shapefile geladen: {len(tk25)} MTB-Blätter")
    return tk25


def _build_reference_map(
    mtb_ref_df: pd.DataFrame, log_file_func: Callable[[str], None]
) -> tuple[dict[str, list[tuple[Hashable, pd.Series]]], Optional[str]]:
    """
    Baut den 16tel-Quadranten-Index der Referenzliste auf.

    Returns:
        (ref_map: 16tel-ID → Liste von Referenzzeilen, MTB-Spaltenname oder None)
    """
    mtb_col = next((col for col in mtb_ref_df.columns if col.lower() == "mtb"), None)
    ref_map: dict[str, list[tuple[Hashable, pd.Series]]] = {}
    missing_coords = 0
    if not mtb_ref_df.empty and mtb_col:
        for ref_idx, ref_row in mtb_ref_df.iterrows():
            parts = str(ref_row[mtb_col]).strip().replace(".", ",").split(",")
            if len(parts) >= 2:
                # "1000,233" → Blatt-ID + max. 2 Stellen des Quadranten
                id_key = f"{parts[0].strip()},{parts[1].strip()[:2]}"
            else:
                id_key = parts[0].strip()
            ref_map.setdefault(id_key, []).append((ref_idx, ref_row))

            if pd.isnull(ref_row["ostwert2"]) or pd.isnull(ref_row["nordwert2"]):
                missing_coords += 1

    log_file_func(f"Referenz Datei Einträge: {len(mtb_ref_df)}")
    log_file_func(f"Referenz Datei verschiedene 16tel Quadranten: {len(ref_map)}")
    if missing_coords:
        # Nur als Summe – relevant wird ein fehlender Eintrag erst, wenn eine
        # Beobachtung ihn wirklich braucht (dann Log in _apply_reference_match).
        log_file_func(
            f"Referenz Datei: {missing_coords} Einträge ohne Geokoordinaten "
            f"(ostwert2,nordwert2)"
        )
    return ref_map, mtb_col


def _find_tk25_sheets(point: Point, tk25: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    TK25-Blätter, die den Punkt enthalten.

    Der Spatial-Index (R-Tree) filtert per Bounding-Box vor, das exakte
    ``contains`` läuft dann nur noch auf den wenigen Kandidaten – identisches
    Ergebnis wie ein Full-Scan, aber um Größenordnungen schneller.
    """
    candidates = tk25.iloc[tk25.sindex.query(point)]
    return candidates[candidates.geometry.contains(point)]


def _compute_mtbq(
    bounds: tuple[float, float, float, float], ost: float, nord: float, sheet_id: Any
) -> tuple[str, str]:
    """Berechnet (MTBQ64, MTBQ16) aus Blattgrenzen und Koordinate im 8×8-Raster."""
    xmin, ymin, xmax, ymax = bounds
    grid_col = min(int((ost - xmin) / ((xmax - xmin) / 8)), 7)
    grid_row = min(int((ymax - nord) / ((ymax - ymin) / 8)), 7)
    d1 = _QUAD[(grid_row // 4, grid_col // 4)]
    d2 = _QUAD[((grid_row % 4) // 2, (grid_col % 4) // 2)]
    d3 = _QUAD[(grid_row % 2, grid_col % 2)]
    return f"{sheet_id},{d1}{d2}{d3}", f"{sheet_id},{d1}{d2}"


def _nearest_reference(
    ref_matches: list[tuple[Hashable, pd.Series]], point: Point
) -> Optional[pd.Series]:
    """Referenzzeile mit den nächstgelegenen Koordinaten (oder None, wenn keine hat)."""
    nearest: Optional[pd.Series] = None
    min_distance = float("inf")
    for _ref_idx, ref_row in ref_matches:
        if pd.notnull(ref_row["ostwert2"]) and pd.notnull(ref_row["nordwert2"]):
            distance = point.distance(Point(ref_row["ostwert2"], ref_row["nordwert2"]))
            if distance < min_distance:
                min_distance = distance
                nearest = ref_row
    return nearest


def _csv_value(value: Any) -> Any:
    """NaN/None → leeres Feld, sonst unverändert (für die Änderungs-CSV)."""
    return "" if pd.isna(value) else value


def _copy_reference_row(
    df: pd.DataFrame,
    row_idx: Hashable,
    ref_row: pd.Series,
    mtb_col: str,
    mtbq64: str,
    log_file_func: Callable[[str], None],
    change_func: Optional[Callable[[dict[str, Any]], None]] = None,
) -> None:
    """Übernimmt MTB + Ortsfelder aus einer Referenzzeile (verwirft die Rohkoordinaten)."""
    new_mtb = ref_row[mtb_col]
    df.at[row_idx, "ostwert2"] = None
    df.at[row_idx, "nordwert2"] = None
    df.at[row_idx, "MTB"] = new_mtb

    # Änderungen vor dem Überschreiben erfassen (alt → neu)
    record: dict[str, Any] = {
        "id": row_idx,
        "MTB_alt": _csv_value(mtbq64),
        "MTB_neu": _csv_value(new_mtb),
    }
    change_parts = []
    for s in _MTBQ_REFERENCE_COLUMNS:
        if s in df.columns and s in ref_row.index:
            old, new = df.at[row_idx, s], ref_row[s]
            record[f"{s}_alt"] = _csv_value(old)
            record[f"{s}_neu"] = _csv_value(new)
            change_parts.append(f"{s}: '{old}' → '{new}'")
        else:
            record[f"{s}_alt"] = ""
            record[f"{s}_neu"] = ""
    changes = ", ".join(change_parts)
    log_file_func(
        f"Fundort-Zuordnung:[{row_idx}] --> {mtbq64} ' → ' {new_mtb}', '{changes}"
    )
    if change_func is not None:
        change_func(record)

    for column in _MTBQ_REFERENCE_COLUMNS:
        if column in df.columns and column in ref_row.index:
            df.at[row_idx, column] = ref_row[column]


def _apply_reference_match(
    df: pd.DataFrame,
    row_idx: Hashable,
    ref_matches: list[tuple[Hashable, pd.Series]],
    point: Point,
    mtb_col: str,
    mtbq64: str,
    mtbq16: str,
    log_file_func: Callable[[str], None],
    change_func: Optional[Callable[[dict[str, Any]], None]] = None,
) -> None:
    """Übernimmt den passenden Referenzeintrag (eindeutig oder nächstgelegen)."""
    if len(ref_matches) == 1:
        _copy_reference_row(
            df, row_idx, ref_matches[0][1], mtb_col, mtbq64, log_file_func, change_func
        )
        return

    nearest = _nearest_reference(ref_matches, point)
    if nearest is None:
        log_file_func(
            f"Fundort-Zuordnung:[{row_idx}] --> Error: Keiner der Referenz 16tel "
            f"Quadranten [{mtbq16}] hat Geokoordinaten (ostwert2,nordwert2)"
        )
    else:
        _copy_reference_row(
            df, row_idx, nearest, mtb_col, mtbq64, log_file_func, change_func
        )


def convert_location_to_mtbq64(
    df: pd.DataFrame,
    mtb_ref_df: pd.DataFrame,
    log_file_func: Callable[[str], None],
    change_func: Optional[Callable[[dict[str, Any]], None]] = None,
) -> None:
    """
    Konvertiert Koordinaten in das MTB-Q64 Format (8x8 Raster).

    Lädt das TK25-Shapefile, bestimmt für jeden Punkt das Messtischblatt
    und den 64tel-Quadranten und gleicht das Ergebnis mit der
    Fundort-Referenzliste ab. Mutiert ``df`` in-place.

    ``change_func`` erhält – falls gesetzt – pro Referenzzuordnung einen
    Datensatz (Schema: ``CHANGE_LOG_COLUMNS``) für die Änderungs-CSV.
    """
    tk25 = _load_tk25_shapefile(log_file_func)
    ref_map, mtb_col = _build_reference_map(mtb_ref_df, log_file_func)

    match_count = 0
    for row_idx, row in df.iterrows():
        point = Point(row["ostwert2"], row["nordwert2"])
        sheets = _find_tk25_sheets(point, tk25)

        if sheets.empty:
            log_file_func(
                f"Fundort[{row_idx}] von INaturalist Liste nicht innerhalb der Topographischen Karte Deutschland TK25"
            )
            continue

        if len(sheets) > 1:
            log_file_func(
                f"Warnung: Fundort[{row_idx}] von INaturalist Liste in mehreren Quadranten der Topographischen Karte Deutschland TK25"
            )

        sheet = sheets.iloc[0]
        mtbq64, mtbq16 = _compute_mtbq(
            sheet.geometry.bounds, row["ostwert2"], row["nordwert2"], sheet["id"]
        )
        df.at[row_idx, "MTB"] = mtbq64

        if mtb_col is not None and mtbq16 in ref_map:
            match_count += 1
            _apply_reference_match(
                df,
                row_idx,
                ref_map[mtbq16],
                point,
                mtb_col,
                mtbq64,
                mtbq16,
                log_file_func,
                change_func,
            )

    log_file_func(f"Fundort-Zuordnung: {match_count} wurde zugeordnet")


def parse_coord_no_separator(
    df: pd.DataFrame, log_file_func: Callable[[str], None]
) -> pd.DataFrame:
    """
    Wandelt ostwert2/nordwert2 ohne Dezimaltrennzeichen in Floats um.

    Deutschland: Breite 47–55°N, Länge 6–15°O

    Erste Ziffer ≥ 6  → Längengrad  6– 9° → Komma nach 1. Stelle: "7232"  →  7.232
    Erste Ziffer < 6  → Breiten- oder Längengrad 10–15° → Komma nach 2. Stelle:
                        "51232" → 51.232  |  "13232" → 13.232

    Bereits formatierte Werte ("51,232" / "51.232") werden direkt geparst.
    Log nur bei tatsächlicher Änderung.
    """
    for idx, row in df.iterrows():
        results: dict[str, float | None] = {}
        changed: dict[str, tuple[Any, float | None]] = {}

        for column in ("ostwert2", "nordwert2"):
            value = row.get(column)

            if pd.isna(value) or value is None:
                results[column] = None
                continue

            s = str(value).strip().replace(",", ".")

            # ganzzahlige Floats bereinigen: "52134.0" → "52134"
            if s.endswith(".0"):
                s = s[:-2]

            # Dezimaltrennzeichen nur bei reinen Ziffernfolgen einfügen.
            # (Negative/wissenschaftliche Werte wie "-3" oder "1e5" bleiben
            # unangetastet und werden direkt an float() übergeben – sonst
            # würde int(s[0]) auf dem Vorzeichen crashen.)
            if "." not in s and s.isdigit():
                s = s[:1] + "." + s[1:] if int(s[0]) >= 6 else s[:2] + "." + s[2:]

            try:
                result = float(s)
                results[column] = result
                if result != value:
                    changed[column] = (value, result)
            except ValueError:
                log_file_func(
                    f"parse_coord[{idx}]: Konvertierung fehlgeschlagen '{value}' → None"
                )
                results[column] = None

        if changed:
            parts = ", ".join(
                f"{c}: '{old}' → {new}" for c, (old, new) in changed.items()
            )
            log_file_func(f"parse_coord[{idx}]: {parts}")

        for column, value in results.items():
            df.at[idx, column] = value

    return df


# ==============================================================================
# MAPPING-SCHRITTE (jeweils ein Themenbereich)
# ==============================================================================


def load_mtb_reference(
    mtb_reference_path: str | None,
    log: Callable[[str], None],
    log_file_func: Callable[[str], None],
) -> pd.DataFrame:
    """
    Lädt und validiert die Fundort-Referenzdatei.

    Returns:
        Referenz-DataFrame, oder leeres DataFrame wenn keine/ungültige Datei.
    """
    if mtb_reference_path is None:
        log("Info: Keine Referenzdatei ausgewählt.")
        log_file_func("Info: Keine Referenzdatei ausgewählt.")
        return pd.DataFrame()

    if not Path(mtb_reference_path).is_file():
        msg = f"Warnung: Referenzdatei nicht gefunden: {mtb_reference_path}"
        log(msg)
        log_file_func(msg)
        return pd.DataFrame()

    log(f"Info: Referenzdatei ausgewählt {mtb_reference_path}")
    log_file_func(f"Info: Referenzdatei ausgewählt {mtb_reference_path}")

    mtb_ref_df = read_any_table(Path(mtb_reference_path))
    log_file_func(f"Info: Referenzdatei geladen: {len(mtb_ref_df)} Spalten")
    log(f"{inspect_table_header(mtb_ref_df)}")

    mtb_column = next((col for col in mtb_ref_df.columns if col.lower() == "mtb"), None)
    if mtb_column is None:
        msg = f"Warnung: Kein 'MTB'-Feld in Datei gefunden: {mtb_reference_path}"
        log(msg)
        log_file_func(msg)
        return pd.DataFrame()

    # Die Koordinaten-Spalten werden beim Abgleich zwingend gebraucht
    # (convert_location_to_mtbq64 greift direkt darauf zu).
    missing_coords = [
        c for c in ("ostwert2", "nordwert2") if c not in mtb_ref_df.columns
    ]
    if missing_coords:
        msg = (
            f"Warnung: Referenzdatei fehlen die Spalten "
            f"{', '.join(missing_coords)} – Fundort-Abgleich wird übersprungen: "
            f"{mtb_reference_path}"
        )
        log(msg)
        log_file_func(msg)
        return pd.DataFrame()

    log(f"Info: MTB-Spalte gefunden als '{mtb_column}'")
    log_file_func(f"Info: MTB-Spalte gefunden als '{mtb_column}'")
    return mtb_ref_df


def map_taxonomy(df_in: pd.DataFrame, out_df: pd.DataFrame) -> None:
    """Schreibt GATTUNG und ART aus dem Taxon-Namen."""
    taxon_names = (
        df_in.apply(extract_taxon, axis=1).astype("string").fillna("").str.strip()
    )
    genus = taxon_names.str.split(r"\s+").str[0].fillna("").str.strip()
    epithet = taxon_names.str.split(r"\s+", n=1).str[1].fillna("").str.strip()
    assign_if_exists(out_df, "GATTUNG", genus)
    assign_if_exists(out_df, "ART", epithet)


def map_dates(df_in: pd.DataFrame, out_df: pd.DataFrame) -> None:
    """Schreibt Beobachtungsdatum (BASIS_datum1 und datum2)."""
    dates = df_in.apply(extract_date, axis=1)
    assign_if_exists(out_df, "BASIS_datum1", dates)
    assign_if_exists(out_df, "datum2", dates)


def resolve_erfasser(
    df_in: pd.DataFrame,
    name_ref_path: str | None,
    use_login_as_erfasser: bool,
    log: Callable[[str], None],
    log_file_func: Callable[[str], None],
) -> pd.Series:
    """
    Ermittelt die Erfasser-Namen (auch Basis für Sammler/Bestimmer).

    Reihenfolge:
    1. user_name → "Nachname, Vorname" (bzw. user_login, wenn Option gesetzt)
    2. Namenszuordnungs-Liste (user_login → mykis-name) hat Vorrang
    """
    names_series = df_in.apply(extract_name, axis=1)

    if use_login_as_erfasser:
        names_series = copy_column(df_in, "user_login")
        log("ℹ️  Erfasser: user_login wird unverändert übernommen")

    if name_ref_path and Path(name_ref_path).is_file():
        name_ref_df = read_any_table(Path(name_ref_path))
        name_lookup = build_name_lookup(name_ref_df)
        if name_lookup:
            login_series = copy_column(df_in, "user_login")
            lookup_result = login_series.map(name_lookup)
            # Lookup-Ergebnis hat Vorrang, Fallback auf extract_name
            names_series = lookup_result.where(
                lookup_result.notna()
                & (lookup_result != "nan")
                & (lookup_result != ""),
                names_series,
            )
            log(
                f"✅ Namenskonvertierung: {len(name_lookup)} Einträge, "
                f"{lookup_result.notna().sum()} Treffer"
            )
            log_file_func(
                f"Namenskonvertierung geladen: {name_ref_path}, {len(name_lookup)} Einträge"
            )
    elif name_ref_path:
        log(f"⚠️  Namenskonvertierungs-Datei nicht gefunden: {name_ref_path}")

    return names_series


def map_locations(df_in: pd.DataFrame, out_df: pd.DataFrame) -> None:
    """Schreibt Staat, Provinz, Fundort und Ortslage."""
    # Land (Fallback: letzter Teil bei 2+ Teilen)
    name_staat = extract_location_with_fallback(
        df_in,
        primary_column="place_country_name",
        fallback_position=-1,
        normalize_country=True,
        minimum_parts=2,
    )
    assign_if_exists(out_df, "name_staat", name_staat)

    # Bundesland (Fallback: vorletzter Teil bei 3+ Teilen)
    name_provinz = extract_location_with_fallback(
        df_in,
        primary_column="place_state_name",
        fallback_position=-2,
        minimum_parts=3,
    )
    name_provinz = normalize_german_states(name_provinz)
    assign_if_exists(out_df, "name_provinz", name_provinz)

    # Fundort (adaptive Logik: 1-3 Teile→1., 4+→2. Teil)
    assign_if_exists(out_df, "BASIS_ort", extract_basis_ort(df_in))
    assign_if_exists(
        out_df, "BASIS_ortslage", pd.Series("iNaturalist", index=df_in.index)
    )


def map_coordinates(
    df_in: pd.DataFrame,
    out_df: pd.DataFrame,
    log_file_func: Callable[[str], None],
) -> None:
    """
    Schreibt Koordinaten (latitude=Nordwert, longitude=Ostwert),
    Foto-Referenz und Ungenauigkeit. Mutiert ``out_df`` in-place.
    """
    assign_if_exists(out_df, "nordwert2", copy_numeric_column(df_in, "latitude"))
    assign_if_exists(out_df, "ostwert2", copy_numeric_column(df_in, "longitude"))
    # parse_coord_no_separator mutiert out_df in-place (df.at[...]).
    parse_coord_no_separator(out_df, log_file_func)

    id_col = copy_column(df_in, "id")
    foto_series = "iNNr:" + id_col.astype(str).fillna("")
    assign_if_exists(out_df, "Foto_Zeichnung", foto_series)

    assign_if_exists(out_df, "Ungenauigkeit", copy_column(df_in, "positional_accuracy"))


def map_custom_fields(df_in: pd.DataFrame, out_df: pd.DataFrame) -> None:
    """Schreibt die Mykis-Custom-Fields (Substrat, Wuchsstelle, Wirt …)."""
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
    assign_if_exists(
        out_df, "art_bemerkung", copy_column(df_in, "field:mykis-bemerkung")
    )
    assign_if_exists(out_df, "Wirt", build_wirt_series(df_in))


def build_wirt_series(df_in: pd.DataFrame) -> pd.Series:
    """Übersetzt den Wirts-Namen und ergänzt ' sp.' bei einzelnen Gattungen."""
    uebersetzungen = load_wirt_uebersetzungen()
    wirt_col = copy_column(df_in, "field:mykis-substrat/-wirt").str.strip()
    wirt_lower = wirt_col.str.lower()
    was_translated = wirt_lower.isin(uebersetzungen)
    wirt_col = wirt_col.where(~was_translated, wirt_lower.map(uebersetzungen))
    # Einzelnes Wort (Gattung ohne Art) → " sp." anhängen
    is_genus = (
        wirt_col.notna()
        & (wirt_col != "")
        & ~wirt_col.str.contains(" ")
        & ~was_translated
    )
    return wirt_col.where(~is_genus, wirt_col + " sp.")


def map_collector_determiner(
    df_in: pd.DataFrame, out_df: pd.DataFrame, names_series: pd.Series
) -> None:
    """Schreibt Sammler/Bestimmer (Custom Fields haben Vorrang vor dem Erfasser)."""
    mykis_leg = copy_column(df_in, "field:mykis-leg.")
    mykis_det = copy_column(df_in, "field:mykis-det.")
    assign_if_exists(out_df, "sammler", mykis_leg.where(mykis_leg != "", names_series))
    assign_if_exists(
        out_df, "bestimmer", mykis_det.where(mykis_det != "", names_series)
    )


def map_quality(
    df_in: pd.DataFrame,
    out_df: pd.DataFrame,
    log_file_func: Callable[[str], None],
) -> None:
    """
    Schreibt die Mykis-Qualitäts-ID.

    Fallback: keine Qualität angegeben, aber Sequenzdaten vorhanden → "sequenziert".
    """
    quality_column = "Qualität"
    if quality_column not in out_df.columns:
        return

    qualitaet_text = copy_column(df_in, "field:mykis-qualität")
    qualitaet_normalized = qualitaet_text.str.strip().str.lower()
    qualitaet_id = qualitaet_normalized.map(QUALITAET_IDS).fillna("")

    unknown = (qualitaet_normalized != "") & (qualitaet_id == "")
    for idx in df_in.index[unknown]:
        log_file_func(
            f"Qualität[{idx}]: unbekannter Wert '{qualitaet_text[idx]}' "
            f"in field:mykis-qualität wird ignoriert"
        )

    sequenz_col = copy_column(df_in, "field:mykis-its-sequenz")
    dna_col = copy_column(df_in, "field:dna barcode its:")
    has_sequence = (sequenz_col.str.strip() != "") | (dna_col.str.strip() != "")
    apply_fallback = (qualitaet_id == "") & has_sequence
    qualitaet_id = qualitaet_id.where(~apply_fallback, QUALITAET_IDS["sequenziert"])

    out_df[quality_column] = qualitaet_id


# ==============================================================================
# MAIN MAPPING FUNCTION
# ==============================================================================


def map_inat_to_mykis(
    df_in: pd.DataFrame,
    log_file_func: Callable[[str], None],
    template_path: str | None = None,
    template_sheet: int = 0,
    mtb_reference_path: str | None = None,
    name_ref_path: str | None = None,
    use_login_as_erfasser: bool = False,
    log_func: Optional[Callable[[str], None]] = None,
    change_func: Optional[Callable[[dict[str, Any]], None]] = None,
) -> pd.DataFrame:
    """
    Konvertiert iNaturalist-Daten ins Mykis-Format.

    Args:
        df_in: iNaturalist-Daten
        log_file_func: Logging in die Logdatei
        template_path: Excel-Template mit Spaltendefinition
        template_sheet: Sheet-Index im Template
        mtb_reference_path: optionale Fundort-Referenzdatei (MTB-Abgleich)
        name_ref_path: optionale Namenszuordnungs-Liste (user_login → mykis-name)
        use_login_as_erfasser: user_login unverändert als Erfasser übernehmen
        log_func: Logging ins GUI-Protokoll (Fallback: print)
        change_func: optionaler Callback für die Änderungs-CSV der
            Fundort-Zuordnung (Datensatz-Schema: CHANGE_LOG_COLUMNS)

    Returns:
        DataFrame im Mykis-Format
    """
    log_file_func("=== Start Konvertierung iNaturalist → Mykis ===")
    log = make_logger(log_func)

    # 1. Bereits erfasste Zeilen herausfiltern
    df_in = filter_by_erfassung(df_in, log)
    if len(df_in) == 0:
        log("❌ FEHLER: Keine Zeilen zum Verarbeiten übrig!")
        log("   Alle Beobachtungen wurden bereits erfasst.\n")
        return pd.DataFrame()

    # 2. Template (Spaltendefinition) und Fundort-Referenz laden
    if template_path is None:
        template_path = str(AppConfig().resolve_template_path())
    columns = pd.read_excel(
        template_path, sheet_name=template_sheet, dtype=str, nrows=0
    ).columns.tolist()
    log(f"📋 Template geladen: {len(columns)} Spalten")
    # Index explizit von df_in übernehmen, damit die spaltenweisen
    # Zuweisungen sauber ausgerichtet sind (statt auf pandas' implizite
    # Index-Übernahme bei der ersten Zuweisung zu bauen).
    out_df = pd.DataFrame(columns=columns, index=df_in.index)

    mtb_ref_df = load_mtb_reference(mtb_reference_path, log, log_file_func)

    # 3. Felder Themenbereich für Themenbereich befüllen
    map_taxonomy(df_in, out_df)
    map_dates(df_in, out_df)

    names_series = resolve_erfasser(
        df_in, name_ref_path, use_login_as_erfasser, log, log_file_func
    )
    assign_if_exists(out_df, "erfasser", names_series)
    assign_if_exists(
        out_df, "nachweisquelle", pd.Series("iNaturalist", index=df_in.index)
    )

    map_locations(df_in, out_df)
    map_coordinates(df_in, out_df, log_file_func)
    map_custom_fields(df_in, out_df)
    map_collector_determiner(df_in, out_df, names_series)
    map_quality(df_in, out_df, log_file_func)

    # 4. Koordinaten → MTB-Quadrant (mit Referenzabgleich)
    convert_location_to_mtbq64(
        out_df, mtb_ref_df, log_file_func=log_file_func, change_func=change_func
    )

    # MTB intern als Float speichern (Punkt statt Komma)
    if "MTB" in out_df.columns:
        out_df["MTB"] = pd.to_numeric(
            out_df["MTB"].astype(str).str.replace(",", "."), errors="coerce"
        )

    log(f"✅ Mapping abgeschlossen: {len(out_df)} Zeilen")
    return out_df
