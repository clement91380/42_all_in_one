"""Repo frame — check a GitHub repository."""

from __future__ import annotations

import threading

import customtkinter as ctk

from ...modules.github.repo_checker import check_repo


class RepoFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header, text="Repo Checker", font=ctk.CTkFont(size=22, weight="bold")
        ).pack(side="left")

        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        input_frame.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            input_frame, placeholder_text="https://github.com/user/repo.git"
        )
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.check_btn = ctk.CTkButton(
            input_frame, text="Check Repo", width=120, command=self._check_repo
        )
        self.check_btn.grid(row=0, column=1)

        self.progress = ctk.CTkProgressBar(self)
        self.progress.grid(row=2, column=0, sticky="ew", padx=20, pady=5)
        self.progress.set(0)

        self.output = ctk.CTkTextbox(self, font=ctk.CTkFont(family="monospace", size=13))
        self.output.grid(row=3, column=0, sticky="nsew", padx=20, pady=(5, 20))

    def _check_repo(self):
        url = self.url_entry.get().strip()
        if not url:
            return

        self.output.delete("1.0", "end")
        self.progress.set(0)
        self.check_btn.configure(state="disabled")
        self._log(f"Cloning {url}...\n")
        threading.Thread(target=self._run_check, args=(url,), daemon=True).start()

    def _run_check(self, url: str):
        self._set_progress(0.2)
        result = check_repo(url)
        self._set_progress(0.8)

        self._log(f"\n{'='*50}\n")
        self._log(f"RESULTS: {url}\n")
        self._log(f"{'='*50}\n\n")

        self._log(f"Files found: {len(result.files_found)}\n")
        self._log(f"C files: {len(result.c_files)}\n")
        self._log(f"H files: {len(result.h_files)}\n")
        self._log(f"Makefile: {'Yes' if result.makefile_found else 'No'}\n\n")

        if result.main_issues:
            self._log("MAIN() ISSUES:\n")
            for issue in result.main_issues:
                self._log(f"  {issue['file']}: {issue['issue']} (line {issue['line']})\n")
            self._log("\n")

        self._log("COMPILATION:\n")
        for comp in result.compilation_results:
            status = "OK" if comp["success"] else "FAIL"
            self._log(f"  [{status}] {comp['file']}\n")
            for err in comp["errors"][:3]:
                self._log(f"       {err}\n")
        self._log("\n")

        if result.issues:
            self._log("ISSUES:\n")
            for issue in result.issues:
                self._log(f"  - {issue}\n")
            self._log("\n")

        if result.warnings:
            self._log("WARNINGS:\n")
            for w in result.warnings:
                self._log(f"  - {w}\n")
            self._log("\n")

        self._log(f"SCORE: {result.score}/100\n")
        self._set_progress(1.0)
        self.check_btn.after(0, lambda: self.check_btn.configure(state="normal"))

    def _log(self, text: str):
        self.output.after(0, lambda: self.output.insert("end", text))

    def _set_progress(self, value: float):
        self.progress.after(0, lambda: self.progress.set(value))
