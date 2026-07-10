"""Dashboard frame — overview of all tools."""

from __future__ import annotations

import customtkinter as ctk


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure(3, weight=1)

        title = ctk.CTkLabel(
            self, text="42 All-in-One", font=ctk.CTkFont(size=28, weight="bold")
        )
        title.grid(row=0, column=0, columnspan=3, pady=(30, 5), sticky="w", padx=30)

        subtitle = ctk.CTkLabel(
            self,
            text="Maximise ta vitesse d'apprentissage",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        subtitle.grid(row=1, column=0, columnspan=3, pady=(0, 30), sticky="w", padx=30)

        cards = [
            ("Norminette", "Auto-format ton code\nCheck + Fix en 1 clic", "norm"),
            ("Compilation", "Verifie -Wall -Wextra -Werror\nDetecte main() manquant", "compiler"),
            ("Repo Check", "Clone ton repo GitHub\nVerifie tout automatiquement", "repo"),
            ("Git / GitHub", "Add + Commit + Push en 1 clic\nLogin auto dans le message", "git"),
            ("Exams", "Base d'exercices rank 02-06\nEntrainement exam", "exams"),
            ("Grade Predictor", "Estime ta note avant\nla soutenance", "predictor"),
        ]

        for i, (title_text, desc, target) in enumerate(cards):
            row = 2 + i // 3
            col = i % 3

            card = ctk.CTkFrame(self, corner_radius=12)
            card.grid(row=row, column=col, padx=15, pady=10, sticky="nsew")

            ctk.CTkLabel(
                card, text=title_text, font=ctk.CTkFont(size=16, weight="bold")
            ).pack(pady=(15, 5), padx=15, anchor="w")

            ctk.CTkLabel(
                card, text=desc, font=ctk.CTkFont(size=12), text_color="gray", justify="left"
            ).pack(pady=(0, 10), padx=15, anchor="w")

            if target:
                ctk.CTkButton(
                    card,
                    text="Ouvrir",
                    width=80,
                    height=28,
                    corner_radius=6,
                    command=lambda t=target: app._show_frame(t),
                ).pack(pady=(0, 15), padx=15, anchor="w")
