"""Predictor frame — estimate project grade with smart compilation handling."""

from __future__ import annotations

import subprocess
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from ...modules.compiler.checker import (
    check_project_compilation,
    analyze_main,
)
from ...modules.predictor.grade_predictor import (
    PROJECT_CRITERIA,
    detect_project_from_files,
    predict_grade,
)
from ...modules.norm import NorminetteFormatter


class PredictorFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.formatter = NorminetteFormatter()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._build_header()
        self._build_config()
        self._build_results()

        self.folder_path: str = ""

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        ctk.CTkLabel(hdr, text="Grade Predictor",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")

        self.predict_btn = ctk.CTkButton(
            hdr, text="Predict Grade", width=130,
            command=self._predict
        )
        self.predict_btn.pack(side="right")

    def _build_config(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", padx=20, pady=4)

        ctk.CTkLabel(bar, text="Project:").pack(side="left")
        self.project_var = ctk.StringVar(value="auto-detect")
        projects = ["auto-detect"] + sorted(PROJECT_CRITERIA.keys())
        ctk.CTkOptionMenu(bar, variable=self.project_var,
                          values=projects, width=150).pack(side="left", padx=8)

        ctk.CTkButton(bar, text="Open Folder", width=120,
                      command=self._select_folder).pack(side="left", padx=8)

        self.folder_label = ctk.CTkLabel(bar, text="No folder selected",
                                          text_color="gray")
        self.folder_label.pack(side="left", padx=8)

    def _build_results(self):
        results = ctk.CTkFrame(self)
        results.grid(row=3, column=0, sticky="nsew", padx=20, pady=(8, 16))
        results.grid_columnconfigure(1, weight=1)
        results.grid_rowconfigure(0, weight=1)

        # Left: score + criteria
        left = ctk.CTkFrame(results, width=220, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        left.grid_propagate(False)

        self.score_label = ctk.CTkLabel(
            left, text="--",
            font=ctk.CTkFont(size=54, weight="bold"),
        )
        self.score_label.pack(pady=(20, 4))

        self.pass_label = ctk.CTkLabel(left, text="", font=ctk.CTkFont(size=14))
        self.pass_label.pack()

        self.confidence_label = ctk.CTkLabel(left, text="",
                                              text_color="gray",
                                              font=ctk.CTkFont(size=11))
        self.confidence_label.pack(pady=(2, 12))

        ctk.CTkLabel(left, text="Criteria:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=8)
        self.criteria_frame = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.criteria_frame.pack(fill="both", expand=True, padx=4)

        # Right: detailed log
        self.log = ctk.CTkTextbox(results, font=ctk.CTkFont(family="monospace", size=12))
        self.log.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)

    # ------------------------------------------------------------------

    def _select_folder(self):
        path = filedialog.askdirectory(title="Select project folder")
        if path:
            self.folder_path = path
            self.folder_label.configure(text=path, text_color="white")

    def _predict(self):
        if not self.folder_path:
            return
        self.log.delete("1.0", "end")
        self.predict_btn.configure(state="disabled", text="Analysing...")
        for w in self.criteria_frame.winfo_children():
            w.destroy()
        threading.Thread(target=self._run_prediction, daemon=True).start()

    def _run_prediction(self):
        folder = Path(self.folder_path)
        c_files = list(folder.rglob("*.c"))
        h_files = list(folder.rglob("*.h"))
        all_names = [f.name for f in c_files + h_files]

        project_name = self.project_var.get()
        if project_name == "auto-detect":
            project_name = detect_project_from_files(all_names)
            self._log(f"Detected project: {project_name}\n\n")

        checks = {}

        # ── 1. Compilation ─────────────────────────────────────────
        self._log("=== Compilation ===\n")
        self._log("(main() handled in memory — original files untouched)\n\n")

        proj_comp = check_project_compilation(folder)

        for r in proj_comp.files:
            name = Path(r.file_path).name
            icon = "OK  " if r.success else "FAIL"
            note = ""
            if r.main_was_commented:
                note = "  [main uncommented in memory]"
            elif r.main_was_injected:
                note = "  [stub main injected in memory]"
            self._log(f"  {icon} {name}{note}\n")
            if not r.success:
                for e in r.errors[:3]:
                    self._log(f"       {e}\n")

        checks["compilation"] = proj_comp.all_passed
        status = "PASS" if proj_comp.all_passed else f"FAIL ({proj_comp.passed}/{proj_comp.total})"
        self._log(f"\n  Result: {status}\n\n")

        # ── 2. main() state (for information, not penalized) ───────
        self._log("=== main() status ===\n")
        for c_file in c_files:
            try:
                source = c_file.read_text(errors="replace")
                info = analyze_main(source)
                if info["has_real_main"]:
                    self._log(f"  {c_file.name}: main() present (line {info['main_line']})\n")
                elif info["main_commented_line"] or info["main_commented_block"]:
                    self._log(f"  {c_file.name}: main() commented (line {info['main_line']}) — correct for submission\n")
                else:
                    self._log(f"  {c_file.name}: no main — library file\n")
            except OSError:
                pass
        self._log("\n")

        # ── 3. Norminette ──────────────────────────────────────────
        self._log("=== Norminette ===\n")
        norm_errors = 0
        norm_ok = True
        try:
            for c_file in list(c_files) + list(h_files):
                try:
                    diags = self.formatter.diagnose_file(str(c_file))
                    norm_errors += len(diags)
                    if diags:
                        norm_ok = False
                        self._log(f"  {c_file.name}: {len(diags)} error(s)\n")
                        for d in diags[:3]:
                            self._log(f"    L{d.line} [{d.code}] {d.message}\n")
                    else:
                        self._log(f"  {c_file.name}: OK\n")
                except RuntimeError:
                    pass
        except Exception:
            norm_ok = False

        checks["norminette"] = norm_ok
        self._log(f"\n  Result: {'PASS' if norm_ok else f'FAIL ({norm_errors} errors)'}\n\n")

        # ── 4. Makefile ────────────────────────────────────────────
        makefile = folder / "Makefile"
        has_makefile = makefile.exists()
        if has_makefile:
            checks["makefile"] = True
            # Check required targets
            mk_content = makefile.read_text(errors="replace")
            for target in ["all", "clean", "fclean", "re"]:
                if re.search(rf"^{target}\s*:", mk_content, re.MULTILINE):
                    checks[f"make_{target}"] = True
            self._log(f"=== Makefile ===\n  Found: {makefile}\n")
            for t in ["all", "clean", "fclean", "re"]:
                self._log(f"  {t}: {'YES' if checks.get(f'make_{t}') else 'NO'}\n")
            self._log("\n")

        # ── 5. Function presence (for libft etc.) ─────────────────
        if project_name == "libft":
            self._log("=== libft functions ===\n")
            required = [
                "ft_isalpha","ft_isdigit","ft_isalnum","ft_isascii","ft_isprint",
                "ft_strlen","ft_memset","ft_bzero","ft_memcpy","ft_memmove",
                "ft_strlcpy","ft_strlcat","ft_toupper","ft_tolower","ft_strchr",
                "ft_strrchr","ft_strncmp","ft_memchr","ft_memcmp","ft_strnstr",
                "ft_atoi","ft_calloc","ft_strdup",
            ]
            bonus = ["ft_lstnew","ft_lstadd_front","ft_lstsize","ft_lstlast",
                     "ft_lstadd_back","ft_lstdelone","ft_lstclear","ft_lstiter","ft_lstmap"]

            found = set()
            for c_file in c_files:
                found.add(c_file.stem)

            missing = [f for f in required if f not in found]
            bonus_found = [f for f in bonus if f in found]

            checks["mandatory_functions"] = len(missing) == 0
            checks["bonus_functions"] = len(bonus_found) > 0

            if missing:
                self._log(f"  Missing mandatory: {', '.join(missing)}\n")
            else:
                self._log(f"  All {len(required)} mandatory functions found\n")
            self._log(f"  Bonus: {len(bonus_found)}/{len(bonus)} ({', '.join(bonus_found) or 'none'})\n\n")

        # ── 6. Predict ─────────────────────────────────────────────
        prediction = predict_grade(project_name, checks)

        def _update_ui():
            color = "#4caf50" if prediction.estimated_score >= 80 else \
                    "#ff9800" if prediction.estimated_score >= 50 else "#f44336"
            self.score_label.configure(
                text=f"{prediction.estimated_score}", text_color=color)
            self.pass_label.configure(
                text="/ 125  PASS" if prediction.would_pass else "/ 125  FAIL",
                text_color=color)
            self.confidence_label.configure(
                text=f"Confidence: {prediction.confidence}")

            for c in prediction.criteria:
                row = ctk.CTkFrame(self.criteria_frame, fg_color="transparent")
                row.pack(fill="x", pady=1)
                dot_color = "#4caf50" if c.passed else "#f44336"
                ctk.CTkLabel(row, text="●", text_color=dot_color,
                              font=ctk.CTkFont(size=11), width=16).pack(side="left")
                ctk.CTkLabel(row, text=f"{c.name}",
                              font=ctk.CTkFont(size=11)).pack(side="left", padx=4)
                ctk.CTkLabel(row, text=f"{c.weight:.0%}",
                              text_color="gray",
                              font=ctk.CTkFont(size=10)).pack(side="right")

            self.predict_btn.configure(state="normal", text="Predict Grade")

        self.after(0, _update_ui)

        self._log(f"{'='*40}\n")
        self._log(f"SCORE: {prediction.estimated_score}/125\n")
        self._log(f"PASS:  {'YES' if prediction.would_pass else 'NO'}\n")
        if prediction.notes:
            self._log("\nNotes:\n")
            for n in prediction.notes:
                self._log(f"  - {n}\n")

    def _log(self, text: str):
        self.log.after(0, lambda: self.log.insert("end", text))


import re
