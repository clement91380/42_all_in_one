"""Predictor frame — estimate project grade."""

from __future__ import annotations

import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from ...modules.compiler.checker import check_compilation, check_main_commented_or_missing
from ...modules.predictor.grade_predictor import (
    PROJECT_CRITERIA,
    detect_project_from_files,
    predict_grade,
)


class PredictorFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header, text="Grade Predictor", font=ctk.CTkFont(size=22, weight="bold")
        ).pack(side="left")

        config_frame = ctk.CTkFrame(self, fg_color="transparent")
        config_frame.grid(row=1, column=0, sticky="ew", padx=20)

        ctk.CTkLabel(config_frame, text="Project:").pack(side="left")
        self.project_var = ctk.StringVar(value="auto-detect")
        projects = ["auto-detect"] + sorted(PROJECT_CRITERIA.keys())
        ctk.CTkOptionMenu(
            config_frame, variable=self.project_var, values=projects, width=150
        ).pack(side="left", padx=10)

        self.select_btn = ctk.CTkButton(
            config_frame, text="Select Project Folder", width=150,
            command=self._select_folder
        )
        self.select_btn.pack(side="left", padx=10)

        self.predict_btn = ctk.CTkButton(
            config_frame, text="Predict Grade", width=120, command=self._predict
        )
        self.predict_btn.pack(side="right", padx=5)

        self.folder_label = ctk.CTkLabel(self, text="No folder selected", text_color="gray")
        self.folder_label.grid(row=2, column=0, sticky="w", padx=20, pady=5)

        results_frame = ctk.CTkFrame(self)
        results_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(5, 20))
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_columnconfigure(1, weight=1)
        results_frame.grid_rowconfigure(1, weight=1)

        self.score_label = ctk.CTkLabel(
            results_frame, text="--", font=ctk.CTkFont(size=48, weight="bold")
        )
        self.score_label.grid(row=0, column=0, pady=20)

        self.confidence_label = ctk.CTkLabel(
            results_frame, text="", text_color="gray"
        )
        self.confidence_label.grid(row=0, column=1, pady=20)

        self.details_output = ctk.CTkTextbox(
            results_frame, font=ctk.CTkFont(family="monospace", size=13)
        )
        self.details_output.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))

        self.folder_path: str = ""

    def _select_folder(self):
        path = filedialog.askdirectory(title="Select Project Folder")
        if path:
            self.folder_path = path
            self.folder_label.configure(text=path)

    def _predict(self):
        if not self.folder_path:
            return
        self.details_output.delete("1.0", "end")
        threading.Thread(target=self._run_prediction, daemon=True).start()

    def _run_prediction(self):
        folder = Path(self.folder_path)
        c_files = list(folder.rglob("*.c"))
        h_files = list(folder.rglob("*.h"))
        all_files = [str(f.relative_to(folder)) for f in c_files + h_files]

        project_name = self.project_var.get()
        if project_name == "auto-detect":
            project_name = detect_project_from_files(all_files)
            self._log(f"Detected project: {project_name}\n\n")

        checks = {}

        self._log("Running checks...\n")

        compile_ok = True
        for c_file in c_files:
            result = check_compilation(str(c_file))
            if not result.success:
                compile_ok = False
                self._log(f"  FAIL compile: {c_file.name}\n")
        checks["compilation"] = compile_ok
        self._log(f"  Compilation: {'PASS' if compile_ok else 'FAIL'}\n")

        main_ok = True
        for c_file in c_files:
            source = c_file.read_text(errors="replace")
            main_check = check_main_commented_or_missing(source)
            if main_check["main_commented"]:
                main_ok = False
                self._log(f"  WARNING: main() commented in {c_file.name}\n")
        if not main_ok:
            self._log("  main() issues detected\n")

        try:
            import subprocess
            norm_ok = True
            for c_file in list(c_files)[:20]:
                r = subprocess.run(
                    ["norminette", str(c_file)],
                    capture_output=True, text=True, timeout=10
                )
                if "Error" in r.stdout:
                    norm_ok = False
                    break
            checks["norminette"] = norm_ok
            self._log(f"  Norminette: {'PASS' if norm_ok else 'FAIL'}\n")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            checks["norminette"] = False
            self._log("  Norminette: SKIP (not installed)\n")

        makefile = folder / "Makefile"
        if makefile.exists():
            checks["makefile"] = True
            self._log("  Makefile: FOUND\n")

        prediction = predict_grade(project_name, checks)

        self._set_score(prediction.estimated_score)
        self._set_confidence(prediction.confidence)

        self._log(f"\n{'='*40}\n")
        self._log(f"PROJECT: {prediction.project_name}\n")
        self._log(f"ESTIMATED SCORE: {prediction.estimated_score}/125\n")
        self._log(f"WOULD PASS: {'YES' if prediction.would_pass else 'NO'}\n")
        self._log(f"CONFIDENCE: {prediction.confidence}\n")
        self._log(f"{'='*40}\n\n")

        self._log("CRITERIA:\n")
        for c in prediction.criteria:
            status = "PASS" if c.passed else "FAIL"
            self._log(f"  [{status}] {c.name} (weight: {c.weight:.0%}) - {c.details}\n")

        if prediction.notes:
            self._log(f"\nNOTES:\n")
            for note in prediction.notes:
                self._log(f"  - {note}\n")

    def _log(self, text: str):
        self.details_output.after(0, lambda: self.details_output.insert("end", text))

    def _set_score(self, score: int):
        color = "green" if score >= 80 else "orange" if score >= 50 else "red"
        self.score_label.after(
            0, lambda: self.score_label.configure(text=f"{score}/125", text_color=color)
        )

    def _set_confidence(self, conf: str):
        self.confidence_label.after(
            0, lambda: self.confidence_label.configure(text=f"Confidence: {conf}")
        )
