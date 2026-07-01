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

import csv
import logging
import sys
import threading
import tkinter as tk
import traceback
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable, TextIO

import pandas as pd

from src.config import AppConfig
from src.convert import CHANGE_LOG_COLUMNS, map_inat_to_mykis
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

# Dateifilter für Tabellen-Auswahldialoge (Eingabe, Referenzen)
TABELLEN_FILETYPES = [
    ("Tabellen", "*.csv *.xlsx *.xls"),
    ("CSV", "*.csv"),
    ("Excel", "*.xlsx *.xls"),
    ("Alle Dateien", "*.*"),
]

# Dateifilter für Ausgabe-/Anhänge-Dialoge
MYKIS_FILETYPES = [
    ("Excel 97-2003 (.xls)", "*.xls"),
    ("Excel (.xlsx)", "*.xlsx"),
    ("CSV (.csv)", "*.csv"),
]

# Standard-Abstand für Grid-Widgets
PAD: dict[str, Any] = {"padx": 10, "pady": 8}


class App(tk.Tk):
    """Hauptfenster der Anwendung."""

    def __init__(self) -> None:
        super().__init__()
        self.cfg = AppConfig()
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
        self.var_name_ref = tk.StringVar()
        self.var_use_login_as_erfasser = tk.BooleanVar(value=False)

        # GUI aufbauen
        self._build_ui()

        # Willkommensnachricht
        self.log(f"✅ {__app_name__} v{__version__} ({__date__}) bereit.")
        self.log(f"📁 Template: {self.cfg.template_xls}")

    def _add_file_row(
        self,
        parent: ttk.Frame,
        label_row: int,
        label: str,
        var: tk.StringVar,
        command: Callable[[], None],
        button_text: str = "Durchsuchen…",
        with_clear: bool = False,
    ) -> tuple[ttk.Entry, ttk.Button]:
        """
        Baut eine Datei-Auswahlzeile (Label + Eingabefeld + Button) ins Grid.

        Returns:
            (Eingabefeld, Auswahl-Button) – für Aufrufer, die sie später ändern.
        """
        ttk.Label(parent, text=label).grid(row=label_row, column=0, sticky="w", **PAD)

        row = ttk.Frame(parent)
        row.grid(row=label_row + 1, column=0, sticky="ew", **PAD)

        entry = ttk.Entry(row, textvariable=var)
        entry.pack(side="left", fill="x", expand=True)

        button = ttk.Button(row, text=button_text, command=command)
        button.pack(side="left", padx=6)

        if with_clear:
            ttk.Button(row, text="✕", width=3, command=lambda: var.set("")).pack(
                side="left"
            )
        return entry, button

    def _build_ui(self) -> None:
        """Erstellt die Benutzeroberfläche."""
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True)

        # Datei-Auswahlzeilen
        self._add_file_row(
            frm,
            0,
            "Eingabedatei (iNaturalist CSV/XLSX/XLS):",
            self.var_input,
            self.pick_input,
        )
        self.output_entry, self.output_btn = self._add_file_row(
            frm,
            2,
            "Ausgabedatei (.xls/.xlsx/.csv):",
            self.var_output,
            self.pick_output,
            button_text="Ziel wählen…",
        )
        self._add_file_row(
            frm,
            4,
            "Fundortreferenz - Liste",
            self.var_ref,
            self.pick_ref,
        )
        self._add_file_row(
            frm,
            6,
            "Namenszuordnungs - Liste (user_login → mykis-name):",
            self.var_name_ref,
            self.pick_name_ref,
            with_clear=True,
        )

        # -----------------------------------------------------------------
        # Optionen
        # -----------------------------------------------------------------
        box = ttk.LabelFrame(frm, text="Optionen")
        box.grid(row=8, column=0, sticky="ew", **PAD)
        ttk.Checkbutton(
            box,
            text="An bestehende Mykis-Datei anhängen (Ausgabedatei = Anhänge-Datei)",
            variable=self.var_enable_append,
            command=self._toggle_append_mode,
        ).pack(anchor="w", padx=8, pady=6)

        ttk.Checkbutton(
            box,
            text="Erfasser = user_login (Ausnahme: Einträge aus Namenszuordnungs - Liste)",
            variable=self.var_use_login_as_erfasser,
        ).pack(anchor="w", padx=8, pady=(0, 6))

        # -----------------------------------------------------------------
        # Buttons
        # -----------------------------------------------------------------
        row_btn = ttk.Frame(frm)
        row_btn.grid(row=9, column=0, sticky="e", **PAD)
        ttk.Button(row_btn, text="Konvertieren", command=self.run_convert).pack(
            side="right", padx=6
        )
        ttk.Button(row_btn, text="Beenden", command=self.destroy).pack(side="right")

        # -----------------------------------------------------------------
        # Protokoll (Log-Fenster)
        # -----------------------------------------------------------------
        ttk.Label(frm, text="Protokoll:").grid(row=10, column=0, sticky="w", **PAD)

        self.txt = tk.Text(frm, height=15, wrap="word", font=("Consolas", 9))
        self.txt.grid(row=11, column=0, sticky="nsew", padx=10, pady=(0, 10))

        yscroll = ttk.Scrollbar(frm, orient="vertical", command=self.txt.yview)
        self.txt.configure(yscrollcommand=yscroll.set)
        yscroll.grid(row=11, column=1, sticky="ns", pady=(0, 10))

        # Grid-Gewichte
        frm.columnconfigure(0, weight=1)
        frm.rowconfigure(11, weight=1)

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------

    def log(self, msg: str) -> None:
        """Schreibt Nachricht ins Protokoll-Fenster (thread-sicher)."""
        # Wird auch aus dem Worker-Thread aufgerufen → Tk-Update in den
        # Main-Thread marshallen (Tkinter ist nicht thread-safe).
        self.after(0, self._append_log, msg)

    def _append_log(self, msg: str) -> None:
        """Hängt Text ans Protokoll an (läuft im Tk-Main-Thread)."""
        self.txt.insert("end", msg + "\n")
        self.txt.see("end")

    def _run_on_main(self, func: Callable[[], Any]) -> Any:
        """
        Führt ``func`` im Tk-Main-Thread aus und liefert dessen Ergebnis.

        Blockiert den aufrufenden (Worker-)Thread bis zur Ausführung – nötig
        für modale Dialoge (``messagebox``), die nicht thread-sicher sind.
        """
        # Bereits im Main-Thread? Direkt ausführen – sonst würde done.wait()
        # den Event-Loop blockieren, der den after()-Callback abarbeiten müsste.
        if threading.current_thread() is threading.main_thread():
            return func()

        result: dict[str, Any] = {}
        done = threading.Event()

        def wrapper() -> None:
            try:
                result["value"] = func()
            finally:
                done.set()

        self.after(0, wrapper)
        done.wait()
        return result.get("value")

    @staticmethod
    def _logs_dir() -> Path:
        """
        Verzeichnis für Logdateien (wird bei Bedarf angelegt).

        Gepackte .exe → neben der ausführbaren Datei, sonst Projektwurzel.
        So landen die Logs unabhängig vom Arbeitsverzeichnis an einer
        vorhersehbaren, beschreibbaren Stelle.
        """
        if getattr(sys, "frozen", False):
            base = Path(sys.executable).parent
        else:
            base = Path(__file__).resolve().parent.parent
        d = base / "logs"
        d.mkdir(parents=True, exist_ok=True)
        return d

    # -------------------------------------------------------------------------
    # Dateiauswahl
    # -------------------------------------------------------------------------

    def _pick_table_into(self, var: tk.StringVar, title: str) -> str:
        """Öffnet einen Tabellen-Auswahldialog und speichert das Ergebnis in var."""
        p = filedialog.askopenfilename(title=title, filetypes=TABELLEN_FILETYPES)
        if p:
            var.set(p)
        return p

    def pick_input(self) -> None:
        """Dialog für Eingabedatei."""
        if self._pick_table_into(self.var_input, "Eingabedatei wählen"):
            self.suggest_output()

    def pick_ref(self) -> None:
        """Dialog für optionale Fundort-Referenzdatei."""
        self._pick_table_into(self.var_ref, "Referenzdatei wählen")

    def pick_name_ref(self) -> None:
        """Dialog für optionale Namenskonvertierungs-Datei."""
        self._pick_table_into(self.var_name_ref, "Namenskonvertierungs-Datei wählen")

    def pick_output(self) -> None:
        """Dialog für Ausgabedatei (oder Anhänge-Datei im Anhänge-Modus)."""
        if self.var_enable_append.get():
            # Anhänge-Modus: bestehende Mykis-Datei öffnen
            p = filedialog.askopenfilename(
                title="Bestehende Mykis-Datei zum Anhängen wählen",
                filetypes=MYKIS_FILETYPES + [("Alle Dateien", "*.*")],
            )
        else:
            # Normal-Modus: neue Datei speichern
            p = filedialog.asksaveasfilename(
                title="Ausgabedatei wählen",
                defaultextension=".xls",
                filetypes=MYKIS_FILETYPES,
            )
        if p:
            self.var_output.set(p)

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
        name_ref = self.var_name_ref.get().strip() or None
        use_login_as_erfasser = bool(self.var_use_login_as_erfasser.get())
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
            args=(
                Path(inp),
                Path(out),
                enable_append,
                Path(ref) if ref else None,
                Path(name_ref) if name_ref else None,
                use_login_as_erfasser,
            ),
            daemon=True,
        ).start()

    def _convert_worker(
        self,
        inp: Path,
        out: Path,
        enable_append: bool,
        ref: Path | None = None,
        name_ref: Path | None = None,
        use_login_as_erfasser: bool = False,
    ) -> None:
        """
        Führt Konvertierung durch (läuft in separatem Thread).

        Args:
            inp: Eingabedatei (iNaturalist)
            out: Ausgabedatei (im Anhänge-Modus auch die Datei zum Anhängen)
            enable_append: Wenn True, wird out zuerst geladen und neue Daten angehängt
            ref: Optionale Fundort-Referenzdatei (MTB-Abgleich)
            name_ref: Optionale Namenszuordnungs-Datei (user_login → mykis-name)
            use_login_as_erfasser: Wenn True, wird user_login als Erfasser übernommen
        """
        log_file: TextIO | None = None
        changes_file: TextIO | None = None
        try:
            # -----------------------------------------------------------------
            # 1. Datei einlesen
            # -----------------------------------------------------------------
            self.log(f"\n📂 Lese {inp.name}...")

            if not inp.exists():
                raise FileNotFoundError(f"Datei nicht gefunden: {inp}")

            # Breiter iNaturalist-Export → hoher Schwellwert für die
            # Trennzeichen-Erkennung.
            df = read_any_table(inp, min_columns=10)
            self.log(inspect_table_header(df))

            # -----------------------------------------------------------------
            # 2. Eingabedatei prüfen
            # -----------------------------------------------------------------
            self.log("\n🔍 Prüfe Eingabedatei auf benötigte Spalten...")
            errors, warnings = validate_inat_columns(df)

            for w in warnings:
                self.log(f"  ⚠️  {w}")

            if errors:
                for e in errors:
                    self.log(f"  ❌ {e}")
                self.log("\n❌ Abbruch: Pflichtspalten fehlen.")
                self._run_on_main(
                    lambda: messagebox.showerror(
                        "Eingabedatei unvollständig",
                        "Pflichtspalten fehlen!\n\nDetails siehe Protokoll-Fenster.",
                    )
                )
                return

            if warnings:
                self.log(
                    "  → Pflichtspalten vorhanden, Konvertierung wird fortgesetzt."
                )
            else:
                self.log("  ✅ Alle benötigten Spalten vorhanden.")

            # -----------------------------------------------------------------
            # 3. Konvertierung
            # -----------------------------------------------------------------
            self.log("\n🔄 Konvertiere nach Mykis-Format...")

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_path = self._logs_dir() / f"inat_to_mykis_{timestamp}.log"
            log_handle = open(log_path, "a", encoding="utf-8")
            log_file = log_handle  # für das Schließen im finally

            # Datei bleibt für die gesamte Konvertierung offen (Schließen im finally).
            def log_to_file(message: str) -> None:
                log_handle.write(message + "\n")
                log_handle.flush()

            # Zweites Log: Änderungen der Fundort-Zuordnung als CSV (nur mit
            # Referenzdatei, da nur dann Zuordnungen entstehen).
            change_func: Callable[[dict[str, Any]], None] | None = None
            if ref is not None:
                changes_path = (
                    self._logs_dir() / f"inat_to_mykis_{timestamp}_changes.csv"
                )
                changes_file = open(changes_path, "w", newline="", encoding="utf-8-sig")
                changes_writer = csv.DictWriter(
                    changes_file, fieldnames=CHANGE_LOG_COLUMNS, delimiter=";"
                )
                changes_writer.writeheader()
                change_func = changes_writer.writerow
                self.log(f"📝 Änderungs-CSV: {changes_path.name}")

            template = self.cfg.resolve_template_path()
            out_df = map_inat_to_mykis(
                df,
                template_path=str(template),
                template_sheet=self.cfg.template_sheet,
                mtb_reference_path=str(ref) if ref else None,
                name_ref_path=str(name_ref) if name_ref else None,
                use_login_as_erfasser=use_login_as_erfasser,
                log_func=self.log,
                log_file_func=log_to_file,
                change_func=change_func,
            )

            # -----------------------------------------------------------------
            # 3a. Optional: An bestehende Datei anhängen
            # -----------------------------------------------------------------
            if enable_append:
                self.log(f"\n📎 Anhänge-Modus: Lade bestehende Datei {out.name}")

                if not out.exists():
                    self.log("   ⚠️  Datei existiert noch nicht, wird neu erstellt")
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

                        response = self._run_on_main(
                            lambda: messagebox.askyesno(
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
                        )
                        if not response:
                            self.log("\n❌ Abgebrochen durch Benutzer")
                            return

                    # Anhängen (vertikales concat)
                    old_count = len(existing_df)
                    new_count = len(out_df)
                    out_df = pd.concat([existing_df, out_df], ignore_index=True)
                    self.log("   ✅ Erfolgreich angehängt")
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

            self._run_on_main(
                lambda: messagebox.showinfo(
                    "Fertig",
                    f"Konvertierung erfolgreich!\n\n"
                    f"Zeilen: {len(out_df)}\n"
                    f"Datei: {out.name}",
                )
            )

        except Exception as e:
            # -----------------------------------------------------------------
            # Fehlerbehandlung
            # -----------------------------------------------------------------
            tb = traceback.format_exc()
            self.log(f"\n❌ FEHLER:\n{tb}")

            self._run_on_main(
                lambda: messagebox.showerror(
                    "Fehler",
                    f"Fehler beim Konvertieren:\n\n{e}\n\n"
                    f"Details siehe Protokoll-Fenster.",
                )
            )

        finally:
            if log_file is not None:
                log_file.close()
            if changes_file is not None:
                changes_file.close()
