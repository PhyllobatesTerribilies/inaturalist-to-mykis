# config.py
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    template_xls: Path = Path("assets/2026-02-07_layout_mykdaten.xls")
    template_sheet: int = 0
    layouts_dir: Path = Path("assets")
    shapefile_mtb: Path = Path("assets/b25_utm32s/b25_utm32s.shp")
    wirt_translations: Path = Path("assets/wirt_uebersetzungen.csv")

    @staticmethod
    def _project_root() -> Path:
        """Projektwurzel – im PyInstaller-Bundle _MEIPASS, sonst eine Ebene über src/."""
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        return Path(__file__).parent.parent

    def _resolve_asset(self, relative: Path, description: str) -> Path:
        """Löst einen Asset-Pfad relativ zur Projektwurzel auf und prüft die Existenz."""
        p = (self._project_root() / relative).resolve()
        if not p.exists():
            raise FileNotFoundError(f"{description} nicht gefunden: {p}")
        return p

    def resolve_template_path(self) -> Path:
        return self._resolve_asset(self.template_xls, "Template")

    def resolve_shapefile_path(self) -> Path:
        return self._resolve_asset(self.shapefile_mtb, "Shapefile")

    def resolve_wirt_translations_path(self) -> Path:
        """
        Pfad zur Wirt-Übersetzungstabelle (ohne Existenzprüfung – Loader hat Fallback).

        Gepackt: zuerst neben der .exe (dort frei editierbar), sonst die
        gebündelte Datei. Im Quellcode-Betrieb relativ zur Projektwurzel.
        """
        if getattr(sys, "frozen", False):
            external = (Path(sys.executable).parent / self.wirt_translations).resolve()
            if external.is_file():
                return external
        return (self._project_root() / self.wirt_translations).resolve()
