"""Compiler frame — check compilation with strict flags."""

from __future__ import annotations

import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from ...modules.compiler.checker import check_compilation, check_main_commented_or_missing


class CompilerFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header, text="Compilation Check", font=ctk.CTkFont(size=22, weight="bold")
        ).pack(side="left")

        self.run_btn = ctk.CTkButton(
            header, text="Compile", width=100, command=self._compile
        )
        self.run_btn.pack(side="right", padx=5)

        self.select_btn = ctk.CTkButton(
            header, text="Select Files", width=100,
            fg_color="gray30", command=self._select_files
        )
        self.select_btn.pack(side="right", padx=5)

        flags_frame = ctk.CTkFrame(self, fg_color="transparent")
        flags_frame.grid(row=1, column=0, sticky="ew", padx=20)

        ctk.CTkLabel(flags_frame, text="Flags:").pack(side="left")
        self.wall_var = ctk.BooleanVar(value=True)
        self.wextra_var = ctk.BooleanVar(value=True)
        self.werror_var = ctk.BooleanVar(value=True)

        ctk.CTkCheckBox(flags_frame, text="-Wall", variable=self.wall_var).pack(side="left", padx=10)
        ctk.CTkCheckBox(flags_frame, text="-Wextra", variable=self.wextra_var).pack(side="left", padx=10)
        ctk.CTkCheckBox(flags_frame, text="-Werror", variable=self.werror_var).pack(side="left", padx=10)

        self.check_main_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(flags_frame, text="Check main()", variable=self.check_main_var).pack(side="left", padx=20)

        self.file_label = ctk.CTkLabel(self, text="No files selected", text_color="gray")
        self.file_label.grid(row=2, column=0, sticky="w", padx=20, pady=5)

        self.output = ctk.CTkTextbox(self, font=ctk.CTkFont(family="monospace", size=13))
        self.output.grid(row=3, column=0, sticky="nsew", padx=20, pady=(5, 20))

        self.files: list[str] = []

    def _select_files(self):
        paths = filedialog.askopenfilenames(
            title="Select C files",
            filetypes=[("C files", "*.c"), ("All", "*.*")],
        )
        if paths:
            self.files = list(paths)
            names = ", ".join(Path(f).name for f in self.files[:5])
            self.file_label.configure(text=names)

    def _get_flags(self) -> list[str]:
        flags = []
        if self.wall_var.get():
            flags.append("-Wall")
        if self.wextra_var.get():
            flags.append("-Wextra")
        if self.werror_var.get():
            flags.append("-Werror")
        return flags

    def _compile(self):
        if not self.files:
            return
        self.output.delete("1.0", "end")
        threading.Thread(target=self._run_compile, daemon=True).start()

    def _run_compile(self):
        flags = self._get_flags()
        self._log(f"Compiling with: {' '.join(flags)}\n\n")

        for f in self.files:
            name = Path(f).name

            if self.check_main_var.get():
                source = Path(f).read_text(errors="replace")
                main_check = check_main_commented_or_missing(source)
                if main_check["main_commented"]:
                    self._log(f"WARNING {name}: main() is COMMENTED OUT (line {main_check['main_line']})\n")
                elif not main_check["has_main"]:
                    self._log(f"INFO    {name}: no main() found (library file?)\n")

            result = check_compilation(f, flags)
            if result.success:
                self._log(f"OK      {name}\n")
            else:
                self._log(f"FAIL    {name}\n")
                for err in result.errors:
                    self._log(f"        {err}\n")
                for warn in result.warnings:
                    self._log(f"        {warn}\n")

    def _log(self, text: str):
        self.output.after(0, lambda: self.output.insert("end", text))
