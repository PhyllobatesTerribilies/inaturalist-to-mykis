#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Persistente Benutzereinstellungen (zuletzt gewählte Pfade/Optionen).

Merkt sich die zuletzt verwendeten Datei-Pfade (Ziel-Datei,
Fundort-Referenzliste, Namensliste) und Optionen in einer ``settings.json``,
damit sie beim nächsten Start automatisch wieder vorausgefüllt werden.

Der iNaturalist-Export wird bewusst *nicht* gemerkt: er ist bei jedem Lauf ein
neuer Export, während Ziel-Datei und Referenzlisten dieselben bleiben.

Alle Lese-/Schreibfehler werden nur geloggt und nie geworfen – das Merken der
Einstellungen ist bewusst „best effort" und darf die Anwendung nie blockieren.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

# Nur diese Schlüssel werden gespeichert/geladen. Schützt vor fremden oder
# veralteten Einträgen in der JSON-Datei und dokumentiert zugleich, was gemerkt
# wird.
ALLOWED_KEYS = frozenset(
    {
        "output",
        "ref",
        "name_ref",
        "use_login_as_erfasser",
        "filter_obscured",
    }
)


def settings_path() -> Path:
    """
    Pfad zur Einstellungsdatei.

    Gepackte .exe → neben der ausführbaren Datei, sonst Projektwurzel –
    dieselbe Logik wie beim Logs-Verzeichnis, damit alles beisammenliegt und
    an einer vorhersehbaren, beschreibbaren Stelle landet.
    """
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent.parent
    return base / "settings.json"


def load_settings() -> dict[str, Any]:
    """Lädt die gespeicherten Einstellungen (leeres Dict bei Fehler/fehlender Datei)."""
    path = settings_path()
    if not path.is_file():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logging.warning("Einstellungen nicht lesbar (%s): %s", path, e)
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if k in ALLOWED_KEYS}


def save_settings(settings: dict[str, Any]) -> None:
    """Speichert die Einstellungen (Fehler werden nur geloggt, nicht geworfen)."""
    path = settings_path()
    filtered = {k: v for k, v in settings.items() if k in ALLOWED_KEYS}
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning("Einstellungen nicht speicherbar (%s): %s", path, e)
