# config.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import sys


@dataclass(frozen=True)
class AppConfig:
    template_xls: Path = Path("assets/2026-02-07_layout_mykdaten.xls")
    template_sheet: int = 0
    layouts_dir: Path = Path("assets")
    shapefile_mtb: Path = Path("assets/b25_utm32s/b25_utm32s.shp")

    def resolve_template_path(self, base_dir: Path | None = None) -> Path:
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            project_root = Path(sys._MEIPASS)
        else:
            # Von src/config.py eine Ebene hoch zum Projektroot
            project_root = Path(__file__).parent.parent

        p = (project_root / self.template_xls).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Template nicht gefunden: {p}")
        return p

    def resolve_shapefile_path(self) -> Path:  # ← neu
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            project_root = Path(sys._MEIPASS)
        else:
            project_root = Path(__file__).parent.parent

        p = (project_root / self.shapefile_mtb).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Shapefile nicht gefunden: {p}")
        return p
