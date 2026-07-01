#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
I/O und Validierung für iNaturalist → Mykis Konvertierung

Funktionen:
- Datei einlesen (CSV/Excel mit Auto-Detection)
- Basis-Validierung (Pflichtspalten)
- Datei speichern (XLS/XLSX/CSV)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence, Optional, Callable

import pandas as pd


def make_logger(
    log_func: Optional[Callable[[str], None]],
) -> Callable[[str], None]:
    """Log-Funktion mit ``print`` als Fallback, wenn ``log_func`` fehlt."""

    def log(msg: str) -> None:
        if log_func:
            log_func(msg)
        else:
            print(msg)

    return log


# ==============================================================================
# FILE I/O
# ==============================================================================


def read_any_table(path: Path, min_columns: int = 2) -> pd.DataFrame:
    """
    Liest Tabelle (CSV oder Excel) mit automatischer Format-Erkennung.

    Strategie:
    1. Excel-Dateien direkt laden
    2. CSV mit automatischer Trennzeichen-Erkennung
    3. CSV mit manuellen Trennzeichen (falls Auto fehlschlägt)
    4. Fallback ohne Validierung

    Args:
        path: Dateipfad
        min_columns: Mindestanzahl Spalten, damit ein Parse-Versuch als
            erfolgreich gilt. Dient der Trennzeichen-Disambiguierung: ein
            falsches Trennzeichen liefert oft nur 1 breite Spalte. Für schmale
            Referenzlisten (z.B. 2 Spalten) klein halten, für den breiten
            iNaturalist-Export höher setzen.

    Returns:
        DataFrame mit geladenen Daten

    Raises:
        ValueError: Wenn keine Methode funktioniert
    """

    # Versuch 1: Excel (bei .xlsx/.xls Endung)
    if path.suffix.lower() in [".xlsx", ".xls", ".xlsm"]:
        try:
            return pd.read_excel(path)
        except Exception:
            pass  # Falls Excel fehlschlägt, versuche als CSV

    # Versuch 2: CSV mit automatischer Erkennung
    try:
        df = pd.read_csv(path, sep=None, engine="python", encoding="utf-8")
        if len(df.columns) >= min_columns:
            logging.debug(f"CSV automatisch geladen: {len(df.columns)} Spalten")
            return df
    except Exception:
        pass

    # Versuch 3: CSV mit verschiedenen Trennzeichen
    for sep_name, sep_char in [("Komma", ","), ("Semikolon", ";"), ("Tab", "\t")]:
        try:
            df = pd.read_csv(path, sep=sep_char, engine="python", encoding="utf-8")
            if len(df.columns) >= min_columns:
                logging.debug(f"CSV mit {sep_name} geladen: {len(df.columns)} Spalten")
                return df
        except Exception:
            continue

    # Versuch 4: Andere Encodings
    for encoding in ["latin-1", "cp1252"]:
        try:
            df = pd.read_csv(path, sep=None, engine="python", encoding=encoding)
            if len(df.columns) >= min_columns:
                logging.debug(f"CSV mit Encoding {encoding} geladen")
                return df
        except Exception:
            continue

    # Versuch 5: Fallback ohne Validierung (letzter Versuch)
    try:
        df = pd.read_csv(path, engine="python")
        logging.warning(
            f"CSV mit Fallback geladen: {len(df.columns)} Spalten (möglicherweise falsch!)"
        )
        return df
    except Exception as e:
        raise ValueError(
            f"Konnte Datei nicht laden: {path.name}\n"
            f"Versucht: Excel, CSV (auto), CSV (,;\\t), Encodings (latin-1, cp1252)\n"
            f"Fehler: {e}"
        )


def save_table(
    df: pd.DataFrame, path: Path, log_func: Optional[Callable[[str], None]] = None
) -> None:
    """Speichert DataFrame mit xlwt-Fallback für .xls."""
    log = make_logger(log_func)
    ext = path.suffix.lower()

    if ext == ".xlsx":
        df.to_excel(path, index=False, engine="openpyxl")
        log(f"✅ Gespeichert als .xlsx: {path.name}")

    elif ext == ".xls":
        # Pandas 3.0+ unterstützt xlwt nicht mehr
        # → Nutze xlwt direkt
        try:
            _save_xls_with_xlwt(df, path, log_func)
        except Exception as e:
            log(f"❌ Fehler beim Speichern als .xls: {e}")
            log("   Alternativen:")
            log("   1. Nutze .xlsx (für Access .accdb)")
            log("   2. Downgrade pandas: pip install 'pandas<2.1'")
            raise

    elif ext == ".csv":
        df.to_csv(path, sep=";", index=False, encoding="utf-8-sig")
        log(f"✅ Gespeichert als CSV: {path.name}")

    else:
        raise ValueError(f"Unbekanntes Format: {ext}")


