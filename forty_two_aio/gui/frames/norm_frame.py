"""Norminette frame — check and fix norm errors."""

from __future__ import annotations

import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from ...modules.norm import NorminetteFormatter


class NormFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.formatter = NorminetteFormatter()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header, text="Norminette", font=ctk.CTkFont(size=22, weight="bold")
        ).pack(side="left")

        self.fix_btn = ctk.CTkButton(
            header, text="Auto-Fix All", width=120, command=self._fix_all
        )
        self.fix_btn.pack(side="right", padx=5)

        self.check_btn = ctk.CTkButton(
            header, text="Check", width=100, command=self._check
        )
        self.check_btn.pack(side="right", padx=5)

        self.select_btn = ctk.CTkButton(
            header, text="Select Files", width=100,
            fg_color="gray30", command=self._select_files
        )
        self.select_btn.pack(side="right", padx=5)

        self.file_label = ctk.CTkLabel(self, text="No files selected", text_color="gray")
        self.file_label.grid(row=1, column=0, sticky="w", padx=20)

        self.output = ctk.CTkTextbox(self, font=ctk.CTkFont(family="monospace", size=13))
        self.output.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 20))

        self.status_bar = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_bar.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 10))

        self.files: list[str] = []

    def _select_files(self):
        paths = filedialog.askopenfilenames(
            title="Select C/H files",
            filetypes=[("C files", "*.c *.h"), ("All", "*.*")],
        )
        if paths:
            self.files = list(paths)
            names = ", ".join(Path(f).name for f in self.files[:5])
            if len(self.files) > 5:
                names += f" (+{len(self.files) - 5} more)"
            self.file_label.configure(text=names)

    def _check(self):
        if not self.files:
            self._log("Select files first.\n")
            return
        self.output.delete("1.0", "end")
        self._set_status("Checking...")
        threading.Thread(target=self._run_check, daemon=True).start()

    def _run_check(self):
        total_errors = 0
        for f in self.files:
            try:
                diags = self.formatter.diagnose_file(f)
                name = Path(f).name
                if not diags:
                    self._log(f"OK  {name}\n")
                else:
                    self._log(f"ERR {name}: {len(diags)} error(s)\n")
                    for d in diags:
                        self._log(f"    L{d.line}:{d.col} [{d.code}] {d.message}\n")
                    total_errors += len(diags)
            except RuntimeError as e:
                self._log(f"ERR {Path(f).name}: {e}\n")

        self._set_status(f"Done: {total_errors} total error(s) in {len(self.files)} file(s)")

    def _fix_all(self):
        if not self.files:
            self._log("Select files first.\n")
            return
        self.output.delete("1.0", "end")
        self._set_status("Fixing...")
        threading.Thread(target=self._run_fix, daemon=True).start()

    def _run_fix(self):
        total_fixed = 0
        for f in self.files:
            try:
                result = self.formatter.format_file(f)
                name = Path(f).name
                applied = len(result.applied)
                skipped = len(result.skipped)
                total_fixed += applied
                self._log(f"{name}: {applied} fixed, {skipped} skipped\n")
                for fix in result.applied:
                    self._log(f"    L{fix.line}: {fix.description}\n")
            except RuntimeError as e:
                self._log(f"ERR {Path(f).name}: {e}\n")

        self._set_status(f"Done: {total_fixed} fix(es) applied")

    def _log(self, text: str):
        self.output.after(0, lambda: self.output.insert("end", text))

    def _set_status(self, text: str):
        self.status_bar.after(0, lambda: self.status_bar.configure(text=text))
