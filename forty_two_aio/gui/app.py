"""Main GUI application — 42 All-in-One."""

from __future__ import annotations

import customtkinter as ctk

from .frames.dashboard import DashboardFrame
from .frames.norm_frame import NormFrame
from .frames.compiler_frame import CompilerFrame
from .frames.repo_frame import RepoFrame
from .frames.exams_frame import ExamsFrame
from .frames.predictor_frame import PredictorFrame
from ..core.config import Config


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.config = Config.load()

        self.title("42 All-in-One")
        self.geometry("1200x800")
        self.minsize(900, 600)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._create_sidebar()
        self._create_content()

        self._show_frame("dashboard")

    def _create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        logo_label = ctk.CTkLabel(
            self.sidebar,
            text="42 AIO",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        logo_label.pack(pady=(30, 10))

        subtitle = ctk.CTkLabel(
            self.sidebar,
            text="All-in-One Tool",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        subtitle.pack(pady=(0, 30))

        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "Dashboard"),
            ("norm", "Norminette"),
            ("compiler", "Compilation"),
            ("repo", "Repo Check"),
            ("exams", "Exams"),
            ("predictor", "Grade Predictor"),
        ]

        for key, label in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                anchor="w",
                height=40,
                corner_radius=8,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda k=key: self._show_frame(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn

        spacer = ctk.CTkLabel(self.sidebar, text="")
        spacer.pack(expand=True)

        settings_btn = ctk.CTkButton(
            self.sidebar,
            text="Settings",
            anchor="w",
            height=35,
            corner_radius=8,
            fg_color="transparent",
            text_color="gray",
            hover_color=("gray70", "gray30"),
            command=self._open_settings,
        )
        settings_btn.pack(fill="x", padx=10, pady=(0, 20))

    def _create_content(self):
        self.content_frame = ctk.CTkFrame(self, corner_radius=10)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.frames: dict[str, ctk.CTkFrame] = {}

        frame_classes = {
            "dashboard": DashboardFrame,
            "norm": NormFrame,
            "compiler": CompilerFrame,
            "repo": RepoFrame,
            "exams": ExamsFrame,
            "predictor": PredictorFrame,
        }

        for key, frame_class in frame_classes.items():
            frame = frame_class(self.content_frame, self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[key] = frame

    def _show_frame(self, key: str):
        for btn_key, btn in self.nav_buttons.items():
            if btn_key == key:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")

        self.frames[key].tkraise()

    def _open_settings(self):
        SettingsWindow(self)


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent: App):
        super().__init__(parent)
        self.parent_app = parent
        self.title("Settings")
        self.geometry("500x400")

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Settings", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, pady=20
        )

        form = ctk.CTkFrame(self)
        form.grid(row=1, column=0, sticky="ew", padx=20)
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="GitHub Username:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.github_user = ctk.CTkEntry(form)
        self.github_user.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        self.github_user.insert(0, parent.config.github_username)

        ctk.CTkLabel(form, text="42 Login:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.intra_login = ctk.CTkEntry(form)
        self.intra_login.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        self.intra_login.insert(0, parent.config.intra_login)

        ctk.CTkLabel(form, text="Theme:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.theme_var = ctk.StringVar(value=parent.config.theme)
        theme_menu = ctk.CTkOptionMenu(form, variable=self.theme_var, values=["dark", "light", "system"])
        theme_menu.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

        save_btn = ctk.CTkButton(self, text="Save", command=self._save)
        save_btn.grid(row=2, column=0, pady=20)

    def _save(self):
        self.parent_app.config.github_username = self.github_user.get()
        self.parent_app.config.intra_login = self.intra_login.get()
        self.parent_app.config.theme = self.theme_var.get()
        self.parent_app.config.save()
        ctk.set_appearance_mode(self.theme_var.get())
        self.destroy()


def run():
    app = App()
    app.mainloop()