def _save_xls_with_xlwt(
    df: pd.DataFrame, path: Path, log_func: Optional[Callable[[str], None]] = None
) -> None:
    """
    Speichert DataFrame als echtes .xls mit xlwt direkt.
    Umgeht pandas-Limitierungen in Version 3.0+.
    """
    log = make_logger(log_func)

    if len(df) > 65535:
        raise ValueError(
            f".xls unterstützt max 65.535 Zeilen, DataFrame hat {len(df)} Zeilen.\n"
            f"Nutze .xlsx stattdessen."
        )

    if len(df.columns) > 256:
        raise ValueError(
            f".xls unterstützt max 256 Spalten, DataFrame hat {len(df.columns)} Spalten.\n"
            f"Nutze .xlsx stattdessen."
        )

    try:
        import xlwt
    except ImportError:
        raise ValueError(
            "xlwt nicht installiert.\n" "Installiere mit: pip install xlwt"
        )

    workbook = xlwt.Workbook(encoding="utf-8")
    worksheet = workbook.add_sheet("Sheet1")

    # MTB als Zahl mit deutschem Dezimalformat (0,000) statt als Text schreiben
    style_mtb = xlwt.XFStyle()
    style_mtb.num_format_str = "0.000"
    mtb_col_idx = list(df.columns).index("MTB") if "MTB" in df.columns else None

    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(0, col_idx, str(col_name))

    for row_idx, row in enumerate(df.values, start=1):
        for col_idx, value in enumerate(row):
            if pd.isna(value):
                value = ""
            elif not isinstance(value, (str, int, float, bool)):
                value = str(value)

            if col_idx == mtb_col_idx and isinstance(value, float):
                worksheet.write(row_idx, col_idx, value, style_mtb)
            else:
                worksheet.write(row_idx, col_idx, value)
    workbook.save(str(path))
    log(f"✅ Gespeichert als echtes .xls (mit xlwt direkt): {path.name}")
    log("   Kompatibel mit Access .mdb")


# ==============================================================================
# VALIDATION
# ==============================================================================


def inspect_table_header(df: pd.DataFrame) -> str:
    """
    Erstellt einen lesbaren Überblick über die eingelesene Tabelle.

    Args:
        df: DataFrame zum Inspizieren

    Returns:
        Mehrzeilige String-Beschreibung (Zeilen-/Spaltenzahl + Spaltennamen)
    """
    lines = [
        f"📊 Eingelesen: {len(df)} Zeilen, {len(df.columns)} Spalten",
        "   Erkannte Spalten:",
    ]
    for col in df.columns:
        lines.append(f"     • {col}")
    return "\n".join(lines)


def validate_inat_columns(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """
    Prüft den iNaturalist-Export auf die Spalten, die der Konverter braucht.

    Pflicht (sonst Abbruch):
    - Taxon-Name: scientific_name / taxon_name / species_guess
    - Datum:      observed_on / observed_on_string

    Empfohlen (nur Warnung, jeweils mit Folge bei Fehlen):
    - Koordinaten:     latitude / longitude  → ohne sie keine MTB-Zuordnung
    - Benutzername:    user_name / user_login → Erfasser/Sammler/Bestimmer leer
    - Beobachtungs-ID: id → Rückverweis "iNNr:" (Feld Foto_Zeichnung) ohne Nummer

    Returns:
        (errors, warnings) – leere Listen bedeuten "alles in Ordnung".
    """
    errors: list[str] = []
    warnings: list[str] = []

    # --- Pflichtspalten ---
    if not _has_any(df, ["scientific_name", "taxon_name", "species_guess"]):
        errors.append(
            "Kein Taxon-Feld gefunden "
            "(erwartet: scientific_name, taxon_name oder species_guess)."
        )

    if not _has_any(df, ["observed_on", "observed_on_string"]):
        errors.append(
            "Kein Datumsfeld gefunden "
            "(erwartet: observed_on oder observed_on_string)."
        )

    # --- Empfohlene Spalten: Warnung samt Konsequenz ---
    if not _has_any(df, ["latitude", "longitude"]):
        warnings.append(
            "Koordinaten (latitude/longitude) fehlen – "
            "ohne sie ist keine MTB-Zuordnung möglich."
        )

    if not _has_any(df, ["user_name", "user_login"]):
        warnings.append(
            "Benutzername (user_name/user_login) fehlt – "
            "Erfasser, Sammler und Bestimmer bleiben ggf. leer."
        )

    if "id" not in df.columns:
        warnings.append(
            "Beobachtungs-ID (id) fehlt – "
            "der Rückverweis 'iNNr:' im Feld Foto_Zeichnung bleibt ohne Nummer."
        )

    return errors, warnings


def _has_any(df: pd.DataFrame, cols: Sequence[str]) -> bool:
    """Prüft ob mindestens eine der Spalten existiert."""
    return any(c in df.columns for c in cols)
