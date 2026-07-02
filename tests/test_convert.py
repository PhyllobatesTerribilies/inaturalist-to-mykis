# -*- coding: utf-8 -*-
"""Unit-Tests für die reinen Funktionen der Konvertierung."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from src.convert import (
    _build_reference_map,
    _compute_mtbq,
    build_name_lookup,
    dedupe_name_changes,
    extract_basis_ort,
    extract_name,
    normalize_german_states,
    parse_coord_no_separator,
    resolve_erfasser,
)
from src.io_validate import read_any_table

# ==============================================================================
# _compute_mtbq – 8x8-Rastermathematik (bounds = (0,0,8,8) → Zellgröße 1)
# ==============================================================================

BOUNDS = (0.0, 0.0, 8.0, 8.0)


@pytest.mark.parametrize(
    "ost, nord, expected64, expected16",
    [
        (0.5, 7.5, "1234,111", "1234,11"),  # oben links
        (7.5, 0.5, "1234,444", "1234,44"),  # unten rechts
        (5.5, 4.5, "1234,234", "1234,23"),  # Mitte
    ],
)
def test_compute_mtbq_quadranten(ost, nord, expected64, expected16):
    mtbq64, mtbq16 = _compute_mtbq(BOUNDS, ost, nord, 1234)
    assert mtbq64 == expected64
    assert mtbq16 == expected16


def test_compute_mtbq_clamp_am_rand():
    # Punkt exakt auf xmax/ymax darf nicht auf grid-Index 8 laufen
    mtbq64, mtbq16 = _compute_mtbq(BOUNDS, 8.0, 8.0, 1234)
    assert mtbq64 == "1234,222"


def test_compute_mtbq_sheet_id_als_string():
    mtbq64, _ = _compute_mtbq(BOUNDS, 0.5, 7.5, "3647")
    assert mtbq64.startswith("3647,")


# ==============================================================================
# _build_reference_map – 16tel-Schlüssel, Granularitäten, Spaltenerkennung
# ==============================================================================


def _ref_df(mtb_values, mtb_col="mtb"):
    return pd.DataFrame(
        {
            mtb_col: mtb_values,
            "ostwert2": [1.0] * len(mtb_values),
            "nordwert2": [2.0] * len(mtb_values),
        }
    )


@pytest.mark.parametrize(
    "mtb, expected_key",
    [
        ("3647,243", "3647,24"),  # 64tel → auf 16tel gekürzt
        ("3647,24", "3647,24"),  # 16tel bleibt
        ("3647", "3647"),  # ohne Quadrant
        ("3647.24", "3647,24"),  # Punkt wird zu Komma normalisiert
    ],
)
def test_build_reference_map_schluessel(mtb, expected_key):
    ref_map, mtb_col = _build_reference_map(_ref_df([mtb]), lambda m: None)
    assert mtb_col == "mtb"
    assert expected_key in ref_map


def test_build_reference_map_gleicher_16tel_topf():
    # Zeuthen (64tel) und Schmöckwitz (16tel) landen im selben Topf
    ref_map, _ = _build_reference_map(_ref_df(["3647,243", "3647,24"]), lambda m: None)
    assert list(ref_map.keys()) == ["3647,24"]
    assert len(ref_map["3647,24"]) == 2


def test_build_reference_map_spalte_case_insensitive():
    _, mtb_col = _build_reference_map(
        _ref_df(["3647,24"], mtb_col="MTB"), lambda m: None
    )
    assert mtb_col == "MTB"


def test_build_reference_map_ohne_mtb_spalte():
    df = pd.DataFrame({"foo": ["x"], "ostwert2": [1.0], "nordwert2": [2.0]})
    ref_map, mtb_col = _build_reference_map(df, lambda m: None)
    assert mtb_col is None
    assert ref_map == {}


def test_build_reference_map_warnt_bei_fehlendem_quadrant():
    logs: list[str] = []
    _build_reference_map(_ref_df(["3647", "3648", "3649,12"]), logs.append)
    warnungen = [m for m in logs if "ohne Quadrant" in m]
    assert len(warnungen) == 1
    assert "2 Referenz-Einträge" in warnungen[0]


# ==============================================================================
# parse_coord_no_separator – Dezimaltrennzeichen & Robustheit
# ==============================================================================


def _parse_one(value):
    # object-dtype wie eine gemischte Roh-Spalte; in Produktion float64, aber
    # die Parse-Logik ist identisch (nur das Zurückschreiben braucht object,
    # damit der Test Strings und Floats gleich behandeln kann).
    df = pd.DataFrame(
        {
            "ostwert2": pd.Series([value], dtype=object),
            "nordwert2": pd.Series([value], dtype=object),
        }
    )
    parse_coord_no_separator(df, lambda m: None)
    return df["ostwert2"].iloc[0]


@pytest.mark.parametrize(
    "value, expected",
    [
        ("51232", 51.232),  # ohne Trennzeichen, erste Ziffer < 6
        ("7232", 7.232),  # ohne Trennzeichen, erste Ziffer >= 6
        ("51.232", 51.232),  # bereits mit Punkt
        ("13,5", 13.5),  # deutsches Komma
        (-3.0, -3.0),  # negative Ganzzahl darf nicht crashen (Bugfix)
    ],
)
def test_parse_coord(value, expected):
    assert _parse_one(value) == pytest.approx(expected)


def test_parse_coord_nan_bleibt_leer():
    result = _parse_one(float("nan"))
    assert result is None or (isinstance(result, float) and math.isnan(result))


# ==============================================================================
# extract_basis_ort – adaptive Ortslogik aus place_guess
# ==============================================================================


def _basis_ort(value):
    return extract_basis_ort(pd.DataFrame({"place_guess": [value]})).iloc[0]


@pytest.mark.parametrize(
    "place_guess, expected",
    [
        ("Kiel", "Kiel"),
        ("Bosau, Deutschland", "Bosau"),
        ("Berlin, Brandenburg, Deutschland", "Berlin"),
        ("Meilwald, Erlangen, Bayern, DE", "Erlangen"),  # 4 Teile → 2. Teil
    ],
)
def test_extract_basis_ort(place_guess, expected):
    assert _basis_ort(place_guess) == expected


def test_extract_basis_ort_nan_und_fehlende_spalte():
    assert _basis_ort(float("nan")) == ""
    leer = extract_basis_ort(pd.DataFrame({"anders": [1]}))
    assert list(leer) == [""]


# ==============================================================================
# extract_name – "Nachname, Vorname"
# ==============================================================================


@pytest.mark.parametrize(
    "row, expected",
    [
        ({"user_name": "Max Mustermann"}, "Mustermann, Max"),
        ({"user_name": "Hans Peter Müller"}, "Müller, Hans Peter"),  # Bugfix
        ({"user_name": "Cher"}, "Cher"),
        ({"user_login": "maxm"}, "maxm"),  # login unverändert
    ],
)
def test_extract_name(row, expected):
    assert extract_name(pd.Series(row)) == expected


# ==============================================================================
# normalize_german_states – nur deutsche Bundesländer, sonst ""
# ==============================================================================


def _state(value):
    return normalize_german_states(pd.Series([value])).iloc[0]


@pytest.mark.parametrize(
    "value, expected",
    [
        ("Bayern", "Bayern"),
        ("bavaria", "Bayern"),
        ("NRW", "Nordrhein-Westfalen"),
        ("  Baden-Württemberg  ", "Baden-Württemberg"),
        ("Wien", ""),  # nicht deutsch → leer
        (float("nan"), ""),
    ],
)
def test_normalize_german_states(value, expected):
    assert _state(value) == expected


# ==============================================================================
# read_any_table / build_name_lookup – Referenzlisten inkl. BOM-Toleranz
# ==============================================================================


def test_read_any_table_bom_toleranz(tmp_path):
    # Excel "CSV UTF-8" schreibt ein BOM – der erste Spaltenname darf es nicht behalten.
    p = tmp_path / "ref.csv"
    p.write_text("user_login;mykis-name\nmaxm;Mustermann, Max\n", encoding="utf-8-sig")
    df = read_any_table(p, min_columns=2)
    assert list(df.columns) == ["user_login", "mykis-name"]


def test_build_name_lookup_case_insensitiv_und_leer():
    df = pd.DataFrame(
        {"User_Login": ["maxm", "   "], "MYKIS-NAME": ["Mustermann, Max", "x"]}
    )
    assert build_name_lookup(df) == {"maxm": "Mustermann, Max"}


# ==============================================================================
# resolve_erfasser – Namenskonvertierung + Änderungs-Datensätze
# ==============================================================================


def test_resolve_erfasser_name_change(tmp_path):
    ref = tmp_path / "namen.csv"
    ref.write_text(
        "user_login;mykis-name\nmaxm;Mustermann, Max\n", encoding="utf-8-sig"
    )
    df_in = pd.DataFrame(
        {"user_name": ["Max M", "Anna Schmidt"], "user_login": ["maxm", "nobody"]}
    )
    records: list[dict] = []
    result = resolve_erfasser(
        df_in, str(ref), False, lambda m: None, lambda m: None, records.append
    )
    # nobody bleibt beim Fallback, maxm wird ersetzt
    assert list(result) == ["Mustermann, Max", "Schmidt, Anna"]
    assert records == [
        {
            "id": 0,
            "user_id": "",  # Spalte fehlt im Test-DataFrame → leer
            "user_login": "maxm",
            "user_name": "Max M",
            "erfasser_alt": "M, Max",
            "erfasser_neu": "Mustermann, Max",
        }
    ]


def test_dedupe_name_changes():
    records = [
        {
            "id": 0,
            "user_id": "1",
            "user_login": "maxm",
            "user_name": "Max M",
            "erfasser_alt": "M, Max",
            "erfasser_neu": "Mustermann, Max",
        },
        {
            "id": 5,
            "user_id": "1",
            "user_login": "maxm",
            "user_name": "Max M",
            "erfasser_alt": "M, Max",
            "erfasser_neu": "Mustermann, Max",
        },
        {
            "id": 2,
            "user_id": "9",
            "user_login": "julia",
            "user_name": "Julia G",
            "erfasser_alt": "G, Julia",
            "erfasser_neu": "Grausgruber, Julia",
        },
    ]
    assert dedupe_name_changes(records) == [
        {
            "user_id": "1",
            "user_login": "maxm",
            "user_name": "Max M",
            "erfasser_alt": "M, Max",
            "erfasser_neu": "Mustermann, Max",
            "anzahl": 2,
        },
        {
            "user_id": "9",
            "user_login": "julia",
            "user_name": "Julia G",
            "erfasser_alt": "G, Julia",
            "erfasser_neu": "Grausgruber, Julia",
            "anzahl": 1,
        },
    ]
