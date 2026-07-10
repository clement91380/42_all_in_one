"""Exam Mode frame — timed practice with norminette check only, no automation."""

from __future__ import annotations

import random
import threading
import time
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from ...modules.compiler.checker import check_compilation
from ...modules.exams.database import EXAM_DATABASE, ExamExercise, get_exercises_by_rank
from ...modules.norm import NorminetteFormatter
from ...core.i18n import t


class ExamModeFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.formatter = NorminetteFormatter()

        self.active = False
        self.start_time = 0
        self.timer_job = None
        self.current_exercise: ExamExercise | None = None
        self.hint_count = 0

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_banner()
        self._build_controls()
        self._build_workspace()
        self._build_bottom()

    def _build_banner(self):
        self.banner = ctk.CTkFrame(self, corner_radius=10, fg_color="#1a1a2e")
        self.banner.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 5))

        self.banner_label = ctk.CTkLabel(
            self.banner,
            text=t("exam_mode_title"),
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self.banner_label.pack(side="left", padx=20, pady=12)

        self.timer_label = ctk.CTkLabel(
            self.banner,
            text="00:00",
            font=ctk.CTkFont(family="monospace", size=22, weight="bold"),
            text_color="#00d4ff",
        )
        self.timer_label.pack(side="right", padx=20)

        self.status_dot = ctk.CTkLabel(
            self.banner, text="●", font=ctk.CTkFont(size=18), text_color="gray"
        )
        self.status_dot.pack(side="right", padx=5)

    def _build_controls(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", padx=20, pady=5)

        ctk.CTkLabel(bar, text=t("exam_rank")).pack(side="left")
        self.rank_var = ctk.StringVar(value="2")
        ctk.CTkOptionMenu(
            bar, variable=self.rank_var, values=["2", "3", "4", "5", "6"], width=60
        ).pack(side="left", padx=(4, 20))

        self.start_btn = ctk.CTkButton(
            bar, text=t("exam_start"), width=140, height=34,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#2d7a2d", hover_color="#1e5e1e",
            command=self._toggle_exam,
        )
        self.start_btn.pack(side="left", padx=(0, 8))

        self.pick_btn = ctk.CTkButton(
            bar, text=t("exam_pick"), width=160, height=34,
            state="disabled", command=self._pick_exercise
        )
        self.pick_btn.pack(side="left", padx=4)

        self.hint_btn = ctk.CTkButton(
            bar, text=t("exam_hint"), width=80, height=34,
            state="disabled", fg_color="gray30",
            command=self._show_hint
        )
        self.hint_btn.pack(side="left", padx=4)

    def _build_workspace(self):
        work = ctk.CTkFrame(self)
        work.grid(row=2, column=0, sticky="nsew", padx=20, pady=5)
        work.grid_columnconfigure(0, weight=1)
        work.grid_columnconfigure(1, weight=1)
        work.grid_rowconfigure(1, weight=1)

        # Left: subject
        left = ctk.CTkFrame(work, fg_color="transparent")
        left.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(8, 4), pady=8)
        left.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(left, text="Sujet / Subject",
                     font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w")
        self.subject_box = ctk.CTkTextbox(left, font=ctk.CTkFont(family="monospace", size=13))
        self.subject_box.grid(row=1, column=0, sticky="nsew")

        # Right: your solution file
        right = ctk.CTkFrame(work, fg_color="transparent")
        right.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(4, 8), pady=8)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        top_right = ctk.CTkFrame(right, fg_color="transparent")
        top_right.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(top_right, text="Ton fichier / Your file",
                     font=ctk.CTkFont(weight="bold")).pack(side="left")

        self.file_label = ctk.CTkLabel(top_right, text="", text_color="gray")
        self.file_label.pack(side="left", padx=8)

        ctk.CTkButton(
            top_right, text="Ouvrir / Open", width=120, height=26,
            command=self._open_file
        ).pack(side="right")

        self.check_btn = ctk.CTkButton(
            top_right, text=t("exam_check"), width=150, height=26,
            state="disabled", fg_color="#1a5276",
            command=self._check_file
        )
        self.check_btn.pack(side="right", padx=4)

        self.compile_btn = ctk.CTkButton(
            top_right, text=t("exam_compile"), width=100, height=26,
            state="disabled", fg_color="#1a5276",
            command=self._compile_file
        )
        self.compile_btn.pack(side="right", padx=4)

        self.result_box = ctk.CTkTextbox(
            right, font=ctk.CTkFont(family="monospace", size=12)
        )
        self.result_box.grid(row=1, column=0, sticky="nsew")

        self.current_file: str = ""

    def _build_bottom(self):
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 12))

        self.info_label = ctk.CTkLabel(
            bottom,
            text=t("exam_mode_info"),
            text_color="gray",
            justify="left",
        )
        self.info_label.pack(side="left")

    # ------------------------------------------------------------------

    def _toggle_exam(self):
        if self.active:
            self._stop_exam()
        else:
            self._start_exam()

    def _start_exam(self):
        self.active = True
        self.start_time = time.time()
        self.hint_count = 0

        self.start_btn.configure(
            text=t("exam_stop"), fg_color="#7a2d2d", hover_color="#5e1e1e"
        )
        self.pick_btn.configure(state="normal")
        self.banner_label.configure(text=t("exam_mode_active"), text_color="#ff6b6b")
        self.status_dot.configure(text_color="#00ff88")

        self._tick_timer()

        # Notify app to disable automation features
        self.app.exam_mode = True

    def _stop_exam(self):
        self.active = False
        if self.timer_job:
            self.after_cancel(self.timer_job)

        elapsed = int(time.time() - self.start_time)
        mins, secs = divmod(elapsed, 60)
        self.timer_label.configure(text=f"{mins:02d}:{secs:02d}", text_color="gray")

        self.start_btn.configure(
            text=t("exam_start"), fg_color="#2d7a2d", hover_color="#1e5e1e"
        )
        self.pick_btn.configure(state="disabled")
        self.hint_btn.configure(state="disabled")
        self.check_btn.configure(state="disabled")
        self.compile_btn.configure(state="disabled")
        self.banner_label.configure(text=t("exam_mode_title"), text_color="white")
        self.status_dot.configure(text_color="gray")

        self.app.exam_mode = False

    def _tick_timer(self):
        if not self.active:
            return
        elapsed = int(time.time() - self.start_time)
        mins, secs = divmod(elapsed, 60)
        color = "#ff4444" if elapsed > 3600 else "#ffaa00" if elapsed > 2700 else "#00d4ff"
        self.timer_label.configure(
            text=f"{mins:02d}:{secs:02d}", text_color=color
        )
        self.timer_job = self.after(1000, self._tick_timer)

    def _pick_exercise(self):
        rank = int(self.rank_var.get())
        exercises = get_exercises_by_rank(rank)
        if not exercises:
            return
        self.current_exercise = random.choice(exercises)
        self.hint_count = 0
        self.hint_btn.configure(state="normal")

        self.subject_box.delete("1.0", "end")
        ex = self.current_exercise
        text = (
            f"{'='*46}\n"
            f"  {ex.name}  |  Rank {ex.rank}  |  {'*' * ex.difficulty}\n"
            f"{'='*46}\n\n"
            f"{ex.subject}\n"
        )
        if ex.example_input:
            text += f"\n--- Example ---\nInput:  {ex.example_input}\nOutput: {ex.example_output}\n"
        self.subject_box.insert("1.0", text)
        self.result_box.delete("1.0", "end")

    def _show_hint(self):
        if not self.current_exercise or not self.current_exercise.hints:
            return
        idx = self.hint_count % len(self.current_exercise.hints)
        hint = self.current_exercise.hints[idx]
        self.hint_count += 1
        self.result_box.insert("end", f"[Hint {self.hint_count}] {hint}\n")

    def _open_file(self):
        path = filedialog.askopenfilename(
            title="Select your C file",
            filetypes=[("C files", "*.c"), ("All", "*.*")],
        )
        if path:
            self.current_file = path
            self.file_label.configure(text=Path(path).name)
            self.check_btn.configure(state="normal")
            self.compile_btn.configure(state="normal")

    def _check_file(self):
        if not self.current_file:
            return
        self.result_box.delete("1.0", "end")
        threading.Thread(target=self._run_norm_check, daemon=True).start()

    def _run_norm_check(self):
        try:
            diags = self.formatter.diagnose_file(self.current_file)
            if not diags:
                self._log("Norminette: OK — no errors\n")
            else:
                self._log(f"Norminette: {len(diags)} error(s)\n")
                for d in diags:
                    self._log(f"  L{d.line}:{d.col} [{d.code}] {d.message}\n")
        except RuntimeError as e:
            self._log(f"Error: {e}\n")

    def _compile_file(self):
        if not self.current_file:
            return
        threading.Thread(target=self._run_compile, daemon=True).start()

    def _run_compile(self):
        r = check_compilation(self.current_file, ["-Wall", "-Wextra", "-Werror"])
        if r.success:
            self._log("Compilation: OK\n")
        else:
            self._log(f"Compilation: FAILED\n")
            for e in r.errors:
                self._log(f"  {e}\n")

    def _log(self, text: str):
        self.result_box.after(0, lambda: self.result_box.insert("end", text))
