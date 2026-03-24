#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tkinter GUI für iNaturalist → Mykis Konvertierung

Einfache Benutzeroberfläche mit:
- Dateiauswahl (Input/Output)
- Live-Protokoll
- Fehlerbehandlung
"""

from __future__ import annotations

import logging
import sys
import threading
import tkinter as tk
import traceback
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import os
from datetime import datetime

import pandas as pd

from src.config import AppConfig
from src.convert import map_inat_to_mykis
from src.io_validate import (
    inspect_table_header,
    read_any_table,
    save_table,
    validate_inat_columns,
)
from src.version import __app_name__, __date__, __version__


# ==============================================================================
# LOGGING SETUP
# ==============================================================================


def setup_logging() -> None:
    """Konfiguriert Logging in Datei und Console."""
    log_path = Path.cwd() / "inat_to_mykis.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.info("=== App gestartet ===")
    logging.info("Logfile: %s", log_path)


def install_excepthook() -> None:
    """Fängt unbehandelte Exceptions und loggt sie."""

    def _hook(exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        msg = "".join(traceback.format_exception(exc_type, exc, tb))
        logging.error("Uncaught exception:\n%s", msg)
        print(msg, file=sys.stderr)

    sys.excepthook = _hook


# ==============================================================================
# MAIN GUI
# ==============================================================================


class App(tk.Tk):
    """Hauptfenster der Anwendung."""

    def __init__(self) -> None:
        super().__init__()
        self.cfg = AppConfig()
        # setup_logging()
        install_excepthook()

        # Fenster-Konfiguration
        self.title(f"{__app_name__} v{__version__}")
        self.geometry("800x600")
        self.minsize(760, 520)

        # Variablen
        self.var_input = tk.StringVar()
        self.var_output = tk.StringVar()
        self.var_enable_append = tk.BooleanVar(value=False)
        self.var_ref = tk.StringVar()

        # GUI aufbauen
        self._build_ui()

        # Willkommensnachricht
        self.log(f"✅ {__app_name__} v{__version__} ({__date__}) bereit.")
        self.log(f"📁 Template: {self.cfg.template_xls}")

    def _build_ui(self) -> None:
        """Erstellt die Benutzeroberfläche."""
        pad = {"padx": 10, "pady": 8}
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True)

        # -----------------------------------------------------------------
        # Eingabedatei
        # -----------------------------------------------------------------
        ttk.Label(frm, text="Eingabedatei (iNaturalist CSV/XLSX/XLS):").grid(
            row=0, column=0, sticky="w", **pad
        )

        row_in = ttk.Frame(frm)
        row_in.grid(row=1, column=0, sticky="ew", **pad)
        ttk.Entry(row_in, textvariable=self.var_input).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(row_in, text="Durchsuchen…", command=self.pick_input).pack(
            side="left", padx=6
        )

        # -----------------------------------------------------------------
        # Ausgabedatei
        # -----------------------------------------------------------------
        ttk.Label(frm, text="Ausgabedatei (.xls/.xlsx/.csv):").grid(
            row=2, column=0, sticky="w", **pad
        )

        row_out = ttk.Frame(frm)
        row_out.grid(row=3, column=0, sticky="ew", **pad)

        self.output_entry = ttk.Entry(row_out, textvariable=self.var_output)
        self.output_entry.pack(side="left", fill="x", expand=True)

        self.output_btn = ttk.Button(
            row_out, text="Ziel wählen…", command=self.pick_output
        )
        self.output_btn.pack(side="left", padx=6)

        # -----------------------------------------------------------------
        # Referenzdatei
        # -----------------------------------------------------------------
        ttk.Label(frm, text="Referenz - Liste von bereits vorhandener Fundorte").grid(
            row=4, column=0, sticky="w", **pad
        )

        row_ref = ttk.Frame(frm)
        row_ref.grid(row=5, column=0, sticky="ew", **pad)

        ttk.Entry(row_ref, textvariable=self.var_ref).pack(
            side="left", fill="x", expand=True
        )

        ttk.Button(row_ref, text="Durchsuchen…", command=self.pick_ref).pack(
            side="left", padx=6
        )

        # -----------------------------------------------------------------
        # Optionen: An bestehende Datei anhängen
        # -----------------------------------------------------------------
        box = ttk.LabelFrame(frm, text="Optionen")
        box.grid(row=6, column=0, sticky="ew", **pad)

        ttk.Checkbutton(
            box,
            text="An bestehende Mykis-Datei anhängen (Ausgabedatei = Anhänge-Datei)",
            variable=self.var_enable_append,
            command=self._toggle_append_mode,
        ).pack(anchor="w", padx=8, pady=6)

        # -----------------------------------------------------------------
        # Buttons
        # -----------------------------------------------------------------
        row_btn = ttk.Frame(frm)
        row_btn.grid(row=7, column=0, sticky="e", **pad)
        ttk.Button(
            row_btn,
            text="Konvertieren",
            command=self.run_convert,
        ).pack(side="right", padx=6)
        ttk.Button(row_btn, text="Beenden", command=self.destroy).pack(side="right")

        # -----------------------------------------------------------------
        # Protokoll (Log-Fenster)
        # -----------------------------------------------------------------
        ttk.Label(frm, text="Protokoll:").grid(row=8, column=0, sticky="w", **pad)

        self.txt = tk.Text(frm, height=15, wrap="word", font=("Consolas", 9))
        self.txt.grid(row=9, column=0, sticky="nsew", padx=10, pady=(0, 10))

        yscroll = ttk.Scrollbar(frm, orient="vertical", command=self.txt.yview)
        self.txt.configure(yscrollcommand=yscroll.set)
        yscroll.grid(row=9, column=1, sticky="ns", pady=(0, 10))

        # Grid-Gewichte
        frm.columnconfigure(0, weight=1)
        frm.rowconfigure(9, weight=1)

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------

    def log(self, msg: str) -> None:
        """Schreibt Nachricht ins Protokoll-Fenster."""
        self.txt.insert("end", msg + "\n")
        self.txt.see("end")
        self.update_idletasks()

    # -------------------------------------------------------------------------
    # Dateiauswahl
    # -------------------------------------------------------------------------

    def pick_input(self) -> None:
        """Dialog für Eingabedatei."""
        p = filedialog.askopenfilename(
            title="Eingabedatei wählen",
            filetypes=[
                ("Tabellen", "*.csv *.xlsx *.xls"),
                ("CSV", "*.csv"),
                ("Excel", "*.xlsx *.xls"),
                ("Alle Dateien", "*.*"),
            ],
        )
        if p:
            self.var_input.set(p)
            self.suggest_output()

    def pick_output(self) -> None:
        """Dialog für Ausgabedatei (oder Anhänge-Datei im Anhänge-Modus)."""
        is_append_mode = self.var_enable_append.get()

        if is_append_mode:
            # Anhänge-Modus: Bestehende Datei öffnen
            p = filedialog.askopenfilename(
                title="Bestehende Mykis-Datei zum Anhängen wählen",
                filetypes=[
                    ("Excel 97-2003 (.xls)", "*.xls"),
                    ("Excel (.xlsx)", "*.xlsx"),
                    ("CSV (.csv)", "*.csv"),
                    ("Alle Dateien", "*.*"),
                ],
            )
        else:
            # Normal-Modus: Neue Datei speichern
            p = filedialog.asksaveasfilename(
                title="Ausgabedatei wählen",
                defaultextension=".xls",
                filetypes=[
                    ("Excel 97-2003 (.xls)", "*.xls"),
                    ("Excel (.xlsx)", "*.xlsx"),
                    ("CSV (.csv)", "*.csv"),
                ],
            )

        if p:
            self.var_output.set(p)

    def pick_ref(self) -> None:
        """Dialog für optionale Referenzdatei."""
        p = filedialog.askopenfilename(
            title="Referenzdatei wählen",
            filetypes=[
                ("Tabellen", "*.csv *.xlsx *.xls"),
                ("CSV", "*.csv"),
                ("Excel", "*.xlsx *.xls"),
                ("Alle Dateien", "*.*"),
            ],
        )
        if p:
            self.var_ref.set(p)

    def suggest_output(self) -> None:
        """Schlägt Ausgabedatei basierend auf Eingabe vor."""
        inp = self.var_input.get().strip()
        if not inp:
            return
        stem = Path(inp).stem
        self.var_output.set(str(Path(inp).with_name(f"{stem}_mykis.xls")))

    def _toggle_append_mode(self) -> None:
        """
        Schaltet zwischen Anhänge-Modus und Normal-Modus um.

        Normal-Modus (Checkbox aus):
        - "Ziel wählen" speichert neue Datei

        Anhänge-Modus (Checkbox an):
        - "Ziel wählen" öffnet bestehende Datei zum Anhängen
        """
        enabled = self.var_enable_append.get()

        if enabled:
            # Anhänge-Modus: Button-Text ändern
            self.output_btn.config(text="Datei zum Anhängen wählen…")
            # Bisherigen Vorschlag löschen
            self.var_output.set("")
        else:
            # Normal-Modus: Button-Text zurücksetzen
            self.output_btn.config(text="Ziel wählen…")
            # Vorschlag neu generieren
            self.suggest_output()

    # -------------------------------------------------------------------------
    # Konvertierung
    # -------------------------------------------------------------------------

    def run_convert(self) -> None:
        """Startet Konvertierung in separatem Thread."""
        inp = self.var_input.get().strip()
        out = self.var_output.get().strip()
        ref = self.var_ref.get().strip() or None
        enable_append = bool(self.var_enable_append.get())

        # Validierung
        if not inp:
            messagebox.showwarning("Hinweis", "Bitte eine Eingabedatei auswählen.")
            return

        if not out:
            if not enable_append:
                # Normal-Modus: Vorschlag generieren
                self.suggest_output()
                out = self.var_output.get().strip()

            if not out:
                messagebox.showwarning("Hinweis", "Bitte eine Ausgabedatei wählen.")
                return

        # Thread starten (damit GUI nicht einfriert)
        threading.Thread(
            target=self._convert_worker,
            args=(Path(inp), Path(out), enable_append, Path(ref) if ref else None),
            daemon=True,
        ).start()

    def _convert_worker(
        self,
        inp: Path,
        out: Path,
        enable_append: bool,
        ref: Path | None = None,
    ) -> None:
        """
        Führt Konvertierung durch (läuft in separatem Thread).

        Args:
            inp: Eingabedatei (iNaturalist)
            out: Ausgabedatei (im Anhänge-Modus auch die Datei zum Anhängen)
            enable_append: Wenn True, wird out zuerst geladen und neue Daten angehängt
            ref: Optionale Referenzdatei (z. B. für Abgleich oder Anreicherung)
        """
        try:
            # -----------------------------------------------------------------
            # 1. Datei einlesen
            # -----------------------------------------------------------------
            self.log(f"\n📂 Lese {inp.name}...")

            if not inp.exists():
                raise FileNotFoundError(f"Datei nicht gefunden: {inp}")

            df = read_any_table(inp)
            self.log(inspect_table_header(df))

            # -----------------------------------------------------------------
            # 1b. Referenzdatei einlesen (optional)
            # -----------------------------------------------------------------
            # df_ref = None
            # if ref is not None:
            #     self.log(f"\n📂 Lese Referenzdatei {ref.name}...")
            #     if not ref.exists():
            #         raise FileNotFoundError(f"Referenzdatei nicht gefunden: {ref}")
            #     df_ref = read_any_table(ref)
            #     self.log(inspect_table_header(df_ref))

            # -----------------------------------------------------------------
            # 2. Validierung
            # -----------------------------------------------------------------
            errors, warnings = validate_inat_columns(df)

            if warnings:
                self.log("\n⚠️  Warnungen:")
                for w in warnings:
                    self.log(f"  • {w}")

            if errors:
                self.log("\n❌ Fehler:")
                for e in errors:
                    self.log(f"  • {e}")
                messagebox.showerror(
                    "Fehler",
                    "Pflichtspalten fehlen!\n\nDetails siehe Protokoll.",
                )
                return

            # -----------------------------------------------------------------
            # 3. Konvertierung
            # -----------------------------------------------------------------
            self.log(f"\n🔄 Konvertiere nach Mykis-Format...")

            os.makedirs("logs", exist_ok=True)
            log_path = (
                f"logs/inat_to_mykis_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
            )

            # Funktion nutzt log_path direkt aus dem äußeren Scope
            def log_to_file(message: str) -> None:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(message + "\n")

            template = self.cfg.resolve_template_path()
            out_df = map_inat_to_mykis(
                df,
                template_path=str(template),
                template_sheet=self.cfg.template_sheet,
                mtb_reference_path=str(ref),
                log_func=self.log,
                log_file_func=log_to_file,
            )

            # -----------------------------------------------------------------
            # 3a. Optional: An bestehende Datei anhängen
            # -----------------------------------------------------------------
            if enable_append:
                self.log(f"\n📎 Anhänge-Modus: Lade bestehende Datei {out.name}")

                if not out.exists():
                    self.log(f"   ⚠️  Datei existiert noch nicht, wird neu erstellt")
                else:
                    # Bestehende Datei laden
                    existing_df = read_any_table(out)
                    self.log(
                        f"   📊 Bestehende Datei: {len(existing_df)} Zeilen, {len(existing_df.columns)} Spalten"
                    )

                    # Spalten vergleichen
                    new_cols = set(out_df.columns)
                    existing_cols = set(existing_df.columns)

                    missing_in_new = existing_cols - new_cols
                    missing_in_existing = new_cols - existing_cols

                    if missing_in_new or missing_in_existing:
                        self.log("\n⚠️  WARNUNG: Spalten stimmen nicht überein!")
                        if missing_in_existing:
                            self.log(
                                f"   Fehlen in bestehender Datei ({len(missing_in_existing)}):"
                            )
                            for col in sorted(missing_in_existing)[:10]:
                                self.log(f"      - {col}")
                            if len(missing_in_existing) > 10:
                                self.log(
                                    f"      ... und {len(missing_in_existing) - 10} weitere"
                                )

                        if missing_in_new:
                            self.log(
                                f"   Fehlen in neuen Daten ({len(missing_in_new)}):"
                            )
                            for col in sorted(missing_in_new)[:10]:
                                self.log(f"      - {col}")
                            if len(missing_in_new) > 10:
                                self.log(
                                    f"      ... und {len(missing_in_new) - 10} weitere"
                                )

                        response = messagebox.askyesno(
                            "Spalten unterschiedlich",
                            f"Die Spalten stimmen nicht überein!\n\n"
                            f"Bestehende Datei: {len(existing_cols)} Spalten\n"
                            f"Neue Daten: {len(new_cols)} Spalten\n\n"
                            f"Fehlende Spalten in neuen Daten: {len(missing_in_new)}\n"
                            f"Zusätzliche Spalten in neuen Daten: {len(missing_in_existing)}\n\n"
                            f"Trotzdem fortfahren?\n\n"
                            f"Info: Fehlende Spalten bleiben leer.\n"
                            f"Zusätzliche Spalten werden hinzugefügt.\n"
                            f"(Details im Protokoll-Fenster)",
                            icon="warning",
                        )
                        if not response:
                            self.log("\n❌ Abgebrochen durch Benutzer")
                            return

                    # Anhängen (vertikales concat)
                    old_count = len(existing_df)
                    new_count = len(out_df)
                    out_df = pd.concat([existing_df, out_df], ignore_index=True)
                    self.log(f"   ✅ Erfolgreich angehängt")
                    self.log(f"   📊 Vorher: {old_count} Zeilen")
                    self.log(f"   📊 Hinzugefügt: {new_count} Zeilen")
                    self.log(f"   📊 Gesamt: {len(out_df)} Zeilen")

            # -----------------------------------------------------------------
            # 4. Speichern
            # -----------------------------------------------------------------
            self.log(f"\n💾 Speichere {out.name}...")
            save_table(out_df, out)

            # -----------------------------------------------------------------
            # 5. Erfolgsmeldung
            # -----------------------------------------------------------------
            summary = [
                "\n" + "=" * 50,
                "✅ Konvertierung erfolgreich!",
                "=" * 50,
                f"Zeilen: {len(out_df)}",
                f"Datei: {out}",
                "=" * 50,
            ]

            msg = "\n".join(summary)
            self.log(msg)

            messagebox.showinfo(
                "Fertig",
                f"Konvertierung erfolgreich!\n\n"
                f"Zeilen: {len(out_df)}\n"
                f"Datei: {out.name}",
            )

        except Exception as e:
            # -----------------------------------------------------------------
            # Fehlerbehandlung
            # -----------------------------------------------------------------
            tb = traceback.format_exc()
            self.log(f"\n❌ FEHLER:\n{tb}")

            messagebox.showerror(
                "Fehler",
                f"Fehler beim Konvertieren:\n\n{e}\n\n"
                f"Details siehe Protokoll-Fenster.",
            )
