"""Exams frame — browse and practice exam exercises."""

from __future__ import annotations

import customtkinter as ctk

from ...modules.exams.database import (
    EXAM_DATABASE,
    get_exercises_by_rank,
    search_exercises,
)


class ExamsFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header, text="Exam Exercises", font=ctk.CTkFont(size=22, weight="bold")
        ).pack(side="left")

        self.search_entry = ctk.CTkEntry(
            header, placeholder_text="Search exercises...", width=200
        )
        self.search_entry.pack(side="right", padx=5)
        self.search_entry.bind("<Return>", lambda e: self._search())

        ctk.CTkButton(
            header, text="Search", width=80, command=self._search
        ).pack(side="right", padx=5)

        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.grid(row=1, column=0, sticky="ew", padx=20)

        ctk.CTkLabel(filter_frame, text="Rank:").pack(side="left")
        self.rank_var = ctk.StringVar(value="All")
        rank_menu = ctk.CTkOptionMenu(
            filter_frame,
            variable=self.rank_var,
            values=["All", "2", "3", "4", "5", "6"],
            command=lambda _: self._filter(),
            width=80,
        )
        rank_menu.pack(side="left", padx=10)

        ctk.CTkLabel(
            filter_frame,
            text=f"{len(EXAM_DATABASE)} exercises in database",
            text_color="gray",
        ).pack(side="right")

        content = ctk.CTkFrame(self)
        content.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 20))
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        self.exercise_list = ctk.CTkTextbox(content, width=250, font=ctk.CTkFont(size=12))
        self.exercise_list.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.exercise_list.bind("<Button-1>", self._on_list_click)

        self.detail_view = ctk.CTkTextbox(content, font=ctk.CTkFont(family="monospace", size=13))
        self.detail_view.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        self.current_exercises: list = []
        self._filter()

    def _filter(self):
        rank = self.rank_var.get()
        if rank == "All":
            self.current_exercises = EXAM_DATABASE[:]
        else:
            self.current_exercises = get_exercises_by_rank(int(rank))
        self._update_list()

    def _search(self):
        query = self.search_entry.get().strip()
        if query:
            self.current_exercises = search_exercises(query)
        else:
            self._filter()
            return
        self._update_list()

    def _update_list(self):
        self.exercise_list.delete("1.0", "end")
        for i, ex in enumerate(self.current_exercises):
            difficulty = "*" * ex.difficulty
            self.exercise_list.insert("end", f"[R{ex.rank}] {ex.name} {difficulty}\n")

    def _on_list_click(self, event):
        index = self.exercise_list.index(f"@{event.x},{event.y}")
        line = int(index.split(".")[0]) - 1
        if 0 <= line < len(self.current_exercises):
            self._show_detail(self.current_exercises[line])

    def _show_detail(self, ex):
        self.detail_view.delete("1.0", "end")
        text = (
            f"{'='*50}\n"
            f" {ex.name}\n"
            f"{'='*50}\n\n"
            f"Rank:       {ex.rank}\n"
            f"Difficulty: {'*' * ex.difficulty} ({ex.difficulty}/5)\n"
            f"Language:   {ex.language}\n"
            f"Topics:     {', '.join(ex.topics)}\n\n"
            f"--- SUBJECT ---\n\n"
            f"{ex.subject}\n"
        )
        if ex.example_input:
            text += f"\n--- EXAMPLE ---\nInput:  {ex.example_input}\nOutput: {ex.example_output}\n"
        if ex.hints:
            text += f"\n--- HINTS ---\n"
            for hint in ex.hints:
                text += f"  - {hint}\n"
        self.detail_view.insert("1.0", text)
